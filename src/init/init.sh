#!/bin/bash

if [ -x "$(command -v python3)" ]; then
   PYTHON=python3
else
   exit 1
fi

if [ -x "$(command -v pip3)" ]; then
   PIP=pip3
else
   exit 2
fi

$PIP install ipfshttpclient web3

mkdir .tmp
cd .tmp
wget https://github.com/ipfs/go-ipfs/releases/download/v0.4.19/go-ipfs_v0.4.19_linux-386.tar.gz 2>&1 >> /dev/null
tar zxvf go-ipfs_v0.4.19_linux-386.tar.gz 2>&1 >> /dev/null
cd go-ipfs
./ipfs init 2>&1 >> /dev/null
./ipfs daemon 2>&1 >> /dev/null &

IP=`getent hosts ipfs.ethernity.cloud | awk '{print $1}'`

until ./ipfs swarm connect /ip4/$IP/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5
do
  sleep 1
done

./ipfs bootstrap add /ip4/$IP/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5

cd ../..
mkdir certs

touch .init-done
