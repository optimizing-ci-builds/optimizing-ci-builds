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
        forked_owner: str = "optimizing-ci-builds"
        repo: str = repository["name"].split("/")[1]
        print(f"Running tests on {forked_owner}/{repo}")
        default_branch: str = repository["default_branch"]
        os.system("mkdir " + repo + "_logs")
        try:
            sha: str = utils.retrieve_sha(owner=forked_owner, repo=repo, default_branch=default_branch)
        except ValueError as error:
            print(error)
            pass

        # yml_files_path = repository["Gyml_jacoco"].split(";") + repository["Gyml_cobertura"].split(";")
        yml_files_path = repository["Github Actions"].split(";")
        yml_files_path = [i for i in yml_files_path if i]

        configured_yaml_files = []
        yaml_shas = []
        touch_file_names = []
        for file_path in yml_files_path:
            try:
                yaml_file, yaml_sha = utils.get_yaml_file("optimizing-ci-builds", repo, file_path)
            except ValueError as error:
                print(error)
                # continue
                pass
            configured_yaml, name = utils.configure_yaml_file(yaml_file)
            configured_yaml_files.append(configured_yaml)
            touch_file_names.append(name)
            yaml_shas.append(yaml_sha)
        repository["touch_file_names"] = touch_file_names

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
        runner_version: str = "2.294.1"
        tar_filename: str = f"linux-x64-{runner_version}.tar.gz"
        # utils.setup_runner(tar_filename, runner_version, token, forked_owner, repo)
        runner_token = utils.setup_runner(token, forked_owner, repo)

        # PHASE-3: EXECUTION
        """COMMITTING THE CHANGES IN THE YAML, TRIGGERING THE RUNNER AND INOTIFYWAIT"""
        proc1, proc2, commit_sha = utils.execute(forked_owner, repo, sha, default_branch, yml_files_path, configured_yaml_files, yaml_shas)
        utils.check_runs(forked_owner, repo, commit_sha)

        print("Killing the processes.")
        proc1.kill()
        proc2.kill()
        print("Processes killed.")

        # # PHASE-4: ANALYSIS
        # """ANALYZING THE CSV PRODUCED BY INOTIFYWAIT"""
        utils.analyze(forked_owner, repo, repositories["touch_file_names"])
        # """PRINTING THE JOB (LINE NUMBER) FROM THE YAML FILE CAUSING UNNECESSARY USAGE"""
        os.chdir("..")


if __name__ == "__main__":
    main()

