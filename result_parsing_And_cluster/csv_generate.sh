#!/bin/bash
#$1="Clustering-Unused-Directories/"
#cat $1/* | sort -k1 -n -r -t' ' | uniq  > all_unnecessary.csv
currentDir=$(pwd)
cd $1
unnecessary_files=($(ls))
echo $unnecessary_files
for job in "${unnecessary_files[@]}"
do
    count_files_per_job=0
    while read line 
    do
        x=$(echo $line | cut -d' ' -f1 | sed 's/ //g')
        #echo "x=${x}"
        count_files_per_job=$(($count_files_per_job + $x))
    done < $job

    echo -n "$(echo $job | sed 's/.csv//g')" >> "$currentDir/Result_Unnnecessary_file.csv"
    echo ",$count_files_per_job" >> "$currentDir/Result_Unnnecessary_file.csv"
done    
