# Ethernity Python Client

This repository provides a python example of Proof of eXecution code.


# 1. Create config file:

```
cat << EOF > config
ADDRESS=0xd812E09e331e3bba6ecC6d3E10a8Ac461A77a7F2
PRIVATE_KEY=08075e59c931bcc4fc7a57e79a566a47345fff4048f6970168696d76796a4df3
EOF
```


# 2. Run a script with a fileset

```
$./pox-do -s <script> -f <fileset>

script - a python script to be uploaded via IPFS for running
fileset - a fileset to be uploaded via IPFS for running
```

Examples:

```
edit scripts/uppercase/fileset/file1.txt
./pox-do -s scripts/uppercase/uppercase.py -f scripts/uppercase/fileset

edit scripts/cos-bench/fileset/config
./pox-do -s scripts/cos-bench/cos-bench.py -f scripts/cos-bench/fileset
```



