import base64
import json
import time
import os
from urllib.parse import uses_relative
import requests
import csv
import time
import subprocess
import sys
import pandas as pd
import numpy as np
from base64 import b64encode
from nacl import encoding, public

base_api_url: str = "https://api.github.com"
user_token: str = os.environ["G_AUTH_OP"]
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


def add_secret(owner: str, repo: str):
    # get repo public key
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    response = requests.get(url=url, headers=headers).json()
    # print(response)
    key_id = response['key_id']
    key = response['key']
    # encrypt the key
    public_key = public.PublicKey(key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(user_token.encode("utf-8"))
    value = b64encode(encrypted).decode("utf-8")
    # add secret
    secret_name = "API_TOKEN_GITHUB"
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    body = {
        "encrypted_value": value,
        "key_id": key_id
    }
    response = requests.delete(url=url, headers=headers).json()
    print(response)
    response = requests.put(url=url, data=json.dumps(body), headers=headers).json()
    print(response)


def add_environment_secret(owner: str, repo: str):
    # get repo id
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url=url, headers=headers).json()
    # print(response)
    repository_id = response['id']
    # create environment
    environment_name = "OCB"
    url = f"https://api.github.com/repositories/{repository_id}/environments/{environment_name}"
    body = {
        "wait_timer": 5000,
        "reviewers": []
    }
    response = requests.put(url=url, data=json.dumps(body), headers=headers).json()
    # print(response)
    # get repo environment public key
    url = f"https://api.github.com/repositories/{repository_id}/environments/{environment_name}/secrets/public-key"
    response = requests.get(url=url, headers=headers).json()
    # print(response)
    key_id = response['key_id']
    key = response['key']
    # encrypt the key
    public_key = public.PublicKey(key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(user_token.encode("utf-8"))
    value = b64encode(encrypted).decode("utf-8")
    # add secret
    secret_name = "API_TOKEN_GITHUB_OCB"
    url = f"https://api.github.com/repositories/{repository_id}/environments/{environment_name}/secrets/{secret_name}"
    body = {
        "encrypted_value": value,
        "key_id": key_id
    }
    response = requests.put(url=url, data=json.dumps(body), headers=headers).json()
    # print(response)


def get_yaml_file(forked_owner: str, repo: str, file_path: str):
    url_path: str = f"{base_api_url}/repos/{forked_owner}/{repo}/contents/{file_path}"
    # will change here
    response = requests.get(url=url_path, headers=headers)
    if response.status_code != 200:
        raise ValueError(
            f"There have been a problem while retrieving the .github/workflows/? file from {forked_owner}/{repo}. Error: {response.text}")
    return base64.b64decode(response.json()["content"]).decode("utf-8"), response.json()["sha"]


def configure_yaml_file(yaml_file: str, repo: str, file_path: str, time):
    new_yaml_file: str = ""
    indent = 0
    job_indent = 0
    on_indent = 0
    steps_indent = 0
    in_step_indent = 0
    in_job = False
    in_on = False
    in_steps = False
    job_name = ""
    line_number = 0
    name = ""
    for line_index, line in enumerate(yaml_file.split("\n")):
        if "secrets." in line:
            print(f"Secret in repository: {repo} YAML file: {file_path}")
        line_number += 1
        indent = len(line) - len(line.lstrip())
        if len(line.lstrip()) > 0:
            is_comment = line.lstrip()[0] == "#"
        else:
            is_comment = False
        if (line == "") or is_comment :
            new_yaml_file += line + "\n"
            continue
        elif "if: " in line:
            continue
        else:
            if in_job and (indent == job_indent):
                job_name = line.strip()[:-1]
            if (in_job and (indent <= job_indent)) and (line.strip() != "") and (job_name != line.strip()[:-1]):
                in_job = False

            if in_on and (indent <= on_indent) and (line.strip() != ""):
                in_on = False
            
            condition = None
            try:
                next_line_indent = (len(yaml_file.split("\n")[line_index+1]) - len(yaml_file.split("\n")[line_index+1].lstrip()))
                condition = next_line_indent < steps_indent
            except:
                condition = True
            if (in_steps and condition):
                end_of_step = True
                for l in yaml_file.split("\n")[line_index+1:len(yaml_file.split("\n"))]:
                    if l.strip() != "":
                        end_of_step = False
                        break
                new_yaml_file += line + "\n"
                if end_of_step:
                    in_steps = False
                    new_yaml_file += " " * (in_step_indent) + "- run: touch starting_finished_finished_8979874\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "if: always()\n"
                    new_yaml_file += " " * (in_step_indent) + "- run: rm starting_finished_finished_8979874\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "if: always()\n"
                    new_yaml_file += " " * (in_step_indent) + "- name: Execute py script # run file\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "if: always()\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "run: |\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "python .github/workflows/script.py\n"
                    new_yaml_file += " " * (in_step_indent) + "- name: Pushes analysis to another repository\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "if: always()\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "id: push_directory\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "uses: cpina/github-action-push-to-another-repository@main\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "env:\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "API_TOKEN_GITHUB: ${{ secrets.API_TOKEN_GITHUB }}\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "with:\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "source-directory: 'optimizing-ci-builds-ci-analysis'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "destination-github-username: 'optimizing-ci-builds'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "destination-repository-name: 'ci-analyzes'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + f"target-branch: '{repo}.{time}'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + f"target-directory: '{repo}/{time}/{file_path.replace('.yml', '')}/{job_name}'\n"

                    if end_of_step:
                        for l in yaml_file.split("\n")[line_index+1:len(yaml_file.split("\n"))]:
                            new_yaml_file += l + "\n"
                        break
                    # if in_steps and (indent <= steps_indent):
                    #     new_yaml_file += line + "\n"
                continue

            if line.strip().split(":")[0] == "on":
                in_on = True
                on_indent = indent
                new_yaml_file += " " * indent
                new_yaml_file += "on: [push]\n"
                continue
            elif line.strip().split(":")[0] == "jobs":
                in_job = True
                job_name_index = line_index + 1
                for l in yaml_file.split("\n")[line_index+1:len(yaml_file.split("\n"))]:
                    if l.strip() != "":
                        break
                    job_name_index += 1

                job_indent = len(yaml_file.split("\n")[job_name_index]) - len(yaml_file.split("\n")[job_name_index].lstrip())
            elif line.strip().split(":")[0] == "steps":
                in_steps = True
                for l in yaml_file.split("\n")[line_index+1:len(yaml_file.split("\n"))]:
                        if l.strip() != "":
                            in_step_indent = len(l) - len(l.lstrip())
                            break
                steps_indent = indent
                new_yaml_file += line + "\n"
                new_yaml_file += " " * (in_step_indent) + "- uses: actions/setup-python@v2\n"
                new_yaml_file += " " * (in_step_indent + 2) + "with:\n"
                new_yaml_file += " " * (in_step_indent + 4) + "python-version: '3.10'\n"
                new_yaml_file += " " * (in_step_indent) + "- name: Install dependencies\n"
                new_yaml_file += " " * (in_step_indent + 2) + "run: |\n"
                new_yaml_file += " " * (in_step_indent + 4) + "python -m pip install --upgrade pip\n"
                new_yaml_file += " " * (in_step_indent + 4) + "pip install pandas\n"
                new_yaml_file += " " * (in_step_indent + 4) + "pip install numpy\n"
                new_yaml_file += " " * (in_step_indent) + "- run: sudo apt update\n"
                new_yaml_file += " " * (in_step_indent) + "- run: sudo apt install inotify-tools\n"
                new_yaml_file += " " * (in_step_indent) + f"- run: inotifywait -mr /home/runner/work/{repo}/{repo}/ --format '%T;%w;%f;%e' --timefmt %T -o /home/runner/inotify-logs.csv & echo 'basak'\n"
                continue

            if in_on:
                continue
            
            if "- uses" in line or "- name" in line or "- run" in line:
                if "- uses" in line:
                    res= line.split(":")
                    ress=res[1].split("/")
                    uses_name= ress[1].split("@")
                    #print(uses_name[0])
                    step_name= "uses-" + uses_name[0]
                    #step_name = "uses" + str(line_number)
                else:
                    step_name = ''.join(e for e in line.split(":")[1] if e.isalnum())
                job_name = ''.join(e for e in job_name if e.isalnum())
                name = f"{job_name}_{step_name}_{line_number}"
                change = ' ' * indent + f"- run: touch starting_{name}\n"
                change += ' ' * indent + f"- run: rm starting_{name}\n"
                new_yaml_file += change
                new_yaml_file += line + "\n"
            else:
                new_yaml_file += line + "\n"
    return new_yaml_file


def retrieve_sha_ci_analyzes(owner: str, repo: str, time):
    url = f"https://api.github.com/repos/{owner}/ci-analyzes/branches/main"
    response = requests.get(url=url, headers=headers).json()
    sha = response['commit']['sha']
    create_branch_ci_analyzes(owner, repo, sha, time)


def create_branch_ci_analyzes(owner, repo, sha, time):
    url = f"{base_api_url}/repos/{owner}/ci-analyzes/git/refs/heads/optimizing-ci-builds"
    requests.delete(url=url,  headers=headers)
    url = f"{base_api_url}/repos/{owner}/ci-analyzes/git/refs"
    branch_name = f"refs/heads/{repo}.{time}"
    body = {
            "ref": branch_name,
            "sha": sha
    }
    response = requests.post(url=url, data=json.dumps(body), headers=headers)
    # print(response.json())


def execute(owner: str, repo: str, sha:str, default_branch:str, file_paths, new_files, yaml_shas):
    commit_sha = commit_file(owner, repo, sha, default_branch,file_paths, new_files, yaml_shas)
    return commit_sha


def commit_file(owner: str, repo: str, sha : str, default_branch:str, file_paths, new_file_contents, yaml_shas):
    create_branch(owner, repo, sha)
    blob_shas = create_blobs(owner, repo, new_file_contents)
    tree_sha = create_tree(owner, repo, sha, file_paths, blob_shas)
    new_commit_sha = create_commit(owner, repo, sha, tree_sha)
    commit_to_branch(owner, repo, new_commit_sha)
    open_pull_request(owner, repo, default_branch)
    return new_commit_sha


def create_branch(owner, repo, sha):
    url = f"{base_api_url}/repos/{owner}/{repo}/git/refs/heads/optimizing-ci-builds"
    requests.delete(url=url,  headers=headers)
    url = f"{base_api_url}/repos/{owner}/{repo}/git/refs"
    body = {
            "ref": "refs/heads/optimizing-ci-builds",
            "sha": sha
    }
    response = requests.post(url=url, data=json.dumps(body), headers=headers)
    # print(response.json())



def create_blobs(owner, repo, new_file_contents):
    blob_shas = []
    url = f"{base_api_url}/repos/{owner}/{repo}/git/blobs"
    for content in new_file_contents:
        body = {
            "content": content,
            "encoding": "utf-8"
        }
        response = requests.post(url=url, data=json.dumps(body), headers=headers)
        blob_shas.append(response.json()['sha'])
    text_file = open("script", "r")
    lines = text_file.readlines()
    content = ""
    for line in lines:
        if "{repo}" in line:
            line = line.replace("{repo}", repo)
        content += line
    text_file.close()
    body = {
        "content": content,
        "encoding": "utf-8"
    }
    response = requests.post(url=url, data=json.dumps(body), headers=headers)
    blob_shas.append(response.json()['sha'])
    return blob_shas


def create_tree(owner, repo, sha, file_paths, blob_shas):
    file_paths.append(".github/workflows/script.py")
    url = f"{base_api_url}/repos/{owner}/{repo}/git/trees"
    body = {"base_tree": sha}
    tree = []
    for i in range(0, len(file_paths)):
        tree.append({"path": file_paths[i], "mode": "100644", "type": "blob", "sha": blob_shas[i]})
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
    # print(response.json())
    new_commit_sha = response.json()['sha']
    return new_commit_sha


def commit_to_branch(owner, repo, new_commit_sha):
    url = f"{base_api_url}/repos/{owner}/{repo}/git/refs/heads/optimizing-ci-builds"
    body = {
        "ref": "refs/heads/optimizing-ci-builds",
        "sha": new_commit_sha
    }
    response = requests.post(url=url, data=json.dumps(body), headers=headers)
    # print(response.json())


def open_pull_request(owner: str, repo: str, default_branch:str ):
    url = f"{base_api_url}/repos/{owner}/{repo}/pulls"
    body = {
        "title": "Optimizing CI builds",
        "head":"optimizing-ci-builds",
        "base": default_branch
    }
    response = requests.post(url=url, data=json.dumps(body), headers=headers)
    # print(response.json())


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
    ending_indexes = [0] + df[(df["event_filename"].str.contains("starting_")) & (df["event_name"] == "DELETE")].index.to_list()
    starting_df = df[df["event_filename"].str.contains("starting_")]
    touch_file_names = ["setup"] + [x.replace("starting_", "") for x in starting_df["event_filename"].value_counts().index.to_list()]
    for starting_index, ending_index, touch_file_name in zip(starting_indexes, ending_indexes, touch_file_names):
        steps[touch_file_name] = (ending_index, starting_index)
    print(steps)

    df["watched_filename"] = df["watched_filename"] + df["event_filename"]
    df.drop("event_filename", axis=1, inplace=True)
    df.rename(columns={'watched_filename':'file_name'}, inplace=True)

    modify_df = df[df["event_name"] == "MODIFY"]
    file_names = modify_df["file_name"].value_counts().index.to_list()

    nralw_file_names = []
    info = []
    for file_name in file_names:
        last_access_step = ""
        last_modify_step = ""
        creation_step = ""
        if df[(df["file_name"] == file_name) & (df["event_name"] == "MODIFY")].shape[0] == 0: continue
        last_modify_index = df[(df["file_name"] == file_name) & (df["event_name"] == "MODIFY")].index.to_list()[-1]
        last_access_index = 0
        if df[(df["file_name"] == file_name) & (df["event_name"] == "ACCESS")].shape[0] > 0:
            last_access_index = df[(df["file_name"] == file_name) & (df["event_name"] == "ACCESS")].index.to_list()[-1]
        else:
            last_access_index = -1
            last_access_step = "Not provided"
        if last_access_index < last_modify_index:
            nralw_file_names.append(file_name)
            try:
                creation_index = df[(df["file_name"] == file_name) & (df["event_name"] == "CREATE")].index.to_list()[0]
            except:
                creation_index = -1
                creation_step = "Not provided"
            for touch_file_name, (starting_index, ending_index) in steps.items():
                if (last_access_index > starting_index) & (last_access_index < ending_index):
                    last_access_step = touch_file_name if touch_file_name == "setup" else touch_file_name.split("_")[1]
                if (last_modify_index > starting_index) & (last_modify_index < ending_index):
                    last_modify_step = touch_file_name if touch_file_name == "setup" else touch_file_name.split("_")[1]
                if (creation_index > starting_index) & (creation_index < ending_index):
                    creation_step = touch_file_name if touch_file_name == "setup" else touch_file_name.split("_")[1]

            info.append({"file_name": file_name, "last_access_index": last_access_index, "last_modify_index": last_modify_index, 
                "creation_index": creation_index, "last_access_step":last_access_step , "last_modify_step":last_modify_step,
                "creation_step": creation_step})

    info_df = pd.DataFrame(info)
    info_df.to_csv("info.csv")

    print(f"All files: {len(file_names)}")
    print(f"NRALW files: {len(nralw_file_names)}")
