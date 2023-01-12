#!/bin/bash
#$1

if [[ $1 == "" || $4 == "" ]]; then
	echo "plz give argument link (uses26)"
	echo "plz give project name (JSQlParser)"
    exit
fi
#outputDir="Clustering-Useful-Directories"
outputDir="$5"
if [[ ! -d "$outputDir" ]]; then
    mkdir "$outputDir"
fi
uses_name=$(echo $1 | rev | cut -d'/' -f1 | rev)
#echo ${uses_name}
never_access=${uses_name}
#===========Which are never ever accessed=========

while read line 
do
	#file_name=$(echo $line | cut -d',' -f2) 	
    #echo "file_name=$file_name"
    #check if a line contains a string
    if [[ $line == *"target"* ]]; then
        #echo "**** ${file_name}"
	    prefix_remove=$(sed 's;^.*target;;g' <<< ${line})
    	echo ${prefix_remove} >> "never_accessed_unsort_Prefix_remove.csv"
    fi
done < $1  #"contents_of_all_files_which_are_never_ever_accessed.csv"   

sort "never_accessed_unsort_Prefix_remove.csv" > "$outputDir/${never_access}_sort_Prefix_remove.csv"
rm  "never_accessed_unsort_Prefix_remove.csv"

#======================================== useful.csv ($3)===============================

uses_name=$(echo $3 | rev | cut -d'/' -f1 | rev)
useful=${uses_name}

while read line 
do
    if [[ $line == *"target"* ]]; then
    	#file_name=$(echo $line | cut -d',' -f2)	
	    prefix_remove=$(sed 's;^.*target;;g' <<< ${line})
    	echo ${prefix_remove} >> "useful_unsort_Prefix_remove.csv"
    fi
done < $3  #"contents_of_all_files_which_are_accessed.csv"   
sort "useful_unsort_Prefix_remove.csv" > "$outputDir/${useful}_sort_Prefix_remove.csv"
rm  "useful_unsort_Prefix_remove.csv"

#================= FOR COMPARING this two sorted csv =========================
allClusters=()
if [[ -f  "$outputDir/$4-unnecessary.csv" ]]; then
    rm "$outputDir/$4-unnecessary.csv"
fi
while read line
do
    count_directory_structure=$(echo $line | tr -cd / | wc -c)
    path=""
    boundary=$((count_directory_structure + 1))
    #for i in {1..$count_directory_structure}
    for (( i=2; i<=$boundary; i++ ))
    do
        #echo "i=$i"
        #echo "HI** $count_directory_structure"
        dir=$(echo $line | cut -d'/' -f1-$i)
        #echo "dir=$dir"
        if [[ ! " ${allClusters[*]} " =~ " ${dir} " ]]; then

            if [[ $i < $boundary ]]; then
                found=$(grep -r "$dir/" "$outputDir/${useful}_sort_Prefix_remove.csv" | wc -l)
                path=$dir"/"
            else
                found=$(grep -r "$dir" "$outputDir/${useful}_sort_Prefix_remove.csv" | wc -l)
            fi

            if [[ $found -eq 0 ]]; then
                if [[ $i -eq $boundary ]]; then
                    path="target$dir"
                else
                    path="target$dir/"
                fi
                echo $path >> "$outputDir/$4-unnecessary-with-repetition.csv"
                allClusters+=($path)
                break;
            fi
        else
            echo "need to count same cluster name"
        fi

    done
done <  "$outputDir/${never_access}_sort_Prefix_remove.csv"
sort "$outputDir/$4-unnecessary-with-repetition.csv" | uniq -c > "$outputDir/$4.csv"

rm "$outputDir/${useful}_sort_Prefix_remove.csv"
rm "$outputDir/${never_access}_sort_Prefix_remove.csv"
rm "$outputDir/$4-unnecessary-with-repetition.csv"
