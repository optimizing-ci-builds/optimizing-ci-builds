import json
import requests
import sys
import time


# API endpoints
GITHUB_API = 'https://api.github.com'
TRAVIS_API = 'https://api.travis-ci.org'


# Get GitHub username and password, Travis access token from file
def load_user_from_file(file):
    with open(file) as f:
        lines = [line.strip() for line in f]
    users = []
    tokens = []
    passwords = []
    for l in lines:
        s = l.split(' ')
        users.append(s[0])
        tokens.append(s[1])
        passwords.append(s[2])
    return users, tokens, passwords


# Get a Travis access token given a GitHub access token
def get_token(github_token):
    data = {'github_token': github_token}
    headers = {'User-Agent': 'Travis/1.0'}
    response = requests.post(TRAVIS_API + '/auth/github', data=data, headers=headers).text
    access_token = json.loads(response)['access_token']
    print(access_token)


# Remove all repos of user
def remove_all_repos(username, password):
    for repo in json.loads(requests.get(GITHUB_API + '/users/' + username + '/repos', auth=(username, password)).text):
        requests.delete(GITHUB_API + '/repos/' + username + '/' + repo['name'], auth=(username, password))


# Fork project on GitHub
def fork_project(slug, username, password):
    requests.delete(GITHUB_API + '/repos/' + slug, auth=(username, password))
    time.sleep(1)
    requests.post(GITHUB_API + '/repos/' + slug + '/forks', auth=(username, password))


# Force Travis CI to sync repo info from GitHub
def sync_github_travis(token):
    requests.post(TRAVIS_API + '/users/sync?access_token=' + token)
    while json.loads(requests.get(TRAVIS_API + '/users?access_token=' + token).text)['is_syncing']:
        print('Syncing')
        time.sleep(5)


# Enable Travis CI
def setup_travis(slug, travis_token, cache):
    token = '?access_token=' + travis_token
    while True:
        try:
            # Enable repo
            repo_id = json.loads(requests.get(TRAVIS_API + '/repos/' + slug).text)['id']
            requests.put(TRAVIS_API + '/hooks/' + token, json={'hook': {'id': repo_id, 'active': True}})
            # Turn off auto cancel and limit number of concurrent jobs
            settings = {'auto_cancel_pushes': False, 'maximum_number_of_builds': 1 if cache else 0, 'auto_cancel_pull_requests': False}
            requests.patch(TRAVIS_API + '/repos/' + str(repo_id) + '/settings' + token, json={'settings': settings})
            print(slug)
        except Exception:
            time.sleep(5)
            continue
        break


# Cancel all current builds
def cancel_builds(slug, travis_token):
    token = '?access_token=' + travis_token
    result = json.loads(requests.get(TRAVIS_API + '/repos/' + slug + '/builds').text)
    for r in result:
        if r['state'] != 'finished':
            a = requests.post(TRAVIS_API + '/builds/' + str(r['id']) + '/cancel' + token)
            print(slug + ' ' + a.text)


def main(args):
    file = args[1]
    with open(file) as f:
        projects = [line.strip() for line in f]
    users, tokens, passwords = load_user_from_file(args[2])
    for i in range(len(users)):
        user = users[i]
        token = tokens[i]
        password = passwords[i]
        # for slug in projects:
            # forked_slug = user + '/' + slug.split('/')[1]
            # cancel_builds(forked_slug, token)  # cancel all builds
        # remove_all_repos(user, password)  # remove all repos
        for slug in projects:  # fork projects
            fork_project(slug, user, password)
        sync_github_travis(token)  # sync Travis after all projects are forked
        for slug in projects:  # Enable Travis and change repo settings
            forked_slug = user + '/' + slug.split('/')[1]
            setup_travis(forked_slug, token, i > 1)


if __name__ == '__main__':
    main(sys.argv)
    # main(['', '', '../projects/apache_projects_filtered.txt', '../ACCOUNTS'])