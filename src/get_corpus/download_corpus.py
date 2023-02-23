import time
from urllib.request import urlopen
from urllib.request import Request
import json
import redis

r = redis.Redis('localhost', 6379, 4)
'''
0:es-list
1:jsx-2000
2:jsx-topic-1000:star>1
3:tsc-4000
4:react
'''


def get_results(search, headers, page, stars):
    url = 'https://api.github.com/search/repositories?q={search}%20stars:<={stars}&page={num}&per_page=100&sort=stars' \
          '&order=desc'.format(search=search, num=page, stars=stars)
    req = Request(url, headers=headers)
    response = urlopen(req).read()
    result = json.loads(response.decode())
    return result


def get_topic(search, headers, page, stars):
    url = 'https://api.github.com/search/repositories?q=topic:{search}%20stars:<={stars}&page={num}&per_page=100&sort=stars' \
          '&order=desc'.format(search=search, num=page, stars=stars)
    req = Request(url, headers=headers)
    response = urlopen(req).read()
    result = json.loads(response.decode())
    return result


def get_repos():
    # Specify JavaScript Repository
    # es6_list = ['es6', 'es7', 'es8', 'es9', 'es10',
    #             'es2015', 'es2016', 'es2017', 'es2018', 'es2019', 'es2020', 'es2021', 'es2022',
    #             'es.next']
    # es_git_dict = {}
    # search = 'es6'
    es6_list = ['react']

    # Modify the GitHub token value
    headers = {'User-Agent': 'Mozilla/5.0',
               'Authorization': 'token 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',
               'Content-Type': 'application/json',
               'Accept': 'application/json'
               }

    # The highest value of JavaScript repository STAR is 116000, repository is freeCodeCamp.
    stars = 216000
    for i in range(0, 4):
        for search in es6_list:
            print(search)
            repos_list = []
            stars_list = []
            for page in range(1, 11):
                results = get_results(search, headers, page, stars)
                for item in results['items']:
                    repos_list.append([item["name"], item["clone_url"]])
                    stars_list.append(item["stargazers_count"])
                print(len(repos_list))
            stars = stars_list[-1]
            print(stars)
            for repos in repos_list:
                r.set(repos[0], repos[1])
        time.sleep(60)


def keep_repos():
    count = 1
    keys = r.keys()
    with open('react.txt', 'a', encoding='utf-8') as f:
        for key in keys:
            if count > 865:
                f.write(str(count) + ',' + key.decode('utf-8') + ',' + r.get(key).decode('utf-8') + '\n')
            count += 1


if __name__ == '__main__':
    get_repos()
    keep_repos()