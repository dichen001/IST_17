import os, re, csv
import ast
from prepare_data import data_dir, g
from get_info import get_pr_repo_info, get_cores, get_user_info



def convert_csv(input_csv, output_csv):
    with open(input_csv, 'r') as csv_in:
        reader = csv.DictReader(csv_in)
        with open(output_csv, 'wb') as csv_out:
            g.fields.append('pr_closer')
            writer = csv.DictWriter(csv_out, fieldnames= g.fields)
            writer.writeheader()
            for row in reader:
                details = {}
                details['repo_owner'] = row['OWNER']
                details['repo_name'] = row['repo']
                details['pr_id'] = row['github_pr_id']
                ## extra info, different from
                details['pr_closer'] = row['closer']
                details['pr_html'] = 'https://github.com/' + row['OWNER'] + '/' + row['repo'] + '/pull/' + str(row['github_pr_id'])

                more_info = get_pr_repo_info(row['OWNER'], row['repo'], row['github_pr_id'])
                if more_info:
                    details.update(more_info)
                else:
                    g.r_info_miss_num += 1
                    continue

                ## submiter's info
                details['s_id'] = row['submitter']
                user_info = get_user_info(details['s_id'])
                details['s_stars'], details['s_followers'] = user_info['stars'], user_info['followers']
                if not details['s_stars'] or not details['s_followers']:
                    print 'Not Found -- Submitter: ' + details['s_id']
                    g.s_miss_num += 1
                    continue

                # core info
                details['repo_cores'] = get_cores(details['repo_owner'], details['repo_name'])
                if not details['repo_cores']:
                    print 'Not Found -- Repo: ' + details['repo_owner'] + '/' + details['repo_name']
                    g.core_miss_num += 1
                    continue

                try:
                    writer.writerow(details)
                except ValueError:
                    print 'hi there'
    print 'done'


def get_MT_csv(input_csv, output_csv):
    with open(input_csv, 'r') as csv_in:
        reader = csv.DictReader(csv_in)
        with open(output_csv, 'wb') as csv_out:
            fields = ['HIT_ID', 'pr_link', 'contributors_url', 'cores', 'merged', 'submitter', 'closer', 'cores', 'p_num', 'c_num']
            writer = csv.DictWriter(csv_out, fieldnames= fields)
            writer.writeheader()
            for row in reader:
                info = {}
                info['HIT_ID'] = row['HIT_ID']
                urls = row['pr_html'].split('/pulls/')
                if len(urls) > 2:
                    continue
                info['pr_link'] = urls[0] + '/pull/' + urls[1]
                info['contributors_url'] = urls[0] + '/graphs/contributors'
                core = ast.literal_eval(row['repo_cores'])
                core = [str(i) for i in core]
                info['cores'] = ', '.join(core)
                info['submitter'] = row['s_id']
                info['closer'] = row['pr_closer']
                info['merged'] = row['pr_merged']
                info['p_num'] = 0
                if row['c_participants']:
                    participants = ast.literal_eval(row['c_participants'])
                    info['p_num'] = len(participants)
                info['c_num'] = row['pr_comments']
                writer.writerow(info)

def prepare_golden_query(input_csv, output_csv):
    with open(input_csv, 'r') as csv_in:
        reader = csv.DictReader(csv_in)
        with open(output_csv, 'wb') as csv_out:
            fields = ['HIT_ID', 'pr_link', 'contributors_url', 'merged', 'submitter', 'closer', 'cores', 'p_num', 'c_num']
            writer = csv.DictWriter(csv_out, fieldnames= fields)
            writer.writeheader()
            for row in reader:
                info = {}
                info['HIT_ID'] = row['HIT_ID']
                info['pr_link'] = row['pr_link']
                info['contributors_url'] = row['contributors_url']

                core = get_cores(row['repo_owner'], row['repo_name'])
                if core:
                    core = [str(i) for i in core]
                    info['cores'] = ', '.join(core)
                else:
                    print '?'

                detail = get_pr_repo_info(row['repo_owner'], row['repo_name'], row['pr_id'])
                if detail:
                    info['merged'] = detail['pr_merged']
                    info['p_num'] = len(detail['c_participants'])
                    info['c_num'] = detail['pr_comments']
                else:
                    print '?'

                writer.writerow(info)

if __name__ == '__main__':
    GHTorrent_csv = os.path.join(data_dir, 'GHTorrent', 'final_sql_part.csv')
    converted_csv = os.path.join(data_dir, 'GHTorrent', 'final_sql_converted.csv')
    # convert_csv(GHTorrent_csv, converted_csv)
    MT_upload_csv = os.path.join(data_dir, 'MT_data', 'MT_upload.csv')
    # get_MT_csv(converted_csv, MT_upload_csv)
    golden_input = os.path.join(data_dir, 'MT_data', 'golden_query_links.csv')
    golden_output = os.path.join(data_dir, 'MT_data', 'golden_query_4MT.csv')
    prepare_golden_query(golden_input, golden_output)
