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

# Current script version is 20210914_1900
# Dedicated to Ubuntu only
# TBD: rpm-based distrs, windows setup (separate script)

# Setup full stack of supplicant before installation
if [ ! -x "$(command -v git)" ]; then
   GIT=git
fi

if [ ! -x "$(command -v python3)" ]; then
   PYTHON=python3
fi

if [ ! -x "$(command -v pip3)" ]; then
   PIP=python3-pip
fi

if [ ! -x "$(command -v curl)" ]; then
  CURL=curl
fi

sudo apt -y install ${GIT} ${PYTHON} ${PIP} ${CURL}

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
   xdg-open https://faucet.bloxberg.org/
fi
