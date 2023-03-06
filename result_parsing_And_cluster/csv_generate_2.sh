#!/bin/bash
#for item in ${arr_unnecessary_files_items[@]}
currentDir=$(pwd)
cd $1
while read line
do
    #echo $item
    files=($(grep -lr "${line}$"))
    total=0
    for file in ${files[@]}
    do
        echo $file
        count=0
        proj_name=$(echo $file | cut -d':' -f1 | cut -d'#' -f1)
        job_name=$(echo $file | cut -d':' -f1 | cut -d'#' -f2 | sed 's/.csv//g')
        #echo $(cat file)
        res=($(cat $file | cut -d'/' -f7- | grep -x -n "\b${line}$")) # |)) #13:lib/
        echo $res
        #echo "len=${#res[@]}"
        for i in ${res[@]}
        do
            line_num=$(echo $i | cut -d':' -f1)
            echo $line_num
            #exit
            ll=$(head -${line_num} $file | tail -1)
            echo $ll
            l=$(echo $ll | cut -d'/' -f1 | sed 's/ //g')
            echo $l
            #exit
            count=$(($count + $l)) 
            total=$(($total+$l))
        done
        if [[ $count -gt 0 ]]; then
            echo "$line,$proj_name,$job_name,$count" >> "$currentDir/tmp.csv"
        fi
    done
    echo "total=$total"
    exit
done < "../x.csv"
#sort -k1 "$currentDir/Histogram_for_each_unnecessary_file.csv"
sort -k4 -n -t, -r "$currentDir/tmp.csv" > "$currentDir/Histogram_for_each_unnecessary_file.csv"
rm "$currentDir/tmp.csv"
