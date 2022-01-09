#!/bin/bash
# Version 20210922_1904

if [ "$OS" == "Windows_NT" ]
then
    PYTHON_BIN=python
    echo ""
    echo "Installing Visual Studio C++ Build Tools"
    src/init/deps/Win/vs_BuildTools.exe --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 Microsoft.VisualStudio.Component.Windows10SDK.18362 --passive --norestart --addProductLang en-us --installWhileDownloading
    echo -en "Press ENTER when Setup is finished. "
    read -r RESPONSE
else
    PYTHON_BIN="python3"
fi

echo "${PYTHON_BIN}"

if [ -x "$(command -v ${PYTHON_BIN})" ]; then
   PYTHON=${PYTHON_BIN}
else
   exit 1
fi

if [ -x "$(command -v pip3)" ]; then
   PIP="${PYTHON_BIN} -m pip"
else
   exit 2
fi

echo -en "Installing Python3 dependencies... "

if [ -f /etc/os-release ]; then
# CentOS 8 requires sudo for pip upgrade
   if [ "$(grep -E "^NAME=" /etc/os-release | grep CentOS)"  ]; then
      sudo $PIP install --upgrade pip -qq > /dev/null 2>&1
   fi
else
   $PIP install --upgrade pip -qq > /dev/null 2>&1
fi

$PIP install ipfshttpclient==0.8.0a2 web3 psutil --upgrade -qq > /dev/null 2>&1
echo "done"

[ -d certs ] || mkdir certs

touch .init-done
