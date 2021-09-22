#!/bin/bash
#
# Copyright (C) 2021 Ethernity HODL UG
#
# This file is part of ETHERNITY CLIENT.
#
# ETHERNITY SC is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# Version is 20210922_1905
# Tested distribution:
# ubuntu-18.04.5-desktop-amd64
# ubuntu-20.04.3-desktop-amd64
# ubuntu-21.04-desktop-amd64
# debian-11.0.0-amd64
# debian-10.10.0-amd64
# CentOS-7-x86_64-Everything-2009 - no chance it will work
# CentOS-Stream-8-x86_64-20210907
# TBD: Windows setup (another script)

# Error exit codes:
# 1 - run as root
# 2 - doesn't have sudo permission
# 3 - unsupported distribution

PKG_MGR=""
GIT=""
PYTHON=""
PIP=""
CURL=""
DNS=""
DEV=""

if [[ "$(whoami)" == root ]]; then
   echo "This script doesn't support run as root"
   exit 1
elif [ ! "$(sudo date)" ]; then
   echo "You need sudo permission to run this script, consider add current user to wheel group with command usermod -aG wheel $(whoami) or usermod -aG sudo $(whoami)"
   exit 2
fi

if [ -f /etc/os-release ]; then
   case "$(grep -E "^NAME=" /etc/os-release)" in
      *Ubuntu*)
         if [[ ! "$(lsb_release -r)" == *18.04* && ! "$(lsb_release -r)" == *20.04* && ! "$(lsb_release -r)" == *21.04* ]]; then
            echo "This script supports: Ubuntu desktop 18.04, 20.04, 21.04; Debian 10, 11 only"
            exit 3
         else
            PKG_MGR="apt"
         fi
         ;;
      *Debian*)
         if [[ ! "$(lsb_release -r)" == *10* && ! "$(lsb_release -r)" == *11* ]]; then
            echo "This script supports: Ubuntu desktop 18.04, 20.04, 21.04; Debian 10, 11 only"
            exit 3
         else
            PKG_MGR="apt"
         fi
         ;;
      *CentOS*)
         if [ "$(grep -E "^VERSION_ID=" /etc/os-release | grep "8")" ]; then
            PKG_MGR="yum"
            DEV="gcc python36-devel"
         else
            echo "This script supports: Ubuntu desktop 18.04, 20.04, 21.04; Debian 10, 11 only"
	         exit 3
         fi
         ;;
      *)
         echo "This script supports: Ubuntu desktop 18.04, 20.04, 21.04; Debian 10, 11 only"
         exit 3
         ;;
   esac
else
   echo "This script supports: Ubuntu desktop 18.04, 20.04, 21.04; Debian 10, 11 only"
   exit 3
fi

# Setup full stack of supplicants before installation
if [ ! -x "$(command -v git)" ]; then
   GIT="git"
fi

if [ ! -x "$(command -v python3)" ]; then
   PYTHON="python3"
fi

if [ ! -x "$(command -v pip3)" ]; then
   PIP="python3-pip"
fi

if [ ! -x "$(command -v curl)" ]; then
  CURL="curl"
fi

if [ ! -x "$(command -v nslookup)" ]; then
   if [[ ${PKG_MGR} == apt ]]; then
      DNS="dnsutils"
   elif [[ ${PKG_MGR} == yum ]]; then
      DNS="bind-utils"
   fi
fi

sudo ${PKG_MGR} -y install ${GIT} ${PYTHON} ${PIP} ${CURL} ${DNS} ${DEV}

if [ -d "mvp-pox-client" ]; then
   rm -rf mvp-pox-client
fi

git clone https://github.com/ethernity-cloud/mvp-pox-client.git

cd mvp-pox-client

utils/linux/ethkey generate random > client_wallet.txt
grep "address" client_wallet.txt | sed "s/address: /ADDRESS=/" > config && grep "secret" client_wallet.txt | sed "s/secret:  /PRIVATE_KEY=/" >> config

echo "To fund the wallet on testnet and start testing you should open the bloxberg faucet at:
https://faucet.bloxberg.org
Your address is $(grep "address" client_wallet.txt | sed "s/address: //")"

if [ -x "$(command -v xdg-open)" ]; then
   xdg-open https://faucet.bloxberg.org/ > /dev/null 2>&1
fi
