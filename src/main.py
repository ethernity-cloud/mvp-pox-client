#!/usr/bin/python3
# -*- coding: utf-8 -*-

from email import message
import time
import ipfshttpclient
from ipfshttpclient.exceptions import StatusError
import ntpath
import urllib.parse
import psutil
import sys
import socket
from datetime import datetime

from web3 import Web3
from eth_account import Account
from web3.middleware import geth_poa_middleware

from web3.exceptions import TimeExhausted, ContractLogicError
from config import os, parser, arguments, bcolors

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
    _node = ""

    def __init__(self):

        # read abi
        self._readABI()

        # get arguments from command line or from config (.env, .env.config) files
        self.parse_args(parser = parser, arguments=arguments)
    
        # base configs
        self._baseConfigs()

        # connect to ipfs
        self.__connect_ipfs_gateway()

        # do request
        self.add_do_request()

        # main loop
        self.wait_for_processor()

    @property
    def __get_ipfs_address(self):
        url = 'http://127.0.0.1:5001' if not self._ipfsgateway else self._ipfsgateway
        addr = urllib.parse.urlsplit(url)
        return '/'.join(['/dns', addr.hostname, 'tcp', str(addr.port), addr.scheme])

    @property
    def __get_ipfs_executable_path(self):
        return os.path.join('.tmp', 'go-ipfs', 'ipfs')

    def __get_ipfs_output_file_path(self, file):
        if not os.path.isdir(os.path.join('.tmp')):
            os.mkdir(os.path.join('.tmp'))
        return os.path.join('.tmp', file)

    def __restart_ipfs(self):
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
        
    def _baseConfigs(self):
        self.__w3 = Web3(Web3.HTTPProvider("https://bloxberg.ethernity.cloud"))
        self.__w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.__acct = Account.privateKeyToAccount(self._private_key)
        self.__etny = self.__w3.eth.contract(address=self.__w3.toChecksumAddress(self._contract_address), abi=self.__contract_abi)

    def _log(self, message = '', mode = '_end'):
        mode = str(mode.upper() if type(mode) == str else bcolors[mode].name)
        prefix = f"{bcolors[mode].value}{bcolors.BOLD.value}{bcolors[mode].name}{bcolors._END.value}: " if mode not in ['_END', 'BOLD', 'UNDERLINE'] else ""
        print(f"{prefix}{bcolors[mode].value}{str(message)}{bcolors._END.value}")

    def _readABI(self):
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/pox.abi') as f:
                self.__contract_abi = f.read()
        except FileNotFoundError as e:
            self._log(e, 'ERROR')

    def parse_args(self, parser, arguments):
        parser = parser.parse_args()
        for args_type, args in arguments.items():
            for arg in args:
                value = args_type(getattr(parser, arg))
                value = os.environ.get(arg.upper()) if value in ['None', None] and os.environ.get(arg.upper()) else value
                setattr(self, f"_{arg}", value)
        self.__local = self._ipfsgateway == ""
        self._log('contract_address = '+str(self._contract_address), "message")

    def __connect_ipfs_gateway(self):
        while True:
            try:
                auth = None if not self._ipfsuser and not self._ipfspassword else (self._ipfsuser, self._ipfspassword)
                self.__client = ipfshttpclient.connect(self.__get_ipfs_address, auth=auth)
                if self.__local:
                    self.__ipfsnode = socket.gethostbyname('ipfs.ethernity.cloud')
                    self.__client.bootstrap.add(f'/ip4/{self.__ipfsnode}/tcp/4001/ipfs/{self._ipfshash}')
                break
            except Exception as e:
                self._log(e, 'error')
                sys.stdout.write('/')
                sys.stdout.flush()
                time.sleep(2)
                self.__restart_ipfs()
                

    def __upload_ipfs(self, file, recursive=False):
        while True:
            try:
                if self.__local and self.__ipfsnode is not None:  # hasattr(self, 'ipfsnode'):
                    cmd = "%s swarm connect /ip4/%s/tcp/4001/ipfs/%s > %s" % (
                              self.__get_ipfs_executable_path, 
                              self.__ipfsnode,
                              self._ipfshash,
                              self.__get_ipfs_output_file_path('ipfsconnect.txt'))
                    os.system(cmd)
            except Exception as e:
                sys.stdout.write('*')
                sys.stdout.flush()
                continue
            res = self.__add_to_ipfs(file, recursive)

            if isinstance(res, list):
                for item in res:
                    if item['Name'] == ntpath.basename(file):
                        return item['Hash']
            else:
                return res['Hash']
    
    def __add_to_ipfs(self, file, recursive=False):
        while True:
            try:
                return self.__client.add(file, recursive=recursive)
            except Exception:
                time.sleep(1)
                continue
            except StatusError:
                self._log("You have reached request limit, please wait or try again later", 'error')
                time.sleep(60)
                continue

    def add_do_request(self):
        nonce = self.__w3.eth.get_transaction_count(self._address)

        self._log(str(datetime.now())+ " - Sending payload to IPFS...", 'message')

        self._scripthash = self.__upload_ipfs(self._script)
        self._log('self._scripthash = '+str(self._scripthash), 'bold')
        self._filesethash = self.__upload_ipfs(self._fileset, True)
        self._log('self._filesethash = '+str(self._filesethash), 'bold')

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
            self._node
        ]
        print(_params)
        unicorn_txn = self.__etny.functions._addDORequest(*_params).buildTransaction({
            'gas': 1000000,
            'chainId': 8995,
            'nonce': nonce,
            'gasPrice': self.__w3.toWei("1", "mwei"),
        })
        signed_txn = self.__w3.eth.account.sign_transaction(unicorn_txn, private_key=self.__acct.key)
        self.__w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        transactionhash = self.__w3.toHex(self.__w3.sha3(signed_txn.rawTransaction))
       
        self._log(str(datetime.now())+" - Submitting transaction for DO request", 'message')
        receipt = None
        for i in range(100):
            try:
                receipt = self.__w3.eth.wait_for_transaction_receipt(transactionhash)
                processed_logs = self.__etny.events._addDORequestEV().processReceipt(receipt)
                self.__dorequest = processed_logs[0].args._rowNumber
            except KeyError:
                time.sleep(1)
                continue
            except Exception as e:
                print(e)
                raise
            else:
                self._log(str(datetime.now())+ " - Request %s created successfuly!" % self.__dorequest, 'message')
                self._log(str(datetime.now())+ (f" - TX Hash 1: {transactionhash}, address: {self._address} "), 'bold')
                self.__dohash = transactionhash
                break

        if receipt is None:
            self._log(str(datetime.now())+ " - Unable to create request, please check conectivity with bloxberg node", 'warning')
            sys.exit()


    def wait_for_processor(self):
        self._log(str(datetime.now())+ f" - Waiting for Ethernity network... {str(self.__dorequest)}", "message")
        while True:
            try:
                order = self.find_order(self.__dorequest)
            except Exception as e:
                print('--------', str(e))
            if order is not None:
                print("")
                self._log(str(datetime.now())+ " - Connected!", "info")
                self.approve_order(order)

                if self._redistribute is True and self.__local:
                    self._log(str(datetime.now())+ " - Checking IPFS payload distribution...", "message")
                    scripthash = self.__check_ipfs_upload(self.__script)
                    filesethash = self.__check_ipfs_upload(self.__fileset, True)
                    if scripthash is not None and filesethash is not None:
                        self._log(str(datetime.now())+ " - IPFS payload distribution confirmed!", "info")
                self.get_result_from_order(order)
            else:
                time.sleep(5)
    
    def find_order(self, doreq):
        sys.stdout.write('.')
        sys.stdout.flush()
        count = self.__etny.functions._getOrdersCount().call()
        for i in range(count - 1, count - 5, -1):
            order = self.__etny.caller()._getOrder(i)
            if order[2] == doreq and order[4] == 0:
                return i
        return None


    def approve_order(self, order):
        nonce = self.__w3.eth.get_transaction_count(self._address)

        unicorn_txn = self.__etny.functions._approveOrder(order).buildTransaction({
            'gas': 1000000,
            'chainId': 8995,
            'nonce': nonce,
            'gasPrice': self.__w3.toWei("1", "mwei"),
        })

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
                self._log(str(datetime.now())+ " - Order %s approved successfuly!" % order, 'info')
                self._log(str(datetime.now())+ " - TX Hash 2: %s" % transactionhash, 'message')
                break

        if receipt is None:
            self._log(str(datetime.now())+ " - Unable to approve order, please check connectivity with bloxberg node", "warning")
            sys.exit()

    def rPrintOutput(self, message, repeats_count = 2):
        [print(message) for x in range(repeats_count)]

    def get_result_from_order(self, order):
        try:
            self._log(str(datetime.now())+ " - Waiting for task to finish...", "message")
            self._log('order_id = '+str(order), "message")
        except Exception as e:
            print('----|----', str(e))

        while True:
            result = 0
            try:
                orderInfo = self.__etny.caller()._getOrder(order)
                print(orderInfo)
                result = self.__etny.caller(transaction={'from': self._address})._getResultFromOrder(order)
            except Exception as e:
                if type(e) != ContractLogicError:
                    print(e, type(e), '-1')
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(5)
                continue
            else:
                self.rPrintOutput(message = '', repeats_count=1)
                self._log(str(datetime.now())+ " - Found result hash: %s" % result, 'info')
                self._log(str(datetime.now())+ " - Fetching result from IPFS...", 'message')

                while True:
                    try:
                        self.__client.get(result)
                    except Exception:
                        print(e, type(e), '-2')
                        sys.stdout.write('.')
                        sys.stdout.flush()
                        time.sleep(1)
                        continue
                    else:
                        break

                file = os.path.dirname(os.path.realpath(__file__)) + '/../' + result
                with open(file) as f:
                    content = f.read()
                os.unlink(file)

                self.rPrintOutput(message = '', repeats_count=1)
                self._log(str(datetime.now())+ " - Certificate information is shown below this line", 'underline')
                self.rPrintOutput(message = '')

                transaction = self.__w3.eth.get_transaction(self.__dohash)
                block = self.__w3.eth.get_block(transaction['blockNumber'])
                blocktimestamp = (block['timestamp'])
                blockdatetime = datetime.fromtimestamp(blocktimestamp)
                endblocknumber = self.__w3.eth.block_number
                startblocknumber = endblocknumber - 20

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

                self.__write_to_cert(self.__dohash, ('#' * 109))
                self.__write_to_cert(self.__dohash, f"{'#' * 41} bloxberg PoX certificate {'#' * 42}")
                self.__write_to_cert(self.__dohash, ('#' * 109))
                self.__write_to_cert(self.__dohash, f"{'#' * 6}{' ' * 97}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [INFO] contract address: {self._contract_address} {' ' * 27}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [INFO] input transaction: {self.__dohash}   {'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [INFO] output transaction: {resulttransactionhash.hex()}  {'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [INFO] PoX processing order: {str(order).zfill(16)}{' ' * 50}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}{' ' * 97}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [INPUT] public image: {self._image}{' ' * 14}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [INPUT] public script: {self._scripthash}{' ' * 26}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [INPUT] public fileset: {self._filesethash}{' ' * 25}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [INPUT] timestamp: {str(blockdatetime)} [{str(blocktimestamp)}]{' ' * 44}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [OUTPUT] public result: {result} {' ' * 24}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}  [OUTPUT] timestamp: {str(resultblockdatetime)} [{str(resultblocktimestamp)}] {' ' * 42}{'#' * 6}")
                self.__write_to_cert(self.__dohash, f"{'#' * 6}{' ' * 97}{'#' * 6}")
                self.__write_to_cert(self.__dohash, ('#' * 109))
                self.__write_to_cert(self.__dohash, ('#' * 109))
                self.__write_to_cert(self.__dohash, ('#' * 109))

                self.rPrintOutput(message = '')

                self._log(str(datetime.now())+ " - Actual result of the processing is printed below this line", 'underline')
                self.rPrintOutput(message = '')
                print(content)

                print('')

                sys.exit()

    def __write_to_cert(self, dohash, text):
        with open('certs/' + dohash, 'a+') as r:
            r.write(text + '\n')
        print(text)
                

    def __check_ipfs_upload(self, file, recursive=False):
        print('-----check ipfs upload')
        if self.__local:
            while True:
                res = self.__add_to_ipfs(file, recursive)

                sys.stdout.write('.')
                sys.stdout.flush()

                if isinstance(res, list):
                    for item in res:
                        return self.__process_ipfs_result(item)
                else:
                    return self.__process_ipfs_result(res)

                sys.stdout.write('*')
                sys.stdout.flush()
                self.__restart_ipfs()

        return None

    def __process_ipfs_result(self, resultitem):
        retries = 0
        while retries < 3:
            try:
                cmd = "%s swarm connect /ip4/%s/tcp/4001/ipfs/%s > %s" % (
                    self.__get_ipfs_executable_path(), 
                    self.__ipfsnode,
                    self._ipfshash,
                    self.__get_ipfs_output_file_path('ipfsconnect.txt'))
                print(cmd)
                os.system(cmd)
                time.sleep(1)
                for dht in self.__client.dht.findprovs(resultitem['Hash'], timeout=10):
                    if dht['Responses'] is not None:
                        for response in dht['Responses']:
                            if response['ID'] == self._ipfshash:
                                sys.stdout.write('#')
                                sys.stdout.flush()
                                return resultitem['Hash']
            except Exception:
                pass
            sys.stdout.write('.')
            sys.stdout.flush()
            retries += 1

if __name__ == '__main__':
    print('-----------')
    app = EtnyPoXClient()