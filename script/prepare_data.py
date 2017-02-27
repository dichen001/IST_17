"""
As the row json data from GithubArchive is distributed
by hour for all the activities, we need to:
    - download raw zipped json file for about 1 month
    - filter out other activities, and only keep pull requests
    - only keep the closed pull requests, i.e. the merged and rejected ones
    - save them together in pickle file for future easy re-use
"""
import os
import gc
import json
import sys
import threading
import urllib
from Queue import Queue
import logging
import pickle


base_dir = os.path.abspath(os.path.join(__file__, "../../"))
data_dir = os.path.join(base_dir, 'Data')
raw_data_dir = os.path.join(data_dir, 'suplement_unziped')
# raw_data_dir = os.path.join(data_dir, 'temp')
saved_file = os.path.join(data_dir, 'suplement_pickle')

class globals:
    pass
g = globals()
g.auth_id = ['dichen001Test01', 'dichen001', 'Ginfung', 'azhe825', 'vivekaxl', 'weifoo', 'amritbhanu', 'bigfatnoob']
g.auth_token = ['baa47b85673e038fd817acb54974b598b82ff560', '597318e91d03aed54fc94da21b30c20bc62c0fb8', '5ff97d2057473851206a8d4b27c863c67499c00e', '1f2752db0428439512848167b6ff7cdcb85ab60e', '54790cc4fdc5861b6c3a17983638378f7f420b96', 'a1c331c863cc9285f0ab21d9437414c5975fbfe2', 'e05de2f1d89a729cafda8e087c7cad0862074f3a', 'ff606da49d201bcfb5eafba4df350b0f942a6470']
g.auth_index = 0
g.s_miss_num = 0
g.core_miss_num = 0
g.comment_miss_num = 0
g.r_info_miss_num = 0
g.fields = ['repo_owner', 'repo_name', 'repo_stars', 'repo_forks', 'repo_watchers', 'repo_cores',\
              's_id', 's_stars', 's_followers',\
              'pr_id', 'pr_html', 'pr_commits', 'pr_comments', 'pr_assignees', 'pr_changed_files', 'pr_additions', 'pr_deletions', 'pr_has_milestone',\
              'pr_mergeable', 'pr_mergeable_state', 'pr_merged', 'pr_merged_by', 'pr_merge_duration', 'pr_close_duration', 'pr_created_time', 'pr_merged_time', 'pr_closed_time',\
              'c_participants', 'c_mentions', 'c_response_times', 'c_response_average'
              ]




class Downloader(threading.Thread):
    def __init__(self, queue):
        super(Downloader, self).__init__()
        self.queue = queue

    def run(self):
        while True:
            download_url, save_as = self.queue.get()
            # sentinal
            if not download_url:
                return
            try:
                urllib.urlretrieve(download_url, filename=save_as)
            except Exception, e:
                logging.error("error downloading %s: %s" % (download_url, e))


def get_data():
    queue = Queue()
    threads = []
    for i in xrange(5):
        threads.append(Downloader(queue))
        threads[-1].start()
    # for line in 'http://data.githubarchive.org/2015-01-01-0.json.gz':#sys.stdin:
    for year in [2013]:
        for month in [7]:
            for day in xrange(1,32):
                for hour in xrange(24):
                    url = 'http://data.githubarchive.org/' + str(year) + '-' + str(month) + '-' + str(day) + '-' + str(hour) + '.json.gz'
                    filename = url.split('/')[-1]
                    print "Download %s as %s" % (url, filename)
                    queue.put((url, os.path.join(data_dir, filename)))


def process_json():
    merged, rejected = [], []
    all_data = {'open': [], 'merged': [], 'rejected': []}
    comment_numbers = []
    days = set()
    open_count, close_count, merged_count, rejected_count, has_comments_count = 0, 0, 0, 0, 0
    json_files = os.listdir(raw_data_dir)
    for id, json_file in enumerate(json_files):
        print 'No.' + str(id) + ' -- Processing ' + json_file
        days.add(json_file.split('-')[-2])
        for line in open(os.path.join(raw_data_dir, json_file), 'r'):
            data = json.loads(line)
            if data['type'] == u'PullRequestEvent':
                # print 'action: ' + data['payload']['action']
                # print 'state: ' + data['payload']['pull_request']['state']
                if data['payload']['pull_request']['state'] == 'open':
                    open_count += 1
                    # opened.append(data)
                else:
                    close_count += 1
                    if data['payload']['pull_request']['merged']:
                        merged_count += 1
                        merged.append(data)
                    else:
                        rejected_count += 1
                        rejected.append(data)
                if data['payload']['pull_request']['comments'] != 0:
                    has_comments_count += 1
                    comment_numbers.append(data['payload']['pull_request']['comments'])
            if days and len(days) % 4 == 0:
                with open(os.path.join(saved_file, '_rejected_' + '-'.join(sorted(days)) + '.pickle'), 'wb') as f:
                    pickle.dump(rejected, f)
                    del rejected
                    gc.collect()
                with open(os.path.join(saved_file, 'merged_' + '-'.join(sorted(days)) + '.pickle'), 'wb') as f:
                    pickle.dump(merged, f)
                    del merged
                    gc.collect()
                print 'file saved in: ' + saved_file + '_' + '-'.join(days)
                merged, rejected = [], []
                days = set()
    print 'open ' + str(open_count/(float(open_count + close_count)))
    print 'close ' + str(close_count/(float(open_count + close_count)))
    print 'merged ' + str(merged_count/(float(close_count)))
    print 'rejected ' + str(rejected_count/(float(close_count)))
    print 'has_comments ' + str(has_comments_count/(float(open_count + close_count)))



if __name__ == '__main__':
    jf = os.path.join(data_dir, 'TEMP', 'output.json')
    j_file = open(jf, 'r')
    j_data = json.load(j_file)

    # get_raw_data()
    process_json()
    print 'done'



