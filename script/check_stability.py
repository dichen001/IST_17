import os, re, csv, cPickle
import numpy as np
import random, collections
from prepare_data import data_dir
from os.path import join as path
from csv_processing import CSV_PROC
from scipy.stats import chi2_contingency


def getDistribution(data, keys, headers, isGold=False):
    dist = {}
    for h in headers:
        dist[h + '-Y'] = 0
        dist[h + '-N'] = 0
    for k in keys:
        for h in headers:
            if isGold:
                if data[k][h] == 'N':
                    dist[h + '-N'] += 1
                else:
                    dist[h + '-Y'] += 1
            else:
                if data[k][h] == '1':
                    dist[h + '-Y'] += 1
                else:
                    dist[h + '-N'] += 1
    return dist

def runStabCheck(rept=100, cnt1=15, cnt2=5):
    # g, p, dof, expctd = [0]*10, [0]*10, [0]*10, [0]*10
    samples, details = [0]*rept, [0] * rept
    for i in range(rept):
        random.shuffle(merged)
        random.shuffle(reject)
        mt = merged[:cnt1] + reject[:cnt2]
        dist = getDistribution(id2item, mt, names, isGold=False)
        samples[i] = [dist_gold.values(), dist.values()]
        details[i] = [chi2_contingency([samples[i][0][k*2:k*2+2], samples[i][1][k*2:k*2+2]]) for k in range(4)]
        print i

    P_details = [[]] * 4
    for i in range(4):
        P_details[i] = [detail[i][1] for detail in details]

    return P_details




csv_proc = CSV_PROC()
env_dir = path(data_dir, 'MT_data')
gold_csv = path(env_dir, 'golden_query_true_answers_expectations.csv')
gold_data = csv_proc.getDictFromCsv(gold_csv)
id2item_gold = {}
headers = ['Answer.Q1_Support?', 'Answer.Q2_Alternate S?', 'Answer.Q3_Dis_Solution?', 'Answer.Q4_Dis_Problem?']
for k, id in enumerate(gold_data['Input.HIT_ID']):
    id2item_gold[id] = {name: gold_data[name][k] for name in headers}
dist_gold = getDistribution(id2item_gold, id2item_gold.keys(), headers, isGold=True)

combined_csv = path(env_dir, '2&3', '2&3.csv')
combined_data = csv_proc.getDictFromCsv(combined_csv)
names =  ['F_Q1_support', 'F_Q2_alternate', 'F_Q3_dis_s', 'F_Q4_dis_p']
# names = ['Q1_Support?', 'Q2_Alternate S?', 'Q3_Dis_Solution?', 'Q4_Dis_Problem?']
id2item = {}
for k, id in enumerate(combined_data['AssignmentId']):
    # ignore the PR from TDH
    if int(combined_data['HIT_ID'][k]) > 9999:
        continue
    id2item[id] = {name: combined_data[name][k] for name in names + ['merged']}
merged = [id for id in id2item.iterkeys() if id2item[id]['merged'] == 'TRUE']
reject = [id for id in id2item.iterkeys() if id2item[id]['merged'] == 'FALSE']


PP = runStabCheck(rept=100, cnt1=15, cnt2=5)
PPP = runStabCheck(rept=100, cnt1=87, cnt2=29)
details = {'15(merged):5(rejected)': PP, '87(merged):29(rejected)': PPP}
details_path = path(env_dir, 'stability_details.p')
cPickle.dump(details, open(details_path, 'wb'))


result_path = path(env_dir, 'p_stability.csv')
result_headers = ['Question' ,'0%', '25%', '50%', '75%', '100%', 'IQR', 'Mean']

with open(result_path, 'wb') as csv_out:
    writer = csv.DictWriter(csv_out, fieldnames= result_headers)
    writer.writeheader()
    for i, Q in enumerate(['Q1', 'Q2', 'Q3', 'Q4', 'Total']):
        tmp_dict = {'Question': Q}
        tmp_dict['0%'] = min(PP[i])
        tmp_dict['100%'] = max(PP[i])
        tmp_dict['Mean'] = np.mean(PP[i])
        tmp_dict['25%'] = np.percentile(PP[i], 25)
        tmp_dict['50%'] = np.percentile(PP[i], 50)
        tmp_dict['75%'] = np.percentile(PP[i], 75)
        tmp_dict['IQR'] = tmp_dict['75%'] - tmp_dict['25%']
        row = {k : round(v, 2) for k, v in tmp_dict.iteritems() if k != 'Question' }
        writer.writerow(row)

print 'done'










