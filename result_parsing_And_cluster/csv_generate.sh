#!/bin/bash
#$1="Clustering-Unused-Directories/"
#cat $1/* | sort -k1 -n -r -t' ' | uniq  > all_unnecessary.csv
if [[ $1 == "" || $2 == "" || $3 == "" ]]; then
    echo "please give Ununsed directory"
    echo "please give Output directory (Parsed-Results-of-Different-clusters/Result_Unnnecessary_file.csv)"
    echo "please give Output directory (Parsed-Results-of-Different-clusters/Histogram_for_each_unnecessary_file.csv)"
    exit
fi

currentDir=$(pwd)
cd $1
total=0
unnecessary_files=($(ls))
arr_unnecessary_files_items=()
echo $unnecessary_files
# This will generate the 1st csv (projec, job, #unnecessary files)
for job in "${unnecessary_files[@]}"
do
    count_files_per_job=0
    while read line 
    do
        x=$(echo $line | cut -d' ' -f1 | sed 's/ //g')
        unnecessary_file_item=$(echo $line | cut -d' ' -f2 | sed 's/ //g' | cut -d'/' -f7-)
        if [[ ! "${arr_unnecessary_files_items[*]}" =~ "${unnecessary_file_item}" ]]; then 
            echo "${unnecessary_file_item}" >> "$currentDir/x.csv"
            arr_unnecessary_files_items+=(${unnecessary_file_item}) #number of unique files
        fi
        count_files_per_job=$(($count_files_per_job + $x))
    done < $job
    total=$(( $total+ $count_files_per_job))
    echo -n "$(echo $job | cut -d'#' -f1)" >> "$currentDir/$2" #project_name
    echo -n ",$(echo $job | cut -d'#' -f2 | sed 's/.csv//g')" >> "$currentDir/$2" #job_name
    echo ",$count_files_per_job" >> "$currentDir/$2" #count of unnecessary files in a job    
done    
echo "total=$total"
len=${#arr_unnecessary_files_items[@]}
echo $len
cd $currentDir
bash csv_generate_2.sh "$1" "$3"

#for item in ${arr_unnecessary_files_items[@]}
#do
    #echo $item
#    x=$(grep -r "$item" $1 ) 
#done
#cat $1/* | sort -k1 -n -r -t' ' | tr -s " " | uniq  > all_unnecessary.csv
