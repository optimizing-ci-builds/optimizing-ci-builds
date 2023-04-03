import os
import requests
import json
import csv
import sys
import datetime


TOKEN: str = os.environ["G_AUTH_OP"]
OWNER = "optimizing-ci-builds"
ci_analyzes_branch = sys.argv[1] #1678918537-5a20a5b, 1678921743-5a20a5b, 1678931171-5a20a5b, 1678940360-bbc60b2
log_dir = "logs"
raw_log_dir = "raw_logs"
analysis_dir = "analysis"
jobs_file = os.path.join("raw_logs", ci_analyzes_branch, "jobs.csv")
last_log_downloaded = ""
wo_instrumentation_log_dir = "one-run-to-find-them-all"

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
    
with open(os.path.join(analysis_dir, f"{ci_analyzes_branch}.csv"), 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["Project", "Sha", "Workflow", "Job", "Result_with_instrumentation", "Result_without_instrumentation", "Runtime_with_instrumentation","Runtime_without_instrumentation", "path_to_pass_fail_log_with_instrumentation", "path_to_pass_fail_log_without_instrumentation", "path_to_inotify_log", "category"])
    
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
        # print(f"Downloading logs for {project} for instrumented run with ci_analyzes branch: {ci_analyzes_branch} and run-id: {run_id} for job: {job_name}")
        
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

            with open(os.path.join(analysis_dir, f"{ci_analyzes_branch}.csv"), 'a') as f:
                writer = csv.writer(f)
                
                # assuming `log` contains the JSON log data
                if 'jobs' not in workflow_run:
                    print("No jobs in workflow_run " + str(workflow_name) + " for project " + str(project))
                    continue
                for job in workflow_run['jobs']:
                    # extract the relevant information from the job
                    sha = job['head_sha']
                    workflow = job['workflow_name']
                    job_name = job['name']
                    conclusion = job['conclusion']
                    started_at = job['started_at']
                    completed_at = job['completed_at']
                    pass_fail_log = job['html_url']
                    
                    completed_at = datetime.datetime.strptime(job['completed_at'][:-1], '%Y-%m-%dT%H:%M:%S')
                    started_at = datetime.datetime.strptime(job['started_at'][:-1], '%Y-%m-%dT%H:%M:%S')
                    runtime = completed_at - started_at
                    path=""
 
                    for step in job['steps']:
                        if 'name' in step and 'Run echo' in step['name'] and '/.github/workflows/' in step['name']:
                            # extract the path from the step name
                            path = step['name'].split(' ')[-1]
                            # path = step['name']
                            break
                    # writer.writerow([project, sha, workflow, job_name, conclusion, "", runtime, pass_fail_log, "", path])
                    
                    conclusion_wo_instrumentation = ""
                    runtime_wo_instrumentation = ""
                    pass_fail_log_wo_instrumentation = ""
                    without_instrumentation_log_dir = os.path.join(log_dir,wo_instrumentation_log_dir, project)
                    if not os.path.exists(without_instrumentation_log_dir):
                        writer.writerow([project, sha, workflow, job_name, conclusion, conclusion_wo_instrumentation, runtime, runtime_wo_instrumentation, pass_fail_log, pass_fail_log_wo_instrumentation, path, ""])
                        continue
                        
                    for filename in os.listdir(without_instrumentation_log_dir):
                        if filename.endswith(".json"):
                            with open(os.path.join(without_instrumentation_log_dir, filename), 'r') as f:
                                without_instrumentation_log = json.load(f)
                                if 'jobs' not in without_instrumentation_log:
                                    print("No jobs in workflow_run " + str(workflow_name) + " for project " + str(project))
                                    continue
                                for job_wo_instrumentation in without_instrumentation_log['jobs']:
                                    if job_wo_instrumentation['name'] == job_name:
                                        conclusion_wo_instrumentation = job_wo_instrumentation['conclusion']
                                        started_at_wo_instrumentation = job_wo_instrumentation['started_at']
                                        completed_at_wo_instrumentation = job_wo_instrumentation['completed_at']
                                        pass_fail_log_wo_instrumentation = job_wo_instrumentation['html_url']
                                        completed_at_wo_instrumentation = datetime.datetime.strptime(job_wo_instrumentation['completed_at'][:-1], '%Y-%m-%dT%H:%M:%S')
                                        started_at_wo_instrumentation = datetime.datetime.strptime(job_wo_instrumentation['started_at'][:-1], '%Y-%m-%dT%H:%M:%S')
                                        runtime_wo_instrumentation = completed_at_wo_instrumentation - started_at_wo_instrumentation
                                        break
                        else:
                            continue
                    writer.writerow([project, sha, workflow, job_name, conclusion, conclusion_wo_instrumentation, runtime, runtime_wo_instrumentation, pass_fail_log, pass_fail_log_wo_instrumentation, path, ""])
 
# both_success_count=0
# only_wo_fail_count=0
# only_w_fail_count=0
# both_fail_count = 0
# with open(os.path.join(analysis_dir, f"{ci_analyzes_branch}.csv"), 'r') as f:
#     reader = csv.reader(f)
#     for row in reader:
#         project = row[0]
#         sha = row[1]
#         workflow = row[2]
#         job_name = row[3]
#         conclusion = row[4]
#         conclusion_wo_instrumentation = row[5]
#         runtime = row[6]
#         runtime_wo_instrumentation = row[7]
#         pass_fail_log = row[8]
#         pass_fail_log_wo_instrumentation = row[9]
#         path = row[10]
#         category = row[11]
        
#         # count the number of projects that are success in both 4th and 5th column
#         if conclusion == "success" and conclusion_wo_instrumentation == "success":
#             both_success_count += 1
#         if conclusion == "success" and conclusion_wo_instrumentation == "failure":
#             only_wo_fail_count += 1
#         if conclusion == "failure" and conclusion_wo_instrumentation == "success":
#             only_w_fail_count += 1
#         if conclusion == "failure" and conclusion_wo_instrumentation == "failure":
#             both_fail_count += 1

# print("both_success_count: " + str(both_success_count))
# print("only_wo_fail_count: " + str(only_wo_fail_count))
# print("only_w_fail_count: " + str(only_w_fail_count))
# print("both_fail_count: " + str(both_fail_count))