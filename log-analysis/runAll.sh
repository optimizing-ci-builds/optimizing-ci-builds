#!/bin/bash

if [[ $1 == "" ]]; then
    echo "plz give the branch name"
fi

python3 download_logs.py $1 

python3 log_analysis.py logs/$1/  > Result_$1
