#!/bin/bash
if [[ $1 == "" ]]; then
    echo "Unused_clusters_info.csv" 
    exit
fi

echo  "job_name,#unnecessary_files_without_maven(can ignore .git), #unnecessary_files_with_maven,#useful_file_with_maven" > "Paper-Table-1.csv"

while read line
do
   job_name=$(echo $line | cut -d',' -f5) 
   echo $job_name
   echo -n $job_name >> "Paper-Table-1.csv"
   unnecessary_file_without_maven=$(grep -v -e "target" -e ".git" "Clustering-Unused-Directories/$job_name" | wc -l)
   unnecessary_file_with_maven=$(grep -r "target" "Clustering-Unused-Directories/$job_name" | wc -l)
   useful_file_with_maven=$(grep -r "target" "Clustering-Used-Directories/$job_name" | wc -l)
   echo -n ",$unnecessary_file_without_maven" >> "Paper-Table-1.csv"
   echo -n ",$unnecessary_file_with_maven" >> "Paper-Table-1.csv"
   echo -n ",$useful_file_with_maven" >>  "Paper-Table-1.csv"
   echo "" >> "Paper-Table-1.csv"
   #exit
done < $1
