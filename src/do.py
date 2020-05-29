#!/usr/bin/python3

import time
import argparse
import ipfshttpclient
import ntpath
import os
import sys
import json
import re
from pprint import pprint
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
        parser.add_argument("-p", "--publickey", help = "Etherem publickey (0x0x0123456789abcDEF0123456789abcDEF01234567)", required = True)
        parser.add_argument("-k", "--privatekey", help = "Etherem privatekey (0x0123456789abcDEF0123456789abcDEF0123456789abcDEF0123456789abcDEF)", required = True)
        parser.add_argument("-c", "--cpu", help = "Number of CPUs (count)", required = False, default = "1")
        parser.add_argument("-m", "--memory", help = "Amount of memory (GB)", required = False, default = "1")
        parser.add_argument("-d", "--storage", help = "Amount of storage (GB)", required = False, default = "40")
        parser.add_argument("-b", "--bandwidth", help = "Amount of bandwidth (GB)", required = False, default = "1")
        parser.add_argument("-t", "--duration", help = "Amount of time allocated for task (minutes)", required = False, default = "60")
        parser.add_argument("-n", "--instances", help = "Number of instances to run simmultaneously (count)", required = False, default = "1")
        parser.add_argument("-i", "--image", help = "IPFS location of docker repository in format [HASH:container]",  required = False, default = "QmSXJN2k2RLG3M19jYGA32rS6VFpTtUFjUEgiWuuL1zyyA:etny-pynithy")
        parser.add_argument("-s", "--script", help ="PATH of python script",  required = True, default = "" )
        parser.add_argument("-f", "--fileset", help ="PATH of the fileset",  required = True, default = "" )





        argument = parser.parse_args()
        status = False

        if argument.publickey:
            etnyPoX.publickey = format(argument.publickey)
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

        f = open(os.path.dirname(os.path.realpath(__file__)) + '/pox.abi')
        etnyPoX.contract_abi = f.read()
        f.close()

        etnyPoX.w3 = Web3(Web3.HTTPProvider("https://core.bloxberg.org"))
        etnyPoX.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        etnyPoX.acct = Account.privateKeyToAccount(etnyPoX.privatekey)
        etnyPoX.etny = etnyPoX.w3.eth.contract(address=etnyPoX.w3.toChecksumAddress("0x99738e909a62e2e4840a59214638828E082A9A2b"), abi=etnyPoX.contract_abi)

        etnyPoX.dorequest = etnyPoX.etny.functions._getDORequestsCount().call() - 3;
        etnyPoX.dohash = 0;




    def uploadIPFS(file, recursive=False):
        client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')

        res = client.add(file, recursive=recursive)

   
        if isinstance(res,list):
            for item in res:
                if item['Name'] == ntpath.basename(file):
                    return item['Hash']
        else:
            return res['Hash']

        return None


    def addDORequest():
        nonce = etnyPoX.w3.eth.getTransactionCount(etnyPoX.publickey)

        etnyPoX.scriptHash = etnyPoX.uploadIPFS(etnyPoX.script)
        etnyPoX.filesetHash = etnyPoX.uploadIPFS(etnyPoX.fileset, True)

        unicorn_txn = etnyPoX.etny.functions._addDORequest(
            etnyPoX.cpu, etnyPoX.memory, etnyPoX.storage, etnyPoX.bandwidth, etnyPoX.duration, etnyPoX.instances, 0, etnyPoX.imageHash, etnyPoX.scriptHash, etnyPoX.filesetHash, ""
        ).buildTransaction({
            'gas': 1000000,
            'chainId': 8995,
            'nonce': nonce,
            'gasPrice': etnyPoX.w3.toWei("100", "gwei"),
        })

        signed_txn = etnyPoX.w3.eth.account.sign_transaction(unicorn_txn, private_key=etnyPoX.acct.key)
        etnyPoX.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        hash = etnyPoX.w3.toHex(etnyPoX.w3.sha3(signed_txn.rawTransaction))

        try:
            etnyPoX.w3.eth.waitForTransactionReceipt(hash)
        except:
            raise
        else:
            print(datetime.now(), "Request created successfuly!")
            print(datetime.now(), "TX Hash: %s" % hash)
            etnyPoX.dohash = hash

    def waitForProcessor():
        while True:
            doReq = etnyPoX.findNextDORequest()
            count = etnyPoX.etny.functions._getDPRequestsCount().call()
            for i in range(count-3, count):
                dpReq = etnyPoX.etny.caller()._getDPRequest(i)
                order = etnyPoX.findOrder(doReq, i)
                if order is not None:
                    etnyPoX.approveOrder(order);
        return None

    def approveOrder(order):
        nonce = etnyPoX.w3.eth.getTransactionCount(etnyPoX.publickey)

        unicorn_txn = etnyPoX.etny.functions._approveOrder(order).buildTransaction({
            'gas': 1000000,
            'chainId': 8995,
            'nonce': nonce,
            'gasPrice': etnyPoX.w3.toWei("100", "gwei"),
        })


        signed_txn = etnyPoX.w3.eth.account.sign_transaction(unicorn_txn, private_key=etnyPoX.acct.key)
        etnyPoX.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        hash = etnyPoX.w3.toHex(etnyPoX.w3.sha3(signed_txn.rawTransaction))

        try:
            etnyPoX.w3.eth.waitForTransactionReceipt(hash)
        except:
            raise
        else:
            print("")
            print(datetime.now(),"Order %s approved successfuly!" % order)
            print(datetime.now(),"TX Hash: %s" % hash)

        etnyPoX.getResultFromOrder(order)

    def getResultFromOrder(order):
        print(datetime.now(),"Waiting for task to finish...")
        while True:
            result = 0
            try:
                result = etnyPoX.etny.caller(transaction={'from': etnyPoX.publickey})._getResultFromOrder(order)
            except:
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(5)
                continue
            else:
                print("")
                print(datetime.now(),"Found result hash: %s" % result)
                print(datetime.now(),"Fetching result from IPFS...")
                client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')

                while True:
                    try:
                        client.get(result)
                    except:
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

                print(datetime.now(),"Certificate information is shown below this line")
                print('')
                print('')
                etnyPoX.writeToCert(etnyPoX.dohash,'#################################################################################################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'########################################### bloxberg PoX Certificate ############################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'#################################################################################################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'######                                                                                                     ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INFO] Contract address: 0x99738e909a62e2e4840a59214638828E082A9A2b                                ######') 
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INFO] DO request transaction: ' + etnyPoX.dohash +'  ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INFO] PoX processing order: ' + str(order).zfill(16) +'                                                      ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######                                                                                                     ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INPUT] public image hash: ' + etnyPoX.imageHash + '             ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INPUT] public script hash: ' + etnyPoX.scriptHash + '                         ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INPUT] public fileset hash: ' + etnyPoX.filesetHash + '                        ######')


                transaction = etnyPoX.w3.eth.getTransaction(etnyPoX.dohash)
                block = etnyPoX.w3.eth.getBlock(transaction['blockNumber'])
                blocktimestamp = (block['timestamp'])
                blockdatetime = datetime.fromtimestamp(blocktimestamp)
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [INPUT] timestamp: ' + str(blockdatetime) + ' [' + str(blocktimestamp) + ']                                                ######')
                endBlockNumber = etnyPoX.w3.eth.blockNumber
                startBlockNumber = endBlockNumber - 10
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
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [OUTPUT] public result hash: ' + result + '                        ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######  [OUTPUT] result timestamp: ' + str(resultblockdatetime) + ' [' + str(resultblocktimestamp) + ']                                        ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'######                                                                                                     ######')
                etnyPoX.writeToCert(etnyPoX.dohash,'#################################################################################################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'#################################################################################################################')
                etnyPoX.writeToCert(etnyPoX.dohash,'#################################################################################################################')

                print('')
                print('')


                print(datetime.now(),"Actual result of the processing is printed below this line")
                print('')
                print('')

                print(content)

                print('')


                sys.exit()

    def writeToCert(hash, str):
        f = open('certs/' + etnyPoX.dohash, 'a+')
        f.write(str + '\n')
        f.close()
        print(str)

    def findOrder(doReq, dpReq):
        sys.stdout.write('.')
        sys.stdout.flush()
        #print("Finding order match for %s and %s" % (doReq, dpReq))
        count=etnyPoX.etny.functions._getOrdersCount().call()
        for i in range(count-3, count):
            if i == count - 1:
                time.sleep(3)
            order = etnyPoX.etny.caller()._getOrder(i)
            if order[2] == doReq and order[3] == dpReq and order[4] == 0:
                return i
        return None


    def findNextDORequest():
        count = etnyPoX.etny.functions._getDORequestsCount().call()
        if etnyPoX.dorequest >= count:
            etnyPoX.dorequest = count-3;
        req = etnyPoX.etny.caller()._getDORequest(etnyPoX.dorequest)
        if req[0] == etnyPoX.publickey:
            etnyPoX.dorequest += 1;
            return etnyPoX.dorequest-1;
        etnyPoX.dorequest += 1;
            
    

if __name__ == '__main__':
    app = etnyPoX()
    etnyPoX.addDORequest()
    print(datetime.now(),"Waiting for Ethernity network...")
    order = etnyPoX.waitForProcessor()
