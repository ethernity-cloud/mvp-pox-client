#!/bin/bash
cd .tmp/go-ipfs/
./ipfs daemon 2>&1 >> /dev/null &

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

for hash in `./ipfs pin ls | awk '{print $1}'`; do ./ipfs pin rm $hash 2>&1 >> /dev/null ; done




