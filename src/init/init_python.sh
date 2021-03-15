#!/bin/bash

if [ "$OS" == "Windows_NT" ]
then
    PYTHON_BIN=python
else
    PYTHON_BIN=python3
fi

echo "${PYTHON_BIN}"

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
$PIP install --upgrade pip
$PIP install ipfshttpclient web3 psutil

cd ../..
mkdir certs

touch .init-done