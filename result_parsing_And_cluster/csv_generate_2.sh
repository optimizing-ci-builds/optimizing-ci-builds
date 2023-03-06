#!/bin/bash
#for item in ${arr_unnecessary_files_items[@]}A
currentDir=$(pwd)
cd $1
while read line
do
    #echo $item
    files=($(grep -lr "${line}$"))
    #echo $m
    #echo ${#m[@]}
    for file in ${files[@]}
    do
        #echo $file
        count=0
        proj_name=$(echo $file | cut -d':' -f1 | cut -d'#' -f1)
        job_name=$(echo $file | cut -d':' -f1 | cut -d'#' -f2 | sed 's/.csv//g')
        res=($(grep -r "${line}" $file | cut -d'/' -f1 | sed 's/ //g'))
        echo "len=${#res[@]}"
        for i in ${res[@]}
        do
           count=$((count + i)) 
        done
        echo "$line,$proj_name,$job_name,$count" >> "$currentDir/Histogram_for_each_unnecessary_file.csv"
    done
    #exit
done < "../x.csv"
