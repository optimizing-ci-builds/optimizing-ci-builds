#!/bin/bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "provide args (Clustering_Unused_dir , Result-File)"
    exit
fi

find $1 -maxdepth 1 -size +0 -print > all_files.csv
while read line 
do
    echo -n "$line" >> $2 #job-name
    arr=($(rev $line | cut -d'/' -f1-3 | rev | sort -u | grep  "^target/"))
    for i in "${arr[@]}"
    do
      echo -n ",$i" >> $2
       # do whatever on "$i" here
    done
    echo "," >> $2
done < "all_files.csv"
#(ls $1) >
