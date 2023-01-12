#!/usr/bin/python3
# -*- coding: utf-8 -*-

from email import message
from operator import mod
import time
import ipfshttpclient
from ipfshttpclient.exceptions import StatusError
from ipfshttpclient.client.base import ResponseBase
import ntpath
import urllib.parse
import psutil
import sys
import socket
import re
from datetime import datetime

from web3 import Web3
from eth_account import Account
from web3.middleware import geth_poa_middleware

from web3.exceptions import TimeExhausted, ContractLogicError
from config import os, parser, arguments, bcolors
from typing import Union
from multiprocessing import Pool, Lock
from functools import partial
from models import OrderStatus
import signal

MAXIMUM_NUMBER_OF_MINUTES = 2
MAXIMUM_NUMBER_OF_NODES = 100

# for background processes
def signal_handler(signal, frame):
    EtnyPoXClient.log('\nYou pressed Ctrl+C, keyboardInterrupt detected!')
    sys.exit() 
signal.signal(signal.SIGINT, signal_handler)

class CustomLock:
    def __new__(cls, lock) -> None:
        cls.lock = lock

    @classmethod
    def acquire(cls):
        try:
            cls.lock.acquire()
        except:pass

    @classmethod
    def release(cls):
        try:
            cls.lock.release()
        except:pass
        
class EtnyPoXClient:
    # class variables

    __etny = None
    __acct = None
    __w3 = None
    __contract_abi = None
    __ipfsnode = None
    __dohash = 0


    _address = None
    _private_key = None
    _dorequest = 0
    _dohash = 0
    _ipfsgateway = None
    _ipfshash = None
    _ipfsuser = None
    _ipfspassword = None
    _client = None
    _scripthash = None
    _filesethash = None
    _bandwidth = None
    _contract_address = None
    _redistribute = None
    _web3_provider = None
    _ipfs_cloud = None
    _node = ""

    _nodes = None
    

    def __init__(self):
        try:
            # read abi
            self._readABI()

            # get arguments from command line or from config (.env, .env.config) files
            self._parse_args(parser = parser, arguments=arguments)
    
            # connect to ipfs
            self._connect_ipfs_gateway()

            # do request
            try:
                nodes = self._node_addreses
                if nodes:
                    started_at = time.time()
                    lock = Lock()
                    nodes_count = len(nodes)
                    with Pool(nodes_count, initializer=CustomLock, initargs=(lock,)) as p:
                        p.map(partial(self._add_do_request, nodes_count = nodes_count), nodes)
                    print('----------')
                    print(f'Total time spent: {self.__display_date(int(time.time() - started_at))}')
                else:
                    self._add_do_request(node = self._node)
            except ValueError as e:
                raise Exception(e)
        except Exception as e:
            self.log(message = str(e), mode='error')

    @property
    def __get_ipfs_address(self) -> str:
        url = 'http://127.0.0.1:5001' if not self._ipfsgateway else self._ipfsgateway
        addr = urllib.parse.urlsplit(url)
        return '/'.join(['/dns', addr.hostname, 'tcp', str(addr.port), addr.scheme])

    @property
    def __get_ipfs_executable_path(self) -> str:
        return os.path.join('.tmp', 'go-ipfs', 'ipfs')

    @property
    def __get_nonce(self):
        return self.__w3.eth.get_transaction_count(self._address)

    @property
    def __transaction_object(self) -> object:
        return  {
            'gas': 1000000,
            'chainId': 8995,
            'nonce': self.__get_nonce,
            'gasPrice': self.__w3.toWei("1", "mwei"),
        }

    @property
    def _node_addreses(self):
        try:
            if not self._node:
                raise Exception('empty!')
            nodes = self._node
            if not self.__is_address(nodes, display_error = False):
                self._node = ''
                if not os.path.exists(nodes):
                    raise Exception(f"The file named {nodes}, containing node addresses does not exist!")
                with open(nodes) as r:
                    nodes = list(set(x.strip()[:-1] if x.strip().endswith(',') else x.strip() for x in r.read().splitlines() if not x.startswith("#") and self.__is_address(x)))[:MAXIMUM_NUMBER_OF_NODES]
                    print('nodes = ')
                    print(nodes)
                    print('nodes = ')
            elif ',' in nodes:
                nodes = list(set(x.strip()[:-1] if x.strip().endswith(',') else x.strip() for x in nodes.split(',') if  not x.startswith("#") and self.__is_address(x)))[:MAXIMUM_NUMBER_OF_NODES]
            else:
                raise Exception('')
            if len(nodes) > 1:
                return nodes
            else:
                self._node = nodes[0]
        except Exception as e:
            pass

        return None

    @property
    def _getDoRequestCount(self):
        return self.__etny.caller()._getDORequestsCount()

    @property
    def __get_current_date(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _readABI(self) -> None:
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/pox.abi') as f:
                self.__contract_abi = f.read()
        except FileNotFoundError as e:
            self.log(e, 'ERROR')

    def _parse_args(self, parser, arguments) -> None:
        parser = parser.parse_args()
        for args_type, args in arguments.items():
            for arg in args:
                value = args_type(getattr(parser, arg))
                value = os.environ.get(arg.upper()) if value in ['None', None] and os.environ.get(arg.upper()) else value
                setattr(self, f"_{arg}", value)
        self.__local = self._ipfsgateway == ""

    def _baseConfigs(self) -> None:
        self.__w3 = Web3(Web3.HTTPProvider(self._web3_provider)) 
        self.__w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.__acct = Account.privateKeyToAccount(self._private_key)
        self.__etny = self.__w3.eth.contract(address=self.__w3.toChecksumAddress(self._contract_address), abi=self.__contract_abi)

    def _connect_ipfs_gateway(self) -> None:
        while True:
            try:
                auth = None if not self._ipfsuser and not self._ipfspassword else (self._ipfsuser, self._ipfspassword)
                self.__client = ipfshttpclient.connect(self.__get_ipfs_address, auth=auth)
                if self.__local:
                    self.__ipfsnode = socket.gethostbyname(self._ipfs_cloud) 
                    self.__client.bootstrap.add(f'/ip4/{self.__ipfsnode}/tcp/4001/ipfs/{self._ipfshash}')
                break
            except Exception as e:
                self.log(e, 'warning')
                self.__sys_stdout(char='/')
                time.sleep(2)
                self.__restart_ipfs()
                
    def _add_do_request(self, node = '', nodes_count = 0) -> None:
        

        started_at = time.time()
        self._baseConfigs()
        self.log(f"{self.__get_current_date} - Sending payload to IPFS...", 'message')

        self._scripthash = self.__upload_ipfs(self._script)
        self._filesethash = self.__upload_ipfs(self._fileset, True)
        
        if ':' not in self._image:
            self._image += ':etny-pynithy'

        if not nodes_count and len(node) and self.__is_address(node):
            nodes_count = 1

        _params = [
            self._cpu, 
            self._memory, 
            self._storage, 
            self._bandwidth,
            self._duration, 
            self._instances, 
            0,
            self._image, 
            self._scripthash, 
            self._filesethash, 
            node
        ]

        # lock initialization (works only for multiple nodes, will be ignored in case single node)
        CustomLock.acquire()
        
        node_address = None
        _count = self._getDoRequestCount
        transaction_object = self.__transaction_object
        unicorn_txn = self.__etny.functions._addDORequest(*_params).buildTransaction(transaction_object)
        signed_txn = self.__w3.eth.account.sign_transaction(unicorn_txn, private_key=self.__acct.key)
        self.__w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        if nodes_count: 
            node_address = node
            while _count == self._getDoRequestCount or transaction_object['nonce'] == self.__get_nonce:
                time.sleep(.1)
            # release the lock
            CustomLock.release()
            
        transactionhash = self.__w3.toHex(self.__w3.sha3(signed_txn.rawTransaction))
       
        self.log(str(self.__get_current_date)+" - Submitting transaction for DO request", 'message')
        self.log(f"{self.__get_current_date} - TX Hash: {transactionhash}", 'message')

        self.__rPrintOutput(message = ('-' * 10), repeats_count=1)
        self.log(f"Public IPFS Image: {self._image.split(':')[0]}")
        self.log(f"Public Script: {self._scripthash}")
        self.log(f"Public Fileset: {self._filesethash}")
        self.__rPrintOutput(message = ('-' * 10), repeats_count=1)

        receipt = None
        do_request = None
        for i in range(100):
            try:
                receipt = self.__w3.eth.wait_for_transaction_receipt(transactionhash)
                processed_logs = self.__etny.events._addDORequestEV().processReceipt(receipt)
                do_request = processed_logs[0].args._rowNumber
            except KeyError:
                time.sleep(1)
                continue
            except Exception as e:
                print(e)
                raise
            else:
                self.log(f"{self.__get_current_date} - Request {do_request} created successfuly!", 'message')
                self.__dohash = transactionhash
                break

        if receipt is None:
            self.log(f"{self.__get_current_date} - Unable to create request, please check conectivity with bloxberg node", 'error')

        # main loop
        self._wait_for_processor(
            do_request=do_request,
            node_address = node_address,
            started_at = started_at,
            nodes_count = nodes_count
        )

    def _wait_for_processor(self, do_request, node_address, started_at: int, nodes_count: int) -> None:
        self.log(str(self.__get_current_date)+ f" - Waiting for Ethernity network...", "message")
        order = None
        while True:
            try:
                order = self.__find_order(do_request, nodes_count)
                if order == None and (time.time() - started_at) > (60 * MAXIMUM_NUMBER_OF_MINUTES):
                    node_info = f'from the node "{node_address}" is ' if node_address else ''
                    return self.log(f'\nAnswer {node_info}not received in {MAXIMUM_NUMBER_OF_MINUTES} minutes.', 'error', hide_prefix=True, force_exit=False)                    
            except Exception as e:
                print('--------', str(e), type(e))
            if order is not None:
                self.log(f"{self.__get_current_date} - Connected!", "info")

                if nodes_count == 0 and self.__approve_order(order):
                    break

                if self._redistribute is True and self.__local:
                    self.log(f"{self.__get_current_date} - Checking IPFS payload distribution...", "message")
                    scripthash = self.__check_ipfs_upload(self.__script)
                    filesethash = self.__check_ipfs_upload(self.__fileset, True)
                    if scripthash is not None and filesethash is not None:
                        self.log(f"{self.__get_current_date} - IPFS payload distribution confirmed!", "info")
                if self.__get_result_from_order(order, node_address, started_at):
                    break
            else:
                time.sleep(5)   
    
    def __find_order(self, doreq, nodes_count: int) -> Union[int, None]:
        self.__sys_stdout(char='.')
        count = self.__etny.functions._getOrdersCount().call()
        status = OrderStatus.PROCESSING if nodes_count > 0 else OrderStatus.OPEN
        for i in range(count - 1, (count - 5 - (nodes_count)), -1):
            order = self.__etny.caller()._getOrder(i)
            if order[2] == doreq and order[4] == status:
                return i
        return None

    def __approve_order(self, order) -> bool:
        unicorn_txn = self.__etny.functions._approveOrder(order).buildTransaction(self.__transaction_object)

        signed_txn = self.__w3.eth.account.sign_transaction(unicorn_txn, private_key=self.__acct.key)
        self.__w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        transactionhash = self.__w3.toHex(self.__w3.sha3(signed_txn.rawTransaction))

        receipt = None
        for i in range(100):
            try:
                receipt = self.__w3.eth.wait_for_transaction_receipt(transactionhash)
            except KeyError:
                time.sleep(1)
                continue
            except TimeExhausted:
                raise
            except Exception as e:
                print('erorr = ', e)
                raise
            else:
                self.log(f"{datetime.now()} - Order {order} approved successfuly!" , 'info')
                self.log(f"{datetime.now()} - TX Hash: {transactionhash}", 'message')
                break

        if receipt is None:
            self.log(f"{datetime.now()} - Unable to approve order, please check connectivity with bloxberg node", "warning")
            return True
        return False

    def __get_result_from_order(self, order, node_address, started_at: int) -> bool:
        try:
            self.log(f"{self.__get_current_date} - Waiting for task to finish...", "message")
        except Exception as e:
            print('----|----', str(e))

        while True:
            result = 0
            _iter = 0
            try:
                self.__etny.caller()._getOrder(order)
                result = self.__etny.caller(transaction={'from': self._address})._getResultFromOrder(order)
            except Exception as e:
                if type(e) != ContractLogicError:
                    print(e, type(e), '-1')
                self.__sys_stdout()
                time.sleep(5)
                continue
            else:
                self.__rPrintOutput(message = '', repeats_count=1)
                self.log(f"{self.__get_current_date} - Found result hash: {result}", 'info')
                self.log(f"{self.__get_current_date} - Fetching result from IPFS...", 'message')

                try_count = 0
                while True:
                    try:
                        self.__client.get(result)
                    except Exception as e:
                        print(e, type(e), '-2')
                        self.__sys_stdout()
                        time.sleep(1)
                        
                        if try_count > 5:
                            return self.log('can`t download ipfs Image', 'error')
                        try_count += 1

                        continue
                    else:
                        break

                file = os.path.dirname(os.path.realpath(__file__)) + '/../' + result
                with open(file) as f:
                    content = f.read()
                os.unlink(file)

                self.__rPrintOutput(message = '', repeats_count=1)
                self.log(f"{self.__get_current_date} - Certificate information is shown below this line", 'underline')
                self.__rPrintOutput(message = '')

                blocktimestamp, blockdatetime, endblocknumber, startblocknumber = self.__get_block_details()

                resulttransactionhash = None
                resultblocktimestamp = None
                resultblockdatetime = None
                for i in range(endblocknumber, startblocknumber, -1):
                    block = self.__w3.eth.get_block(i, True)
                    if block is not None and block.transactions is not None:
                        transactions = block["transactions"]
                        for transaction in transactions:
                            if transaction["to"] == self._contract_address:
                                transactioninput = self.__etny.decode_function_input(transaction.input)
                                function = transactioninput[0]
                                params = transactioninput[1]
                                if "_addResultToOrder" in function.fn_name and params['_orderItem'] == order:
                                    # resulthash = params['_result']
                                    resulttransactionhash = transaction['hash']
                                    # resultblock = self.__w3.eth.getBlock(transaction['blockNumber'])
                                    resultblocktimestamp = (block['timestamp'])
                                    resultblockdatetime = datetime.fromtimestamp(resultblocktimestamp)

                print()
                cert_result = ""
                try:
                    cert_result += self.__pre_suf(multiply=109, new_line=True)
                    cert_result += f"{self.__pre_suf(multiply=41)} bloxberg PoX certificate {self.__pre_suf(multiply=42, new_line=True)}"
                    cert_result += self.__pre_suf(multiply=109, new_line=True)
                    cert_result += f"{self.__pre_suf()}{self.__pre_suf(char=' ', multiply=97)}{self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [INFO] contract address: {self._contract_address} {self.__pre_suf(char=' ', multiply=27)}{self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [INFO] input transaction: {self.__dohash}   {self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [INFO] output transaction: {resulttransactionhash.hex()}  {self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [INFO] PoX processing order: {str(order).zfill(16)}{self.__pre_suf(char=' ', multiply=50)}{self.__pre_suf(new_line=True)}"
                    if node_address:
                        cert_result += f"{self.__pre_suf()}  [INFO] Node Address: {str(node_address)}{self.__pre_suf(char=' ', multiply=32)}{self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  {self.__pre_suf(char=' ', multiply=94)} {self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [INPUT] public image: {self._image}{self.__pre_suf(char=' ', multiply=14)}{self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [INPUT] public script: {self._scripthash}{self.__pre_suf(char=' ', multiply=26)}{self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [INPUT] public fileset: {self._filesethash}{self.__pre_suf(char=' ', multiply=25)}{self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [INPUT] timestamp: {str(blockdatetime)} [{str(blocktimestamp)}]{self.__pre_suf(char=' ', multiply=44)}{self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [OUTPUT] public result: {result} {self.__pre_suf(char=' ', multiply=24)}{self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}  [OUTPUT] timestamp: {str(resultblockdatetime)} [{str(resultblocktimestamp)}] {self.__pre_suf(char=' ', multiply=42)}{self.__pre_suf(new_line=True)}"
                    cert_result += f"{self.__pre_suf()}{self.__pre_suf(char=' ', multiply=97)}{self.__pre_suf(new_line=True)}"
                    cert_result += self.__pre_suf(multiply=109, new_line=True)
                    cert_result += self.__pre_suf(multiply=109, new_line=True)
                    cert_result += self.__pre_suf(multiply=109, new_line=True)
                finally:
                    self.__write_to_cert(self.__dohash, cert_result)

                self.__rPrintOutput(message = '')
                if node_address:
                    self.log(f"{self.__get_current_date} - Node Address: {node_address}", 'bold')

                with open('results.txt', 'a') as w:
                    w.write(f"{self.__get_current_date} - {node_address} - {self.__display_date(int(time.time() - started_at))}\n")
                
                self.log(f"The Task took: {self.__display_date(int(time.time() - started_at))} to complete!")
                self.log(f"{self.__get_current_date} - Actual result of the processing is printed below this line", 'underline')
                self.__rPrintOutput(message = '')

                # result
                self.log(content, 'bold')
                # result

                if node_address:
                    self.__rPrintOutput(message=('-' * 10), repeats_count=1)
                    
                return True

    def __get_ipfs_output_file_path(self, file) -> str:
        if not os.path.isdir(os.path.join('.tmp')):
            os.mkdir(os.path.join('.tmp'))
        return os.path.join('.tmp', file)

    def __restart_ipfs(self) -> None:
        if self.__local:
            for proc in psutil.process_iter():
                if proc.name() == "ipfs.exe":
                    proc.kill()
                if proc.name() == "ipfs":
                    proc.kill()
            cmd = 'start /B "" "%s" daemon > %s' % (self.__get_ipfs_executable_path, self.__get_ipfs_output_file_path('ipfsoutput.txt'))
            print(cmd)
            os.system(cmd)
        return None

    @staticmethod
    def log(message = '', mode = '_end', hide_prefix = False, force_exit = True) -> None:
        mode = str(mode.upper() if type(mode) == str else bcolors[mode].name)
        prefix = f"{bcolors[mode].value}{bcolors.BOLD.value}{bcolors[mode].name}{bcolors._END.value}: " if mode not in ['_END', 'BOLD', 'UNDERLINE'] and not hide_prefix else ""
        print(f"{prefix}{bcolors[mode].value}{str(message)}{bcolors._END.value}")
        if mode == 'ERROR' and force_exit: sys.exit()

    def __upload_ipfs(self, file, recursive=False) -> str:
        while True:
            try:
                if self.__local and self.__ipfsnode is not None:  # hasattr(self, 'ipfsnode'):
                    self.__ipfs_swarm_connect()
            except Exception as e:
                self.__sys_stdout(char='*')
                continue
            res = self.__add_to_ipfs(file, recursive)
            if isinstance(res, list):
                for item in res:
                    if item['Name'] == ntpath.basename(file):
                        return item['Hash']
            else:
                return res['Hash']
    
    def __add_to_ipfs(self, file, recursive=False) -> Union[ResponseBase, list, None]:
        while True:
            try:
                return self.__client.add(file, recursive=recursive)
            except Exception as e:
                time.sleep(1)
                continue
            except StatusError:
                self.log("You have reached request limit, please wait or try again later", 'warning')
                time.sleep(60)
                continue

    def __rPrintOutput(self, message, repeats_count = 2) -> str:
        [print(message) for x in range(repeats_count)]

    def __sys_stdout(self, char = '.') -> None:
        sys.stdout.write(char)
        sys.stdout.flush()

    def __pre_suf(self, char = "#", multiply = 6, new_line = False) -> str:
        result = (char * multiply) 
        return f"{result}\n" if new_line else result

    def __get_block_details(self) -> list:
        transaction = self.__w3.eth.get_transaction(self.__dohash)
        block = self.__w3.eth.get_block(transaction['blockNumber'])
        blocktimestamp = (block['timestamp'])
        blockdatetime = datetime.fromtimestamp(blocktimestamp)
        endblocknumber = self.__w3.eth.block_number
        startblocknumber = endblocknumber - 20

        return [blocktimestamp, blockdatetime, endblocknumber, startblocknumber]

    def __write_to_cert(self, dohash, text) -> None:
        with open('certs/' + dohash, 'a+') as r:
            r.write(text + '\n')
        print(text)
                
    def __check_ipfs_upload(self, file, recursive=False) -> None:
        if self.__local:
            while True:
                res = self.__add_to_ipfs(file, recursive)
                self.__sys_stdout()

                if isinstance(res, list):
                    for item in res:
                        return self.__process_ipfs_result(item)
                else:
                    return self.__process_ipfs_result(res)

                self.__sys_stdout(char='*')

                self.__restart_ipfs()
        return None

    def __process_ipfs_result(self, resultitem) -> None:
        retries = 0
        while retries < 3:
            try:
                self.__ipfs_swarm_connect()
                time.sleep(1)
                for dht in self.__client.dht.findprovs(resultitem['Hash'], timeout=10):
                    if dht['Responses'] is not None:
                        for response in dht['Responses']:
                            if response['ID'] == self._ipfshash:
                                self.__sys_stdout(char='#')
                                return resultitem['Hash']
            except Exception as e:
                pass
            self.__sys_stdout()
            retries += 1

    def __ipfs_swarm_connect(self, log = False) -> None:
        cmd = "%s swarm connect /ip4/%s/tcp/4001/ipfs/%s > %s" % (
                    self.__get_ipfs_executable_path, 
                    self.__ipfsnode,
                    self._ipfshash,
                    self.__get_ipfs_output_file_path('ipfsconnect.txt'))
        if log: print(cmd)
        os.system(cmd)

    def __is_address(self, address, display_error = True):
        if address.strip().endswith(','):
            address = address[:-1]
        result = re.match(r'^(0x)?[0-9a-f]{40}$', address.lower())
        if display_error and not result:
            self.log(f' Address "{address}" is invalid, skipping.', 'warning')
        return bool(result)

    @staticmethod
    def __display_date(seconds):
        try:
            h = [str(seconds//3600), 'hours']
            m = [str((seconds%3600)//60), 'minutes']
            s = [str((seconds%3600)%60), 'seconds']
            return ", ".join([" ".join(i) for i in [h, m, s] if int(i[0])])
        except: 
            return 0
        

if __name__ == '__main__':
    print('-' * 20)
    app = EtnyPoXClient()
