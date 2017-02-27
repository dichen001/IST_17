import os
import gc
import csv
import time
import pickle

from dateutil import parser
from prepare_data import data_dir, g



auth_id = 'dichen001Test01'
auth_token = 'baa47b85673e038fd817acb54974b598b82ff560'
pickle_folder = 'suplement_pickle'
# auth_id = 'dichen001'
# auth_token = '597318e91d03aed54fc94da21b30c20bc62c0fb8'
csv_output = os.path.join(data_dir, 'output.csv')


from get_info import get_user_info, get_cores, get_comment_info


def load_pickle(file_path):
    with open(file_path, 'r') as f:
        data = pickle.load(f)
    return data


def dump_pickle(data, file_path):
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)

def data_selection(list):
    list_after_selection = []
    print 'length before selection: ' + str(len(list))
    for item in list:
        # Excluded forks
        if not item['public'] or item['repository']['fork'] or item['repository']['master_branch']!='master':
            continue
        # active and estblished repos
        if item['repository']['stargazers']<100:
            continue
        # closed pull requests:
        if item['payload']['pull_request']['state'] != 'closed':
            continue
        # highly discussed
        if item['payload']['pull_request']['comments'] < 9:
            continue
        list_after_selection.append(item)
    print 'length after selection: ' + str(len(list_after_selection))
    return list_after_selection

def get_qualified_data(type):
    # list = []
    selected = []
    comments_num = []
    i = 1
    total_len = 0
    while i+3 <= 10:
        start = time.time()
        file_name = 'list_for_all_data_' + type + '_' + '-'.join([str(c).zfill(2) for c in range(i, i+4)]) + '.pickle'
        print 'loading ' + file_name + '...'
        file_path = os.path.join(data_dir, pickle_folder, file_name)
        tmp_list = load_pickle(file_path)
        print '------- time spent for loading: ' + str(round(time.time()-start,3)) + 's  -------'
        tmp_selected = data_selection(tmp_list)
        tmp_num = [item['payload']['pull_request']['comments'] for item in tmp_list]
        # print 'list length: ' + str(len(tmp_list))
        # total_len += len(tmp_list)

        # tmp_list = get_most_discussed(tmp_list)
        # print 'after filtering, length is: ' + str(len(tmp_list))
        print 'extending list'
        # list.extend(tmp_list)
        selected.extend(tmp_selected)
        comments_num.extend(tmp_num)
        print 'deleting tmp '
        del tmp_selected
        del tmp_list
        del tmp_num
        print 'release memory'
        gc.collect()
        i += 3
        print '------- time spent: ' + str(round(time.time()-start,3)) + 's  -------'
    comments_save_path = os.path.join(data_dir, pickle_folder, 'comments_num_distribution_' + type + '.pickle')
    dump_pickle(comments_num, comments_save_path)
    pr_save_path = os.path.join(data_dir, pickle_folder, 'selected_pull_requests_' + type + '.pickle')
    dump_pickle(selected, pr_save_path)
    print 'all ' + type + ' data loaded'
    print 'total length: ' + str(total_len)


def get_most_discussed(list):
    for data in list:
        if data['payload']['pull_request']['comments'] < 8:
            list.remove(data)
    return list


def get_necessary_details():
    merged_fp = os.path.join(data_dir, pickle_folder, 'selected_pull_requests_' + 'merged' + '.pickle')
    merged = load_pickle(merged_fp)
    rejected_fp = os.path.join(data_dir, pickle_folder, 'selected_pull_requests_' + 'rejected' + '.pickle')
    rejected = load_pickle(rejected_fp)
    all = merged
    all.extend(rejected)
    # all = rejected
    # fields = ['repo_owner', 'repo_name', 'repo_stars', 'repo_forks', 'repo_watchers', 'repo_cores',\
    #           's_id', 's_stars', 's_followers',\
    #           'pr_id', 'pr_html', 'pr_commits', 'pr_comments', 'pr_assignees', 'pr_changed_files', 'pr_additions', 'pr_deletions', 'pr_has_milestone',\
    #           'pr_mergeable', 'pr_mergeable_state', 'pr_merged', 'pr_merged_by', 'pr_merge_duration', 'pr_close_duration', 'pr_created_time', 'pr_merged_time', 'pr_closed_time',\
    #           'c_participants', 'c_mentions', 'c_response_times', 'c_response_average'
    #           ]
    with open(csv_output, 'wb') as csvOut:
        writer = csv.DictWriter(csvOut, fieldnames= g.fields)
        writer.writeheader()
        for index, item in enumerate(all):
            print 'processing ' + str(index) + '/' + str(len(all))
            details = {}
            ## submiter's info
            details['s_id'] = item['actor']
            user_info = get_user_info(details['s_id'])
            details['s_stars'], details['s_followers'] = user_info['stars'], user_info['followers']
            if not details['s_stars'] or not details['s_followers']:
                print 'Not Found -- Submitter: ' + details['s_id']
                continue

            # repo info
            details['repo_owner'] = item['repository']['owner']
            details['repo_name'] = item['repository']['name']
            details['repo_stars'] = item['repository']['stargazers']
            details['repo_forks'] = item['repository']['forks']
            details['repo_watchers'] = item['repository']['watchers']
            details['repo_cores'] = get_cores(details['repo_owner'], details['repo_name'])
            if not details['repo_cores']:
                print 'Not Found -- Repo: ' + details['repo_owner'] + '/' + details['repo_name']
                continue

            # pull request info
            details['pr_id'] = item['payload']['number']
            details['pr_html'] = item['payload']['pull_request']['_links']['html']['href']
            details['pr_commits'] = item['payload']['pull_request']['commits']
            details['pr_comments'] = item['payload']['pull_request']['comments']
            details['pr_assignees'] = item['payload']['pull_request']['assignee']
            details['pr_additions'] = item['payload']['pull_request']['additions']
            details['pr_deletions'] = item['payload']['pull_request']['deletions']
            details['pr_changed_files'] = item['payload']['pull_request']['changed_files']
            details['pr_has_milestone'] = item['payload']['pull_request']['milestone']
            details['pr_created_time'] = parser.parse(item['payload']['pull_request']['created_at'])
            details['pr_closed_time'] = parser.parse(item['payload']['pull_request']['closed_at'])
            details['pr_close_duration'] = (details['pr_closed_time'] - details['pr_created_time']).days
            details['pr_mergeable'] = item['payload']['pull_request']['mergeable']
            details['pr_mergeable_state'] = item['payload']['pull_request']['mergeable_state']
            details['pr_merged'] = item['payload']['pull_request']['merged']
            if details['pr_merged']:
                details['pr_merged_by'] = item['payload']['pull_request']['merged_by']['login']
                details['pr_merged_time'] = parser.parse(item['payload']['pull_request']['merged_at'])
                details['pr_merge_duration'] = (details['pr_merged_time'] - details['pr_created_time']).days




            ## comments info: participants? mention msg? response time?
            comment_url = item['payload']['pull_request']['_links']['comments']['href']
            result = get_comment_info(comment_url)
            if not result:
                print 'Not Found -- Comment: ' + comment_url
                continue
            details['c_participants'] = list(result['participants'])
            details['c_response_times'] = result['response_times']
            details['c_mentions'] = result['mentions']
            details['c_response_average'] = result['response_average']

            ## prior interaction-- today, delta, decide
            ## continue contribution?
            ##### cannot code here. cause the only 30 seach allowed per hour.  #####

            writer.writerow(details)


    print 'done'

if __name__ == '__main__':
    get_qualified_data('merged')
    get_qualified_data('rejected')

    get_necessary_details()
