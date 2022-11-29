import os
from enum import Enum
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv('.env' if os.path.exists('.env') else '.env.config') 
except ImportError as e:
    pass

print(os.environ.get('ADDRESS'))

class bcolors(Enum):
    MESSAGE = '\033[94m'
    INFO = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    _END = '\033[0m'


parser = argparse.ArgumentParser(description="Ethernity PoX request")
parser.add_argument("-a", "--address", help="Etherem address (0x627306090abab3a6e1400e9345bc60c78a8bef57)", default="0x627306090abab3a6e1400e9345bc60c78a8bef57")
parser.add_argument("-b", "--bandwidth", help="Amount of bandwidth (GB)", default="1")
parser.add_argument("-c", "--cpu", help="Number of CPUs (count)", default="1")
parser.add_argument("-d", "--storage", help="Amount of storage (GB)", default="40")
parser.add_argument("-e", "--instances", help="Number of instances to run simmultaneously (count)", default="1")
parser.add_argument("-f", "--fileset", help="PATH of the fileset", required=True, default="")
parser.add_argument("-j", "--ipfsgateway", help="IPFS Gateway host url", default="")
parser.add_argument("-i", "--image", help="IPFS location of docker repository in format [HASH:container]", default="QmexKQm3wqeV63kR1G83ktCzodMAsdYRi4vV4RGhn1e1NT:etny-pynithy")
parser.add_argument("-g", "--ipfshash", help="IPFS Gateway host url", default="QmRBc1eBt4hpJQUqHqn6eA8ixQPD3LFcUDsn6coKBQtia5")
parser.add_argument("-k", "--private_key", help="Etherem privatekey (c87509a1c067bbde78beb793e6fa76530b6382a4c0241e5e4a9ec0a0f44dc0d3)", default="08075e59c931bcc4fc7a57e79a566a47345fff4048f6970168696d76796a4df3")
parser.add_argument("-l", "--contract_address", help="constractaddress", default="0x549A6E06BB2084100148D50F51CF77a3436C3Ae7")
parser.add_argument("-m", "--memory", help="Amount of memory (GB)", default="1")
parser.add_argument("-n", "--node", help="Node Address", default="")
parser.add_argument("-o", "--ipfs_cloud", help="Ipfs cloud address", default='ipfs.ethernity.cloud')
parser.add_argument("-p", "--ipfspassword", help="IPFS Gateway password", default="")
parser.add_argument("-r", "--redistribute", help="Check and redistribute IPFS payload after order validation", action='store_true')
parser.add_argument("-s", "--script", help="PATH of python script", required=True, default="")
parser.add_argument("-t", "--duration", help="Amount of time allocated for task (minutes)", default="60")
parser.add_argument("-u", "--ipfsuser", help="IPFS Gateway username", default="")
parser.add_argument("-w", "--web3_provider", help="Web3 Http Provider", default="https://bloxberg.ethernity.cloud")


arguments = {
    str: ['address', 'private_key', 'image', 'script', 'fileset', 'redistribute', 'ipfsgateway', 'ipfshash', 'ipfsuser', 'ipfspassword', 'contract_address', 'node', 'web3_provider', 'ipfs_cloud'],
    int: ['cpu', 'memory', 'storage', 'storage', 'bandwidth', 'duration', 'instances']
}
