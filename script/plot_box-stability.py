from prepare_data import data_dir
from os.path import join as path
import plotly
plotly.tools.set_credentials_file(username='dichen001', api_key='czrCH0mQHmX5HLXSHBqS')
import plotly.plotly as py
import plotly.graph_objs as go
import cPickle


env_dir = path(data_dir, 'MT_data')
details_path = path(env_dir, 'stability_details.p')
details = cPickle.load(open(details_path, 'rb'))
# n1, n2, n3, n4 = 'MS_alone', 'Lit', 'MT-wo-MS', 'Combined'
# t1, t2, t3, t4 = 'Single Feature:\nmergeable_state', 'Quantitative Features:\nLiterature', 'Quanlitative Features:\nMTurk', 'Combination of Qualitat Last Two'
n1, n2 = '15(merged):5(rejected)', '87(merged):29(rejected)'
t1, t2 = 'TDH(15:5) vs Crowd(15:5)', 'TDH(15:5) vs Crowd(87:29)'


#x = ['day 1', 'day 1', 'day 1', 'day 1', 'day 1', 'day 1',
#     'day 2', 'day 2', 'day 2', 'day 2', 'day 2', 'day 2']
l = len(details[n1][0])
# x = [t1] * l + [t2] * l + [t3] * l + [t4] * l
x = [t1] * l + [t2] * l

Q1 = go.Box(
    y = sorted(details[n1][0]) + sorted(details[n2][0]),
    x=x,
    name='Q1',
    marker=dict(
        color='#3D9970'
    )
)
Q2 = go.Box(
    y = sorted(details[n1][1]) + sorted(details[n2][1]),
    x=x,
    name='Q2',
    marker=dict(
        color='#FF4136'
    )
)
Q3 = go.Box(
    y = sorted(details[n1][2]) + sorted(details[n2][2]),
    x=x,
    name='Q3',
    marker=dict(
        color='#FF851B'
    )
)
Q4 = go.Box(
    y = sorted(details[n1][3]) + sorted(details[n2][3]),
    x=x,
    name='Q4',
    marker=dict(
        color='#17BECF'
    )
)
data = [Q1, Q2, Q3, Q4]
layout = go.Layout(
    yaxis=dict(
        title='',
        zeroline=False
    ),
    boxmode='group'
)
fig = go.Figure(data=data, layout=layout)
py.iplot(fig)
