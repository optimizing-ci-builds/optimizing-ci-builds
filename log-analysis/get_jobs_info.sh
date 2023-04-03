# Combines all the job.csv files into one jobs.csv file and put it inside the project_log directory
# Run this file from the log-analysis directory inorder to set all the paths correctly
# CLA: $1 = ci-analyzes branch to use

# Declear variables
ci_analyzes_branch=$1
replace_logs="false"
current_dir=$(pwd)
ci_analyzes_dir=$current_dir/data/ci-analyzes
projects_dir=$current_dir/data/projects/
# jobs_file="$current_dir/jobs.csv"
project_log_dir="$current_dir/raw_logs/$ci_analyzes_branch"
jobs_file="$project_log_dir/jobs.csv"
filtered_repositories_file="$current_dir/../data/filtered_repositories.csv"

mkdir -p $project_log_dir

# clone/update ci-analyzes
if [ ! -d $ci_analyzes_dir ]; then
    echo "Cloning ci-analyzes"
    git clone git@github.com:UT-SE-Research/ci-analyzes.git $ci_analyzes_dir
    cd $ci_analyzes_dir
    git fetch --all
    git checkout $ci_analyzes_branch
    cd $current_dir
fi
if [ -d $ci_analyzes_dir ]; then
    echo "Updating ci-analyzes"
    cd $ci_analyzes_dir
    git fetch --all
    git checkout $ci_analyzes_branch
    cd $current_dir
fi

echo "ci_analyzes_branch,run_id,job_name,project,workflow_name" > $jobs_file

echo "combining job.csv files into jobs.csv..."
find $ci_analyzes_dir -name "job.csv" -exec sh -c 'sed "s/^/'"$ci_analyzes_branch"',/" "{}"; echo' \; >> $jobs_file
awk '!seen[$0]++' $jobs_file > $jobs_file.tmp && mv $jobs_file.tmp $jobs_file # remove duplicates