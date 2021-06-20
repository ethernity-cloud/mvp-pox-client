#!/bin/bash

if [ "$OS" == "Windows_NT" ]
then
    PYTHON_BIN=python
    echo ""
    echo "Installing Visual Studio C++ Build Tools"
    src/init/deps/Win/vs_BuildTools.exe --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 Microsoft.VisualStudio.Component.Windows10SDK.18362 --passive --norestart --addProductLang en-us --installWhileDownloading
    echo -en "Press ENTER when Setup is finished. "
    read -r RESPONSE
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

echo -en "Installing Python3 dependencies... "
$PIP install --upgrade pip  2>&1 > /dev/null
$PIP install ipfshttpclient web3 psutil --upgrade 2>&1 > /dev/null
echo "done"

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

echo "Installing and running go-ipfs"
curl ${URL} --output ${FILENAME}
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
