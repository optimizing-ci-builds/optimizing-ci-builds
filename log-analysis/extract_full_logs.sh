# Run this file from the log-analysis directory inorder to set all the paths correctly

# Declear variables
ci_analyzes_branch=$1
replace_logs="false"
current_dir=$(pwd)
ci_analyzes_dir=$current_dir/data/ci-analyzes
projects_dir=$current_dir/data/projects/
jobs_file="$current_dir/jobs.csv"
project_log_dir="$current_dir/logs/$ci_analyzes_branch"
filtered_repositories_file="$current_dir/../data/filtered_repositories.csv"


# create directories if they do not exist
if [ ! -d $projects_dir ]; then
    mkdir -p $projects_dir
fi
if [ ! -d $project_log_dir ]; then
    mkdir -p $project_log_dir
fi


# clone/update all the projects
for repo in $(cat $filtered_repositories_file | tail -n +2 | cut -d ',' -f1 | cut -d '/' -f2); do
    if [ ! -d "$projects_dir/$repo" ]; then
        cd $projects_dir
        if [ ! -d $repo ]; then
            echo "Cloning $repo"
            git clone git@github.com:optimizing-ci-builds/$repo.git
        else
            echo "Updating $repo"
            cd $repo
            git fetch --all
        fi
    fi
done


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


# create jobs.csv file if it does not existß
if [ ! -f $jobs_file ]; then
    echo "ci_analyzes_branch, run_id, job_name, project" >> $jobs_file
fi

echo "combining job.csv files into jobs.csv..."
find $ci_analyzes_dir -name "job.csv" -exec sh -c 'sed "s/^/'"$ci_analyzes_branch"',/" "{}"; echo' \; >> $jobs_file
awk '!seen[$0]++' $jobs_file > $jobs_file.tmp && mv $jobs_file.tmp $jobs_file # remove duplicates

# for each row in jobs.csv, read the 2nd column (run_id) and the 4th column (project) into variables
for row in $(cat $jobs_file | tail -n +2); do
    if [ $(echo $row | cut -d ',' -f1) != $ci_analyzes_branch ]; then
        continue
    fi
    run_id=$(echo $row | cut -d ',' -f2)
    project=$(echo $row | cut -d ',' -f4)

    # download logs for each project if they do not exist
    if [ ! -f $project_log_dir/$project.log ] || [ $replace_logs = "true" ]; then
        echo "Downloading logs for $project, run_id: $run_id"
        cd $projects_dir
        cd $project
        gh run view $run_id --log > $project_log_dir/$project.log
    else
        echo "Logs for $project, run_id: $run_id already exist"
    fi
done
