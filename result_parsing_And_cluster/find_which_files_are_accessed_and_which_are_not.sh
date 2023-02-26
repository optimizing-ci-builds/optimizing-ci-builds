#!/bin/bash
#MavenTestCI
#remotes/origin/JSqlParser.1671859411
#remotes/origin/fabric-sdk-java.1672108464
#jv-fruit-shop.1672108464
#Algorithms.1671724402
#mooc-software-testing.1672101501
#git checkout -f  MavenTestCI.1670985148

if [[ $1 == "" ]]; then
    echo "give csv $1 (workflow_dir.csv)"
    #echo "give $2 (Project name)"
#    echo "give $3 (useful.csv)"
    exit
fi
currentDir=$(pwd)
Output="Output"
if [[ -f "projects_name_per_yaml.csv" ]]; then
    rm "projects_name_per_yaml.csv"
fi

#while read row_line
#do
    #echo "$row_line ***************"
    output_proj_name=$2
    workflow_name=$(echo $1 | rev |cut -d'/' -f2-3| rev | sed 's/\//-/g' )
    echo "workflow name= ${workflow_name}"
    proj_with_workflow="${output_proj_name}-$workflow_name"
    
    echo $proj_with_workflow >> "projects_name_per_yaml.csv"
    
    if [ -f "$currentDir/$Output/$proj_with_workflow-never-accessed" ]; then
        rm "$currentDir/$Output/$proj_with_workflow-never-accessed"
    fi
    
    if [ -f "$currentDir/$Output/$proj_with_workflow-accessed" ]; then
        rm "$currentDir/$Output/$proj_with_workflow-accessed"
    fi
    dir_arr=($(cd "$1" && printf -- '%s\n' */))
    echo "Line 39 ${dir_arr}"
    #$(find . -maxdepth 1 -type d -printf '%f\n')
    cd "$1"
    #echo "PWD= ${dir_arr}"
    never_accessed_file_name_array=("cm_a.csv" "c_m_a.csv" "c_m__a.csv" "cm__a.csv"  "_cm_a.csv"  "_cm__a.csv.csv"  "_c_m_a.csv" "_c_m__a.csv" )
    accessed_file_name_array=("cma.csv" "c_ma.csv" "_cma.csv"  "_c_ma.csv"  )
    
    if [[ ! -d "$currentDir/$Output" ]]; then
        mkdir "$currentDir/$Output"
    fi
    
    for i in "${dir_arr[@]}"
    do
    
        echo "==========$i ========== $(pwd)"
        if [[ "$i" =~ .*"checkout".* ]]; then
            echo "checkout found"
            continue
        elif [[ "$i" =~ .*"setup".* ]]; then
           echo "setup found"
           continue
        else
            for j in "${never_accessed_file_name_array[@]}"
            do
                #echo $i$j
                if [ -f $i$j ]; then
                    echo "Found $i$j"
                    cat "$i$j" >> "$currentDir/$Output/$proj_with_workflow-never-accessed"
                else 
                    echo "Not Found"
                fi
            done
    
            for k in "${accessed_file_name_array[@]}"
            do
                if [ -f $i$k ]; then
                    echo "accessed *******************************pwd =$(pwd)"
                    echo $i$k
                    cat "$i$k" >> "$currentDir/$Output/$proj_with_workflow-accessed"
                fi
            done
    
        fi
        #if [[ $i != "." ]]; then
        #fi
    done
    
    cat "$currentDir/$Output/$proj_with_workflow-never-accessed" | cut -d',' -f2 > "$currentDir/tmp1"
    cat "$currentDir/tmp1" | sort | uniq > "$currentDir/tmp"
    cp "$currentDir/tmp" "$currentDir/$Output/$proj_with_workflow-never-accessed" 
    rm "$currentDir/tmp1"
    rm "$currentDir/tmp"
    
    if [[ -f "$currentDir/$Output/$proj_with_workflow-accessed" ]]; then
        cat "$currentDir/$Output/$proj_with_workflow-accessed" | cut -d',' -f2 > "$currentDir/tmp-access"
        cat "$currentDir/tmp-access" | sort | uniq > "$currentDir/tmp-access1"
        cp "$currentDir/tmp-access1" "$currentDir/$Output/$proj_with_workflow-accessed" 
    
        rm "$currentDir/tmp-access1"
        rm "$currentDir/tmp-access"
    
        comm -13 <(sort -u "$currentDir/$Output/$proj_with_workflow-never-accessed") <(sort -u  "$currentDir/$Output/$proj_with_workflow-never-accessed") >  "$currentDir/$Output/$proj_with_workflow-common"
    fi
    
    ### Process useful.csv

    cd $currentDir
    if [[ -f  "$currentDir/$Output/$proj_with_workflow-useful" ]]; then  
        rm "$currentDir/$Output/$proj_with_workflow-useful"
    fi
    row_count=1
    while read line
    do
        if [[ ${row_count} -gt 1 ]]; then
            file_name=$(echo $line | cut -d',' -f2)
            echo $file_name >>  "$currentDir/$Output/$proj_with_workflow-useful" 
        fi
        row_count=$((row_count+1))
    done < "$1/../useful.csv"

#done < $1
