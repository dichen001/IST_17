import os
import re
import csv
import ast
import time
import pickle
import numpy as np
from dateutil import parser
from prepare_data import data_dir
from datetime import datetime, timedelta

import pydot
from sklearn import tree
from IPython.display import Image
from sklearn.externals.six import StringIO


pr_csv_file = os.path.join(data_dir, '1400_results.csv')
feature_csv_file = os.path.join(data_dir, '1400_result_features.csv')
selected_feature_csv_file = os.path.join(data_dir, '1400_result_features_selected.csv')
features = ['repo_stars', 'repo_forks', 's_stars', 's_followers', \
            'pr_commits', 'pr_comments', 'pr_files', 'pr_additions', 'pr_deletions', 'pr_has_assignee', 'pr_has_milestone', 'pr_mergeable', 'pr_close_duration',\
            'c_participants', 'c_mentioned_times', 'c_mentioners', 'c_mentionees', 'c_response_average', 'MERGED']
selected_features = ['repo_stars', 's_stars', 's_followers', \
            'pr_comments', 'pr_files','pr_has_assignee', 'pr_has_milestone', 'pr_mergeable',\
            'c_participants', 'c_mentioned_times', 'c_response_average', 'MERGED']
distributions = {}


def featureExtraction(csv_in_f, csv_out_f):
    with open(csv_in_f, 'r') as csv_in:
        reader = csv.DictReader(csv_in)
        with open(csv_out_f, 'wb') as csv_out:
            writer = csv.DictWriter(csv_out, fieldnames= selected_features)
            writer.writeheader()
            count = 0
            for row in reader:
                print str(count)
                count += 1
                n_row = {}
                n_row['repo_stars'] = int(row['repo_stars'])
                # n_row['repo_forks'] = int(row['repo_forks'])
                n_row['s_stars'] = int(row['s_stars'])
                n_row['s_followers'] = int(row['s_followers'])
                # n_row['pr_commits'] = int(row['pr_commits'])
                n_row['pr_comments'] = int(row['pr_comments'])
                n_row['pr_files'] = int(row['pr_changed_files'])
                # n_row['pr_additions'] = int(row['pr_additions'])
                # n_row['pr_deletions'] = int(row['pr_deletions'])
                n_row['pr_has_assignee'] = 1 if row['pr_assignees'] else 0 # boolen
                n_row['pr_has_milestone'] = 1 if row['pr_has_milestone'] else 0 # boolen
                if row['pr_mergeable_state'] == 'clean':
                    n_row['pr_mergeable'] = 2
                elif row['pr_mergeable_state'] == 'unstable':
                    n_row['pr_mergeable'] = 1
                elif row['pr_mergeable_state'] == 'unknown':
                    n_row['pr_mergeable'] = 0
                else:
                    n_row['pr_mergeable'] = -1
                # n_row['pr_merge_duration'] = row['pr_merge_duration'] # null -> 0
                # n_row['pr_close_duration'] = int(row['pr_close_duration'])
                n_row['c_participants'] = len(ast.literal_eval(row['c_participants']))  # -> int
                n_row['c_mentioned_times'] = sum([len(l) for l in ast.literal_eval(row['c_mentions']).values()])  # -> int
                # n_row['c_mentioners'] = len(ast.literal_eval(row['c_mentions']).keys())
                # s = set()
                # for d in ast.literal_eval(row['c_mentions']).values():
                #     s.update(list(set(d)))
                # n_row['c_mentionees'] = len(s)
                try:
                    n_row['c_response_average'] = int(round(float(row['c_response_average'])))  # -> int
                except ValueError:
                    continue
                n_row['MERGED'] = 1 if (row['pr_merged']).lower() == 'true' else 0
                writer.writerow(n_row)


def build_decisionTrees(feature_csv):
    min_samples = [5,10,20,50,100,200]
    max_depths = [3,6,10,15,20]
    for n in [1]:
        with open(feature_csv, 'r') as csv_in:
            reader = csv.reader(csv_in)
            all = list(reader)
            clf = tree.DecisionTreeClassifier(max_depth=4)
            feature_names = all[0]
            data = map(lambda x: [int(i) for i in x[:-4]], all[1:])
            # data = [[int(x[7])] for x in all[1:]]
            target = map(lambda x: int(x[-2]), all[1:])
            clf = clf.fit(data, target)

            dot_data = "t.dot"
            tree.export_graphviz(clf, out_file=dot_data,
                             feature_names=feature_names[:-4],
                             # feature_names=feature_names[7],
                             class_names=['Not-Implemented', 'Implemented'],
                             filled=True, rounded=True,
                             special_characters=True,)
            # os.system("dot -Tpdf t.dot -o %s.pdf" % ('dTree_Min_Smaple_'+str(n)))
            os.system("dot -Tpdf t.dot -o %s.pdf" % ('../Data/Analyzing/all_implemented_tree'))

        # graph = pydot.graph_from_dot_data(dot_data.getvalue())
        # Image(graph.create_png())

        # graph.write_pdf("iris.pdf")
        print 'done'



def drawTree(name, clf, write_dot=True, drawPng=False, drawPdf=False):
   file2draw = name
   if write_dot or drawPng or drawPdf:
       with open(file2draw+'.dot', 'w+') as f:
           tree.export_graphviz(clf, out_file=f)
   else:
       f = cStringIO.StringIO()
       tree.export_graphviz(clf, out_file=f)
       tree_dot = f.getvalue()
       f.close()
       return tree_dot

   if drawPdf:
       os.system("dot -Tpdf %s.dot -o %s.pdf" % (dot_data, 'cao'))
   if drawPng:
       os.system("dot -Tpng %s.dot -o %s.png" % (file2draw, file2draw))



if __name__ == '__main__':
    pr_csv_file = os.path.join(data_dir, 'GHTorrent', 'final_sql_converted_3.csv')
    selected_feature_csv_file = os.path.join(data_dir, 'GHTorrent_result_features.csv')
    # featureExtraction(pr_csv_file, selected_feature_csv_file)

    tree_input_csv = os.path.join(data_dir, 'Analyzing', 'feature_all.csv')
    build_decisionTrees(tree_input_csv)




