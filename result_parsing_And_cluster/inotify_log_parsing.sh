#!/bin/bash
if [[ $1 == "" ]]; then
    #echo "please provide the inotify log(e.g., ci-analyzes/joda-time/.github/workflows/build/build/inotify-logs.csv)"
    echo "please provide the inotify log(e.g., ci-analyzes)"
    #echo "please provide the project name (e.g., joda-time)"
    exit
fi
currentDir=$(pwd)
cd $1
branch_name=$(git rev-parse --abbrev-ref HEAD)
result="$currentDir/Output.csv"
echo ${branch_name} >> $result
find -name "inotify-logs.csv" > "$currentDir/all_inotify-logs.csv"

while read inotify
do
    
    line_count=1
    arr_unique_line=()
    proj_name="$(echo $inotify | cut -d'/' -f2)-$(echo $inotify | rev | cut -d'/' -f2 | rev)"
    echo $proj_name
    while read line
    do
        echo $line
        time=$(echo $line | cut -d';' -f1)
        created_file_dir=$(echo $line | cut -d';' -f2)
        created_file_name=$(echo $line | cut -d';' -f3)
        create_flag=0
        modify_flag=0
        if [[  -z $created_file_name ]]; then 
            continue
        else
            full_file_name="${created_file_dir};${created_file_name};"
            echo $full_file_name
            if [[ ! " ${arr_unique_line[*]} " =~ "${full_file_name}" ]]; then
                arr_unique_line+=(${full_file_name})
                #Need to check
                grep -n "$created_file_name;" $inotify >> "tmp.csv"
                create_line=($(grep -n "CREATE" "tmp.csv" | cut -d':' -f1))  # to get the line numbe of the create
                echo $create_line
    
                modify_line=($(grep -n "MODIFY" "tmp.csv" | cut -d':' -f1)) 
                echo $modify_line
                boundary=0 
                
                if (( ${#create_line[@]} )); then 
                    create_flag=1 
                fi
                if (( ${#modify_line[@]} )); then 
                    modify_flag=1 
                fi #echo not empty
    
                if [ $modify_flag -eq 1 ] && [ $create_flag -eq 0 ] ; then
                    boundary=${modify_line[-1]}
                elif [ $modify_flag -eq 0 ] && [ $create_flag -eq 1 ] ; then
                    boundary=${create_line[-1]}
                else
                   if [[ ${modify_line[-1]} -gt ${create_line[-1]} ]]; then #to get the last element from the array, because mutilple create and modify might exists
                       boundary=${modify_line[-1]}
                   else 
                       boundary=${create_line[-1]}
                   fi
                fi
                #echo $boundary
                total_line=$(wc -l < "tmp.csv")
                echo $total_line
                tail -n +$((boundary+1)) "tmp.csv" >> "all_lines_after_last_modify_or_create.csv"
                count=$(grep -r "ACCESS"  "all_lines_after_last_modify_or_create.csv" | wc -l)
                if [[ $count -gt 0 ]]; then # USEFUL FILE
                    echo $full_file_name   >> "USEFUL_FILE_${proj_name}.csv"
                else
                    echo $full_file_name   >> "UNUSED_FILE_${proj_name}.csv"
                fi
                line_count=$((line_count + 1)) 
    
                #Collect all operation's execution sequence 
                arr_all_operation=($(cut -d';' -f1,4 "tmp.csv" ))
                echo $arr_all_operation
                
                all_operation=""
                all_lines=""
                for i in "${arr_all_operation[@]}"
                do
                    echo $i
                    if [[ "$i" =~ "CREATE" ]]; then
                        all_operation+="C"
                        all_lines+="$(echo $i |  cut -d':' -f1)_"
    
                    elif [[ "$i" =~ "MODIFY" ]]; then 
                        all_operation+="M"
                        all_lines+="$(echo $i | cut -d':' -f1)_"
                    elif [[ "$i" =~ "ACCESS" ]]; then
                        all_lines+="$(echo $i | cut -d':' -f1)_"
                        all_operation+="A"
                    fi
                done
                echo $all_lines
                echo $all_operation
                exit
                rm "tmp.csv"
                rm "all_lines_after_last_modify_or_create.csv"
            fi
        fi
       #exit 
    done<"$inotify"
done < "$currentDir/all_inotify-logs.csv"
