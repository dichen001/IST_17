import os, re, csv, cPickle
import numpy as np
from prepare_data import data_dir
from os.path import join as path
from dateutil import parser
from feature_extraction import build_decisionTrees
from csv_processing import CSV_PROC
from get_info import get_pr_repo_info
from get_features import get_all_important_features
from prepare_data import g
from classfications import *
from sklearn import preprocessing



def get_MT_answers(MT_results):
    answers = {}
    gold_answers = {}
    looking_for = ['AssignmentId', 'WorkerId', 'Input.HIT_ID', 'Input.pr_link', 'Input.contributors_url', 'Input.merged', 'Input.submitter', 'Input.closer', 'Input.cores', 'Input.p_num', 'Input.c_num', 'Answer.P1_Submitter', 'Answer.P2_Cores', 'Answer.P3_External', 'Answer.Q1_Support?', 'Answer.Q2_Alternate S?', 'Answer.Q3_Dis_Solution?', 'Answer.Q4_Dis_Problem?', 'Answer.Q5_Outcome?']
    with open(MT_results, 'rU') as csv_in:
        reader = csv.DictReader(csv_in)
        headers = reader.fieldnames
        for row in reader:
            if not row['RejectionTime']:
                is_gold = True if int(row['Input.HIT_ID']) in range(10001, 10021) else False
                for looking in looking_for:
                    # print row['Input.HIT_ID']
                    stripped = looking.split('.')[-1]
                    answers[stripped] = answers.get(stripped, []) + [row[looking]]
                    if is_gold:
                        gold_answers[stripped] = gold_answers.get(stripped, []) + [row[looking]]
    return answers, gold_answers


def get_golden_truthes(GoldenTruth):
    golden_truthes = {}
    with open(GoldenTruth, 'rU') as csv_in:
        reader = csv.DictReader(csv_in)
        headers = reader.fieldnames
        for row in reader:
            for key, value in row.iteritems():
                stripped = key.split('.')[-1]
                golden_truthes[stripped] = golden_truthes.get(stripped, []) + [value]
    return golden_truthes


def evaluate_answer_quality(gold_answers, golden_truthes):
    answers_HIDs = gold_answers['HIT_ID']
    answer_cnt = len(answers_HIDs)
    truth_HIDs = golden_truthes['HIT_ID']
    truth_cnt = len(truth_HIDs)
    keys = golden_truthes.keys()
    if answer_cnt != truth_cnt:
        redundent_HIDs = [i for i in range(truth_cnt) if truth_HIDs[i] not in answers_HIDs]
        tmp_golden_truthes = {}
        for i in range(truth_cnt):
            if i not in redundent_HIDs:
                for k in keys:
                    tmp_golden_truthes[k] = tmp_golden_truthes.get(k,[]) + [golden_truthes[k][i]]
        golden_truthes = tmp_golden_truthes

    questions = [[]] * 6
    for key in keys:
        if key in ['HIT_ID', 'pr_link', 'merged']:
            continue
        answer = gold_answers[key]
        truth = golden_truthes[key]
        Pos = 'Y'
        if key == 'Q5_Outcome?':
            truth = [v if v != 'Merged.' else 'Y' for i, v in enumerate(truth)]
        tuple = zip(answer, truth)
        TP = [z[0].__contains__(Pos) and z[1].__contains__(Pos) for z in tuple].count(True)
        FP = [z[0].__contains__(Pos) and not z[1].__contains__(Pos) for z in tuple].count(True)
        FN = [not z[0].__contains__(Pos) and z[1].__contains__(Pos) for z in tuple].count(True)
        TN = [not z[0].__contains__(Pos) and not z[1].__contains__(Pos) for z in tuple].count(True)
        # pre = len(TP) / float(len(TP) + len(FP))
        # rec = len(TP) / float(len(TP) + len(FN))
        pre = TP / float( TP + FP ) if TP else 0
        rec = TP / float( TP + FN ) if TP else 0
        f1 = 2 * pre * rec / (pre + rec) if pre and rec else 0
        Q_num = int(re.search('\d+', key).group(0))
        questions[Q_num] = [TP, TN, FP, FN, pre, rec, f1]
    TP = sum([t[0] for t in questions[1:]])
    TN = sum([t[1] for t in questions[1:]])
    FP = sum([t[2] for t in questions[1:]])
    FN = sum([t[3] for t in questions[1:]])
    pre = round(TP / float( TP + FP ) if TP else 0, 3)
    rec = round(TP / float( TP + FN ) if TP else 0, 3)
    f1 = round(2 * pre * rec / (pre + rec) if pre and rec else 0, 3)
    print '\t0 \t1 \t <--answers'
    print '\t' + str(TN) + ' \t' + str(FP) + ' \t |0 '
    print '\t' + str(FN) + ' \t' + str(TP) + ' \t |1 '
    print 'precition:\t' + str(pre) + '\trec:\t' + str(rec) + '\tF1\t' + str(f1)
    return pre, rec, f1


def add_all_features(incomplete_features_csv, complete_featuer_csv):
    count = 0
    with open(incomplete_features_csv, 'rU') as csv_in:
        reader = csv.DictReader(csv_in)
        no_headers = True
        headers = reader.fieldnames
        with open(complete_featuer_csv, 'wb') as csv_out:
            for row in reader:
                count += 1
                print '^_^  --> running ' + str(count)
                important_features = get_all_important_features(row['pr_link'])
                if no_headers:
                    headers = reader.fieldnames
                    headers.extend(important_features.keys())
                    writer = csv.DictWriter(csv_out, fieldnames= headers)
                    writer.writeheader()
                    no_headers = False
                row.update(important_features)
                writer.writerow(row)


def convert_s2n(s):
    """convert string to numeric data"""
    if not s:
        print 'converting None to number 0'
        return 0
    s = s.lower()
    if s in ['false', 'true']:
        return 1 if s is 'true' else 0
    if '.' in s:
        return float(s)
    return int(s)


def normalize_features(input_csv, output_csv):
    data_set, scaled_data_set, labels = [], [], []
    if os.path.exists(data_paths[0]):
        for data_path in data_paths:
            data = cPickle.load(open(data_path, 'rb'))
            data_set.append(data)
        labels = cPickle.load(open(label_path, 'rb'))
    else:
        feature_dict = csv_proc.getDictFromCsv(input_csv)
        features = feature_dict.keys()
        cols = len(feature_dict[features[0]])
        newly_found_feature = ['mergeable_state']
        MT_features = ['F_Q1_support', 'F_Q1_core_s', 'F_Q1_other_s', 'F_Q2_alternate', 'F_Q2_a_core', 'F_Q2_a_other', 'F_Q3_dis_s', 'F_Q3_dis_s_bug', 'F_Q3_dis_s_improve', 'F_Q3_dis_s_constc', 'F_Q4_dis_p', 'F_Q4_dis_p_nv', 'F_Q4_dis_p_nf']
        MT_features_selected = ['mergeable_state', 'F_Q3_dis_s', 'F_Q4_dis_p']
        MT_features_selected_s1 = ['F_Q3_dis_s', 'F_Q4_dis_p_nv', 'forks']
        Lit_features = ['team_size', 'watchers', 'num_comments', 'social_distance', 'project_maturity', 'CI_result', 'first_response', 'prev_pullreqs', 'src_churn', 'CI_latency', 'requester_succ_rate', 'is_org', 'sloc', 'commits_on_files_touched', 'collaborator_status', 'num_commits', 'perc_external_contribs', 'experience']
        Lit_features_selected = ['num_comments', 'social_distance', 'requester_succ_rate', 'commits_on_files_touched', 'num_commits']
        Lit_features_selected_s1 = ['commits_on_files_touched', 'requester_succ_rate', 'prev_pullreqs']
        combined_features_selected = ['mergeable_state', 'F_Q3_dis_s', 'F_Q4_dis_p', 'requester_succ_rate', 'project_maturity']
        combined_features_selected_s1 = ['F_Q3_dis_s', 'commits_on_files_touched', 'requester_succ_rate', 'prev_pullreqs']
        visiable_features = ['stars', 'forks', 'open_issues', 'comments', 'commits', 'participants', 'changed_files', 'additions', 'deletions', 'submitter_status', 'lables', 'milestones', 'assignees']
        label_set = ['F_API_merged', 'F_Q5_merged']


        feature_sets = [        MT_features + newly_found_feature, \
                                Lit_features, \
                                MT_features + newly_found_feature + Lit_features, \
                                MT_features_selected, \
                                Lit_features_selected, \
                                combined_features_selected, \
                                visiable_features, \
                                visiable_features + MT_features, \
                                MT_features, \
                                Lit_features + newly_found_feature, \
                                visiable_features + newly_found_feature, \
                                newly_found_feature, \
                                Lit_features + MT_features, \
                                Lit_features + visiable_features, \
                                Lit_features + MT_features + visiable_features, \
                                MT_features_selected_s1, \
                                Lit_features_selected_s1, \
                                combined_features_selected_s1
                                ]
        data_set = [[] for i in range(len(data_paths))]
        with open(output_csv, 'wb') as csv_out:
            headers = feature_dict.keys() + ['mergeable_state']
            writer = csv.DictWriter(csv_out, fieldnames= headers)
            writer.writeheader()
            for i in range(cols):
                print i
                if not feature_dict['CI_latency'][i]:
                    feature_dict['CI_latency'][i] = 365 * 24 * 60 # 1 yeas in minutes
                if not feature_dict.get('mergeable_state'):
                    feature_dict['mergeable_state'] = [''] * cols
                if feature_dict['mergeable_state'][i] == 'dirty':
                    feature_dict['mergeable_state'][i] = -1
                elif feature_dict['mergeable_state'][i] == 'unknown':
                    feature_dict['mergeable_state'][i] = 0
                elif feature_dict['mergeable_state'][i] == 'unstable':
                    feature_dict['mergeable_state'][i] = 1
                elif feature_dict['mergeable_state'][i] == 'clean':
                    feature_dict['mergeable_state'][i] = 2

                row = {}
                for k in feature_dict.keys():
                    row.update({k: feature_dict[k][i]})
                writer.writerow(row)


                for j in range(len(data_paths)):
                    data_set[j].append([])
                    for f in feature_sets[j] :
                        data = feature_dict[f][i]
                        data = convert_s2n(data) if isinstance(data, basestring) else data
                        data_set[j][i].append(data)

                labels.append([])
                for l in label_set:
                    label = feature_dict[l][i]
                    label = convert_s2n(label) if isinstance(label, basestring) else label
                    labels[i].append(label)

        for i in range(len(data_paths)):
            cPickle.dump(data_set[i], open(data_paths[i], 'wb'))
        cPickle.dump(labels, open(label_path, 'wb'))

    for i in range(len(scaled_data_paths)):
        data = np.array(data_set[i])
        scaler = preprocessing.MinMaxScaler()
        scaled_data_set.append(scaler.fit_transform(data))
        cPickle.dump(scaled_data_set[i], open(scaled_data_paths[i], 'wb'))
    labels = np.array(labels)
    scaler0 = preprocessing.MinMaxScaler()
    labels_scaled = scaler0.fit_transform(labels)
    cPickle.dump(labels_scaled, open(label_path.split('.')[0] + suffix, 'wb'))

    return scaled_data_set, labels_scaled


def get_median_iqr(performance_details, output_csv):
    measures = ['precision', 'recall', 'f1', 'f2']
    headers = ['test_name'] + measures
    for i in range(len(measures)):
        headers.append(measures[i] + '_IQR')
    test_name = performance_details.keys()
    with open(output_csv, 'wb') as csv_out:
        writer = csv.DictWriter(csv_out, fieldnames= headers)
        writer.writeheader()
        for test in test_name:
            row = {}
            row['test_name'] = test
            for measure in measures:
                row[measure] = np.median(performance_details[test][measure])
                row[measure + '_IQR'] = np.percentile(performance_details[test][measure], 75) - np.percentile(performance_details[test][measure], 25)
            writer.writerow(row)



if __name__ == '__main__':
    csv_proc = CSV_PROC()
    # """all the variables below are a dict of lists."""
    env_dir = path(data_dir, 'MT_data', '3rdRun')

    MT_result = path(env_dir, 'raw_3rd.csv')
    golden_truthe_csv = path(data_dir, 'MT_data', 'golden_query_true_answers_expectations.csv')
    answers_csv = path(env_dir, 'extracted_answers.csv')
    feauralized_answers_csv = path(env_dir, 'feauralized_answers.csv')
    complete_featuer_csv = path(env_dir, 'complete_featuers.csv')

    #  be careful that MT_result should be ranged by **HIT_ID** in acsending order.
    ## Manual operation from Excel is needed!!
    answers, gold_answers = get_MT_answers(MT_result)
    csv_proc.transDict2Csv(answers, answers_csv)

    golden_truthes = get_golden_truthes(golden_truthe_csv)
    pre, rec, f1 = evaluate_answer_quality(gold_answers, golden_truthes)
    #
    # # transform MT answers into features && adding visible features and mergeable state.
    # csv_proc.featuralizeAnswers(answers_csv, feauralized_answers_csv)
    #
    # # add features from lit-review : slow here.
    # add_all_features(feauralized_answers_csv, complete_featuer_csv)


    data_names = ['data_MT.p', 'data_Lit.p', 'data_all.p', \
                  'data_MT_selected.p', 'data_Lit_selected.p', 'data_all_selected.p', \
                  'data_visiable.p', 'data_visiable_MT.p', \
                  'data_MT_wo_MS.p', 'data_Lit_w_MS.p', 'data_Visiable_w_MS.p', 'data_MS_alone.p',\
                  'data_lit_MT.p', 'data_lit_Visiable.p', 'data_lit_MT_Visiable.p', \
                  'data_MT_s1', 'data_lit_s1', 'data_all_s1']

    suffix = '_scaled.p'
    data_paths, scaled_data_paths = [], []
    for name in data_names:
        data_path = path(env_dir, 'TEMP', name)
        data_paths.append(data_path )
        scaled_data_paths.append(data_path.split('.')[0] + suffix)
    label_path = path(env_dir, 'label.p')

    complete_featuer_csv = path(env_dir, 'complete_featuers.csv')
    fully_complete_featuer_csv =  path(env_dir, 'fully_complete_featuers.csv')
    scaled_data_set, scaled_labels = normalize_features(complete_featuer_csv, fully_complete_featuer_csv)

    label1 = [scaled_labels[i][0] for i in range(len(scaled_labels))]
    test_data = scaled_data_set
    test_label = [label1 for i in range(len(test_data))]
    # test_name = ['MT', 'Visiable', 'Visiable + MT',  'LitRv', 'LitRv + MT']
    test_name = ['MT', 'LitRv', 'All', 'MT-selected', 'LitRv-selected', 'All-selected', 'Visiable', 'Visiable + MT', 'MT_wo_MS', 'Lit_w_MS', 'Visiable_w_MS', 'MS_alone', 'Lit + MT', 'Lit + Visiable', 'Lit + MT + Visible', 'MT-wo-MS', 'Lit', 'Combined']
    performance_details = {}
    # classifier = svm.SVC()
    classifier = tree.DecisionTreeClassifier()
    for i in range(len(test_name)):
        performance_details[test_name[i]] = cross_val(clf=classifier, data=test_data[i], label=test_label[i], target_label=1, folds=5, title=test_name[i])
    print 'done'
    details_path = path(env_dir, 'performance_details_tree.p')
    cPickle.dump(performance_details, open(details_path, 'wb'))
    final_csv = path(env_dir, 'ready_for_plot_tree.csv')
    general_performance = get_median_iqr(performance_details, final_csv)
