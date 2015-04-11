import requests
from requests.auth import HTTPBasicAuth
from jinja2 import Template
import yaml

yaml_file = open('config.yaml')
credentials = yaml.load(yaml_file)['credentials']

auth = HTTPBasicAuth(credentials['user'], credentials['password'])

REPO_STATS_URL_FORMAT = "https://api.github.com/repos/{owner}/{repo}/stats/contributors"
WATCHING_URL_FORMAT = "https://api.github.com/users/{user}/subscriptions"

def get_repos_info():
    repos = [get_repo_info(owner, repo) for owner, repo in get_repos()]
    return sorted(repos, key=lambda r: -r['total_commits'])

def get_repos():
    url = WATCHING_URL_FORMAT.format(user=credentials['user'])
    data = requests.get(url, auth=auth, params={'per_page': '100'}).json()
    return [r['full_name'].split("/") for r in data]

def get_repo_info(owner, repo):
    authors = get_authors_info(owner, repo)
    return {
        'owner': owner,
        'repo': repo,
        'authors': authors,
        'url': 'https://github.com/{owner}/{repo}'.format(owner=owner, repo=repo),
        'total_commits': sum(a['commits'] for a in authors)}

def get_authors_info(owner, repo):
    url = REPO_STATS_URL_FORMAT.format(owner=owner, repo=repo)
    print url
    authors_request = requests.get(url, auth=auth)
    if authors_request.status_code == 204:
        return []
    authors = authors_request.json()
    author_infos = [author_info(author) for author in authors if author['author']]
    return sorted(author_infos, key= lambda a: -a['commits'])

def author_info(author):
    name = author['author']['login']
    avatar = author['author']['avatar_url']
    commits = sum([w['c'] for w in author['weeks']])
    return {"avatar": avatar, "name": name, "commits": commits}


def render(repos):
    template_content = open('template.html').read().decode('utf-8')
    template = Template(template_content)
    return template.render(repos=repos)

if __name__ == '__main__':
    repos = get_repos_info()
    with open("index.html", "w") as f:
        f.write(render(repos).encode('utf-8'))

