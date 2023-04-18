if [[ $1 == "" ]]; then
    echo "Give the csv that is generated from (data/all_successful_job.csv)"
    exit
fi

currentDir=$(pwd)
#cut -d',' -f1-5,15 "$currentDir/data/master_cell.csv" > 
#ssconvert  ~/Downloads/master_cell.xlsx data/all_proj.csv
#exit
#branch_name=$(echo $1 | rev | cut -d'/' -f1 | rev | cut -d'-' -f2- | cut -d'.' -f1)
echo $branch_name
if [[ ! -d "ccc/ci-analyzes" ]]; then
    git clone https://github.com/UT-SE-Research/ci-analyzes.git 
fi

while read line
do 

    cd "$currentDir/ccc/ci-analyzes"
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    branch_name=$(echo $line | cut -d',' -f15) 
    #echo $branch_name
    git checkout ${branch_name}
    cd $currentDir
    proj_name=$(echo $line | cut -d',' -f1) 
    echo -n "$proj_name"  >> "$currentDir/clusters_info.csv"
    workflow_path=$(echo ${line} | cut -d',' -f3)
    echo -n ",${workflow_path}" >> "$currentDir/clusters_info.csv"

    workflow_job_name=$(echo ${line} | cut -d',' -f10 | cut -d'/' -f11- | sed 's;\/;-;g') # example, Parsing(https://github.com/UT-SE-Research/ci-analyzes/tree/1680156014-f3221fe/soot/.github/workflows/ci/BuildAndTest)
    echo ",${proj_name}_${workflow_job_name}.csv" >> "$currentDir/clusters_info.csv"

    echo "${proj_name}_${workflow_job_name}"
    bash make_cluster_for_each_category.sh "${proj_name}_${workflow_job_name}" "Clustering-Unused-Directories" "Unused" "Useful"  # file_name in the inotofy dir ($1_$3), useful file_name in inotify dir ($1_$4), Loop through($1_$3) 
    bash make_cluster_for_each_category.sh "${proj_name}_${workflow_job_name}" "Clustering-Used-Directories" "Useful"  "Unused" 
done < $1
