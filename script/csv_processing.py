import os, csv
from prepare_data import data_dir
from os.path import join as path
from feature_extraction import build_decisionTrees
from get_info import *

class CSV_PROC():

    def getDictFromCsv(self, csvInput, en_coding=None):
        """from a csv file, return a dict. key is the header, value is a list of the all the cells under this header."""
        dict = {}
        with open(csvInput, 'rU') as csvInput:
            reader = csv.DictReader(csvInput)
            fields = reader.fieldnames
            for row in reader:
                for field in fields:
                    a = dict.get(field)
                    if not a:
                        a = [row.get(field)]
                    else:
                        a.append(row.get(field))
                    dict.update({field: a})
        return dict


    def transDict2Csv(self, csvDict, csvOuput):
        """from a dict, whose keys are the headers, values are lists of the all the cells under each header."""
        headers = csvDict.keys()
        columns = len(csvDict[headers[0]])
        with open(csvOuput, 'wb') as csv_out:
                writer = csv.DictWriter(csv_out, fieldnames= headers)
                writer.writeheader()
                for i in range(columns):
                    row = {}
                    for header in headers:
                        row[header] = csvDict[header][i]
                    writer.writerow(row)
        print 'dict succssfully saved in: ' + csvOuput


    def getCsvDiff(self, old_csv, new_csv, out_csv, prim_key='AssignmentId'):
        old = self.getDictFromCsv(old_csv)[prim_key]
        new = self.getDictFromCsv(new_csv)[prim_key]
        with open(new_csv, 'rU') as csv_in:
            reader = csv.DictReader(csv_in)
            headers = reader.fieldnames
            with open(out_csv, 'wb') as csv_out:
                writer = csv.DictWriter(csv_out, fieldnames= headers)
                writer.writeheader()
                for row in reader:
                    if row[prim_key] not in old:
                        writer.writerow(row)


    def addMergableState(self, full_csv, result_csv, out_csv):
        full = self.getDictFromCsv(full_csv)
        full_dict = {url.replace('/pulls/','/pull/'): full['pr_mergeable_state'][id]  for id, url in enumerate(full['pr_html'])}
        result = self.getDictFromCsv(result_csv)['Input.pr_link']
        overlap_dict = {k:v for k,v in full_dict.iteritems() if k in result}
        with open(result_csv, 'rU') as csv_in:
            reader = csv.DictReader(csv_in)
            headers = reader.fieldnames
            headers.append('mergeable')
            with open(out_csv, 'wb') as csv_out:
                writer = csv.DictWriter(csv_out, fieldnames= headers)
                writer.writeheader()
                count = 0
                for row in reader:
                    try:
                        m_state = overlap_dict[row['Input.pr_link']]
                        if m_state == 'dirty':
                            row['mergeable'] = -1
                        elif m_state == 'unknown':
                            row['mergeable'] = 0
                        elif m_state == 'unstable':
                            row['mergeable'] = 1
                        elif m_state == 'clean':
                            row['mergeable'] = 2
                        else:
                            print 'impossible!'
                    except KeyError:
                        row['mergeable'] = 0
                        count += 1
                        print count
                    writer.writerow(row)


    def addMS(self, input_csv, out_csv):
        with open(input_csv, 'rU') as csv_in:
            reader = csv.DictReader(csv_in)
            headers = reader.fieldnames
            headers.extend(['merged', 'mergeable_state', 'stars', 'forks', 'open_issues', 'comments', 'commits', 'participants', 'changed_files', 'additions', 'deletions', 'submitter_status', 'lables', 'milestones', 'assignees'])
            with open(out_csv, 'wb') as csv_out:
                writer = csv.DictWriter(csv_out, fieldnames= headers)
                writer.writeheader()
                count = 0
                for row in reader:
                    try:
                        owner = row['`owner`']
                        repo = row['`repo`']
                        pr_id = row['`github_pr_id`']
                        pr_repo_info = get_pr_repo_info(owner, repo, pr_id, get_all_features=False, minimal=True)
                        # status, labels, participants = s.scrape_pr_page(owner, repo, pr_id)
                        row['merged'] = pr_repo_info['pr_merged']
                        row['mergeable_state'] = pr_repo_info['pr_mergeable_state']
                        ## add visible_features
                        row['stars'] = pr_repo_info['repo_stars']
                        row['forks'] = pr_repo_info['repo_forks']
                        row['open_issues'] = pr_repo_info['repo_issues_count']
                        row['comments'] = pr_repo_info['pr_comments']
                        row['commits'] = pr_repo_info['pr_commits']
                        # row['participants'] = participants
                        row['changed_files'] = pr_repo_info['pr_changed_files']
                        row['additions'] = pr_repo_info['pr_additions']
                        row['deletions'] = pr_repo_info['pr_deletions']
                        # row['submitter_status'] = 1 if status == 'member' else 0
                        # row['lables'] = labels
                        row['milestones'] = 1 if pr_repo_info['pr_has_milestone'] else 0
                        row['assignees'] = pr_repo_info['pr_assignee_num']
                        writer.writerow(row)
                        print count
                        count += 1
                    except:
                        print '/'.join([owner, repo, pr_id])


    def completeGoldenInfo(self, incomplete_csv, complete_csv):
        """ add submitter and closer for each PR. """
        with open(incomplete_csv, 'rU') as csv_in:
            reader = csv.DictReader(csv_in)
            headers = reader.fieldnames
            with open(complete_csv, 'wb') as csv_out:
                writer = csv.DictWriter(csv_out, fieldnames= headers)
                writer.writeheader()
                for row in reader:
                    pr_url = row['pr_link'].split('/')
                    owner, repo, pr_id = pr_url[-4], pr_url[-3], pr_url[-1]
                    response = robust_request('https://api.github.com/repos/' + owner + '/' + repo + '/pulls/' + str(pr_id), auth=(g.auth_id[g.auth_index], g.auth_token[g.auth_index]))
                    if not response or response.status_code != 200:
                        return None
                    data = response.json()
                    row['submitter'] = data["user"]['login']
                    closer = get_pr_closer(owner, repo, pr_id)
                    row['closer']  = closer
                    writer.writerow(row)


    def featuralizeAnswers(self, answer_csv, feature_output):
        s = scraper()
        with open(answer_csv, 'rU') as csv_in:
            reader = csv.DictReader(csv_in)
            headers = reader.fieldnames
            visible_features = ['stars', 'forks', 'open_issues', \
                                'comments', 'commits', 'participants', \
                                'changed_files', 'additions', 'deletions', \
                                'submitter_status', 'lables', 'milestones', 'assignees']
            MT_features = ['F_Q1_support', 'F_Q1_core_s', 'F_Q1_other_s',\
                           'F_Q2_alternate', 'F_Q2_a_core', 'F_Q2_a_other', \
                           'F_Q3_dis_s', 'F_Q3_dis_s_bug', 'F_Q3_dis_s_improve', 'F_Q3_dis_s_constc',\
                           'F_Q4_dis_p', 'F_Q4_dis_p_nv', 'F_Q4_dis_p_nf', \
                           'F_Q5_merged', 'F_Q5_implemented', \
                           'F_API_merged']
            strong_feature = 'mergeable_state'
            headers.extend(visible_features)
            headers.extend(MT_features)
            headers.append(strong_feature)
            with open(feature_output, 'wb') as csv_out:
                writer = csv.DictWriter(csv_out, fieldnames= headers)
                writer.writeheader()
                for row in reader:
                    pr_url = row['pr_link']
                    url_parts = pr_url.split('/')[-4:]
                    owner, repo, pr_id = url_parts[0], url_parts[1], url_parts[-1]
                    pr_repo_info = get_pr_repo_info(owner, repo, pr_id, get_all_features=False, minimal=True)
                    status, labels, participants = s.scrape_pr_page(owner, repo, pr_id)
                    row['mergeable_state'] = pr_repo_info['pr_mergeable_state']
                    ## add visible_features
                    row['stars'] = pr_repo_info['repo_stars']
                    row['forks'] = pr_repo_info['repo_forks']
                    row['open_issues'] = pr_repo_info['repo_issues_count']
                    row['comments'] = pr_repo_info['pr_comments']
                    row['commits'] = pr_repo_info['pr_commits']
                    row['participants'] = participants
                    row['changed_files'] = pr_repo_info['pr_changed_files']
                    row['additions'] = pr_repo_info['pr_additions']
                    row['deletions'] = pr_repo_info['pr_deletions']
                    row['submitter_status'] = 1 if status == 'member' else 0
                    row['lables'] = labels
                    row['milestones'] = 1 if pr_repo_info['pr_has_milestone'] else 0
                    row['assignees'] = pr_repo_info['pr_assignee_num']


                    ## transform MT answers into features and add
                    row['F_API_merged'] = 1 if row['merged'] == 'TRUE' else 0
                    # Q-1
                    if row['Q1_Support?'].__contains__('Y'):
                        row['F_Q1_support'] = 1
                    else:
                        row['F_Q1_support'] = 0

                    if row['Q1_Support?'].__contains__('Y,core'):
                        row['F_Q1_core_s']= 1
                    else:
                        row['F_Q1_core_s']= 0
                    if row['Q1_Support?'].__contains__('Y,others'):
                        row['F_Q1_other_s'] = 1
                    else:
                        row['F_Q1_other_s'] = 0

                    # Q-2
                    if row['Q2_Alternate S?'].__contains__('Y'):
                        row['F_Q2_alternate'] = 1
                    else:
                        row['F_Q2_alternate'] = 0

                    if row['Q2_Alternate S?'].__contains__('Y,core'):
                        row['F_Q2_a_core'] = 1
                    else:
                        row['F_Q2_a_core'] = 0
                    if row['Q2_Alternate S?'].__contains__('Y,others'):
                        row['F_Q2_a_other'] = 1
                    else:
                        row['F_Q2_a_other'] = 0

                    # Q-3
                    if row['Q3_Dis_Solution?'].__contains__('Y'):
                        row['F_Q3_dis_s'] = 1
                    else:
                        row['F_Q3_dis_s'] = 0

                    if row['Q3_Dis_Solution?'].__contains__('Y,bug'):
                        row['F_Q3_dis_s_bug'] = 1
                    else:
                        row['F_Q3_dis_s_bug'] = 0
                    if row['Q3_Dis_Solution?'].__contains__('Y,improve'):
                        row['F_Q3_dis_s_improve'] = 1
                    else:
                        row['F_Q3_dis_s_improve'] = 0
                    if row['Q3_Dis_Solution?'].__contains__('Y,inconsistency'):
                        row['F_Q3_dis_s_constc'] = 1
                    else:
                        row['F_Q3_dis_s_constc'] = 0

                    # Q-4
                    if row['Q4_Dis_Problem?'].__contains__('Y'):
                        row['F_Q4_dis_p'] = 1
                    else:
                        row['F_Q4_dis_p'] = 0

                    if row['Q4_Dis_Problem?'].__contains__('Y, no value'):
                        row['F_Q4_dis_p_nv'] = 1
                    else:
                        row['F_Q4_dis_p_nv'] = 0
                    if row['Q4_Dis_Problem?'].__contains__('Y,not fit.'):
                        row['F_Q4_dis_p_nf'] = 1
                    else:
                        row['F_Q4_dis_p_nf'] = 0

                    # Q-5
                    if row['Q5_Outcome?'].__contains__('Merged'):
                        row['F_Q5_merged'] = 1
                    else:
                        row['F_Q5_merged'] = 0

                    if row['Q5_Outcome?'].__contains__('implemented') or row['Q5_Outcome?'].__contains__('Merged'):
                        row['F_Q5_implemented'] = 1
                    else:
                        row['F_Q5_implemented'] = 0
                    writer.writerow(row)


    """ old version """
    # def featuralizeAnswers(self, answer_csv, feature_output):
    #     with open(answer_csv, 'rU') as csv_in:
    #         reader = csv.DictReader(csv_in)
    #         headers = reader.fieldnames
    #         headers.extend(['F_Q1_support', 'F_Q1_core_s', 'F_Q1_other_s',\
    #                        'F_Q2_alternate', 'F_Q2_a_core', 'F_Q2_a_other', \
    #                        'F_Q3_dis_s', 'F_Q3_dis_s_bug', 'F_Q3_dis_s_improve', 'F_Q3_dis_s_constc',\
    #                        'F_Q4_dis_p', 'F_Q4_dis_p_nv', 'F_Q4_dis_p_nf', \
    #                        'F_Q5_merged', 'F_Q5_implemented', \
    #                        'F_API_merged'])
    #         with open(feature_output, 'wb') as csv_out:
    #             writer = csv.DictWriter(csv_out, fieldnames= headers)
    #             writer.writeheader()
    #             for row in reader:
    #                 row['F_API_merged'] = 1 if row['Input.merged'] == 'TRUE' else 0
    #                 # Q-1
    #                 if row['Answer.Q1_Support?'].__contains__('Y'):
    #                     row['F_Q1_support'] = 1
    #                 else:
    #                     row['F_Q1_support'] = 0
    #
    #                 if row['Answer.Q1_Support?'].__contains__('Y,core'):
    #                     row['F_Q1_core_s']= 1
    #                 else:
    #                     row['F_Q1_core_s']= 0
    #                 if row['Answer.Q1_Support?'].__contains__('Y,others'):
    #                     row['F_Q1_other_s'] = 1
    #                 else:
    #                     row['F_Q1_other_s'] = 0
    #
    #                 # Q-2
    #                 if row['Answer.Q2_Alternate S?'].__contains__('Y'):
    #                     row['F_Q2_alternate'] = 1
    #                 else:
    #                     row['F_Q2_alternate'] = 0
    #
    #                 if row['Answer.Q2_Alternate S?'].__contains__('Y,core'):
    #                     row['F_Q2_a_core'] = 1
    #                 else:
    #                     row['F_Q2_a_core'] = 0
    #                 if row['Answer.Q2_Alternate S?'].__contains__('Y,others'):
    #                     row['F_Q2_a_other'] = 1
    #                 else:
    #                     row['F_Q2_a_other'] = 0
    #
    #                 # Q-3
    #                 if row['Answer.Q3_Dis_Solution?'].__contains__('Y'):
    #                     row['F_Q3_dis_s'] = 1
    #                 else:
    #                     row['F_Q3_dis_s'] = 0
    #
    #                 if row['Answer.Q3_Dis_Solution?'].__contains__('Y,bug'):
    #                     row['F_Q3_dis_s_bug'] = 1
    #                 else:
    #                     row['F_Q3_dis_s_bug'] = 0
    #                 if row['Answer.Q3_Dis_Solution?'].__contains__('Y,improve'):
    #                     row['F_Q3_dis_s_improve'] = 1
    #                 else:
    #                     row['F_Q3_dis_s_improve'] = 0
    #                 if row['Answer.Q3_Dis_Solution?'].__contains__('Y,inconsistency'):
    #                     row['F_Q3_dis_s_constc'] = 1
    #                 else:
    #                     row['F_Q3_dis_s_constc'] = 0
    #
    #                 # Q-4
    #                 if row['Answer.Q4_Dis_Problem?'].__contains__('Y'):
    #                     row['F_Q4_dis_p'] = 1
    #                 else:
    #                     row['F_Q4_dis_p'] = 0
    #
    #                 if row['Answer.Q4_Dis_Problem?'].__contains__('Y, no value'):
    #                     row['F_Q4_dis_p_nv'] = 1
    #                 else:
    #                     row['F_Q4_dis_p_nv'] = 0
    #                 if row['Answer.Q4_Dis_Problem?'].__contains__('Y,not fit.'):
    #                     row['F_Q4_dis_p_nf'] = 1
    #                 else:
    #                     row['F_Q4_dis_p_nf'] = 0
    #
    #                 # Q-5
    #                 if row['Answer.Q5_Outcome?'].__contains__('Merged'):
    #                     row['F_Q5_merged'] = 1
    #                 else:
    #                     row['F_Q5_merged'] = 0
    #
    #                 if row['Answer.Q5_Outcome?'].__contains__('implemented') or row['Answer.Q5_Outcome?'].__contains__('Merged'):
    #                     row['F_Q5_implemented'] = 1
    #                 else:
    #                     row['F_Q5_implemented'] = 0
    #                 writer.writerow(row)




if __name__ == '__main__':
    mt_dir = path(data_dir, 'MT_data')



    featuralized_results = path(mt_dir, '2nd_run_100_2nd_Results_mergeable_added_copy.csv')
    # build_decisionTrees(featuralized_results)

    all_qualified = path(mt_dir, 'MT_upload_qualified.csv')
    qualified_200_1st_run = path(mt_dir, 'MT_upload_qualified_w_GQ_200_1st_run.csv')
    qualified_100_2nd_run = path(mt_dir, 'MT_upload_qualified_w_GQ_100_2nd_run.csv')
    qualified_100_3rd_run = path(mt_dir, 'MT_upload_qualified_w_GQ_150_3rd_run.csv')
    qualified_left1 = path(mt_dir, 'MT_upload_qualified_left_-2.csv')
    qualified_left = path(mt_dir, 'MT_upload_qualified_left_-2-3.csv')

    old_result = path(mt_dir, '2nd_run_100_1st_Results_raw_reviewd_upload.csv')
    new_result = path(mt_dir, '2nd_run_100_2nd_Results_raw.csv')
    diff_result = path(mt_dir, '2nd_run_100_2nd_suplement.csv')

    GHTorrent_csv = path(mt_dir, 'ghtorrent_Sept.csv')
    GHTorrent_added_csv = path(mt_dir, 'ghtorrent_Sept_added.csv')
    C = CSV_PROC()
    C.addMS(GHTorrent_csv, GHTorrent_added_csv)

    # C.getCsvDiff(old_result, new_result, diff_result)
    C.getCsvDiff(qualified_100_3rd_run, qualified_left1, qualified_left, prim_key='HIT_ID')

    golden_query_csv = path(mt_dir, 'golden_query_4MT.csv')
    completed_golden_query_csv = path(mt_dir, 'golden_query_4MT_complete_info1.csv')
    # add submitter and closer info
    C.completeGoldenInfo(golden_query_csv, completed_golden_query_csv)

    filtered_results = path(mt_dir, '2nd_run_100_2nd_Results_filtered.csv')
    featuralized_results = path(mt_dir, '2nd_run_100_2nd_Results_featuralized.csv')
    # C.featuralizeAnswers(filtered_results, featuralized_results)

    full_csv = path(mt_dir, 'MT_converted_from_GHTorrent.csv')
    meageable_added_csv = path(mt_dir, '2nd_run_100_2nd_Results_mergeable_added.csv')
    all_important_features_added = path(mt_dir, '2nd_run_100_2nd_Results_all_important_features_added.csv')
    C.addMergableState(full_csv, featuralized_results, meageable_added_csv)
