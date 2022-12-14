import csv
import os
import time
from datetime import datetime
import requests

github_auth_token = os.environ["G_AUTH_TOKEN"]
headers = {
    'Authorization': 'token ' + github_auth_token
}

# Read the repositories from the csv file.
repositories = []
with open("data/repositories.csv", "r", newline="", encoding="utf-8") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    next(csv_reader, None)
    for row in csv_reader:
        repositories.append({"name": row[0], "link": row[1], "default_branch": row[2], "sha": row[3],
                            "stargazers_count": row[4], "forks_count": row[5], "date": row[6]})
print("Repositories taken.")

i = 0
while i < len(repositories):
    # Making all columns "" as default
    repository = repositories[i]
    repository["Maven"] = ""
    repository["Gradle"] = ""
    repository["Travis CI"] = ""
    repository["Github Actions"] = ""
    try:
        files = requests.get(url="https://api.github.com/repos/" + repository["name"] + "/git/trees/" +
                                 repository["sha"] + "?recursive=1", headers=headers).json()
        for file in files["tree"]:
            # checking if the repository has pom.xml in its root
            if "pom.xml" in file["path"]:
                repository["Maven"] = repository["Maven"] + file["path"]+";"
            # checking if the repository has build-gradle in its root
            if ".gradle" in file["path"]:
                repository["Gradle"] = repository["Gradle"] + file["path"]+";"
            # checking if the repository has .travis.yml in its root
            if ".travis.yml" in file["path"]:
                repository["Travis CI"] = repository["Travis CI"] + file["path"]+";"
            if ".github/workflows" in file["path"] and (".yml" in file["path"] or ".yaml" in file["path"]):
                repository["Github Actions"] = repository["Github Actions"] + file["path"] + ";"
        repositories[i] = repository
        i = i+1
        print(i)
    except:
        repository["Maven"] = "Skipped"
        repository["Gradle"] = "Skipped"
        repository["Travis CI"] = "Skipped"
        repository["Github Actions"] = "Skipped"
        repositories[i] = repository
        time.sleep(3)

# Save data to a csv file
with open("data/file_paths.csv", "w", newline="", encoding="utf-8") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["name", "link", "Default Branch", "SHA", "Stargazers Count", "Forks Count", "Date",
                         "Maven", "Gradle", "Travis CI", "Github Actions"])
    for repository in repositories:
        csv_writer.writerow(
            [repository["name"], repository["link"], repository["default_branch"], repository["sha"],
             repository["stargazers_count"], repository["forks_count"], repository["date"],
             repository["Maven"], repository["Gradle"], repository["Travis CI"],
             repository["Github Actions"]])
print("Done.")
