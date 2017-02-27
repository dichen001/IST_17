import os
from get_info import *
from bs4 import BeautifulSoup as bs
import urllib
import multiprocessing
from selenium import webdriver
import time

dir = os.path.dirname(os.path.realpath(__file__))

def normalize_merge_state(m_state):
    if m_state == 'dirty':
        return -1
    elif m_state == 'unknown':
        return 0
    elif m_state == 'unstable':
        return 1
    elif m_state == 'clean':
        return 2
    else:
        return None


def get_all_important_features(pr_url):
    important_features = {}
    url_parts = pr_url.split('/')[-4:]
    owner, repo, pr_id = url_parts[0], url_parts[1], url_parts[-1]
    pr_repo_info = get_pr_repo_info(owner, repo, pr_id)
    if not pr_repo_info:
        return {}
    owner_info = get_user_info(owner)
    submitter_info = get_user_info(pr_repo_info['pr_submitter'])
    if not owner_info:
        """ need more consideration here """
        owner_info = get_org_info(owner)
        important_features['is_org'] = 1
    else:
        important_features['is_org'] = 0
    important_features['num_commits'] = pr_repo_info['pr_commits']
    important_features['src_churn'] = pr_repo_info['pr_additions'] + pr_repo_info['pr_deletions']
    important_features['num_comments'] = pr_repo_info['pr_comments']
    # whether the submitter follows the closer
    important_features['social_distance'] = 1 if pr_repo_info['pr_closer'] in submitter_info['followings'] else 0
    # first response for the pull request in minutes
    important_features['first_response'] = pr_repo_info['c_first_reponse']
    #  Time interval in minutes from pull request creation to the last commit tested by CI.
    important_features['CI_latency'] = pr_repo_info['CI_latency']
    # Binary variables to encode the presence of errors
    important_features['CI_result'] = pr_repo_info['CI_result']
    # number of excutable lines at creation time
    important_features['sloc'] = pr_repo_info['repo_code_size']
    # active core members in the last 3 months
    important_features['team_size'] = len(pr_repo_info['active_cores'])
    # The ratio of commits from external members over core team members in the last 3 months prior to creation.
    important_features['perc_external_contribs'] = round(pr_repo_info['non_core_commits']/float(pr_repo_info['core_commits']), 2) if pr_repo_info['core_commits'] else 0
    important_features['commits_on_files_touched'] = pr_repo_info['commits_on_files_touched']
    ###  (T_T)    (T_T)    (T_T)    (T_T)    (T_T)
    # important_features['test_lines_per_kloc'] = 0
    ###  (T_T)    (T_T)    (T_T)    (T_T)    (T_T)
    important_features['watchers'] = pr_repo_info['repo_stars']
    important_features['project_maturity'] = pr_repo_info['repo_forks']
    important_features['prev_pullreqs'] = pr_repo_info['prev_pr_num']
    important_features['requester_succ_rate'] = pr_repo_info['requester_succ_rate']
    important_features['collaborator_status'] = pr_repo_info['pr_submitter'] in pr_repo_info['repo_cores']
    important_features['experience'] = (pr_repo_info['pr_created_time'] - submitter_info['created_at']).days

    # # my finding for important features
    # important_features['mergeable'] = pr_repo_info['pr_mergeable']
    # important_features['mergeable_state'] = pr_repo_info['pr_mergeable_state']
    return important_features


def test_b():
    url = 'https://github.com/duckduckgo/zeroclickinfo-goodies/pull/2024/commits'
    base = 'https://github.com'
    r = urllib.urlopen(url).read()
    soup = bs(r, "lxml")
    commits = soup.select("div.commit-links-cell.table-list-cell")
    first_commit = commits[0].find_all('a')
    repo_at_that_time = base + first_commit[1]['href']
    print soup.prettify()[0:100]


def test_b_core(owner, repo):
    cores = {}
    base = 'https://github.com'
    url = base + '/' + owner + '/' + repo + '/graphs/contributors'
    driver = webdriver.PhantomJS(executable_path=os.path.join(dir, "phantomjs"))
    driver.get(url)
    time.sleep(3)
    soup = bs(driver.page_source, 'lxml')
    driver.close()

    contributors = soup.find_all('li', class_='capped-card')
    if not contributors:
        print 'no core get scraped for: ' + owner + '/' + repo
        return cores
    for c in contributors:
        core = c.select("h3 > a")[0].get_text()
        commit = c.select("h3 > span.ameta > span > a")[0].get_text()
        commit = int(commit.split(' ')[0].replace(',', ''))
        if commit > 50:
            cores[core] = commit
    return cores

if __name__ == '__main__':
    # test_b_core('Homebrew', 'legacy-homebrew')
    get_all_important_features('https://api.github.com/repos/duckduckgo/zeroclickinfo-goodies/pull/2024')


