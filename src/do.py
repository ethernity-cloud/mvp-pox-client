#!/usr/bin/python3

import time
import argparse
import ipfshttpclient
import ntpath
import os
import psutil
import sys
import socket
from datetime import datetime

from web3 import Web3
from eth_account import Account
from web3.middleware import geth_poa_middleware
from web3.exceptions import (
    BlockNotFound,
    TimeExhausted,
    TransactionNotFound,
)


class etnyPoX:
    def __init__(self):
        parser = argparse.ArgumentParser(description = "Ethernity PoX request")
        parser.add_argument("-a", "--address", help = "Etherem address (0x627306090abab3a6e1400e9345bc60c78a8bef57)", required = True)
        parser.add_argument("-k", "--privatekey", help = "Etherem privatekey (c87509a1c067bbde78beb793e6fa76530b6382a4c0241e5e4a9ec0a0f44dc0d3)", required = True)
        parser.add_argument("-c", "--cpu", help = "Number of CPUs (count)", required = False, default = "1")
        parser.add_argument("-m", "--memory", help = "Amount of memory (GB)", required = False, default = "1")
        parser.add_argument("-d", "--storage", help = "Amount of storage (GB)", required = False, default = "40")
        parser.add_argument("-b", "--bandwidth", help = "Amount of bandwidth (GB)", required = False, default = "1")
        parser.add_argument("-t", "--duration", help = "Amount of time allocated for task (minutes)", required = False, default = "60")
        parser.add_argument("-n", "--instances", help = "Number of instances to run simmultaneously (count)", required = False, default = "1")
        parser.add_argument("-i", "--image", help = "IPFS location of docker repository in format [HASH:container]",  required = False, default = "QmYF7WuHAH4tr896YXxwahaBEWT6YPcagB1dpotGWtCbwS:etny-pynithy")
        parser.add_argument("-s", "--script", help = "PATH of python script",  required = True, default = "" )
        parser.add_argument("-f", "--fileset", help = "PATH of the fileset",  required = True, default = "" )
        parser.add_argument("-r", "--redistribute", help ="Check and redistribute IPFS payload after order validation", required = False, action = 'store_true')
        parser.add_argument("-l", "--local", help="Use local IPFS Gateway", required=False, action = 'store_true')


        argument = parser.parse_args()
        status = False

        if argument.address:
            etnyPoX.address = format(argument.address)
            status = True
        if argument.privatekey:
            etnyPoX.privatekey = format(argument.privatekey)
            status = True
        if argument.cpu:
            etnyPoX.cpu = int(format(argument.cpu))
            status = True
        if argument.memory:
            etnyPoX.memory = int(format(argument.memory))
            status = True
        if argument.storage:
            etnyPoX.storage = int(format(argument.storage))
            status = True
        if argument.bandwidth:
            etnyPoX.bandwidth = int(format(argument.bandwidth))
            status = True
        if argument.duration:
            etnyPoX.duration = int(format(argument.duration))
            status = True
        if argument.instances:
            etnyPoX.instances = int(format(argument.instances))
            status = True
        if argument.image:
            etnyPoX.image = format(argument.image)
            etnyPoX.imageHash = format(argument.image)
            status = True
        if argument.script:
            etnyPoX.script = format(argument.script)
            etnyPoX.scriptHash = ''
            status = True
        if argument.fileset:
            etnyPoX.fileset = format(argument.fileset)
            etnyPoX.filesetHash = ''
            status = True
        if argument.redistribute:
            etnyPoX.redistribute = True
            status = True
        else:
            etnyPoX.redistribute = False
        etnyPoX.local, status = (argument.local, argument.local or status)

        f = open(os.path.dirname(os.path.realpath(__file__)) + '/pox.abi')
        etnyPoX.contract_abi = f.read()
        f.close()

        etnyPoX.w3 = Web3(Web3.HTTPProvider("https://bloxberg.ethernity.cloud"))
        etnyPoX.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        etnyPoX.acct = Account.privateKeyToAccount(etnyPoX.privatekey)
        etnyPoX.etny = etnyPoX.w3.eth.contract(address=etnyPoX.w3.toChecksumAddress("0x99738e909a62e2e4840a59214638828E082A9A2b"), abi=etnyPoX.contract_abi)

        etnyPoX.connectIPFSGateway()

        etnyPoX.dorequest = 0
        etnyPoX.dohash = 0

    @staticmethod
    def getIPFSExecutablePath():
        return os.path.join('..', '.tmp','go-ipfs','ipfs')

    @staticmethod
    def getIPFSOutputFilePath(file):
        return os.path.join('..', '.tmp', file)

    @staticmethod
    def connectIPFSGateway():
        while True:
            if not etnyPoX.local:
                # If not local, then connect automatically to infura gateway
                etnyPoX.client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
                break
            # Try to connect local gateway
            try:
                etnyPoX.client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
                etnyPoX.ipfsnode = socket.gethostbyname('ipfs.ethernity.cloud')
                etnyPoX.client.bootstrap.add('/ip4/%s/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5' % etnyPoX.ipfsnode)
            except:
                # Can't connect to local gateway connect to infura
                sys.stdout.write('/')
                sys.stdout.flush()
                etnyPoX.restartIPFS()
                continue
        return

    def uploadIPFS(file, recursive=False):
        while True:
            try:
                if etnyPoX.local and hasattr(etnyPoX, 'ipfsnode'):
                    cmd = "%s swarm connect /ip4/%s/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5 > %s" % (etnyPoX.getIPFSExecutablePath(), etnyPoX.ipfsnode, etnyPoX.getIPFSOutputFilePath('ipfsconnect.txt'))
                    os.system(cmd)
            except:
                sys.stdout.write('*')
                sys.stdout.flush()
                continue


            res = etnyPoX.client.add(file, recursive=recursive)
   

            if isinstance(res,list):
                for item in res:
                    if item['Name'] == ntpath.basename(file):
                        return item['Hash']
            else:
                return res['Hash']
        return None

    def checkIPFSUpload(file, recursive=False):
        while True:

            res = etnyPoX.client.add(file, recursive=recursive)

            sys.stdout.write('.')
            sys.stdout.flush()

            retries = 0

            if isinstance(res,list):
                for item in res:
                    while retries < 3:
                        try:
                            cmd = "%s swarm connect /ip4/%s/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5 > %s" % (etnyPoX.getIPFSExecutablePath(), etnyPoX.ipfsnode, etnyPoX.getIPFSOutputFilePath('ipfsconnect.txt'))
                            os.system(cmd)
                            time.sleep(1)
                            for dht in etnyPoX.client.dht.findprovs(item['Hash'], timeout=10):
                                if dht['Responses'] != None:
                                    for response in dht['Responses']:
                                        if(response['ID'] == "QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5"):
                                            sys.stdout.write('#')
                                            sys.stdout.flush()
                                            return item['Hash']
                        except:
                            pass
                        sys.stdout.write('.')
                        sys.stdout.flush()
                        retries += 1
            else:
                while retries < 3:
                    try:
                        #client.swarm.connect('/ip4/81.95.5.72/tcp/4001/ipfs/') # bug tracked under https://github.com/ipfs-shipyard/py-ipfs-http-client/issues/246
                        cmd = "%s swarm connect /ip4/%s/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5 > %s" % (etnyPoX.getIPFSExecutablePath(), etnyPoX.ipfsnode, etnyPoX.getIPFSOutputFilePath('ipfsconnect.txt'))
                        os.system(cmd)
                        time.sleep(1)
                        for dht in etnyPoX.client.dht.findprovs(res['Hash'], timeout=10):
                            if dht['Responses'] != None:
                                for response in dht['Responses']:
                                    if(response['ID'] == "QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5"):
                                        sys.stdout.write('#')
                                        sys.stdout.flush()
                                        return res['Hash']
                    except:
                        pass
                    sys.stdout.write('.')
                    sys.stdout.flush()
                    retries += 1

            sys.stdout.write('*')
            sys.stdout.flush()
            etnyPoX.restartIPFS()

        return None

    def restartIPFS():

        for proc in psutil.process_iter():
            if proc.name() == "ipfs.exe":
                proc.kill()
            if proc.name() == "ipfs":
                proc.kill()
        cmd = 'start /B "" "%s" daemon > %s' % (etnyPoX.getIPFSExecutablePath(), etnyPoX.getIPFSOutputFilePath('ipfsoutput.txt'))
        os.system(cmd)
        return None

    def addDORequest():
        nonce = etnyPoX.w3.eth.getTransactionCount(etnyPoX.address)

        print(datetime.now(),"Sending payload to IPFS...")

        etnyPoX.scriptHash = etnyPoX.uploadIPFS(etnyPoX.script)
        etnyPoX.filesetHash = etnyPoX.uploadIPFS(etnyPoX.fileset, True)

        unicorn_txn = etnyPoX.etny.functions._addDORequest(
            etnyPoX.cpu, etnyPoX.memory, etnyPoX.storage, etnyPoX.bandwidth, etnyPoX.duration, etnyPoX.instances, 0, etnyPoX.imageHash, etnyPoX.scriptHash, etnyPoX.filesetHash, ""
        ).buildTransaction({
            'gas': 1000000,
            'chainId': 8995,
            'nonce': nonce,
            'gasPrice': etnyPoX.w3.toWei("1", "mwei"),
        })

        signed_txn = etnyPoX.w3.eth.account.sign_transaction(unicorn_txn, private_key=etnyPoX.acct.key)
        etnyPoX.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        hash = etnyPoX.w3.toHex(etnyPoX.w3.sha3(signed_txn.rawTransaction))

        print(datetime.now(), "Submitting transaction for DO request")


        for i in range(100):
            try:
                receipt = etnyPoX.w3.eth.waitForTransactionReceipt(hash)
                processed_logs = etnyPoX.etny.events._addDORequestEV().processReceipt(receipt)
                etnyPoX.dorequest = processed_logs[0].args._rowNumber
            except KeyError:
                time.sleep(1)
                continue
            except:
                raise
            else:
                print(datetime.now(), "Request %s created successfuly!" % etnyPoX.dorequest)
                print(datetime.now(), "TX Hash: %s" % hash)
                etnyPoX.dohash = hash
                break

        if (receipt == None):
            print(datetime.now(), "Unable to create request, please check conectivity with bloxberg node")
            sys.exit()            
            



    def waitForProcessor():
        while True:
                order = etnyPoX.findOrder(etnyPoX.dorequest)
                if order is not None:
                    print("")
                    print(datetime.now(),"Connected!")
                    etnyPoX.approveOrder(order)

                    if etnyPoX.redistribute == True:
                        print(datetime.now(),"Checking IPFS payload distribution...")
                        scriptHash = etnyPoX.checkIPFSUpload(etnyPoX.script)
                        filesetHash = etnyPoX.checkIPFSUpload(etnyPoX.fileset, True)
                        if scriptHash != None and filesetHash != None:
                            print("")
                            print(datetime.now(),"IPFS payload distribution confirmed!")
                    etnyPoX.getResultFromOrder(order)
                else:
                    time.sleep(5)
        return None

    def approveOrder(order):
        nonce = etnyPoX.w3.eth.getTransactionCount(etnyPoX.address)

        unicorn_txn = etnyPoX.etny.functions._approveOrder(order).buildTransaction({
            'gas': 1000000,
            'chainId': 8995,
            'nonce': nonce,
            'gasPrice': etnyPoX.w3.toWei("1", "mwei"),
        })


        signed_txn = etnyPoX.w3.eth.account.sign_transaction(unicorn_txn, private_key=etnyPoX.acct.key)
        etnyPoX.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        hash = etnyPoX.w3.toHex(etnyPoX.w3.sha3(signed_txn.rawTransaction))

        for i in range(100):
            try:
                receipt = etnyPoX.w3.eth.waitForTransactionReceipt(hash)
            except KeyError:
                time.sleep(1)
                continue
            except:
                raise
            else:
                print(datetime.now(),"Order %s approved successfuly!" % order)
                print(datetime.now(),"TX Hash: %s" % hash)
                break

        if (receipt == None):
            print(datetime.now(),"Unable to approve order, please check connectivity with bloxberg node")
            sys.exit()


    def getResultFromOrder(order):
        print(datetime.now(),"Waiting for task to finish...")
        while True:
            result = 0
            try:
                result = etnyPoX.etny.caller(transaction={'from': etnyPoX.address})._getResultFromOrder(order)
            except:
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(5)
                continue
            else:
                print("")
                print(datetime.now(),"Found result hash: %s" % result)
                print(datetime.now(),"Fetching result from IPFS...")
                #client.swarm.connect('/ip4/%s/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5' % ipfsnode) # bug tracked under https://github.com/ipfs-shipyard/py-ipfs-http-client/issues/246



                while True:
                    try:
                        etnyPoX.client.get(result)
                    except:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                        time.sleep(1)
                        continue
                    else:
                        break

                file = os.path.dirname(os.path.realpath(__file__)) + '/../' + result
                # file = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), result)))
                # file = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)), result)
                f = open(file) 
                content = f.read()
                f.close()
                os.unlink(file)

                print(datetime.now(),"Certificate information is shown below this line")
                print('')
                print('')
                
                transaction = etnyPoX.w3.eth.getTransaction(etnyPoX.dohash)
                block = etnyPoX.w3.eth.getBlock(transaction['blockNumber'])
                blocktimestamp = (block['timestamp'])
                blockdatetime = datetime.fromtimestamp(blocktimestamp)
                endBlockNumber = etnyPoX.w3.eth.blockNumber
                startBlockNumber = endBlockNumber - 20
                
                for i in range(endBlockNumber, startBlockNumber, -1):
                    block = etnyPoX.w3.eth.getBlock(i,True)
                    if block is not None and block.transactions is not None:
                        transactions = block["transactions"]
                        for transaction in transactions:
                            if transaction["to"] == "0x99738e909a62e2e4840a59214638828E082A9A2b":
                                input = etnyPoX.etny.decode_function_input(transaction.input)
                                function = input[0]
                                params = input[1]
                                if "_addResultToOrder" in function.fn_name and params['_orderItem'] == order:
                                    resulthash = params['_result']
                                    resulttransactionhash = transaction['hash']
                                    resultblock = etnyPoX.w3.eth.getBlock(transaction['blockNumber'])
                                    resultblocktimestamp = (block['timestamp'])
                                    resultblockdatetime = datetime.fromtimestamp(resultblocktimestamp)

                etnyPoX.writeToCert(etnyPoX.dohash,'#############################################################################################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'######################################### bloxberg PoX certificate ##########################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'#############################################################################################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'######                                                                                                 ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INFO] contract address: 0x99738e909a62e2e4840a59214638828E082A9A2b                            ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INFO] input transaction: ' + etnyPoX.dohash + '   ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INFO] output transaction: ' + str(resulttransactionhash.hex()) + '  ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INFO] PoX processing order: ' + str(order).zfill(16) +'                                                  ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######                                                                                                 ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INPUT] public image: ' + etnyPoX.imageHash + '              ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INPUT] public script: ' + etnyPoX.scriptHash + '                          ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INPUT] public fileset: ' + etnyPoX.filesetHash + '                         ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INPUT] timestamp: ' + str(blockdatetime) + ' [' + str(blocktimestamp) + ']                                            ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [OUTPUT] public result: ' + result + '                         ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [OUTPUT] timestamp: ' + str(resultblockdatetime) + ' [' + str(resultblocktimestamp) + ']                                           ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######                                                                                                 ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'#############################################################################################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'#############################################################################################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'#############################################################################################################')

                print('')
                print('')


                print(datetime.now(),"Actual result of the processing is printed below this line")
                print('')
                print('')

                print(content)

                print('')


                sys.exit()

    def writeToCert(hash, str):
        if os.path.isfile(os.path.join('certs/' + etnyPoX.dohash)):
            with open(os.path.join('certs/' + etnyPoX.dohash), 'a+') as f:
                f.write(str + '\n')
                print(str)
            return
        if not os.path.isdir(os.path.join("..", "certs")):
            os.mkdir(os.path.join("..", "certs"))
        with open(os.path.join('certs/' + etnyPoX.dohash), 'x+') as f:
            f.write(str + '\n')
            print(str)

    def findOrder(doReq):
        sys.stdout.write('.')
        sys.stdout.flush()
        count=etnyPoX.etny.functions._getOrdersCount().call()
        for i in range(count-1, count-5, -1):
            order = etnyPoX.etny.caller()._getOrder(i)
            if order[2] == etnyPoX.dorequest and order[4] == 0:
                return i
        return None

if __name__ == '__main__':
    app = etnyPoX()
    etnyPoX.addDORequest()
    print(datetime.now(),"Waiting for Ethernity network...")
    order = etnyPoX.waitForProcessor()