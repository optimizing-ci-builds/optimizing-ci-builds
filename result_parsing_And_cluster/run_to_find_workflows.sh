if [[ $1 == "" ]]; then
    echo "plz give the directory of your ci-analyzes projects(e.g.,../../ci-analyzes/)"
    exit
fi

#find $1 -mindepth 1 -type d \( -name '.*' -prune -o -print \) | rev | cut -d'/' -f1 | rev  | sort -u | sed -r '/^\s*$/d'  > "projects_name.csv"

#sed -i '/.git/d'  "projects_name.csv"

org_currentDir=$(pwd)
if [[ -f "${org_currentDir}/workflow_dir.csv" ]]; then 
    #echo "${org_currentDir}/workflow_dir.csv"
    #cat "${org_currentDir}/workflow_dir.csv"
    rm "${org_currentDir}/workflow_dir.csv"
fi

while read line
do
    cd "$1$line/.github/workflows/"
    currentDir=$(pwd)
    #echo $currentDir
    my_array=($(ls))
    for i in "${my_array[@]}"
    do
        dir_arr=($(ls $i))
        for j in "${dir_arr[@]}"
        do
            echo "$currentDir/$i/$j" >> "$org_currentDir/workflow_dir.csv"
        done
    done
    cd $org_currentDir
done < "projects_name.csv"
