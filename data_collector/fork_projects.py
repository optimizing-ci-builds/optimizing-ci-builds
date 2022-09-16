import base64
import json
import os
from urllib.parse import uses_relative
import requests
import csv
import time
import subprocess

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

def get_filtered_repos():
    repositories = []
    with open("data/file_paths_filtered.csv", "r", newline="", encoding="utf8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        for row in csv_reader:
            repositories.append(
                {"name": row[0], "link": row[1], "default_branch": row[2], "sha": row[3],
                "stargazers_count": row[4], "forks_count": row[5],
                "Maven": row[6], "Gradle": row[7], "Travis CI": row[8], "Github Actions": row[9]})
    return repositories


# GET THE PROJECTS
os.chdir("..")
repositories = get_filtered_repos()
os.chdir("job_analyzer")

for repository in repositories:
    # PHASE-1: COLLECTION
    """FORKING THE PROJECT (VIA GITHUB API)"""
    """PARSING THE YAML FILE"""
    """CHANGING THE YAML FILE"""
    owner: str = repository["name"].split("/")[0]
    repo: str = repository["name"].split("/")[1]
    sha: str = repository["sha"]
    default_branch: str = repository["default_branch"]
    os.system("mkdir " + repo + "_logs")
    try:
        response = fork_project(owner=owner, repo=repo)
        # response = {"owner": {"login": "optimizing-ci-builds"}}
        forked_owner = response["owner"]["login"]
    except ValueError as error:
        print(error)
        # continue
        pass