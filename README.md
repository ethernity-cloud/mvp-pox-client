# Ethernity Python Client

This repository provides a python example of Proof of eXecution code.


# 1. Create config file:

```
cat << EOF > config
PUBLIC_KEY=0x0123456789abcdef0123456789abcdef01234567
PRIVATE_KEY=0x0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF
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



