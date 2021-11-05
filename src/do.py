#!/usr/bin/python3

import time
import argparse
import ipfshttpclient
from ipfshttpclient.exceptions import StatusError
import ntpath
import urllib.parse
import os
import psutil
import sys
import socket
from datetime import datetime

from web3 import Web3
from eth_account import Account
from web3.middleware import geth_poa_middleware

from web3.exceptions import (
    # BlockNotFound,
    TimeExhausted,
    # TransactionNotFound,
)


class EtnyPoXClient:
    # class variables

    __address = None
    __privateKey = None
    __contract_abi = None
    __etny = None
    __acct = None
    __w3 = None
    __dorequest = 0
    __dohash = 0
    __ipfsnode = None
    __ipfsgateway = None
    __ipfsuser = None
    __ipfspassword = None
    __client = None
    __scripthash = None
    __filesethash = None

    def __init__(self):
        arguments = self.__read_arguments()
        self.__parse_arguments(arguments)

        f = open(os.path.dirname(os.path.realpath(__file__)) + '/pox.abi')
        self.__contract_abi = f.read()
        f.close()

        self.__w3 = Web3(Web3.HTTPProvider("https://bloxberg.ethernity.cloud"))
        self.__w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.__acct = Account.privateKeyToAccount(self.__privateKey)
        self.__etny = self.__w3.eth.contract(
            address=self.__w3.toChecksumAddress("0x549A6E06BB2084100148D50F51CF77a3436C3Ae7"),
            abi=self.__contract_abi)

        self.__connect_ipfs_gateway()

        self.__dorequest = 0
        self.__dohash = 0

    @staticmethod
    def __read_arguments():
        parser = argparse.ArgumentParser(description="Ethernity PoX request")
        parser.add_argument("-a", "--address", help="Etherem address (0x627306090abab3a6e1400e9345bc60c78a8bef57)",
                            required=True)
        parser.add_argument("-k", "--privatekey",
                            help="Etherem privatekey "
                                 "(c87509a1c067bbde78beb793e6fa76530b6382a4c0241e5e4a9ec0a0f44dc0d3)",
                            required=True)
        parser.add_argument("-c", "--cpu", help="Number of CPUs (count)", required=False, default="1")
        parser.add_argument("-m", "--memory", help="Amount of memory (GB)", required=False, default="1")
        parser.add_argument("-d", "--storage", help="Amount of storage (GB)", required=False, default="40")
        parser.add_argument("-b", "--bandwidth", help="Amount of bandwidth (GB)", required=False, default="1")
        parser.add_argument("-t", "--duration", help="Amount of time allocated for task (minutes)", required=False,
                            default="60")
        parser.add_argument("-n", "--instances", help="Number of instances to run simmultaneously (count)",
                            required=False, default="1")
        parser.add_argument("-i", "--image", help="IPFS location of docker repository in format [HASH:container]",
                            required=False, default="QmeQiSC1dLMKv4BvpvjWt1Zeak9zj6TWgWhN7LLiRznJqC:etny-pynithy")
        parser.add_argument("-s", "--script", help="PATH of python script", required=True, default="")
        parser.add_argument("-f", "--fileset", help="PATH of the fileset", required=True, default="")
        parser.add_argument("-r", "--redistribute", help="Check and redistribute IPFS payload after order validation",
                            required=False, action='store_true')
        parser.add_argument("-g", "--ipfsgateway", help="IPFS Gateway host url", required=False, default="")
        parser.add_argument("-u", "--ipfsuser", help="IPFS Gateway username", required=False, default="")
        parser.add_argument("-p", "--ipfspassword", help="IPFS Gateway password", required=False, default="")
        return parser.parse_args()

    def __parse_arguments(self, arguments):
        if arguments.address:
            self.__address = format(arguments.address)
        if arguments.privatekey:
            self.__privateKey = format(arguments.privatekey)
        if arguments.cpu:
            self.__cpu = int(format(arguments.cpu))
        if arguments.memory:
            self.__memory = int(format(arguments.memory))
        if arguments.storage:
            self.__storage = int(format(arguments.storage))
        if arguments.bandwidth:
            self.__bandwidth = int(format(arguments.bandwidth))
        if arguments.duration:
            self.__duration = int(format(arguments.duration))
        if arguments.instances:
            self.__instances = int(format(arguments.instances))
        if arguments.image:
            self.__image = format(arguments.image)
            self.__imageHash = format(arguments.image)
        if arguments.script:
            self.__script = format(arguments.script)
            self.__scripthash = ''
        if arguments.fileset:
            self.__fileset = format(arguments.fileset)
            self.__filesethash = ''
        if arguments.redistribute:
            self.__redistribute = True
        else:
            self.__redistribute = False
        if arguments.ipfsuser:
            self.__ipfsuser = format(arguments.ipfsuser)
        if arguments.ipfspassword:
            self.__ipfspassword = format(arguments.ipfspassword)
        self.__ipfsgateway = self.__get_ipfs_address(
            arguments.ipfsgateway if arguments.ipfsgateway != "" else 'http://127.0.0.1:5001')

        # Set the default behaviour of do.py to use the local node, if gateway url (-h) is not specified
        self.__local = arguments.ipfsgateway == ""

    @staticmethod
    def __get_ipfs_address(url):
        addr = urllib.parse.urlsplit(url)
        return '/'.join(['/dns', addr.hostname, 'tcp', str(addr.port), addr.scheme])

    @staticmethod
    def __get_ipfs_executable_path():
        return os.path.join('.tmp', 'go-ipfs', 'ipfs')

    @staticmethod
    def __get_ipfs_output_file_path(file):
        if not os.path.isdir(os.path.join('.tmp')):
            os.mkdir(os.path.join('.tmp'))
        return os.path.join('.tmp', file)

    # @staticmethod
    def __connect_ipfs_gateway(self):
        while True:
            try:
                auth = None if self.__ipfsuser is None and self.__ipfspassword is None else (
                    self.__ipfsuser, self.__ipfspassword)
                self.__client = ipfshttpclient.connect(self.__ipfsgateway,
                                                       auth=auth)
                if self.__local:
                    self.__ipfsnode = socket.gethostbyname('ipfs.ethernity.cloud')
                    self.__client.bootstrap.add(
                        '/ip4/%s/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5' % self.__ipfsnode)
                break
            except Exception as e:
                print(e)
                sys.stdout.write('/')
                sys.stdout.flush()
                self.__restart_ipfs()
                continue
        return

    # @staticmethod
    def __add_to_ipfs(self, file, recursive=False):
        while True:
            # noinspection PyBroadException
            try:
                res = self.__client.add(file, recursive=recursive)
                return res
            except Exception:
                time.sleep(1)
                continue
            except StatusError:
                print("You have reached request limit, please wait or try again later")
                time.sleep(60)
                continue

    def __upload_ipfs(self, file, recursive=False):
        while True:
            # noinspection PyBroadException
            try:
                if self.__local and self.__ipfsnode is not None:  # hasattr(self, 'ipfsnode'):
                    cmd = "%s swarm " \
                          "connect /ip4/%s/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5 > %s" % (
                              self.__get_ipfs_executable_path(), self.__ipfsnode,
                              self.__get_ipfs_output_file_path('ipfsconnect.txt'))
                    os.system(cmd)
            except Exception:
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
        return None

    def __check_ipfs_upload(self, file, recursive=False):
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
            # noinspection PyBroadException
            try:
                # client.swarm.connect('/ip4/81.95.5.72/tcp/4001/ipfs/') # bug tracked
                # under https://github.com/ipfs-shipyard/py-ipfs-http-client/issues/246
                cmd = "%s swarm connect /ip4/%s/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5 > %s" % (
                    self.__get_ipfs_executable_path(), self.__ipfsnode,
                    self.__get_ipfs_output_file_path('ipfsconnect.txt'))
                os.system(cmd)
                time.sleep(1)
                for dht in self.__client.dht.findprovs(resultitem['Hash'], timeout=10):
                    if dht['Responses'] is not None:
                        for response in dht['Responses']:
                            if response['ID'] == "QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5":
                                sys.stdout.write('#')
                                sys.stdout.flush()
                                return resultitem['Hash']
            except Exception:
                pass
            sys.stdout.write('.')
            sys.stdout.flush()
            retries += 1

    def __restart_ipfs(self):
        if self.__local:
            for proc in psutil.process_iter():
                if proc.name() == "ipfs.exe":
                    proc.kill()
                if proc.name() == "ipfs":
                    proc.kill()
            cmd = 'start /B "" "%s" daemon > %s' % (
                self.__get_ipfs_executable_path(), self.__get_ipfs_output_file_path('ipfsoutput.txt'))
            os.system(cmd)
        return None

    def add_do_request(self):
        nonce = self.__w3.eth.get_transaction_count(self.__address)

        print(datetime.now(), "Sending payload to IPFS...")

        self.__scripthash = self.__upload_ipfs(self.__script)
        self.__filesethash = self.__upload_ipfs(self.__fileset, True)

        unicorn_txn = self.__etny.functions._addDORequest(
            self.__cpu, self.__memory, self.__storage, self.__bandwidth,
            self.__duration, self.__instances, 0,
            self.__imageHash, self.__scripthash, self.__filesethash, ""
        ).buildTransaction({
            'gas': 1000000,
            'chainId': 8995,
            'nonce': nonce,
            'gasPrice': self.__w3.toWei("1", "mwei"),
        })

        signed_txn = self.__w3.eth.account.sign_transaction(unicorn_txn, private_key=self.__acct.key)
        self.__w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        transactionhash = self.__w3.toHex(self.__w3.sha3(signed_txn.rawTransaction))

        print(datetime.now(), "Submitting transaction for DO request")

        receipt = None
        for i in range(100):
            try:
                receipt = self.__w3.eth.wait_for_transaction_receipt(transactionhash)
                processed_logs = self.__etny.events._addDORequestEV().processReceipt(receipt)
                self.__dorequest = processed_logs[0].args._rowNumber
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
        # unreachable code
        # return None

    def approve_order(self, order):
        nonce = self.__w3.eth.get_transaction_count(self.__address)

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
            except Exception:
                raise
            else:
                print(datetime.now(), "Order %s approved successfuly!" % order)
                print(datetime.now(), "TX Hash: %s" % transactionhash)
                break

        if receipt is None:
            print(datetime.now(), "Unable to approve order, please check connectivity with bloxberg node")
            sys.exit()

    def get_result_from_order(self, order):
        print(datetime.now(), "Waiting for task to finish...")
        while True:
            result = 0
            try:
                result = self.__etny.caller(transaction={'from': self.__address})._getResultFromOrder(
                    order)
            except Exception:
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(5)
                continue
            else:
                print("")
                print(datetime.now(), "Found result hash: %s" % result)
                print(datetime.now(), "Fetching result from IPFS...")
                # client.swarm.connect('/ip4/%s/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5' %
                # ipfsnode)
                # bug tracked under https://github.com/ipfs-shipyard/py-ipfs-http-client/issues/246

                while True:
                    try:
                        self.__client.get(result)
                    except Exception:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                        time.sleep(1)
                        continue
                    else:
                        break

                file = os.path.dirname(os.path.realpath(__file__)) + '/../' + result
                f = open(file)
                content = f.read()
                f.close()
                os.unlink(file)

                print(datetime.now(), "Certificate information is shown below this line")
                print('')
                print('')

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
                            if transaction["to"] == "0x549A6E06BB2084100148D50F51CF77a3436C3Ae7":
                                transactioninput = self.__etny.decode_function_input(transaction.input)
                                function = transactioninput[0]
                                params = transactioninput[1]
                                if "_addResultToOrder" in function.fn_name and params['_orderItem'] == order:
                                    # resulthash = params['_result']
                                    resulttransactionhash = transaction['hash']
                                    # resultblock = self.__w3.eth.getBlock(transaction['blockNumber'])
                                    resultblocktimestamp = (block['timestamp'])
                                    resultblockdatetime = datetime.fromtimestamp(resultblocktimestamp)

                self.__write_to_cert(self.__dohash,
                                     '######################################'
                                     '#######################################################################')
                self.__write_to_cert(self.__dohash,
                                     '#################################'
                                     '######## bloxberg PoX certificate ##########################################')
                self.__write_to_cert(self.__dohash,
                                     '################################'
                                     '#############################################################################')
                self.__write_to_cert(self.__dohash,
                                     '######                         '
                                     '                                                                        ######')
                self.__write_to_cert(self.__dohash,
                                     '######  [INFO] contract address: 0x549A6E06BB2084100148D50F51CF77a3436C3Ae7  '
                                     '                          ######')
                self.__write_to_cert(self.__dohash,
                                     '######  [INFO] input transaction: ' + str(self.__dohash) + '   ######')
                self.__write_to_cert(self.__dohash, '######  [INFO] output transaction: ' + str(
                    resulttransactionhash.hex()) + '  ######')
                self.__write_to_cert(self.__dohash, '######  [INFO] PoX processing order: ' + str(order).zfill(
                    16) + '                                                  ######')
                self.__write_to_cert(self.__dohash,
                                     '######                          '
                                     '                                                                       ######')
                self.__write_to_cert(self.__dohash,
                                     '######  [INPUT] public image: ' + self.__imageHash + '              ######')
                self.__write_to_cert(self.__dohash,
                                     '######  [INPUT] public script: '
                                     + self.__scripthash + '                          ######')
                self.__write_to_cert(self.__dohash,
                                     '######  [INPUT] public fileset: '
                                     + self.__filesethash + '                         ######')
                self.__write_to_cert(self.__dohash, '######  [INPUT] timestamp: '
                                     + str(blockdatetime) + ' ['
                                     + str(blocktimestamp) + ']                                            ######')
                self.__write_to_cert(self.__dohash,
                                     '######  [OUTPUT] public result: '
                                     + result + '                         ######')
                self.__write_to_cert(self.__dohash,
                                     '######  [OUTPUT] timestamp: '
                                     + str(resultblockdatetime) + ' [' + str(
                                         resultblocktimestamp) + ']                                           ######')
                self.__write_to_cert(self.__dohash,
                                     '######                                               '
                                     '                                                  ######')
                self.__write_to_cert(self.__dohash,
                                     '##############################'
                                     '###############################################################################')
                self.__write_to_cert(self.__dohash,
                                     '###################################'
                                     '##########################################################################')
                self.__write_to_cert(self.__dohash,
                                     '##############################################'
                                     '###############################################################')

                print('')
                print('')

                print(datetime.now(), "Actual result of the processing is printed below this line")
                print('')
                print('')

                print(content)

                print('')

                sys.exit()

    @staticmethod
    def __write_to_cert(dohash, text):
        f = open('certs/' + dohash, 'a+')
        f.write(text + '\n')
        f.close()
        print(text)

    def find_order(self, doreq):
        sys.stdout.write('.')
        sys.stdout.flush()
        count = self.__etny.functions._getOrdersCount().call()
        for i in range(count - 1, count - 5, -1):
            order = self.__etny.caller()._getOrder(i)
            if order[2] == doreq and order[4] == 0:
                return i
        return None


if __name__ == '__main__':
    app = EtnyPoXClient()
    app.add_do_request()
    print(datetime.now(), "Waiting for Ethernity network...")
    # wait_for_processor doesn't return nothing
    # order = app.wait_for_processor()
    app.wait_for_processor()
