# Ethernity Python Client

This repository provides a python example of Proof of eXecution code.


# 1. Create config file:

```
cat << EOF > config
ADDRESS=0x627306090abaB3A6e1400e9345bC60c78a8BEf57
PRIVATE_KEY=C87509A1C067BBDE78BEB793E6FA76530B6382A4C0241E5E4A9EC0A0F44DC0D3
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



