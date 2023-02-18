# Continuous Integration Build Optimization

This repository has been created in order to optimize continuous integration builds. We concentrate on code coverage files that are generated during continuous integration and then deleted without being saved anywhere. For the time being, we are solely focusing on open-source Java Maven projects and GitHub Actions.

## How To Run

Running the scripts are pretty simple, inputs and outputs are created by the scripts and there is no need to format them in between.
There are 3 folders under this project: ``Data Collector``, ``Data`` and ``Job analyzer``.

### Data Collector

Scripts are run in this order: ``repository_collector``, ``file_collector``, ``content_collector``.

#### repository_collector:

Finds ``["Name", "Link", "Default Branch", "SHA", "Stargazers Count", "Forks Count", "Date"]`` of the repositories and saves it to the ``repositories.csv`` file.

#### file_collector:

Reads repositories.csv file and finds files and their paths related to ``["Maven", "Gradle", "Travis CI", "Github Actions"]``. Then it saves the information to the file ``file_paths.csv``.

#### content_collector:

Reads ``file_paths.csv`` file and finds keywords related to Jacoco, Cobertura or Javadoc. If there is a dependency for these plugins in ``pom.xml`` file or in ``build.gradle`` file it saves the path under its column e.g. ``Maven Jacoco``: ``pom.xml``. If there is a keyword for these dependencies on the yml file like "``jacoco``" it saved the file path under the corresponding CI tool and the plugin name column e.g. ``GA(GitHub Actions) Jacoco``: ``.github/workflows.main.yml``. It also collects if these yml files are potentially using a platform for uploading code coverage results (since our first aim was to find unnecessary code coverage reports) by looking keywords e.g. ``GA Coveralls``: ``.github/workflows/main.yml``.

We used three different script to find information about the repositories because sometimes we encounter errors and this failed the collection of information. Thus, we needed to run the script again however there is an API request limit on GitHub and running the scripts from the beginning (from the collection of repositories) could cause unnecessary request repetition and wasting the requests.

### Data

Under this folder there are the files created by the data collector. ``filtered_repositories.csv`` file contains the repositories which you wanted to use for job analyzer. Simply copy the row of the repository from the ``file_contents.csv`` file and paste it here.

### Job Analyzer

This script takes the repository information then take the yml file contents and configure it. After configuring, it pushes the changes to the forked repository and automatically triggers GitHub Actions to start the build with configured yml files. In the build files generated are monitored and analyzed and the results pushed to the ``optimizing-ci-builds/ci-analyzes`` repository.

The ``main.py`` script contains four parts and is designed to automate the entire procedure.

### Phases

#### Phase 1: Collection

We fork the repository and add necessary GitHub Environment secrets to the repository (This part done once and not used if there isn't a new repository or change in the added secret). After that we collect the yml file contents.

#### Phase 2: Configuring The Yaml Files

In the second phase, we hard coded configuration of files. It adds some steps to yaml files to set up Inotifywait, runs a python script to analyze the Inotifywait logs and lastly pushes the results to another repository.

#### Phase 3: Pushing the Changes

After configuring the files, we push them to our forked version of the corresponding repositories.

#### Phase 4: Analysis

Analysis part are done under by CI builds, using the python script we added to yml file, and the results are pushed to the ci-analyzes repository.

### Download logs

To download logs related to the push in specofoc branch in [ci-analyzes](https://github.com/UT-SE-Research/ci-analyzes) repo, you should run the following the python file 

`.py` in the root of the project. You should specify the `G_AUTH` and `BRANCH` environment variables as follows

```
G_AUTH_OP=<your_github_token> BRANCH=<ci-analyzes-branch> python download_logs.py
```

This script will download all the logs from all the projects for the run that pushed to the specified branch in the ci-analyzes repository. The logs are found inside `logs/<ci-analyzes-branch>/<project-name>/<workflow-name>.json`
