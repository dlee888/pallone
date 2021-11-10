#!/bin/bash

# Get to a predictable directory, the directory of this script
cd ~/bots/pallone

# [ -e environment ] && . ./environment

while true; do
    git pull
    python3.8 main.py

    (( $? == 69 )) && break

    echo '==================================================================='
    echo '=                       Restarting                                ='
    echo '==================================================================='
done