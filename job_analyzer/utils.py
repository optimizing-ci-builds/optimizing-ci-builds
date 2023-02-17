import base64
import itertools
import json
import textwrap
import os
from urllib.parse import uses_relative
import requests
import csv
import subprocess
import sys
import pandas as pd
import numpy as np
from base64 import b64encode
from nacl import encoding, public
# import yaml
import oyaml as yaml
from yaml.resolver import BaseResolver
import ruamel.yaml
import copy


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


def divide_yaml_per_job(yaml_string):
    new_set_of_jobs = []
    
    loaded_yaml = ruamel.yaml.safe_load(yaml_string)   
    
    # get high level keys of the yaml file
    yaml_keys = list(loaded_yaml.keys())
    
    # find the index of the jobs key
    jobs_index = yaml_keys.index("jobs")
    
    jobs_names = list(loaded_yaml["jobs"].keys())
    for job_name in jobs_names:
        print("Evaluating job: " + job_name)
        # if the job has a strategy->matrix, then we need to create a new yaml file per matrix
        # if loaded_yaml["jobs"][job_name]["strategy"]["matrix"]:
        if "strategy" in loaded_yaml["jobs"][job_name] and "matrix" in loaded_yaml["jobs"][job_name]["strategy"]:
            print("found matrix in the job: " + job_name)
            
            matrix_key = list(loaded_yaml["jobs"][job_name]["strategy"]["matrix"].keys())[0]
            matrix_values = loaded_yaml["jobs"][job_name]["strategy"]["matrix"][matrix_key]
            
            print("matrix key: " + matrix_key)
            
            temp_dict = loaded_yaml.copy()
            temp_dict["jobs"] = {}
            temp_dict["jobs"][job_name] = loaded_yaml["jobs"][job_name]
            
            for matrix_value in matrix_values:
                print("Evalueating matrix value: " + matrix_value + " for key: " + matrix_key)
                
                # replace the matrix value to the job
                temp_dict["jobs"][job_name]["strategy"]["matrix"][matrix_key] = [matrix_value]
                
                # print(ruamel.yaml.dump(temp_dict))
            
                new_set_of_jobs.append({job_name+"_"+matrix_value: yaml.dump(temp_dict)})
        
            if "needs" in loaded_yaml["jobs"][job_name]:
                print("found needs in the job: " + job_name)
            
            else:
                temp_dict = loaded_yaml.copy()
                

        else:
            # part2 += "  " +  ruamel.yaml.dump(loaded_yaml["jobs"][job_name], Dumper=ruamel.yaml.RoundTripDumper)
            print("no matrix in the job: " + job_name)

            # in a temp dict, copy the loaded_yaml and remove the value of jobs other than the current job name
            # then append the temp dict to the new_set_of_jobs
            
            temp_dict = loaded_yaml.copy()
            temp_dict["jobs"] = {}
            temp_dict["jobs"][job_name] = loaded_yaml["jobs"][job_name]
            
            new_set_of_jobs.append({job_name: yaml.dump(temp_dict)})
            
            
            
    print("done")
    
    # replace the 'on': with on: in the new_set_of_jobs
    for job in new_set_of_jobs:
        job[list(job.keys())[0]] = job[list(job.keys())[0]].replace("'on':", "on:") 
    
    return new_set_of_jobs


def divide_yaml(yaml_string):
    new_yaml_files = []
    lines = yaml_string.splitlines()
    matrix_start = -1
    matrix_end = -1
    indentation = -1
    for i in range(len(lines)):
        line = lines[i]
        if "strategy:" in line:
            matrix_start = i
            indentation = len(line) - len(line.lstrip())
        if matrix_start != -1 and (line.strip() == "" or (indentation != -1 and len(line) - len(line.lstrip()) < indentation)):
            matrix_end = i
            break
    if matrix_start == -1 or matrix_end == -1:
        print("No strategy matrix found.")
        new_yaml_files.append("\n".join(lines))
        return new_yaml_files
    part1 = "\n".join(lines[:matrix_start])
    part2 = textwrap.dedent("\n".join(lines[matrix_start:matrix_end]))
    part3 = textwrap.dedent("\n".join(lines[matrix_end:]))
    # load the yaml string into a dictionary
    part2_dict = yaml.safe_load(part2)
    
    print(part2)
    # extract the matrix values
    # extract the keys of the matrix
    matrix_key = list(part2_dict["strategy"]["matrix"].keys())[0]
    matrix_values = part2_dict["strategy"]["matrix"][matrix_key]
    # so there should be len(matrix_values) new yaml files
    # generating new strings for each matrix value
    for value in matrix_values:
        part2_dict["strategy"]["matrix"][matrix_key] = [value]
        new_string = yaml.dump(part2_dict)
        # new_yaml_files.append(f"{part1}{new_string}{part3}")
        
        # append a dictionary with the new string and the matrix value
        new_yaml_files.append({"yaml": f"{part1}{new_string}{part3}", "matrix_value": value})
    
    # print(new_yaml_files[0]["yaml"])
    return new_yaml_files

        
def configure_yaml_file(yaml_file: str, repo: str, file_path: str, time, job_with_matrix, default_python_version):
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
    append_to_target_dir = ""
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
                
                # If the job has a matrix, then append the matrix name and value to the target directory
                if job_name in job_with_matrix:
                    for matrix_name in list(job_with_matrix[job_name].keys()):
                        append_to_target_dir += "_" + matrix_name + "_${{ matrix." + matrix_name + " }}"
                        

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
                    next_line_indent = (len(l) - len(l.lstrip()))
                    if l.strip() != "":
                        end_of_step = False
                        if(next_line_indent < in_step_indent):
                            end_of_step = True
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
                    new_yaml_file += " " * (in_step_indent + 4) + "destination-github-username: 'UT-SE-Research'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "destination-repository-name: 'ci-analyzes'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + f"target-branch: '{time}'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + f"target-directory: '{repo}/{file_path.replace('.yml', '')}/{job_name}{append_to_target_dir}'\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "continue-on-error: true\n"
                    new_yaml_file += " " * (in_step_indent) + "- name: Check push directory exit code\n"
                    new_yaml_file += " " * (in_step_indent + 2) + f"if: steps.push_directory.outcome == 'failure'\n"
                    new_yaml_file += " " * (in_step_indent + 2) + "run: |\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "echo 'push failed, trying pull and then push'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "git config --global user.name 'optimizing-ci-builds'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "git config --global user.email 'ocibsummerresearch2022@gmail.com'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "git add .\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "git commit -m 'report ${{ github.head_ref }}'\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "while ! git push origin {time}; do\n"
                    new_yaml_file += " " * (in_step_indent + 6) + f"git pull --rebase https://github.com/UT-SE-Research/ci-analyzes.git {time}\n"
                    new_yaml_file += " " * (in_step_indent + 6) + f"git push https://github.com/UT-SE-Research/ci-analyzes.git HEAD:{time}\n"
                    new_yaml_file += " " * (in_step_indent + 4) + "done"

                    append_to_target_dir = ""
                        
                    # check if there is another job
                    for l in yaml_file.split("\n")[line_index+1:len(yaml_file.split("\n"))]:
                        if l.strip() == "steps:":
                            end_of_step = False
                            new_yaml_file += "\n"
                            break

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
                new_yaml_file += " " * (in_step_indent + 4) + f"python-version: '{default_python_version}'\n"
                new_yaml_file += " " * (in_step_indent) + "- name: Install dependencies\n"
                new_yaml_file += " " * (in_step_indent + 2) + "run: |\n"
                new_yaml_file += " " * (in_step_indent + 4) + "python -m pip install --upgrade pip\n"
                new_yaml_file += " " * (in_step_indent + 4) + "pip install pandas\n"
                new_yaml_file += " " * (in_step_indent + 4) + "pip install numpy\n"
                new_yaml_file += " " * (in_step_indent) + "- run: sudo apt update\n"
                new_yaml_file += " " * (in_step_indent) + "- run: sudo apt install inotify-tools\n"
                new_yaml_file += " " * (in_step_indent) + f"- run: inotifywait -mr /home/runner/work/{repo}/{repo}/ --format '%T;%w;%f;%e' --timefmt %T -o /home/runner/inotify-logs.csv & echo 'optimizing-ci-builds'\n"
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
    # print("Saving the new yaml file: ", f"{file_path}")
    # with open ("newyaml.yaml", "w") as f:
    #     f.write(new_yaml_file)
    return new_yaml_file


def load_yaml(yaml_file: str):
    loaded_yaml = ruamel.yaml.safe_load(yaml_file)
    return loaded_yaml

def get_job_with_matrix(loaded_yaml):
    # loaded_yaml = ruamel.yaml.safe_load(yaml_file)
    jobs_names = list(loaded_yaml["jobs"].keys()) 
    
    # create a dict with the job names that has matrix
    jobs_with_matrix = {}
    for job_name in jobs_names:
        print("Checking if the job has matrix: ", job_name)
        if "strategy" in loaded_yaml["jobs"][job_name]:
            if "matrix" in loaded_yaml["jobs"][job_name]["strategy"]:
                jobs_with_matrix[job_name] = loaded_yaml["jobs"][job_name]["strategy"]["matrix"]
    return jobs_with_matrix


def get_python_version(loaded_yaml):
    # loaded_yaml = ruamel.yaml.safe_load(yaml_file)
    jobs_names = list(loaded_yaml["jobs"].keys()) 
    
    # create a dict with the job names that has matrix
    default_py_version = "3.10"
    for job_name in jobs_names:
        print("Checking if the job has default python version specified: ", job_name)
        
        # check for all "uses" in the job
        if "steps" in loaded_yaml["jobs"][job_name]:
            for step in loaded_yaml["jobs"][job_name]["steps"]:
                if "uses" in step:
                    if "actions/setup-python" in step["uses"]:
                        if "python-version" in step["with"]:
                            default_py_version = step["with"]["python-version"]
    return default_py_version


def split_matrix(yaml_file: str):
    loaded_yaml = ruamel.yaml.safe_load(yaml_file)
    jobs_names = list(loaded_yaml["jobs"].keys()) 
    
    temp_dict = loaded_yaml.copy()
    
    # create a dict with the job names that has matrix
    jobs_with_matrix = {}
    for job_name in jobs_names:
        print("Checking if the job has matrix: ", job_name)
        if "strategy" in loaded_yaml["jobs"][job_name]:
            if "matrix" in loaded_yaml["jobs"][job_name]["strategy"]:
                jobs_with_matrix[job_name] = loaded_yaml["jobs"][job_name]["strategy"]["matrix"]
            
    for job_name in jobs_names:
        print("Evaluating the job: ", job_name)
        
        if job_name in jobs_with_matrix.keys():
            print("The job has matrix : " + job_name)
            
            # Extract the matrices for this particular job with matrix
            matrix_keys = list(jobs_with_matrix[job_name].keys())
            # print("The following matrix are found : ", matrix_keys)
            
            # create cartesian product of the matrix values
            final_matrix = list(itertools.product(*jobs_with_matrix[job_name].values()))
            # print("The cartesian product of the matrix values: ", final_matrix)
            
            # Based on the cartesian product, create new jobs
            for i, values in enumerate(final_matrix):
                matrix_dict = {}
                new_job_name = job_name
                
                # create new job name, and new sub-matrix dictioanry
                for j, value in enumerate(values):
                    new_job_name += "_" + matrix_keys[j] + "_" + str(value)
                    matrix_dict[matrix_keys[j]] = [value]  
                
                # print("New job name: ", new_job_name)
                # print("Matrix dict: ", matrix_dict)
                
                temp_dict["jobs"][new_job_name] = copy.deepcopy(loaded_yaml["jobs"][job_name])
                temp_dict["jobs"][new_job_name]["strategy"]["matrix"]={}
                temp_dict["jobs"][new_job_name]["strategy"]["matrix"]= matrix_dict    
                
            # Remove the original job
            # del temp_dict["jobs"][job_name]

    
    new_yaml_file = yaml.dump(temp_dict)
    
    # replace the 'on': with on: in the new_set_of_jobs
    new_yaml_file = new_yaml_file.replace("'on':", "on:")
        
    # with open (f"{file_path}", "w") as f:
    #     f.write(new_yaml_file)
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
    branch_name = f"refs/heads/{time}"
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
