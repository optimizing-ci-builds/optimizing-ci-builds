#!/bin/bash
#There are total _c_m__a,(_cm__a,cm__a),( _cma,cma),c,m
#I will not consider _c_m__a because it is not creating, modifying and accessing any file (src/test..) at the build time
#So, I considered 1st group(_cm__a,cm__a) and then 2nd group(__cma,cma) in the following code. It is noteworthy that all files in c and m are generated in target/
#$1

if [[ $1 == "" || $4 == "" ]]; then
	echo "plz give argument link (uses26)"
	echo "plz give project name (JSQlParser)"
    exit
fi
outputDir="Clustering-Useful"
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
	    prefix_remove=$(sed 's;^.*target/;;g' <<< ${line})
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
	    prefix_remove=$(sed 's;^.*target/;;g' <<< ${line})
    	echo ${prefix_remove} >> "useful_unsort_Prefix_remove.csv"
    fi
done < $3  #"contents_of_all_files_which_are_accessed.csv"   
sort "useful_unsort_Prefix_remove.csv" > "$outputDir/${useful}_useful_sort_Prefix_remove.csv"
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
    #for i in {1..$count_directory_structure}
    for (( i=1; i<=$count_directory_structure; i++ ))
    do
        #echo "i=$i"
        dir=$(echo $line | cut -d'/' -f1-$i)
        #echo "dir=$dir"
        if [[ ! " ${allClusters[*]} " =~ " ${dir} " ]]; then
            found=$(grep -r "$dir" "$outputDir/${useful}_useful_sort_Prefix_remove.csv" | wc -l)
            #echo $found
            path=$dir"/"
            if [[ $found -eq 0 ]]; then
                echo $path >> "$outputDir/$4-unnecessary-with-repetition.csv"
                allClusters+=($path)
                break;
            fi
        else
            echo "need to count same cluster name"
        fi

    done
done <  "$outputDir/${never_access}_sort_Prefix_remove.csv"
sort "$outputDir/$4-unnecessary-with-repetition.csv" | uniq -c > "$outputDir/$4-unnecessary.csv"

rm "$outputDir/${useful}_useful_sort_Prefix_remove.csv"
rm "$outputDir/${never_access}_sort_Prefix_remove.csv"
rm "$outputDir/$4-unnecessary-with-repetition.csv"
