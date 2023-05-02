#/bin/bash
if [[ $1 == "" ]]; then
    echo "give arg1"
    #$1=Clustering-Unused-Directories
    exit
fi
all_file_name_tmp=($(ls "$1"))
echo $all_file_name_tmp
mkdir "after_target_$1"
for file in ${all_file_name_tmp[@]};do
    all_lines=$(cat $1/$file)
    while read line;
    do
        echo $line
        target_right=$(echo $line |  awk -F "target/" '{print $2}')
        if [[ $target_right != "" ]]; then
            echo $target_right >> "after_target_$1/$file"
        fi
   done < "$1/$file"
done
