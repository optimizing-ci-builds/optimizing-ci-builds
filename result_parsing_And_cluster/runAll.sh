if [[ $1 == "" ]]; then
    echo "Give the csv that is generated from (../log-analysis/AutoGeneratedGithubAction-1677165960-c4e224e.csv)"
    exit
fi
currentDir=$(pwd)
branch_name=$(echo $1 | rev | cut -d'/' -f1 | rev | cut -d'-' -f2- | cut -d'.' -f1)
echo $branch_name
#exit
if [[ ! -d "ci-analyzes" ]]; then
    git clone https://github.com/UT-SE-Research/ci-analyzes.git 
fi
cd ci-analyzes
git checkout ${branch_name}

cd $currentDir
#p="Hello"
#echo "PP = $p HI"
count=0 
while read line
do 
    count=$((count+1))
    if [[ ${line} =~ ^\# ]]; then
        echo "Line starts with Hash $line"
        continue
    fi
    #echo "hi"
    commaCount=$(echo $line | tr -cd , | wc -c)
    index=$(( commaCount + 1))
    instrumentation_status_with_noise=$(echo $line | cut -d',' -f$index) 
    #echo ${instrumentation_status_with_noise}
    instrumentation_status=$(echo "|${instrumentation_status_with_noise//[$'\t\r\n ']}|")
    #echo "i amd shan= ${instrumentation_status} !!!!!!!!!1"
    #echo "mu"
    if [ "${instrumentation_status}" == "|success|" ]; then
        echo "SUCEESS"
        proj_name=$(echo $line | cut -d',' -f1) 
        echo ${proj_name} 
        echo $(pwd)
        workflow_name="ci-analyzes/${proj_name}/.github/workflows"
        step_details_dir=($(find ${workflow_name} -name "step-details"))
        size=${#step_details_dir[@]}
        echo "size= $size"
        if [[ $size -gt 1 ]]; then 
            echo "large size"
            #exit
        fi
        for (( i=0; i<$size; i++ )); 
            do 
            echo "HI step-details = ${step_details_dir[$i]}" ; 
            echo ${step_details_dir[$i]} >> P.csv
            bash  find_which_files_are_accessed_and_which_are_not.sh "${step_details_dir[$i]}" ${proj_name}
        done

        #bash make_cluster_for_each_category.sh Output/${proj_name}-never-accessed  "" Output/${proj_name}-useful ${proj_name}
        #exit
    fi
    #if [[ $count == 2 ]];then
    #  exit
    #fi
done < "$1"
