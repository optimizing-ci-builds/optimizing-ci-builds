import base64
import json
import os
from urllib.parse import uses_relative
import requests
import csv
import time

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
    response = requests.get(url=url_path, headers=headers).json()
    # if response.status_code != 200:
    #     raise ValueError(
    #         f"There have been a problem while retrieving the .github/workflows/{file_name} file from {forked_owner}/{repo}. Error: {response.text}")
    return base64.b64decode(response["content"]).decode("utf-8"), response["sha"]


def configure_yaml_file(yaml_file: str):
    new_yaml_file: str = ""
    line_number: int = 0
    indent = 0
    for line in yaml_file.split("\n"):
        line_number += 1
        if line.strip().split(":")[0] == "runs-on":
            new_yaml_file += " " * (len(line) - len(line.lstrip()))
            new_yaml_file += "runs-on: self-hosted\n"
            continue
        if "- uses" in line or "- name" in line or "- run" in line:
            indent = len(line) - len(line.lstrip())
            change = ' ' * indent + "- run: touch starting_" + str(line_number) + "\n"
            new_yaml_file += change
            new_yaml_file += line + "\n"
        else:
            new_yaml_file += line + "\n"
    return new_yaml_file


def get_runner_token(owner: str, repo: str):
    url_path: str = f"{base_api_url}/repos/{owner}/{repo}/actions/runners/registration-token"
    response = requests.post(url_path, headers=headers)
    if response.status_code != 201:
        raise ValueError(
            f"There have been a problem while getting a token for the runner on {owner}/{repo}. Error: {response.text}")
    return response.json()["token"]


def setup_runner(tar_filename, runner_version, token, owner, repo):
    url_path: str = f"{base_api_url}/repos/{owner}/{repo}/actions/runners"
    response = requests.get(url_path, headers=headers)

    if response.json()["total_count"] == 0:
        os.system(f"mkdir "+repo+"_runner")
        runner_url = f"https://github.com/actions/runner/releases/download/v{runner_version}/actions-runner-{tar_filename}"
        target_path = f""+repo+"_runner/actions-runner-"+tar_filename
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

        os.system(f"tar xzf ./"+repo+"_runner/actions-runner-"+tar_filename+" -C "+repo+"_runner")

        os.system("mkdir "+repo+"_runner/_work")
        os.chdir(""+repo+"_runner")
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
    proc1 = os.popen(f"inotifywait -mr _work/ --format %T,%w%f,%e --timefmt %T -o ../{repo}_logs/{owner}-{repo}.csv")
    proc2 = os.popen("./run.sh")
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
    
