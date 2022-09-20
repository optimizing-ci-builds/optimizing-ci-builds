import base64
import json
import os
from urllib.parse import uses_relative
import requests
import csv
import time
import subprocess
import sys
import pandas as pd
import numpy as np

base_api_url: str = "https://api.github.com"
# user_token: str = os.environ["G_AUTH_OP"]
headers: dict = {"Accept": "application/vnd.github+json",
                 "Authorization": f"token {user_token}"}


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


def retrieve_sha(owner: str, repo: str, default_branch: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{default_branch}"
    response = requests.get(url=url, headers=headers).json()
    sha = response['commit']['sha']
    return sha


def get_yaml_file(forked_owner: str, repo: str, file_path: str):
    url_path: str = f"{base_api_url}/repos/{forked_owner}/{repo}/contents/{file_path}"
    # will change here
    response = requests.get(url=url_path, headers=headers)
    if response.status_code != 200:
        raise ValueError(
            f"There have been a problem while retrieving the .github/workflows/? file from {forked_owner}/{repo}. Error: {response.text}")
    return base64.b64decode(response.json()["content"]).decode("utf-8"), response.json()["sha"]


def configure_yaml_file(yaml_file: str):
    new_yaml_file: str = ""
    indent = 0
    job_indent = 0
    in_job = False
    job_name = ""
    line_number = 0
    name = ""
    for line in yaml_file.split("\n"):
        line_number += 1
        if line.strip().split(":")[0] == "runs-on":
            new_yaml_file += " " * (len(line) - len(line.lstrip()))
            new_yaml_file += "runs-on: self-hosted\n"
            continue
        indent = len(line) - len(line.lstrip())

        if in_job and (indent <= job_indent):
            in_job = False
        if line.strip().split(":")[0] == "jobs":
            in_job = True
        if in_job and ((indent - 2) == job_indent):
            job_name = line.strip()[:-1]
        
        if "- uses" in line or "- name" in line or "- run" in line:
            step_name = line.split(":")[1].replace(" ", "")
            name = f"{job_name}_{step_name}_{line_number}".replace("/", "")
            change = ' ' * indent + f"- run: touch starting_{name}\n"
            new_yaml_file += change
            new_yaml_file += line + "\n"
        else:
            new_yaml_file += line + "\n"
    return new_yaml_file, name


def get_runner_token(owner: str, repo: str):
    url_path: str = f"{base_api_url}/repos/{owner}/{repo}/actions/runners/registration-token"
    response = requests.post(url_path, headers=headers)
    if response.status_code != 201:
        raise ValueError(
            f"There have been a problem while getting a token for the runner on {owner}/{repo}. Error: {response.text}")
    return response.json()["token"]


def setup_runner(token, owner, repo):
    url_path: str = f"{base_api_url}/repos/{owner}/{repo}/actions/runners"
    response = requests.get(url_path, headers=headers)

    if response.json()["total_count"] == 0:
        runner_applications = requests.get(f"{base_api_url}/repos/{owner}/{repo}/actions/runners/downloads", headers=headers).json()
        url_found = False
        for runner in runner_applications:
            if runner["os"] == "linux" and runner["architecture"] == "x64":
                runner_url = runner["download_url"]
                tar_filename = runner["filename"]
                url_found = True
                break
        if not url_found:
            print("Runner url not found!")
            sys.exit()
        os.system(f"mkdir "+repo+"_runner")
        # runner_url = f"https://github.com/actions/runner/releases/download/v{runner_version}/actions-runner-{tar_filename}"
        target_path = f"{repo}_runner/{tar_filename}"
        try:
            response = requests.get(runner_url, stream=True)
            if response.status_code == 200:
                with open(target_path, 'wb') as f:
                    f.write(response.raw.read())
            else:
                raise ValueError(f"There was a problem while downloading the runner on {owner}/{repo}. Error: {response.text}")
        except:
            print("There was a problem while downloading the runner.")
            # continue
            pass

        os.system(f"tar xzf ./{repo}_runner/{tar_filename} -C {repo}_runner")

        os.system(f"mkdir {repo}_runner/_work")
        os.chdir(f"{repo}_runner")
        os.system(
            f"echo | ./config.sh --url https://github.com/{owner}/{repo} --token {token}")
    return token


def execute(owner: str, repo: str, sha:str, default_branch:str, file_paths, new_files, yaml_shas):
    proc1 = subprocess.Popen(f"inotifywait -mr _work/ --format '%T;%w;%f;%e' --timefmt %T -o ../{repo}_logs/{owner}-{repo}.csv", shell=True)
    proc2 = subprocess.Popen("./run.sh")
    print("Processes created.")
    commit_sha = commit_file(owner, repo, sha, default_branch,file_paths, new_files, yaml_shas)
    return proc1, proc2, commit_sha


def commit_file(owner: str, repo: str, sha : str, default_branch:str, file_paths, new_file_contents, yaml_shas):
    create_branch(owner, repo, sha)
    blob_shas = create_blobs(owner, repo, new_file_contents)
    tree_sha = create_tree(owner, repo, sha, file_paths, blob_shas)
    new_commit_sha = create_commit(owner, repo, sha, tree_sha)
    commit_to_branch(owner, repo, new_commit_sha)
    open_pull_request(owner, repo, default_branch)
    return new_commit_sha


def create_branch(owner, repo, sha):
    response = requests.delete(f"{base_api_url}/repos/{owner}/{repo}/git/refs/heads/optimizing-ci-build")
    print(response)
    url = f"{base_api_url}/repos/{owner}/{repo}/git/refs"
    body = {
            "ref": "refs/heads/optimizing-ci-builds",
            "sha": sha
    }
    requests.post(url=url, data=json.dumps(body), headers=headers)


def create_blobs(owner, repo, new_file_contents):
    blob_shas = []
    for content in new_file_contents:
        url = f"{base_api_url}/repos/{owner}/{repo}/git/blobs"
        body = {
            "content": content,
            "encoding": "utf-8"
        }
        response = requests.post(url=url, data=json.dumps(body), headers=headers)
        blob_shas.append(response.json()['sha'])
    return blob_shas


def create_tree(owner, repo, sha, file_paths, blob_shas):
    url = f"{base_api_url}/repos/{owner}/{repo}/git/trees"
    body = {}
    body["base_tree"] = sha
    tree = []
    for i in range(0,len(file_paths)):
        tree.append({"path": file_paths[i], "mode": "100644", "type": "blob", "sha": blob_shas[i] })
    body["tree"] = tree
    response = requests.post(url=url, data=json.dumps(body), headers=headers)
    tree_sha = response.json()['sha']
    return tree_sha


def create_commit(owner, repo, sha, tree_sha):
    url = f"{base_api_url}/repos/{owner}/{repo}/git/commits"
    body = {
        "message": "Changed yaml files",
        "author": {
          "name": "optimizing-ci-builds",
          "email": "ocibsummerresearch2022@gmail.com"
        },
        "parents": [sha],
        "tree": tree_sha
    }
    response = requests.post(url=url, data=json.dumps(body), headers=headers)
    new_commit_sha = response.json()['sha']
    return new_commit_sha


def commit_to_branch(owner, repo, new_commit_sha):
    url = f"{base_api_url}/repos/{owner}/{repo}/git/refs/heads/optimizing-ci-builds"
    body = {
        "ref": "refs/heads/optimizing-ci-builds",
        "sha": new_commit_sha
    }
    response = requests.post(url=url, data=json.dumps(body), headers=headers)


def open_pull_request(owner: str, repo: str, default_branch:str ):
    url = f"{base_api_url}/repos/{owner}/{repo}/pulls"
    body = {
        "title": "Optimizing CI builds",
        "head":"optimizing-ci-builds",
        "base": default_branch
    }
    response = requests.post(url=url, data=json.dumps(body), headers=headers)


def check_runs(owner: str, repo: str, commit_sha:str):
    while(True):
        time.sleep(60)
        url = f"{base_api_url}/repos/{owner}/{repo}/commits/{commit_sha}/check-runs"
        response = requests.get(url=url, headers=headers).json()
        done = 1
        for check_run in response["check_runs"]:
            if check_run["status"] != "completed":
                done = 0
        if done == 1:
            break
    

def analyze(owner: str, repo: str):
    csv_path = f"../{repo}_logs/{owner}-{repo}"
    df = pd.read_csv(f"{csv_path}.csv", sep = ';', names=["time", "watched_filename", "event_filename", "event_name"])
    df['event_filename'] = df['event_filename'].replace(np.nan, '')
    # print(f"{df['event_name'].value_counts()}")
    steps = {}
    starting_indexes = df[(df["event_filename"].str.contains("starting_")) & (df["event_name"] == "CREATE")].index.to_list() + [df.shape[0]]
    ending_indexes = [0] + df[(df["event_filename"].str.contains("starting_")) & (df["event_name"] == "CLOSE_WRITE,CLOSE")].index.to_list()
    touch_file_names = ["setup"] + touch_file_names
    touch_file_names = touch_file_names[0:len(starting_indexes)]
    for starting_index, ending_index, touch_file_name in zip(starting_indexes, ending_indexes, touch_file_names):
        steps[touch_file_name] = (ending_index, starting_index)
    print(steps)

    df["watched_filename"] = df["watched_filename"] + df["event_filename"]
    df.drop("event_filename", axis=1, inplace=True)
    df.rename(columns={'watched_filename':'file_name'}, inplace=True)

    modify_df = df[df["event_name"] == "MODIFY"]
    file_names = modify_df["file_name"].value_counts().index.to_list()

    nralw_file_names = []
    for file_name in file_names:
        if df[(df["file_name"] == file_name) & (df["event_name"] == "MODIFY")].shape[0] == 0: continue
        last_modify_index = df[(df["file_name"] == file_name) & (df["event_name"] == "MODIFY")].index.to_list()[-1]
        last_access_index = 0
        if df[(df["file_name"] == file_name) & (df["event_name"] == "ACCESS")].shape[0] > 0:
            last_access_index = df[(df["file_name"] == file_name) & (df["event_name"] == "ACCESS")].index.to_list()[-1]
        if last_access_index < last_modify_index:
            nralw_file_names.append(file_name)

    # for filename in nralw_file_names:
    #     print(filename)
