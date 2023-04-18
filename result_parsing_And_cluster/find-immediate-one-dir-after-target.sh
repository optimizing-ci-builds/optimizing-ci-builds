#!/bin/bash
if [[ $1 == "" || $2 == "" ]]; then
    echo "provide args (Clustering_Unused_dir, One-level-File-or-directory-after-target2)"
    exit
fi

echo "unused_csv_file,unused_dirs" >> $2 

find $1 -maxdepth 1 -size +0 -print > all_files.csv
while read line 
do
    proj_name=$(echo $line | cut -d'/' -f2 | cut -d'_' -f1)
    only_csv=$(echo $line | cut -d'/' -f2)
    if [[ $only_csv == "" ]]; then
        continue
    else
        echo -n "$only_csv," >> $2 #job-name
    fi

    arr=($(rev $line | cut -d'/' -f1-3 | rev | sort -u | grep  "^target/"))
    for i in "${arr[@]}"
    do
      echo -n "$i~" >> $2 # each unused directory is separated by ~ sign
       # do whatever on "$i" here
    done
    echo "" >> $2
done < "all_files.csv"
#(ls $1) >
