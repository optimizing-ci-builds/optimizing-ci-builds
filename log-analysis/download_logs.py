import os
import requests
import json
import csv

TOKEN: str = os.environ["G_AUTH_OP"]
OWNER="optimizing-ci-builds"
ci_analyzes_branch=os.environ["BRANCH"]

def get_filtered_repos():
    repositories = []
    with open("data/filtered_repositories.csv", "r", newline="", encoding="utf8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        for row in csv_reader:
            repositories.append(
                {"name": row[0], "link": row[1], "default_branch": row[2], "sha": row[3],
                "stargazers_count": row[4], "forks_count": row[5], "Date": row[6],
                "Maven": row[7], "Gradle": row[8], "Travis CI": row[9], "Github Actions": row[10]})
    return repositories


repositories = get_filtered_repos()

base_api_url: str = "https://api.github.com"
user_token: str = TOKEN
headers: dict = {"Accept": "application/vnd.github+json",
                 "Authorization": f"token {user_token}"}


# Making the logs directory if it does not exist already
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# make the ci_analyzes_branch inside the logs dir
branch_dir = os.path.join(log_dir,ci_analyzes_branch)
if not os.path.exists(branch_dir):
    os.makedirs(branch_dir)

for index, repository in enumerate(repositories):
    repo: str = repository["name"].split("/")[1]
    print(repo)
    url = f"{base_api_url}/repos/{OWNER}/{repo}/actions/workflows"
    response = requests.get(url, headers=headers).json()       

    # list workflow runs for a repository
    url = f"{base_api_url}/repos/{OWNER}/{repo}/actions/runs"
    runs = requests.get(url, headers=headers).json()

    for run in runs["workflow_runs"]:
        for workflow in response["workflows"]:
            if run["workflow_id"] == workflow["id"]:
                workflow_file_name =  str(workflow["path"]).split("/")[-1].split(".")[-2]
                page = requests.get(f"https://github.com/optimizing-ci-builds/{repo}/actions/runs/{run['id']}/workflow").text
                if ci_analyzes_branch in page:
                    print("found the workflow for repo: " + repo)
                    print(f"https://github.com/optimizing-ci-builds/{repo}/actions/runs/{run['id']}/workflow")
                    print("****")
                    
                    workflow_run_url = f"{base_api_url}/repos/{OWNER}/{repo}/actions/runs/{run['id']}/jobs"
                    workflow_run = requests.get(workflow_run_url, headers=headers).json()

                    repo = os.path.join(branch_dir,repo)
                    if not os.path.exists(repo):
                        os.makedirs(repo)
                    workflow_name = workflow["name"]
                    # if / are in workflow name then that means that there is no name in that workflow, so simply consider the name of the yaml file which is the default name
                    if "/" in str(workflow_name):
                        workflow_name = str(workflow_name).split("/")[-1].split(".")[-2]
                    with open (f"{repo}/{workflow_name}.json", "w") as f:
                        f.write(json.dumps(workflow_run, indent=2))
