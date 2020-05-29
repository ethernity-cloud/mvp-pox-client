#!/bin/bash
mkdir .tmp
cd .tmp
wget https://github.com/ipfs/go-ipfs/releases/download/v0.4.19/go-ipfs_v0.4.19_linux-386.tar.gz 2>&1 >> /dev/null
tar zxvf go-ipfs_v0.4.19_linux-386.tar.gz 2>&1 >> /dev/null
cd go-ipfs
./ipfs init 2>&1 >> /dev/null
./ipfs daemon 2>&1 >> /dev/null &
sleep 3
cd ../..
touch .init-done


