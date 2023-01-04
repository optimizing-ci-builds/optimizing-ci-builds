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
if [[ ! -d "Clustering" ]]; then
    mkdir "Clustering"
fi
uses_name=$(echo $1 | rev | cut -d'/' -f1 | rev)
echo ${uses_name}
never_access=${uses_name}
#===========Which are never ever accessed=========

while read line 
do
	file_name=$(echo $line | cut -d',' -f2) 	
	prefix_remove=$(sed 's;^.*target/;;g' <<< ${file_name})
	echo ${prefix_remove} >> "cm_unsort_Prefix_remove.csv"
done < $1  #"contents_of_all_files_which_are_never_ever_accessed.csv"   

sort "cm_unsort_Prefix_remove.csv" > "Clustering/${uses_name}_sort_Prefix_remove.csv"
rm  "cm_unsort_Prefix_remove.csv"

#==========For Making Cluster============
group_arr=$(cut -f1 -d'/' "Clustering/${uses_name}_sort_Prefix_remove.csv"  | sort | uniq)
echo "group,count" > "Clustering/${uses_name}_Clustering.csv"
for group in ${group_arr[@]}; do
    count=$(grep -r "$group" "Clustering/${uses_name}_sort_Prefix_remove.csv" | wc -l)
    echo "$group,$count" >> "Clustering/${uses_name}_Clustering.csv"
    if [[ $group == "site" ]]; then
        grep -r "site" "Clustering/${uses_name}_sort_Prefix_remove.csv"  > "tmp_site.csv"
         group_site_arr=$(cut -f2 -d'/' "tmp_site.csv"  | sort | uniq)
         for group_site in ${group_site_arr[@]}; do
            count_site=$(grep -r "${group_site}" "tmp_site.csv" | wc -l)
            #echo ${group_site},${count_site}
            echo "site/${group_site},${count_site}" >> "Clustering/${uses_name}_Clustering.csv"
         done
    fi
done
rm "Clustering/${uses_name}_sort_Prefix_remove.csv"

if [[ -f "tmp_site.csv" ]]; then
    rm "tmp_site.csv"
fi
#======================================== useful.csv ($3)===============================

uses_name=$(echo $3 | rev | cut -d'/' -f1 | rev)
useful=${uses_name}

while read line 
do
	file_name=$(echo $line | cut -d',' -f2)	
	prefix_remove=$(sed 's;^.*target/;;g' <<< ${file_name})
	echo ${prefix_remove} >> "useful_unsort_Prefix_remove.csv"
done < $3  #"contents_of_all_files_which_are_accessed.csv"   

sort "useful_unsort_Prefix_remove.csv" > "Clustering/${uses_name}_useful_sort_Prefix_remove.csv"
rm  "useful_unsort_Prefix_remove.csv"


#==========For Making Cluster============
group_arr=$(cut -f1 -d'/' "Clustering/${uses_name}_useful_sort_Prefix_remove.csv"  | sort | uniq)
echo "group,count" > "Clustering/${uses_name}_Clustering.csv"
for group in ${group_arr[@]}; do
    count=$(grep -r "$group" "Clustering/${uses_name}_useful_sort_Prefix_remove.csv" | wc -l)
    echo "$group,$count" >> "Clustering/${uses_name}_Clustering.csv"
    if [[ $group == "site" ]]; then
        grep -r "site" "Clustering/${uses_name}_useful_sort_Prefix_remove.csv"  > "tmp_site.csv"
         group_site_arr=$(cut -f2 -d'/' "tmp_site.csv"  | sort | uniq)
         for group_site in ${group_site_arr[@]}; do
            count_site=$(grep -r "${group_site}" "tmp_site.csv" | wc -l)
            #echo ${group_site},${count_site}
            echo "site/${group_site},${count_site}" >> "Clustering/${uses_name}_Clustering.csv"
         done
    fi
done
rm "Clustering/${uses_name}_useful_sort_Prefix_remove.csv"

if [[ -f "tmp_site.csv" ]]; then
    rm "tmp_site.csv"
fi

#==========================WHICH ARE uncommon in useful file ==================================

cat "Clustering/${never_access}_Clustering.csv" | cut -d',' -f1 > "tmp1_never"
cat "Clustering/${useful}_Clustering.csv" | cut -d',' -f1 > "tmp2_useful"
comm -13 <(sort -u "tmp2_useful") <(sort -u "tmp1_never") > "Clustering/$4-unnecessary.csv"  # Looking at is not in useful category but exists in never access
rm "tmp1_never"
rm "tmp2_useful"
#================ WHICH are Aceesessed($2) ============================================
    if [[ $2 == "" ]]; then
        echo "arg2 is required"
        exit
    else
    
    uses_name=$(echo $2 | rev | cut -d'/' -f1 | rev)
#---------Extract file names which have target directory ------------
    while read line 
    do
    	file_name=$(echo $line | cut -d',' -f2)	
    	prefix_remove=$(sed 's;^.*target/;;g' <<< ${file_name})
    	echo ${prefix_remove} >> "cma_unsort_Prefix_remove.csv"
    done < $2  #"contents_of_all_files_which_are_accessed.csv"   
    
    if [[ -f "cma_unsort_Prefix_remove.csv" ]]; then
        sort "cma_unsort_Prefix_remove.csv" > "${uses_name}_cma_sort_Prefix_remove.csv"
        rm  "cma_unsort_Prefix_remove.csv"

        #==========For Making Cluster============
            
        group_arr=$(cut -f1 -d'/' "${uses_name}_cma_sort_Prefix_remove.csv"  | sort | uniq)
        echo "group,count" > "${uses_name}_cma_Clustering.csv"
        for group in ${group_arr[@]}; do
            count=$(grep -r "$group" "${uses_name}_cma_sort_Prefix_remove.csv" | wc -l)
            echo "$group,$count" >> "${uses_name}_cma_Clustering.csv"
            if [[ $group == "site" ]]; then
                grep -r "site" "${uses_name}_cma_sort_Prefix_remove.csv"  > "tmp_site.csv"
                 group_site_arr=$(cut -f2 -d'/' "tmp_site.csv"  | sort | uniq)
                 for group_site in ${group_site_arr[@]}; do
                    count_site=$(grep -r "${group_site}" "tmp_site.csv" | wc -l)
                    #echo ${group_site},${count_site}
                    echo "site/${group_site},${count_site}" >> "${uses_name}_cma_Clustering.csv"
                 done
            fi
        done
        
        rm "tmp_site.csv"
    fi
fi


#python3 pychart_generator.py "${uses_name}_cm_Clustering.csv"
