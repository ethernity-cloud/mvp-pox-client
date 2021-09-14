#!/bin/bash

if [ -x src/init/init_python.sh ]; then
   src/init/init_python.sh || { ec=$?; exit $ec; }
   rm .init-done
else
   exit 3
fi

[ -d .tmp ] || mkdir .tmp
cd .tmp

IPFS_VERSION='v0.6.0'
MIRROR="https://dist.ipfs.io/go-ipfs/${IPFS_VERSION}/"

if [ "$OS" == "Windows_NT" ]
then
    FILENAME="go-ipfs_${IPFS_VERSION}_windows-amd64.zip"
    EXTRACT_COMMAND='unzip -o'
else
    FILENAME="go-ipfs_${IPFS_VERSION}_linux-amd64.tar.gz"
    EXTRACT_COMMAND='tar -zxvf'
fi

URL=${MIRROR}${FILENAME}

if [ -x "$(command -v curl)" ]; then
   echo "Installing and running go-ipfs"
   curl ${URL} --output ${FILENAME}
else
   exit 4
fi

${EXTRACT_COMMAND} ${FILENAME} 2>&1 > /dev/null
cd go-ipfs
./ipfs init 2>&1 > /dev/null
./ipfs daemon 2>&1 > /dev/null &

echo "Conneting to Ethernity IPFS network"

IP=`nslookup ipfs.ethernity.cloud 2>&1 | grep -A 1 ethernity.cloud | grep 'Address' | awk '{print $2}'`

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
[ -d certs ] || mkdir certs

touch .init-done
