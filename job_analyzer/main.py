import utils
import os
import subprocess


def main():
    # GET THE PROJECTS
    os.chdir("..")
    repositories = utils.get_filtered_repos()
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
            response = utils.fork_project(owner=owner, repo=repo)
            # response = {"owner": {"login": "optimizing-ci-builds"}}
            forked_owner = response["owner"]["login"]
        except ValueError as error:
            print(error)
            # continue
            pass

        # yml_files_path = repository["Gyml_jacoco"].split(";") + repository["Gyml_cobertura"].split(";")
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
            configured_yaml_files.append(utils.configure_yaml_file(yaml_file))
            yaml_shas.append(yaml_sha)

        # PHASE-2: SETUP
        """SETTING UP RUNNER"""
        """SETTING UP THE ENVIRONMENT FOR THE RUNNER AND THE INOTIFYWAIT"""
        """RUNNING THE RUNNER AND THE INOTIFYWAIT"""
        try:
            token: str = utils.get_runner_token(forked_owner, repo)
        except ValueError as error:
            print(error)
            # continue
            pass
        runner_version: str = "2.296.1"
        tar_filename: str = f"linux-x64-{runner_version}.tar.gz"
        runner_token = utils.setup_runner(tar_filename, runner_version, token, forked_owner, repo)

        # PHASE-3: EXECUTION
        """COMMITTING THE CHANGES IN THE YAML, TRIGGERING THE RUNNER AND INOTIFYWAIT"""
        proc1, proc2, commit_sha = utils.execute(forked_owner, repo, sha, default_branch, yml_files_path, configured_yaml_files, yaml_shas)
        utils.check_runs(forked_owner, repo, commit_sha)

        proc1.kill()
        proc2.kill()
        print("Processes killed.")

        # # PHASE-4: ANALYSIS
        # """ANALYZING THE CSV PRODUCED BY INOTIFYWAIT"""
        # """PRINTING THE JOB (LINE NUMBER) FROM THE YAML FILE CAUSING UNNECESSARY USAGE"""
        

        # Return to the job_analyzer dir
        os.chdir("..")


if __name__ == "__main__":
    main()

