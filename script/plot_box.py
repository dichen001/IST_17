from prepare_data import data_dir
from os.path import join as path
import plotly
plotly.tools.set_credentials_file(username='dichen001', api_key='czrCH0mQHmX5HLXSHBqS')
import plotly.plotly as py
import plotly.graph_objs as go
import cPickle


env_dir = path(data_dir, 'MT_data', '3rdRun')
details_path = path(env_dir, 'performance_details_tree.p')
details = cPickle.load(open(details_path, 'rb'))
# n1, n2, n3, n4 = 'MS_alone', 'Lit', 'MT-wo-MS', 'Combined'
# t1, t2, t3, t4 = 'Single Feature:\nmergeable_state', 'Quantitative Features:\nLiterature', 'Quanlitative Features:\nMTurk', 'Combination of Qualitat Last Two'
n1, n2, n3 = 'Lit', 'MT-wo-MS', 'Combined'
t1, t2, t3 = 'Quantitative Features\n(From API Mining)', 'Qualitative Features\n(From MTurk Answers)', 'Combined Features\n(Quan. & Qual.)'


#x = ['day 1', 'day 1', 'day 1', 'day 1', 'day 1', 'day 1',
#     'day 2', 'day 2', 'day 2', 'day 2', 'day 2', 'day 2']
l = len(details[n1]['precision'])
# x = [t1] * l + [t2] * l + [t3] * l + [t4] * l
x = [t1] * l + [t2] * l + [t3] * l

Precision = go.Box(
    y = sorted(details[n1]['precision']) + sorted(details[n2]['precision']) + sorted(details[n3]['precision']),
    x=x,
    name='Precision',
    marker=dict(
        color='#3D9970'
    )
)
Recall = go.Box(
    y = sorted(details[n1]['recall']) + sorted(details[n2]['recall']) + sorted(details[n3]['recall']),
    x=x,
    name='Recall',
    marker=dict(
        color='#FF4136'
    )
)
F1 = go.Box(
    y = sorted(details[n1]['f1']) + sorted(details[n2]['f1']) + sorted(details[n3]['f1']),
    x=x,
    name='F1',
    marker=dict(
        color='#FF851B'
    )
)
data = [Precision, Recall, F1]
layout = go.Layout(
    yaxis=dict(
        title='',
        zeroline=False
    ),
    boxmode='group'
)
fig = go.Figure(data=data, layout=layout)
py.iplot(fig)
