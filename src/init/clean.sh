#!/bin/bash
cd .tmp/go-ipfs/
./ipfs daemon 2>&1 >> /dev/null &
sleep 3
for hash in `./ipfs pin ls | awk '{print $1}'`; do ./ipfs pin rm $hash 2>&1 >> /dev/null ; done


