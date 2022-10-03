import utils
import os
import time
import subprocess


def main():
    # GET THE PROJECTS
    os.chdir("..")
    repositories = utils.get_filtered_repos()
    os.chdir("job_analyzer")
    
    for index, repository in enumerate(repositories):
        try:
            if index % 10 == 0:
                time.sleep(108000)
            # PHASE-1: COLLECTION
            """FORKING THE PROJECT (VIA GITHUB API)"""
            """PARSING THE YAML FILE"""
            """CHANGING THE YAML FILE"""
            forked_owner: str = "optimizing-ci-builds"
            repo: str = repository["name"].split("/")[1]
            print(f"Running tests on {forked_owner}/{repo}")
            default_branch: str = repository["default_branch"]

            try:
                sha: str = utils.retrieve_sha(owner=forked_owner, repo=repo, default_branch=default_branch)
            except ValueError as error:
                print(error)
                pass

            # utils.add_secret(owner=forked_owner, repo=repo)

            yml_files_path = repository["Github Actions"].split(";")
            yml_files_path = [i for i in yml_files_path if i]

            configured_yaml_files = []
            yaml_shas = []
            for file_path in yml_files_path:
                try:
                    yaml_file, yaml_sha = utils.get_yaml_file("optimizing-ci-builds", repo, file_path)
                except ValueError as error:
                    print(error)
                    # continue
                    pass
                configured_yaml = utils.configure_yaml_file(yaml_file, repo)
                configured_yaml_files.append(configured_yaml)
                yaml_shas.append(yaml_sha)

            commit_sha = utils.execute(forked_owner, repo, sha, default_branch, yml_files_path, configured_yaml_files, yaml_shas)
            # utils.check_runs(forked_owner, repo, commit_sha)

            os.chdir("..")
        except:
            print("There was an error don't ask me what it is.")

if __name__ == "__main__":
    main()

