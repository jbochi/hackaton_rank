import os
import time
import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from jinja2 import Template

username = os.environ.get("GITHUB_USERNAME", "hackinpoawatcher")
password = os.environ.get("GITHUB_PASSWORD", "PASSWORD")
auth = HTTPBasicAuth(username, password)

REPO_STATS_URL_FORMAT = "https://api.github.com/repos/{owner}/{repo}/stats/contributors"
WATCHING_URL_FORMAT = "https://api.github.com/users/{user}/subscriptions"
REPO_URL_FORMAT = "https://github.com/{owner}/{repo}"
LANG_URL_FORMAT = "https://api.github.com/repos/{owner}/{repo}/languages"


def get_repos_info():
    repos = [get_repo_info(owner, repo) for owner, repo in get_repos()]
    return sorted(repos, key=lambda r: -r['total_commits'])


def get_repos():
    url = WATCHING_URL_FORMAT.format(user=username)
    data = requests.get(url, auth=auth, params={'per_page': '100'}).json()
    return [r['full_name'].split("/") for r in data]


def get_repo_info(owner, repo):
    authors = get_authors_info(owner, repo)
    languages = get_lang_info(owner, repo)
    data = {
        'owner': owner,
        'languages': languages,
        'repo': repo,
        'authors': authors,
        'url': 'https://github.com/{owner}/{repo}'.format(owner=owner, repo=repo),
    }
    data.update(get_page_data(owner, repo))
    return data


def get_page_data(owner, repo):
    url = REPO_URL_FORMAT.format(owner=owner, repo=repo)
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content)
    return {
        'total_commits': get_total_commits(soup),
        'last_commit': get_last_commit(soup)
    }

def get_total_commits(soup):
    result = soup.select(".commits .num")
    if not result:
        return 0
    return int(result[0].text.strip())


def get_last_commit(soup):
    result = soup.select(".commit-title")
    if not result:
        return ""
    text = result[0].text.strip()
    if text.startswith('Fetching latest commit'):
        return ""
    return text


def get_lang_info(owner, repo):
    url = LANG_URL_FORMAT.format(owner=owner, repo=repo)
    print url
    languages_request = requests.get(url, auth=auth)
    if languages_request.status_code == 204:
        return []
    print languages_request.json()
    return languages_request.json()


def get_authors_info(owner, repo):
    url = REPO_STATS_URL_FORMAT.format(owner=owner, repo=repo)
    print url
    for tries in range(5):
        authors_request = requests.get(url, auth=auth)
        if authors_request.status_code == 200:
            break
        print 'Request failed. Sleeping...'
        time.sleep(5)
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
