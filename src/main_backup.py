#!/usr/bin/python3

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

from web3.exceptions import TimeExhausted
from config import os, parser, arguments, bcolors

class EtnyPoXClient:
    # class variables

    __etny = None
    __acct = None
    __w3 = None
    __contract_abi = None
    __ipfsnode = None


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

        self._log(self._private_key, 'error')
        self.__acct = Account.privateKeyToAccount(self._private_key)
        self.__etny = self.__w3.eth.contract(address=self.__w3.toChecksumAddress(self._address), abi=self.__contract_abi)

    def _log(self, message = '', mode = '_end'):
        mode = str(mode.upper() if type(mode) == str else bcolors[mode].name)
        prefix = f"{bcolors[mode].value}{bcolors.BOLD.value}{bcolors[mode].name}{bcolors._END.value}: " if mode not in ['_END'] else ""
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

    def __connect_ipfs_gateway(self):
        print('address = ', self.__get_ipfs_address)
        while True:
            try:
                auth = None if not self._ipfsuser and not self._ipfspassword else (self._ipfsuser, self._ipfspassword)
                self.__client = ipfshttpclient.connect(self.__get_ipfs_address, auth=auth)
                if self.__local:
                    print('dddddd')
                    self.__ipfsnode = socket.gethostbyname('ipfs.ethernity.cloud')
                    self.__client.bootstrap.add(f'/ip4/{self.__ipfsnode}/tcp/4001/ipfs/{self._ipfshash}')
                print('after restarting?')
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
                    print(cmd)
                    os.system(cmd)
            except Exception as e:
                print(e)
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
                print("You have reached request limit, please wait or try again later")
                time.sleep(60)
                continue

    def add_do_request(self):
        nonce = self.__w3.eth.get_transaction_count(self._address)

        print(datetime.now(), "Sending payload to IPFS...")

        self._scripthash = self.__upload_ipfs(self._script)
        self._filesethash = self.__upload_ipfs(self._fileset, True)

        print(
            'self.__cpu = ', self._cpu,'\n', 
            'self.__memory = ', self._memory,'\n', 
            'self.__storage = ', self._storage,'\n', 
            'self.__bandwidth = ', self._bandwidth,'\n',
            'self.__duration = ', self._duration,'\n', 
            'self.__instances = ', self._instances,'\n', 
            'self.__imageHash = ', self._image,'\n', 
            'self.__scripthash = ', self._scripthash,'\n', 
            'self.__filesethash = ', self._filesethash,'\n', 
            'self.__acct.key = ', self.__acct.key,'\n', 
            "")

        unicorn_txn = self.__etny.functions._addDORequest(
            self._cpu, self._memory, self._storage, self._bandwidth,
            self._duration, self._instances, 0,
            self._image, self._scripthash, self._filesethash, ""
        ).buildTransaction({
            'gas': 1000000,
            'chainId': 8995,
            'nonce': nonce,
            'gasPrice': self.__w3.toWei("1", "mwei"),
        })
        print('---')
        print(unicorn_txn)
        print('---')
        signed_txn = self.__w3.eth.account.sign_transaction(unicorn_txn, private_key=self.__acct.key)
        self.__w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        transactionhash = self.__w3.toHex(self.__w3.sha3(signed_txn.rawTransaction))
        print(signed_txn)
        print(transactionhash)
        print(datetime.now(), "Submitting transaction for DO request", self.__acct.key)
        receipt = None
        for i in range(100):
            try:
                receipt = self.__w3.eth.wait_for_transaction_receipt(transactionhash)
                processed_logs = self.__etny.events._addDORequestEV().processReceipt(receipt)
                print(receipt)
                print(transactionhash)
                print('-----------', type(processed_logs))
                print(processed_logs)
                self.__dorequest = processed_logs[0].args._rowNumber
                print('-------after error????')
            except KeyError:
                time.sleep(1)
                continue
            except Exception:
                raise
            else:
                print(datetime.now(), "Request %s created successfuly!" % self.__dorequest)
                print(datetime.now(), "TX Hash: %s" % transactionhash)
                self.__dohash = transactionhash
                break

        if receipt is None:
            print(datetime.now(), "Unable to create request, please check conectivity with bloxberg node")
            sys.exit()


    def wait_for_processor(self):
        
        while True:
            order = self.find_order(self.__dorequest)
            if order is not None:
                print("")
                print(datetime.now(), "Connected!")
                self.approve_order(order)

                if self.__redistribute is True and self.__local:
                    print(datetime.now(), "Checking IPFS payload distribution...")
                    scripthash = self.__check_ipfs_upload(self.__script)
                    filesethash = self.__check_ipfs_upload(self.__fileset, True)
                    if scripthash is not None and filesethash is not None:
                        print("")
                        print(datetime.now(), "IPFS payload distribution confirmed!")
                self.get_result_from_order(order)
            else:
                time.sleep(5)
                

if __name__ == '__main__':
    print('-----------')
    app = EtnyPoXClient()