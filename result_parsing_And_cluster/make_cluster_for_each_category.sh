#!/bin/bash

if [[ $1 == "" ]]; then
	echo "plz give project list in a csv (projects_name.csv)"
    exit
fi
outputDir="$2"
if [[ ! -d "$outputDir" ]]; then
    mkdir "$outputDir"
fi

echo $1
uses_name="${1}_$3" #$(echo $1 | rev | cut -d'/' -f1 | rev) #normally it will be never-accessed
never_access=${uses_name}
#===========Which are never ever accessed=========


cat "data/Inotify-Parse-Result/$uses_name.csv"  > "$outputDir/${never_access}_sort_Prefix_remove.csv"
#======================================== useful.csv ($3)===============================

uses_name="${1}_$4" #$(echo $3 | rev | cut -d'/' -f1 | rev) #normally it will be useful
useful=${uses_name}

cat "data/Inotify-Parse-Result/$uses_name.csv"  > "$outputDir/${useful}_sort_Prefix_remove.csv"

#================= FOR COMPARING this two sorted csv =========================
allClusters=()
if [[ -f  "$outputDir/${1}-unnecessary.csv" ]]; then
    rm "$outputDir/${1}-unnecessary.csv"
fi
while read line
do
    count_directory_structure=$(echo $line | tr -cd / | wc -c)

    path=""
    boundary=$((count_directory_structure + 1))
    #for i in {1..$count_directory_structure}
    for (( i=2; i<=$boundary; i++ ))
    do
        dir=$(echo $line | cut -d'/' -f1-$i)
        if [[ ! " ${allClusters[*]} " =~ " ${dir} " ]]; then
            if [[ $i < $boundary ]]; then # For handling directory and files differently
                found=$(grep -r "$dir/" "$outputDir/${useful}_sort_Prefix_remove.csv" | wc -l)
                path=$dir"/"
            else
                found=$(grep -r "$dir" "$outputDir/${useful}_sort_Prefix_remove.csv" | wc -l)
            fi
            if [[ $found -eq 0 ]]; then
                if [[ $i -eq $boundary ]]; then
                    path="$dir" # it will be file
                else
                    path="$dir/" # it will be directory
                fi
                echo $path >> "$outputDir/${1}-unnecessary-with-repetition.csv"
                allClusters+=($path)
                break;
            fi
        else
            echo "need to count same cluster name"
        fi

    done
done <  "$outputDir/${never_access}_sort_Prefix_remove.csv"
#exit
if [[ -f "$outputDir/${1}-unnecessary-with-repetition.csv" ]]; then
    sort "$outputDir/${1}-unnecessary-with-repetition.csv" | uniq -c > "$outputDir/${1}.csv"
    rm "$outputDir/${1}-unnecessary-with-repetition.csv"
fi

rm "$outputDir/${useful}_sort_Prefix_remove.csv"
rm "$outputDir/${never_access}_sort_Prefix_remove.csv"

