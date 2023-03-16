import os
import requests
import json
import csv
import sys



TOKEN: str = os.environ["G_AUTH_OP"]
OWNER = "optimizing-ci-builds"
ci_analyzes_branch = sys.argv[1] #1678918537-5a20a5b, 1678921743-5a20a5b, 1678931171-5a20a5b
log_dir = "logs"
analysis_dir = "analysis"
jobs_file = os.path.join("raw_logs", ci_analyzes_branch, "jobs.csv")
last_log_downloaded = ""

base_api_url: str = "https://api.github.com"
headers: dict = {"Accept": "application/vnd.github+json",
                 "Authorization": f"token {TOKEN}"}

if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    
if not os.path.exists(analysis_dir):
    os.makedirs(analysis_dir)

branch_dir = os.path.join(log_dir, ci_analyzes_branch)
if not os.path.exists(branch_dir):
    os.makedirs(branch_dir)
    
# Create an analysis csv file inside analysis_dir with name $ci_analyzes_branch.csv and add headers to it. Headers are: Project,Sha,Workflow,Job,Result_with_instrumentation,Result_without_instrumentation,Runtime_with_instrumentation,Runtime_without_instrumentation,path_to_pass_fail_log_with_instrumentation,path_to_pass_fail_log_without_instrumentation,path_to_inotify_log
with open(os.path.join(analysis_dir, f"{ci_analyzes_branch}.csv"), 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["Project", "Sha", "Workflow", "Job", "Result_with_instrumentation", "Result_without_instrumentation", "Runtime_with_instrumentation", "Runtime_without_instrumentation", "path_to_pass_fail_log_with_instrumentation", "path_to_pass_fail_log_without_instrumentation", "path_to_inotify_log"])
    
# read the jobs.csv file that has headers: ci_analyzes_branch, run_id, job_name, project
with open(jobs_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row)
        ci_analyzes_branch = row['ci_analyzes_branch']
        run_id = row['run_id']
        job_name = row['job_name']
        project = row['project']
        # workflow_path = row['workflow_path']
        workflow_name = row['workflow_name']
        print(f"Downloading logs for {project} for instrumented run with ci_analyzes branch: {ci_analyzes_branch} and run-id: {run_id} for job: {job_name}")
        
        # if the project directory does not exist, create it
        if not os.path.exists(os.path.join(branch_dir, project)):
            os.makedirs(os.path.join(branch_dir, project))
        
        if workflow_name != last_log_downloaded:
            workflow_run_url = f"{base_api_url}/repos/{OWNER}/{project}/actions/runs/{run_id}/jobs"
            workflow_run = requests.get(workflow_run_url, headers=headers).json()
            
            last_log_downloaded = workflow_name
            
            # save the workflow_run json file
            if "/" in workflow_name:
                workflow_name = str(workflow_name).split("/")[-1].split(".")[-2]
            with open(os.path.join(branch_dir, project, f"{workflow_name}.json"), 'w') as f:
                json.dump(workflow_run, f)
            
            
            # ANALYSIS OF LOG
            # for each jobs in the workflow_run, get the logs from which extract name,conclusion, runtime (i.e completed_at - started_at), workflow_name, head_sha