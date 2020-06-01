#!/bin/bash
cd .tmp/go-ipfs/
./ipfs daemon 2>&1 >> /dev/null &

IP=`getent hosts ipfs.ethernity.cloud | awk '{print $1}'`

until ./ipfs swarm connect /ip4/$IP/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5
do
  sleep 1
done
./ipfs bootstrap add /ip4/$IP/tcp/4001/ipfs/QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5

for hash in `./ipfs pin ls | awk '{print $1}'`; do ./ipfs pin rm $hash 2>&1 >> /dev/null ; done




