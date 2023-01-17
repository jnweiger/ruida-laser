#! /usr/bin/env bash
#
# author: Heinz Blaettner	heinz@fabmail.org
#
PN=$(basename "$0")
SCRIPT=$(readlink -f "$0")
SCRIPT_DIR=$(dirname $SCRIPT)
SCREEN="/usr/bin/screen"

###
#PROXY_BIN="$HOME/src/github/jnweiger/ruida-laser/RuidaProxy/RuidaProxy.py"
PROXY_BIN="RuidaProxy.py"
PROXY_DIR=$SCRIPT_DIR
PROXY_PATH="$PROXY_DIR/$PROXY_BIN"


printf "\n### $PN\n"
printf "# PROXY_DIR = <$PROXY_DIR>\n"
printf "# PROXY_BIN = <$PROXY_BIN>\n"

cd $PROXY_DIR

$SCREEN -L -S RuidaProxy -D -m $PROXY_PATH 172.22.30.12 172.22.30.50
$SCREEN -ls
