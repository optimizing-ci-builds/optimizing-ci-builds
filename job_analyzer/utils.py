import base64
import json
import os
import requests

base_api_url: str = "https://api.github.com"
user_token: str = os.environ["G_AUTH_OP"]
headers: dict = {"Accept": "application/vnd.github+json",
                 "Authorization": f"token {user_token}"}


def fork_project(owner: str, repo: str):
    url = f"{base_api_url}/repos/optimizing-ci-builds/{repo}"
    requests.delete(url=url, headers=headers)
    url_path: str = f"{base_api_url}/repos/{owner}/{repo}/forks"
    response = requests.post(url_path, headers=headers)
    if response.status_code != 202:
        raise ValueError(
            f"There have been a problem while forking {owner}/{repo}. Error: {response.text}")
    return response.json()


def get_yaml_file(forked_owner: str, repo: str, file_name: str):
    url_path: str = f"{base_api_url}/repos/{forked_owner}/{repo}/contents/.github/workflows/{file_name}"
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
    os.system(f"mkdir actions-runner")

    runner_url = f"https://github.com/actions/runner/releases/download/v{runner_version}/actions-runner-{tar_filename}"
    target_path = f"actions-runner/actions-runner-{tar_filename}"
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

    os.system(f"tar xzf ./actions-runner/actions-runner-{tar_filename} -C actions-runner")

    os.system("mkdir actions-runner/_work")
    os.chdir("actions-runner")
    os.system(
        f"echo | ./config.sh --url https://github.com/{owner}/{repo} --token {token}")



def commit_file(owner: str, repo: str, file_name: str, new_file_content: str, yaml_sha: str):
    url_path: str = f"{base_api_url}/repos/{owner}/{repo}/contents/.github/workflows/{file_name}"
    content = base64.b64encode(bytes(new_file_content, "utf-8"))
    content = content.decode("utf-8")
    data = {
        "message": f"{file_name} updated.",
        "content": content,
        "sha": yaml_sha
    }
    response = requests.put(url=url_path, data=json.dumps(data), headers=headers)
    if response.status_code != 200:
        raise ValueError(f"There was a problem while committing the yaml file on {owner}/{repo}. Error: {response.text}")

        


def execute(owner: str, repo: str, file_name: str, new_file_content: str, yaml_sha: str):
    
    os.popen(f"inotifywait -mr _work/ --format %T,%w%f,%e --timefmt %T -o ../logs/{owner}-{repo}.csv")
    os.popen("./run.sh")
    commit_file(owner, repo, file_name, new_file_content, yaml_sha)

