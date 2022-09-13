import base64
import json
import os
from urllib.parse import uses_relative
import requests
import csv
import time
import subprocess
import sys
# import pandas as pd
# import numpy as np

base_api_url: str = "https://api.github.com"
user_token: str = os.environ["G_AUTH_OP"]
headers: dict = {"Accept": "application/vnd.github+json",
                 "Authorization": f"token {user_token}"}


def fork_project(owner: str, repo: str):
    url = f"{base_api_url}/repos/optimizing-ci-builds/{repo}"
    requests.delete(url=url, headers=headers)
    # if "id" not in response:
    url_path: str = f"{base_api_url}/repos/{owner}/{repo}/forks"
    response = requests.post(url_path, headers=headers)
    if response.status_code != 202:
        raise ValueError(
            f"There have been a problem while forking {owner}/{repo}. Error: {response.text}")
    return response.json()


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
            name = f"{job_name}_{step_name}_{line_number}"
            change = ' ' * indent + f"- run: touch ${name}\n"
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
  

def commit_file(owner: str, repo: str, sha : str, default_branch:str ,file_paths, new_file_contents, yaml_shas):
    create_branch(owner, repo, sha)
    blob_shas = create_blobs(owner, repo, new_file_contents)
    tree_sha = create_tree(owner, repo, sha, file_paths, blob_shas)
    new_commit_sha = create_commit(owner, repo, sha, tree_sha)
    commit_to_branch(owner, repo, new_commit_sha)
    open_pull_request(owner, repo, default_branch)
    return new_commit_sha


def create_branch(owner, repo, sha):
    url = f"{base_api_url}/repos/{owner}/{repo}/git/refs"
    body = {
            "ref": "refs/heads/optimizing-ci-builds",
            "sha": sha
    }
    response = requests.post(url=url, data=json.dumps(body), headers=headers)


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
        tree.append({"path": file_paths[0], "mode": "100644", "type": "blob", "sha": blob_shas[i] })
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

def execute(owner: str, repo: str, sha:str, default_branch:str, file_paths, new_files, yaml_shas):
    proc1 = subprocess.Popen(f"inotifywait -mr _work/ --format '%T;%w;%f;%e' --timefmt %T -o ../{repo}_logs/{owner}-{repo}.csv", shell=True)
    proc2 = subprocess.Popen("./run.sh")
    print("Processes created.")
    commit_sha = commit_file(owner, repo, sha, default_branch,file_paths, new_files, yaml_shas)
    return proc1, proc2, commit_sha


def get_filtered_repos():
    repositories = []
    with open("data/filtered_repositories.csv", "r", newline="", encoding="utf8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        for row in csv_reader:
            repositories.append(
                {"name": row[0], "link": row[1], "default_branch": row[2], "sha": row[3],
                "stargazers_count": row[4], "forks_count": row[5],
                "Maven": row[6], "Gradle": row[7], "Travis CI": row[8], "Github Actions": row[9],
                "MJacoco": row[10], "MCobertura": row[11], "MJavadoc": row[12],
                "GJacoco": row[13], "GCobertura": row[14], "GJavadoc": row[15],
                "Tyml_codecov": row[16], "Tyml_coveralls": row[17], "Tyml_codacy": row[18],
                "Tyml_jacoco": row[19], "Tyml_cobertura": row[20], "Tyml_javadoc": row[21],
                "Gyml_codecov": row[22], "Gyml_coveralls": row[23], "Gyml_codacy": row[24],
                "Gyml_jacoco": row[25], "Gyml_cobertura": row[26], "Gyml_javadoc": row[27]})
    return repositories


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
    

# def analyze(owner: str, repo: str):
#     PATH = f"../{repo}_logs/{owner}-{repo}"
#     df = pd.read_csv(f"{PATH}.csv", sep = ';', names=["time", "watched_filename", "event_filename", "event_name"])
#     print(f"Shape of the {PATH}.csv: {df.shape}")
#     print(f"{df['event_name'].value_counts()}")

#     df['event_filename'] = df['event_filename'].replace(np.nan, '')

#     print(f"Count (jacoco.exec, MODIFY)  : {df[(df['event_name'] == 'MODIFY') & (df['event_filename'] == 'jacoco.exec')].shape[0]}")
#     print(f"Count (cobertura.ser, MODIFY): {df[(df['event_name'] == 'MODIFY') & (df['event_filename'] == 'cobertura.ser')].shape[0]}\n")

#     """Since we don't need duplicate values, we may as well get rid of them"""
#     df.drop_duplicates(inplace=True)
#     print(f"Shape after dropping duplicates {df.shape}")

#     index_by_line_number: dict = {}
#     for row in df.iterrows():
#         if "starting_" in row["event_filename"] and row["event_name"] == "CREATE":
#             line_number = int(row["event_filename"].replace("starting_", ""))
#             index_by_line_number[line_number] = row[0]

#     """Let's merge watched_filename and event_filename"""
#     df["watched_filename"] = df["watched_filename"] + df["event_filename"]
#     df.drop("event_filename", axis=1, inplace=True)
#     df.rename(columns={'watched_filename':'filename'}, inplace=True)

#     print(f"{df['event_name'].value_counts()}\n")

#     df.drop(df[df["event_name"] == "OPEN"].index, inplace=True)
#     df.drop(df[df["event_name"] == "CREATE,ISDIR"].index, inplace=True)
#     df.drop(df[df["event_name"] == "OPEN,ISDIR"].index, inplace=True)
#     df.drop(df[df["event_name"] == "CLOSE_NOWRITE,CLOSE,ISDIR"].index, inplace=True)
#     df.drop(df[df["event_name"] == "ACCESS,ISDIR"].index, inplace=True)
#     df.drop(df[df["event_name"] == "CLOSE_NOWRITE,CLOSE"].index, inplace=True)
#     df.drop(df[df["event_name"] == "CLOSE_WRITE,CLOSE"].index, inplace=True)
#     df.drop(df[df["event_name"] == "DELETE"].index, inplace=True)
#     df.drop(df[df["event_name"] == "DELETE_SELF"].index, inplace=True)
#     df.drop(df[df["event_name"] == "DELETE,ISDIR"].index, inplace=True)
#     df.drop(df[df["event_name"] == "MOVED_FROM"].index, inplace=True)
#     df.drop(df[df["event_name"] == "MOVED_TO"].index, inplace=True)
#     df.drop(df[df["event_name"] == "ATTRIB"].index, inplace=True)

#     print(f"{df['event_name'].value_counts()}\n")

#     """ THERE ARE 4 CASES:
#     1. CREATED, MODIFIED, ACCESSED         - FINE
#     2. CREATED, MODIFIED, NOT ACCESSED     - UNNECESSARY
#     3. CREATED, NOT MODIFIED, ACCESSED     - POSSIBLE?
#     4. CREATED, NOT MODIFIED, NOT ACCESSED - UNNECESSARY
#     """

#     """created accessed then written but the last write might be unnecessary"""
#     """mapping actions to yml file from inotifywait logs"""
#     """ast parser yml file?"""
#     """an automatic tool that prints on this file for this action (like line number)"""

#     df_create = df[df["event_name"] == "CREATE"]
#     df_modify = df[df["event_name"] == "MODIFY"]
#     df_access = df[df["event_name"] == "ACCESS"]


#     case1_filenames = []
#     case2_filenames = []
#     case3_filenames = []
#     case4_filenames = []

#     for idx, row in df_create.iterrows():
#         # print(f"{idx} - {row['filename']} - {row['event_name']}")
#         is_modified = row["filename"] in df_modify["filename"].values
#         is_accessed = row["filename"] in df_access["filename"].values
#         # print(f"is_modified: {is_modified}")
#         # print(f"is_accessed: {is_accessed}\n")
#         if is_modified and is_accessed:
#             case1_filenames.append(row["filename"])
#         elif is_modified and not is_accessed:
#             case2_filenames.append(row["filename"])
#         elif not is_modified and is_accessed:
#             case3_filenames.append(row["filename"])
#         elif not is_modified and not is_accessed:
#             case4_filenames.append(row["filename"])

#     print(f"COUNT CASE1: {len(case1_filenames)}")
#     print(f"COUNT CASE2: {len(case2_filenames)}")
#     print(f"COUNT CASE3: {len(case3_filenames)}")
#     print(f"COUNT CASE4: {len(case4_filenames)}")

#     for fl in case1_filenames:
#         df_ = df[df["filename"] == fl]

            
#     for fl in case4_filenames:
#         print(fl)

# """ analyze on the fly, or analyze at the end? """
# """ can we discuss the algorithm for analyzing the csv file one more time? """
# """ - do we need to measure time taken for the build? """
# """ - do we need to """