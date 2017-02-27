import requests
import os, re
import numpy as np
import multiprocessing
from dateutil import parser
from datetime import datetime, timedelta
from prepare_data import g
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import time


dir = os.path.dirname(os.path.realpath(__file__))

class counter():
    def __init__(self):
        self.counter = 0
    def inc(self):
        self.counter += 1


class scraper():
    def __init__(self):
        self.count = 0
        self.driver = webdriver.PhantomJS(executable_path=os.path.join(dir, "phantomjs"))
        self.base = 'https://github.com'
        self.waitlimit = 16

    def print_info(self, state='begins'):
        print str(self.count) + ' \t' + state

    def start_multi(self, func, tasks):
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        pool.map(func, tasks)
        pool.close()
        pool.join()

    def scrape_cores(self, owner, repo, waittime=4):
        cores = {}
        url = self.base + '/' + owner + '/' + repo + '/graphs/contributors'
        self.driver.get(url)
        self.print_info('begins')
        time.sleep(waittime)
        self.print_info('ends')
        self.count += 1
        soup = bs(self.driver.page_source, 'lxml')

        contributors = soup.find_all('li', class_='capped-card')
        if not contributors:
            if waittime + 4 <= self.waitlimit:
                print 'increase wait time from ' + str(waittime) + ' to ' + str(waittime + 4)
                return self.scrape_cores(owner, repo, waittime= waittime+4)
            else:
                print str(self.count) + ': no core get scraped for: ' + owner + '/' + repo
                return cores
        for c in contributors:
            core = c.select("h3 > a")[0].get_text()
            commit = c.select("h3 > span.ameta > span > a")[0].get_text()
            commit = int(''.join(re.findall(r'\d+', commit)))
            if commit > 50:
                cores[core] = commit
            else:
                top_core = contributors[0].select("h3 > a")[0].get_text()
                top_commit = contributors[0].select("h3 > span.ameta > span > a")[0].get_text()
                top_commit = int(''.join(re.findall(r'\d+', top_commit)))
                if commit >= top_commit/3:
                    cores[core] = commit
        return cores

    def scrape_changed_files4pr(self, owner, repo, pr_id):
        cores = {}
        url = self.base + '/' + owner + '/' + repo + '/pull/' + pr_id + '/files'
        response = requests.get(url)
        soup = bs(response.content, 'lxml')
        # files = soup.find_all('span', class_='user-select-contain')
        # test = soup.findAll('div', id=lambda x: x and x.startswith('diff-'))
        list = soup.select("#files_bucket > div.pr-toolbar.js-sticky.js-sticky-offset-scroll > div > div.diffbar-item.toc-select.select-menu.js-menu-container.js-select-menu > div.select-menu-modal-holder > div > div.select-menu-list.js-navigation-container > div > a")
        file_state = {}
        for f in list:
            file_path = f.select('span.description')[0].contents[0].strip()
            # if not file_path.startwith('...'):
            change_mode = f.select('svg')[0]['title']
            file_state[change_mode] = file_state.get(change_mode, [])
            file_state[change_mode].append(file_path)
        return file_state


    def scrape_pr_page(self, owner, repo, pr_id):
        """
        It's very wired that I can scrape all the `members` but not the other tags! WTF!!!!
        """
        cores = {}
        url = self.base + '/' + owner + '/' + repo + '/pull/' + pr_id
        response = requests.get(url)
        soup = bs(response.content, 'lxml')
        # self.driver.get(url)
        # self.print_info('begins')
        # time.sleep(5)
        # self.print_info('ends')
        # self.count += 1
        # soup = bs(self.driver.page_source, 'lxml')
        status = soup.select('.timeline-comment-header')[0].select('span')
        status = status[0].contents[0].strip().split()[-1] if status else 'newbie'
        labels = soup.select('a.label')
        labels = len(labels)
        participants = soup.select('.participant-avatar')
        participants = len(participants)
        print 'labels: \t' + str(labels) + '\tp_num: \t' + str(participants) + '\tstatus: \t' + status
        return status, labels, participants


def robust_request(url, auth=None):
    try:
        response = requests.get(url, auth=auth)
        if int(response.headers._store['x-ratelimit-remaining'][1]) % 25 == 0:
            print 'remaining requests: \t' + response.headers._store['x-ratelimit-remaining'][1] + '/' +response.headers._store['x-ratelimit-limit'][1]
        if int(response.headers._store['x-ratelimit-remaining'][1]) < 2:
            if g.auth_index + 1 < len(g.auth_id):
                g.auth_index += 1
            else:
                print 'requests exceed limit!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    except requests.exceptions.ConnectionError:
        print "EEEEEEEEEEEEEE------------- Requst Connection Error"
        return None
    except requests.exceptions.ConnectionError:
        print "Connection refused"
        return None
    except:
        print 'other error for request'
        return None
    return response


def search_commit_histories(owner, repo, end_date, trace_back_month=3):
    start = end_date - timedelta(days= trace_back_month*30)
    since = '-'.join([str(start.year), str(start.month), str(start.day)])
    until = '-'.join([str(end_date.year), str(end_date.month), str(end_date.day)])
    search_url = 'https://api.github.com/repos/' + owner + '/' + repo + '/commits?per_page=1000&since=' + since + '&until=' + until
    actives = {}
    while search_url:
        response = robust_request(search_url, auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
        if not response or response.status_code != 200:
            return None
        data = response.json()
        for d in data:
            committer = d.get('committer')
            if committer:
                committer = committer.get('login')
            if not committer:
                # print str(counter.counter) + '?'
                counter.inc()
                c_name = d['commit']['committer']['name']
                actives[committer] = actives.get(c_name, 0) + 1
            else:
                actives[committer] = actives.get(committer, 0) + 1
        next = response.links.get('next')
        search_url = next['url'] if next else None
    return actives


def search_previous_pr(owner, repo, author, pr_date):
    before = '-'.join([str(pr_date.year), str(pr_date.month), str(pr_date.day)])
    # if use search api
    # search_url = 'https://api.github.com/search/issues?q=user:' + owner + '+repo:' + repo + '+author:' + author + '+is:pr+is:closed+created:<' + before
    # if directly use issues api
    search_url = 'https://api.github.com/repos/' + owner + '/' + repo + '/issues?q=is:pr&creator=' + author + '&state=closed&sort=created&per_page=1000'
    prs = {}
    while search_url:
        response = robust_request(search_url, auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
        if not response or response.status_code != 200:
            return None
        data = response.json()
        for d in data:
            if not d.get('pull_request'):
                continue
            tmp_date = parser.parse(d['created_at'])
            if tmp_date > pr_date:
                continue
            pr_url = d['pull_request']['url']
            tmp_response = robust_request(pr_url, auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
            if not tmp_response or tmp_response.status_code != 200:
                return None
            tmp_data = tmp_response.json()
            pr_state = tmp_data['merged']
            prs[pr_url] = pr_state
        next = response.links.get('next')
        search_url = next['url'] if next else None
    return prs


def get_repo_code_size(owner, repo):
    response = robust_request('https://api.github.com/repos/' + owner + '/' + repo + '/languages', auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None
    data = response.json()
    size = 0
    for s in data.itervalues():
        size += s/1024.0
    return int(size)


def get_commits4core(active_committers, cores):
    core_commits, non_core_commits = 0, 0
    for c, n in active_committers.iteritems():
        if c in cores:
            core_commits += n
        else:
            non_core_commits += n
    return core_commits, non_core_commits


def get_commits_on_files_touched(owner, repo, files, end_date='', trace_back_month=3):
    if not files:
        return
    file_history_commits = {}
    start = end_date - timedelta(days= trace_back_month*30)
    for file in files:
        count = 0
        response = robust_request('https://api.github.com/repos/' + owner + '/' + repo + '/commits?path=' + file, auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
        if not response or response.status_code != 200:
            return None
        commits = response.json()
        for c in commits:
            author = c['commit']['author']
            commit_date = parser.parse(author['date'])
            if commit_date > start and commit_date < end_date:
                count += 1
        file_history_commits[file] = count
    return file_history_commits


def get_pr_repo_info(owner, repo, pr_id, get_all_features=True, minimal=False):
    response = robust_request('https://api.github.com/repos/' + owner + '/' + repo + '/pulls/' + str(pr_id), auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None

    data = response.json()
    details = {}
    try:
        details['repo_stars'] = data["base"]["repo"]["stargazers_count"]
        details['repo_forks'] = data["base"]["repo"]["forks"]
        details['repo_watchers'] = data["base"]["repo"]["watchers"]
        details['repo_size'] = data["base"]["repo"]["size"]
        details['repo_issues_count'] = data["base"]["repo"]["open_issues_count"]
        details['repo_code_size'] = get_repo_code_size(owner, repo)

        details['pr_submitter'] = data["user"]['login']
        details['pr_commits'] = data['commits']
        details['pr_comments'] = data['comments']
        details['pr_assignees'] = data['assignee']
        details['pr_assignee_num'] = len(data['assignees'])
        details['pr_additions'] = data['additions']
        details['pr_deletions'] = data['deletions']
        details['pr_changed_files'] = data['changed_files']
        details['pr_has_milestone'] = 1 if data['milestone'] else 0
        details['pr_created_time'] = parser.parse(data['created_at'])
        details['pr_closed_time'] = parser.parse(data['closed_at'])
        details['pr_close_duration'] = (details['pr_closed_time'] - details['pr_created_time']).days
        details['pr_mergeable'] = data['mergeable']
        details['pr_mergeable_state'] = data['mergeable_state']
        details['pr_merged'] = data['merged']
        if details['pr_merged']:
            details['pr_merged_by'] = data['merged_by']['login']
            details['pr_merged_time'] = parser.parse(data['merged_at'])
            details['pr_merge_duration'] = (details['pr_merged_time'] - details['pr_created_time']).days


        if not minimal:
            closer = get_pr_closer(owner, repo, pr_id)
            details['pr_closer'] = closer


            comment_url = data['comments_url']
            comment_info = get_comment_info(comment_url)
            if not comment_info:
                print 'Not Found -- Comment: ' + comment_url
                g.comment_miss_num += 1
            else:
                details['c_participants'] = list(comment_info['participants'])
                details['c_response_times'] = comment_info['response_times']
                details['c_mentions'] = comment_info['mentions']
                details['c_response_average'] = comment_info['response_average']
                details['c_first_reponse'] = comment_info['first_response']

        if get_all_features:
            pr_date = parser.parse(data['created_at'])
            cores = s.scrape_cores(owner, repo)
            if not cores:
                print '!!!!!!!!!failure: ' + owner + '/' + repo + '/pulls/' + str(pr_id)
                return
            active_committers = search_commit_histories(owner, repo, end_date=pr_date, trace_back_month=3)
            core_commits, non_core_commits = get_commits4core(active_committers, cores)
            details['core_commits'] = core_commits
            details['non_core_commits'] = non_core_commits
            details['active_cores'] = set(active_committers.keys()).intersection(cores)
            details['repo_cores'] = cores
            details['repo_actives'] = active_committers

            commits_info = get_commits_info(owner, repo, pr_id, details['pr_created_time'], details['pr_closed_time'])
            details['CI_states'] = commits_info['CI_states']
            details['CI_dates'] = commits_info['CI_dates']
            details['CI_result'] = commits_info['CI_result']
            details['CI_latency'] = (commits_info['CI_latency'] - details['pr_created_time']).seconds / 60 if commits_info['CI_latency'] else None

            files_changed = s.scrape_changed_files4pr(owner, repo, pr_id)
            traceable_files = files_changed.get('modified', []) + files_changed.get('removed', [])
            traceable_files = [f for f in traceable_files if not f.startswith('...')]
            pr_touched_file_history = get_commits_on_files_touched(owner, repo, traceable_files, end_date=pr_date, trace_back_month=3)
            commits_on_files_touched = sum(pr_touched_file_history.values()) if pr_touched_file_history else 0
            details['commits_on_files_touched'] = commits_on_files_touched

            submitter_pr_history = search_previous_pr(owner, repo, details['pr_submitter'], pr_date)
            details['prev_pr_num'] = len(submitter_pr_history)
            sucsessful_pr_num = len([pr_merged for pr_merged in submitter_pr_history.values() if pr_merged is True])
            details['requester_succ_rate'] = round(float(sucsessful_pr_num)/details['prev_pr_num'] if details['prev_pr_num'] else 0, 2)


    except AttributeError:
        print 'exception'
        return None
    return details


def get_commit_CI_info(owner, repo, sha, pr_create_time, pr_close_time):
    response = robust_request('https://api.github.com/repos/' + owner + '/' + repo + '/commits/' + sha + '/statuses', auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None
    data = response.json()
    for d in data:
        time = parser.parse(d['created_at'])
        if time < pr_close_time:
            return d['state'], time
    return 'pending', None


def get_commits_info(owner, repo, pr_id, pr_create_time, pr_close_time):
    response = robust_request('https://api.github.com/repos/' + owner + '/' + repo + '/pulls/' + pr_id + '/commits', auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None
    data = response.json()
    shas, CI_states , CI_dates = [], [], []
    commits_info = {}
    for d in data:
        shas.append(d['sha'])
        state, CI_time = get_commit_CI_info(owner, repo, d['sha'], pr_create_time, pr_close_time)
        CI_states.append(state)
        CI_dates.append(CI_time)
    commits_info['CI_result'] = 0
    if 'failure' in CI_states:
        commits_info['CI_result'] = 1
    commits_info['CI_latency'] = None
    if 'pending' not in CI_states:
        commits_info['CI_latency'] = max(CI_dates)
    commits_info['CI_states'] = CI_states
    commits_info['CI_dates'] = CI_dates
    return commits_info


def get_pr_closer(owner, repo, pr_id):
    # by finding the issue closer. each pr id is also an issue id.
    response = robust_request('https://api.github.com/repos/' + owner + '/' + repo + '/issues/' + str(pr_id), auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None
    data = response.json()
    if data.get('closed_by') and data['closed_by'].get('login'):
        return data['closed_by']['login']
    print '/'.join([owner, repo, str(pr_id)]) + 'no closer'
    return ''


# get repo info, filter repo that stars < 100
def get_repo_info(owner, repo):
    response = robust_request('https://api.github.com/repos/' + owner + repo, auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None, None
    repo_info = response.json()
    stars = repo_info['stargazers_count']
    forks = repo_info['forks_count']
    return int(stars), int(forks)


def get_org_info(org_id):
    response = robust_request('https://api.github.com/orgs/' + org_id, auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None, None
    data = response.json()
    org_info = {}
    org_info['followers'] = data['followers']
    org_info['created_at'] = parser.parse(data['created_at'])
    org_info['public_repos'] = data['public_repos']
    return org_info


def get_all_followings(user_id):
    response = robust_request('https://api.github.com/users/' + user_id + '/following', auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None
    data = response.json()
    followings = []
    if data:
        for d in data:
            followings.append(d['login'])
    return followings



def get_user_info(user_id):
    # response = robust_request('https://api.github.com/users/' + user_id + '/starred?per_page=1', auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    # try:
    #     stars = response.links['last']['url'].split('&page=')[1]
    # except KeyError:
    #     print 'Not Found - no user info: ' + user_id
    #     return None

    response = robust_request('https://api.github.com/users/' + user_id, auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None
    user_info = {}
    data = response.json()
    followers = data['followers']
    ## not useful to record the star for a person. Can't delete due to consistency issues for previous code.
    user_info['stars'] = None
    user_info['followers'] = int(followers)
    user_info['followings'] = get_all_followings(user_id)
    user_info['created_at'] = parser.parse(data['created_at'])
    return user_info


def get_cores(repo_owener, repo_name):
    response = robust_request('https://api.github.com/repos/' + repo_owener + '/' + repo_name + '/contributors', auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None
    contributers = response.json()
    cores = []
    if len(contributers) < 4:
        print 'Error: un-qualified data'
        return None
    for i, c in enumerate(contributers[0:3]):
        con_num = c['contributions']
        if con_num > 99 or i<2:
            cores.append(c['login'])
    if len(cores) < 3:
        print 'Warning: less than 3 cores: ' + repo_owener + '/' + repo_name
    return cores


def get_comment_info(url):
    response = robust_request(url, auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
    if not response or response.status_code != 200:
        return None
    comments = response.json()
    participants = set()
    dates = []
    mentions = {}
    for comment in comments:
        user = comment['user']['login']
        participants.add(user)
        date = parser.parse(comment['created_at'])
        dates.append(date)
        mention_msg = re.findall('@\w+[,.!?:]*\s', comment['body'])
        if mention_msg:
            if mentions.get(user):
                mentions[user].extend(mention_msg)
            else:
                mentions.update({user: mention_msg})
    result_dict = {}
    result_dict['participants'] = participants
    result_dict['dates'] = dates
    # previous measures are day, now changed to minutes
    result_dict['response_times'] = [(d - dates[0]).seconds/60 for d in dates]
    result_dict['first_response'] = (dates[1] - dates[0]).seconds/60
    result_dict['mentions'] = mentions
    result_dict['response_average'] = np.mean(result_dict['response_times'])
    return result_dict

counter = counter()
s = scraper()
# url = ['https://github.com/SpongePowered/SpongeAPI/pull/1012', 'https://github.com/appc/cni/pull/94', 'https://github.com/scummvm/scummvm/pull/645', 'https://github.com/libuv/libuv/pull/672', 'https://github.com/dronekit/dronekit-python/pull/509', 'https://github.com/strongloop/loopback-connector-remote/pull/30', 'https://github.com/naver/arcus-java-client/pull/41', 'https://github.com/facebook/buck/pull/611', 'https://github.com/openshift/origin/pull/6541', 'https://github.com/Homebrew/homebrew/pull/47792']
# for u in url:
#     url_parts = u.split('/')[-4:]
#     owner, repo, pr_id = url_parts[0], url_parts[1], url_parts[-1]
#     s.scrape_pr_page(owner, repo, pr_id)


# tmp_response = robust_request('https://api.github.com/repos/guard/guard/pulls/785', auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
# tmp_data = tmp_response.json()
# a = search_previous_pr('guard', 'guard', 'e2', parser.parse(tmp_data['created_at']))
# get_pr_repo_info('openscad', 'openscad', '421')
# s.scrape_changed_files4pr('openscad', 'openscad', '421')
# s = scraper()
# a = s.scrape_cores('Homebrew', 'legacy-homebrew')
# print a
