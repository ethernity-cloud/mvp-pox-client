#!/bin/bash

if [ "$OS" == "Windows_NT" ]
then
    PYTHON_BIN=python
else
    PYTHON_BIN=python3
fi


if [ -x "$(command -v ${PYTHON_BIN})" ]; then
   PYTHON=${PYTHON_BIN}
else
   exit 1
fi

if [ -x "$(command -v pip3)" ]; then
   PIP=pip3
else
   exit 2
fi

$PIP install ipfshttpclient web3 --upgrade

mkdir .tmp
cd .tmp

IPFS_VERSION='v0.6.0'
MIRROR="https://dist.ipfs.io/go-ipfs/${IPFS_VERSION}/"

if [ "$OS" == "Windows_NT" ]
then
    FILENAME="go-ipfs_${IPFS_VERSION}_windows-amd64.zip"
    EXTRACT_COMMAND='unzip'
else
    FILENAME="go-ipfs_${IPFS_VERSION}_linux-amd64.tar.gz"
    EXTRACT_COMMAND='tar -zxvf'
fi

URL=${MIRROR}${FILENAME}

curl ${URL} --output ${FILENAME} 2>&1
${EXTRACT_COMMAND} ${FILENAME} 2>&1
cd go-ipfs
./ipfs init
./ipfs daemon &

IP=`nslookup ipfs.ethernity.cloud 2>&1 | grep -A 1 ethernity.cloud | grep 'Address' | awk '{print $2}'` 2>&1 > /dev/null

if [ "$OS" == "Windows_NT" ]
then
    until cmd //c "ipfs swarm connect /ip4/${IP}/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5"
    do
	sleep 1
    done

    cmd //c "ipfs bootstrap add /ip4/${IP}/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5"
else
    until ./ipfs swarm connect /ip4/${IP}/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5
    do
	sleep 1
    done
    ./ipfs bootstrap add /ip4/${IP}/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5
fi

cd ../..
mkdir certs

touch .init-done
