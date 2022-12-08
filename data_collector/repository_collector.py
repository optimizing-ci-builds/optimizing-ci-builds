import csv
import os
import time
from datetime import datetime
import requests

github_auth_token = os.environ["G_AUTH_TOKEN"]
headers = {
    'Authorization': 'token ' + github_auth_token
}

repositories = []
names = []

# with open("data/repositories_old.csv", "r", newline="", encoding="utf-8") as csv_file:
#     csv_reader = csv.reader(csv_file, delimiter=',')
#     next(csv_reader, None)
#     for row in csv_reader:
#         names.append(row[0])
# print("Repositories taken.")

i = 0
# There are 30 repos in every page, so with 34 iterations we get 1020 java repositories.
while len(repositories) < 1000:
    try:
        url = "https://api.github.com/search/repositories?q=language:java&sort=forks&order=desc&page=" + str(i)
        response = requests.get(url=url, headers=headers).json()
        for repository in response["items"]:
            item = repository["full_name"]
            if item not in names:
                names.append(item)
                dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                repositories.append({"name": repository["full_name"], "link": repository["html_url"],
                                     "default_branch": repository["default_branch"],
                                     "stargazers_count": repository["stargazers_count"],
                                     "forks_count": repository["forks_count"], "date": dt_string})
        print(i)
        i = i + 1
    except:
        time.sleep(5)
        i = int(len(repositories) / 30)
print("Repositories taken, number of repositories: " + str(len(repositories)))
print("")
repositories = sorted(repositories, key=lambda x: x['forks_count'])


i = 0
while i < len(repositories):
    try:
        repository = repositories[i]
        url = "https://api.github.com/repos/" + repository["name"] + "/branches/" + repository["default_branch"]
        response = requests.get(url=url, headers=headers).json()
        repository["SHA"] = response['commit']['sha']
        repositories[i] = repository
        i = i + 1
        print(i)
    except:
        repository = repositories[i]
        repository["SHA"] = "Skipped"
        repositories[i] = repository
        time.sleep(5)

# Save repositories to a csv file
with open("data/repositories.csv", "w", newline="", encoding="utf-8") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Name", "Link", "Default Branch", "SHA", "Stargazers Count", "Forks Count", "Date"])
    for repository in repositories:
        csv_writer.writerow([repository["name"], repository["link"], repository["default_branch"], repository["SHA"],
                             repository["stargazers_count"], repository["forks_count"], repository["date"]])
