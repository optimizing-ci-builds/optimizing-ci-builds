#!/bin/bash
if [[ $1 == "" ]]; then
    #echo "please provide the inotify log(e.g., ci-analyzes/joda-time/.github/workflows/build/build/inotify-logs.csv)"
    echo "please provide the inotify log(e.g., ci-analyzes)"
    #echo "please provide the project name (e.g., joda-time)"
    exit
fi
currentDir=$(pwd)
cd $1
find -name "inotify-logs.csv" > "$currentDir/all_inotify-logs.csv"
branch_name=$(git rev-parse --abbrev-ref HEAD)
inotify_result_dir="$currentDir/Inotify-Parse-Result"
mkdir "$inotify_result_dir"
result="$currentDir/Inotify-Parse-Result/Output.csv"
echo  "branch,inotify_file_path,line_in_inotify_file,created file,actions_of_this_file,line_number_of_operations_index_in_yaml" >> $result

while read inotify
do

    total_line_of_inotify_log=$(wc -l) 
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
            if [[ ! " ${arr_unique_line[*]} " =~ "${full_file_name}" ]]; then
                
                echo -n ${branch_name} >> $result
                echo -n ",$inotify" >> $result    
                echo -n ",$total_line_of_inotify_log" >> $result
                echo -n ",$full_file_name" >> $result #This is a created file name
                arr_unique_line+=(${full_file_name})
                #Need to check
                grep -n "$created_file_name;" $inotify >> "$inotify_result_dir/tmp.csv"
                create_line=($(grep -n "CREATE" "$inotify_result_dir/tmp.csv" | cut -d':' -f1))  # to get the line numbe of the create
                echo $create_line
    
                modify_line=($(grep -n "MODIFY" "$inotify_result_dir/tmp.csv" | cut -d':' -f1)) 
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
                total_line=$(wc -l < "$inotify_result_dir/tmp.csv")
                echo $total_line
                tail -n +$((boundary+1)) "$inotify_result_dir/tmp.csv" >> "$inotify_result_dir/all_lines_after_last_modify_or_create.csv"
                count=$(grep -r "ACCESS"  "$inotify_result_dir/all_lines_after_last_modify_or_create.csv" | wc -l)
                if [[ $count -gt 0 ]]; then # USEFUL FILE
                    echo $full_file_name   >> "$inotify_result_dir/USEFUL_FILE_${proj_name}.csv"
                else
                    echo $full_file_name   >> "$inotify_result_dir/UNUSED_FILE_${proj_name}.csv"
                fi
                line_count=$((line_count + 1)) 
    
                #Collect all operation's execution sequence 
                arr_all_operation=($(cut -d';' -f1,4 "$inotify_result_dir/tmp.csv" ))
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
                remove_last_underline=$(echo $all_operation | rev | cut -d'_' -f2 | rev)
                last_op=$(echo ${remove_last_underline} | rev | cut -d'_' -f1 | rev)
                category="-"
                if [[ $last_op =~ "A" ]]; then
                    category="Accessed"
                elif [[ ! "$remove_last_underline" =~ "A" ]]; then
                    category="Never_accessed"
                elif [[ $last_op =~ "M" ]]; then
                    category="Unnecessary_modify"
                fi

                echo -n ",$category" >> $result
                echo -n ",$remove_last_underline" >> $result
                ln=$(echo "$all_lines" | rev | cut -d'_' -f2- |rev)

                echo  ",$ln"  >> $result
                #echo  ",$all_lines"  >> $result
                #exit
                rm "$inotify_result_dir/tmp.csv"
                rm "$inotify_result_dir/all_lines_after_last_modify_or_create.csv"
            fi
        fi
    done<"$inotify"
    #exit 
done < "$currentDir/all_inotify-logs.csv"
