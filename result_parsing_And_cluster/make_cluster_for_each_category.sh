#!/bin/bash
#$1

if [[ $1 == "" ]]; then
	echo "plz give project list in a csv (projects_name.csv)"
    exit
fi
#outputDir="Clustering-Useful-Directories"
outputDir="$2"
if [[ ! -d "$outputDir" ]]; then
    mkdir "$outputDir"
fi

while read row_line
do
    echo $row_line
    uses_name="${row_line}-$3" #$(echo $1 | rev | cut -d'/' -f1 | rev) #normally it will be never-accessed
    #echo ${uses_name}
    never_access=${uses_name}
    #===========Which are never ever accessed=========
    
    while read line 
    do
        #check if a line contains a string
        if [[ $line == *"target"* ]]; then
            #echo "**** ${file_name}"
    	    prefix_remove=$(sed 's;^.*target;;g' <<< ${line})
        	echo ${prefix_remove} >> "never_accessed_unsort_Prefix_remove.csv"
        fi
    done < "Output/$uses_name"  #"contents_of_all_files_which_are_never_ever_accessed.csv"   
    if [[ -f   "never_accessed_unsort_Prefix_remove.csv" ]]; then
        sort "never_accessed_unsort_Prefix_remove.csv" > "$outputDir/${never_access}_sort_Prefix_remove.csv"
        rm  "never_accessed_unsort_Prefix_remove.csv"
    else
        touch  "$outputDir/${never_access}_sort_Prefix_remove.csv"
    fi
    
    #======================================== useful.csv ($3)===============================
    
    uses_name="${row_line}-$4" #$(echo $3 | rev | cut -d'/' -f1 | rev) #normally it will be useful
    useful=${uses_name}
    
    while read line 
    do
        if [[ $line == *"target"* ]]; then
        	#file_name=$(echo $line | cut -d',' -f2)	
    	    prefix_remove=$(sed 's;^.*target;;g' <<< ${line})
        	echo ${prefix_remove} >> "useful_unsort_Prefix_remove.csv"
        fi
    done < "Output/$uses_name"  #"contents_of_all_files_which_are_accessed.csv"   
    
    if [[ -f "useful_unsort_Prefix_remove.csv" ]]; then
        sort "useful_unsort_Prefix_remove.csv" > "$outputDir/${useful}_sort_Prefix_remove.csv"
        rm  "useful_unsort_Prefix_remove.csv"
    else
        touch "$outputDir/${useful}_sort_Prefix_remove.csv"
    fi

    
    #================= FOR COMPARING this two sorted csv =========================
    allClusters=()
    if [[ -f  "$outputDir/${row_line}-unnecessary.csv" ]]; then
        rm "$outputDir/${row_line}-unnecessary.csv"
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
                    echo $path >> "$outputDir/${row_line}-unnecessary-with-repetition.csv"
                    allClusters+=($path)
                    break;
                fi
            else
                echo "need to count same cluster name"
            fi
    
        done
    done <  "$outputDir/${never_access}_sort_Prefix_remove.csv"
    if [[ -f "$outputDir/${row_line}-unnecessary-with-repetition.csv" ]]; then
        sort "$outputDir/${row_line}-unnecessary-with-repetition.csv" | uniq -c > "$outputDir/${row_line}.csv"
        rm "$outputDir/${row_line}-unnecessary-with-repetition.csv"
    fi

    rm "$outputDir/${useful}_sort_Prefix_remove.csv"
    rm "$outputDir/${never_access}_sort_Prefix_remove.csv"

done < $1
