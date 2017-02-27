import json, itertools
from os.path import join as path
from prepare_data import data_dir
from csv_processing import CSV_PROC


upper = """
<html>
<body>
 <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>

<div id="sankey_multiple" style="width: 900px; height: 300px;"></div>

<script type="text/javascript">
  google.charts.load("current", {packages:["sankey"]});
  google.charts.setOnLoadCallback(drawChart);
   function drawChart() {
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'From');
    data.addColumn('string', 'To');
    data.addColumn('number', 'Weight');

    data.addRows([\n"""

lower = """
 \n]);

    // Set chart options
    var colors = ['#a6cee3', '#b2df8a', '#fb9a99', '#fdbf6f',
                  '#cab2d6', '#ffff99', '#1f78b4', '#33a02c'];

    var options = {
      width: 1200,
      height: 600,
      sankey: {
        node: {
          width: 20,
          colors: colors,
          label: { fontName: 'Times-Roman',
                         fontSize: 16,
                         color: '#871b47',
                         bold: true,
                         italic: true }
        },
        link: {
          colorMode: 'gradient',
          colors: colors
        }
      }
    };

    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.Sankey(document.getElementById('sankey_multiple'));
    chart.draw(data, options);
   }
</script>
</body>
</html>

"""


def getJson4Sankey(orders, answer_csv, output_json):
    links = []
    answers = C.getDictFromCsv(answer_csv)
    n = len(answers[answers.keys()[0]])
    for i in range(len(orders) - 1):
        start = orders[i]
        dest = orders[i+1]
        for s in start.keys():
            for d in dest.keys():
                if d in ['Merged', 'Rejected']:
                    d_target = 'FALSE' if d == 'Rejected' else 'TRUE'
                else:
                    d_target = '0' if d.startswith('No') else '1'
                s_target = '0' if s.startswith('No') else '1'

                s_key = start[s]
                d_key = dest[d]
                weight = len([i for i in range(n) if answers[s_key][i] == s_target and answers[d_key][i] == d_target])
                links.append([s, d, weight])
    return links

if __name__ == '__main__':
    C = CSV_PROC()


    j_path = path(data_dir, 'MT_data', 'template.json')

    j_file = open(j_path, 'r')
    j_data = json.load(j_file)

    result = 'merged'
    L1 = {'Support From Cores': 'F_Q1_core_s', 'Support From Externals': 'F_Q1_other_s', \
          'Alternate from Cores': 'F_Q2_a_core', 'Alternate from Externals': 'F_Q2_a_other',\
          'No Support': 'F_Q1_support', 'No Alternate': 'F_Q2_alternate'}

    L2 = {'Dis-Solution: Bug': 'F_Q3_dis_s_bug', 'Disapprove Solution: Consitency': 'F_Q3_dis_s_constc', 'Disapprove Solution: Need Improve': 'F_Q3_dis_s_improve', \
          'Dis-Problem: Not Fit': 'F_Q4_dis_p_nf', 'Dis-Problem: No Value': 'F_Q4_dis_p_nv', \
          'No Dis-Solution': 'F_Q3_dis_s', 'No Dis-Problem': 'F_Q4_dis_p'}

    L = {'Support From Cores': 'F_Q1_core_s', 'Support From Externals': 'F_Q1_other_s', \
          'Alternate from Cores': 'F_Q2_a_core', 'Alternate from Externals': 'F_Q2_a_other',\
          'No Support': 'F_Q1_support', 'No Alternate': 'F_Q2_alternate',\
          'Dis-Solution: Bug': 'F_Q3_dis_s_bug', 'Disapprove Solution: Consitency': 'F_Q3_dis_s_constc', 'Disapprove Solution: Need Improve': 'F_Q3_dis_s_improve', \
          'Dis-Problem: Not Fit': 'F_Q4_dis_p_nf', 'Dis-Problem: No Value': 'F_Q4_dis_p_nv', \
          'No Dis-Solution': 'F_Q3_dis_s', 'No Dis-Problem': 'F_Q4_dis_p'
         }

    Q1 = {'Support': 'F_Q1_support', 'No Support': 'F_Q1_support'}
    Q1_details = {'Support From Cores': 'F_Q1_core_s', 'Support From Externals': 'F_Q1_other_s', 'No Support': 'F_Q1_support'}
    Q2 = {'Alternate Solution': 'F_Q2_alternate', 'No Alternate Solution': 'F_Q2_alternate'}
    Q2_details = {'Alternate from Cores': 'F_Q2_a_core', 'Alternate from Externals': 'F_Q2_a_other', 'No Alternate': 'F_Q2_alternate'}
    Q3 = {'Disapprove Solution': 'F_Q3_dis_s', 'No Disapprove Solution': 'F_Q3_dis_s'}
    Q3_details = {'Dis-Solution: Bug': 'F_Q3_dis_s_bug', 'Dis-Solution: Consitency': 'F_Q3_dis_s_constc', 'Dis-Solution: Need Improve': 'F_Q3_dis_s_improve', 'No Dis-Solution': 'F_Q3_dis_s'}
    Q4 = {'Disapprove Problem': 'F_Q4_dis_p', 'No Disapprove Problem': 'F_Q4_dis_p'}
    Q4_details = {'Dis-Problem: Not Fit': 'F_Q4_dis_p_nf', 'Dis-Problem: No Value': 'F_Q4_dis_p_nv', 'No Dis-Problem': 'F_Q4_dis_p'}
    R = {'Merged': 'merged', 'Rejected': 'merged'}
    general = [Q1, Q2, Q3, Q4, R]
    details = [Q1_details, Q2_details, Q3_details, Q4_details, R]
    # details = [L1, L2, R]

    answer_csv = path(data_dir, 'MT_data', '2&3', 'combined2&3.csv')
    output_json = path(data_dir, 'MT_data', '2&3', 'json4sankey.json')


    name = 'all2one'
    links = getJson4Sankey([L1, L2, R], answer_csv, output_json)
    figure_path = path(data_dir, 'figures', name + '.html')
    content = upper + '        ' + str(links)[1:-1] + lower
    print  content
    with open(figure_path, "w") as f:
        f.write(content)


    order = [Q1_details, Q2_details, Q3_details, Q4_details]
    for arrangesment in itertools.permutations([0,1,2,3]):
        this_order, name = [], []
        for i in arrangesment:
            this_order.append(order[i])
            name.append(str(i+1))
        this_order.append(R)
        name = '-'.join(name)
        links = getJson4Sankey(this_order, answer_csv, output_json)

        figure_path = path(data_dir, 'figures', name + '.html')
        content = upper + '        ' + str(links)[1:-1] + lower
        print  content
        with open(figure_path, "w") as f:
            f.write(content)
        print name

    print 'done'
