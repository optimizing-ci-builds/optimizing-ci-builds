import utils
import os
import time
import subprocess

def main():

    repositories = utils.get_filtered_repos()
    time_ = int(time.time())
    
    for repository in repositories:
        try:
            forked_owner: str = "optimizing-ci-builds"
            repo: str = repository["name"].split("/")[1]
            print(f"\nRunning tests on {forked_owner}/{repo}")
            default_branch: str = repository["default_branch"]

            try:
                sha: str = utils.retrieve_sha(owner=forked_owner, repo=repo, default_branch=default_branch)
            except ValueError as error:
                print(f"There was an error, while retrieving the sha: {error}")
                pass

            # utils.add_secret(owner=forked_owner, repo=repo)
            
            yml_files_path = repository["Github Actions"].split(";")
            yml_files_path = [i for i in yml_files_path if i]

            configured_yaml_files = []
            yaml_shas = []

            for file_path in yml_files_path:
                try:
                    yaml_file, yaml_sha = utils.get_yaml_file("optimizing-ci-builds", repo, file_path)
                    yaml_shas.append(yaml_sha)
                except ValueError as error:
                    print(f"There was an error while getting the yaml file: {error}")
                    pass

                configured_yaml = utils.configure_yaml_file(yaml_file, repo, file_path, time_)
                # with open("job_analyzer/Output.yml", "w") as text_file:
                #     print(f"{configured_yaml}", file=text_file)
                configured_yaml_files.append(configured_yaml)

            commit_sha = utils.execute(forked_owner, repo, sha, default_branch, yml_files_path, configured_yaml_files, yaml_shas)
            # utils.check_runs(forked_owner, repo, commit_sha)

        except Exception as e:
            print(f"There was an unexpected error: {e}")
        # break

if __name__ == "__main__":
    main()

