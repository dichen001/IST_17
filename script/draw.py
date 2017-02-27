__author__ = 'amrit'

import matplotlib.pyplot as plt
import os, cPickle
import operator
import numpy as np
import matplotlib.cm as cmx
import matplotlib.colors as colors
from prepare_data import data_dir
from os.path import join as path

if __name__ == '__main__':

    env_dir = path(data_dir, 'MT_data', '2ndRun')
    performances_path = path(env_dir, 'performance_details_tree.p')
    performances = cPickle.load(open(performances_path, 'rb'))
    # test_name = performances.keys()
    # test_name = ['MT', 'LitRv', 'All', 'MT-selected', 'LitRv-selected', 'All-selected', 'Visiable', 'Visiable + MT', 'MT_wo_MS', 'Lit_w_MS', 'Visiable_w_MS']
    # test_name = ['MT', 'MT_wo_MS', 'LitRv','Lit_w_MS', 'MS_alone']
    # test_name = ['MT_wo_MS', 'LitRv', 'Lit + MT']
    test_name = ['MT-wo-MS', 'Lit', 'Combined']
    print(performances)

    # learners = ['dual', 'primal']
    # kernels = ['linear', 'poly', 'rbf', 'sigmoid']
    measures = ['precision', 'recall', 'f1']
    font = {'size'   : 12}
    plt.rc('font', **font)
    paras={'lines.linewidth': 2,'legend.fontsize': 12, 'axes.labelsize': 16, 'legend.frameon': False,'figure.autolayout': True}
    plt.rcParams.update(paras)

    for test in test_name:
        median=[]
        iqr=[]
        #print(x)
        for measure in measures:
            median.append(np.median(performances[test][measure]))
            iqr.append(np.percentile(performances[test][measure], 75) - np.percentile(performances[test][measure], 25))
        X = range(len(measures))
        line, = plt.plot(X, median, marker='o', markersize=12, label=test + ' median')
        plt.plot(X, iqr, linestyle="-.", color=line.get_color(), marker='*', markersize=12, label=test + ' iqr')
    #plt.ylim(-0.1,1.1, )
    #plt.ytext(0.04, 0.5, va='center', rotation='vertical', fontsize=11)
    #plt.text(0.04, 0.5,"Rn (Raw Score)", labelpad=100)
    # plt.title()
    plt.xticks(X, measures)
    plt.ylabel("Performance")
    plt.xlabel("Different Feature Sets and Target Labels")
    plt.legend(bbox_to_anchor=(1.0, 1.25), loc=1, ncol = 3)
    plt.tight_layout()
    fig_path = path(env_dir, 'performance_tree_test_selected.png')
    plt.savefig(fig_path, bbox_inches='tight')
