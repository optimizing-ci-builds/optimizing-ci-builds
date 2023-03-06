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
        echo $file
        proj_name=$(echo $file | cut -d':' -f1 | cut -d'#' -f1)
        job_name=$(echo $file | cut -d':' -f1 | cut -d'#' -f2) #| sed 's/.csv//g')
        res=$(grep -r "${line}" $file | cut -d'/' -f1 | sed 's/ //g')
        #echo "$line,$proj_name,$job_name,$res"
        #after_colon=$(echo $item | cut -d':' -f2)
        #echo "after_colon=$after_colon"
        #count_unnecessary_file=$(echo $after_colon | cut -d'/' -f1)
        echo "$line,$proj_name,$job_name,$res" >> "$currentDir/Result_for_each_unnecessary_file.csv"
    done
    exit
done < "../x.csv"
