import json
import pandas as pd
import re
import time

from common import WfClient, convert_time_to_epoch_msec
from datetime import datetime


# Pre-defines
file_path = '/Users/ssharat/Downloads/formattedOutput.json'
proxy_ip = '10.62.106.23'
aggregate_tables = ['CustomerReport.sheets.MonthlyMaxAppInstancesbyFoundation',
                    'CustomerReport.sheets.MonthlyMaxServiceInstancesbyFoundation',
                    'CustomerReport.sheets.EnvironmentInformationReview']
f = open(file_path)
data = json.load(f)


def month_year_from_date(_datetime):
    import datetime
    _tmp = _datetime.split()[0].split('/')
    _m, _y = _tmp[0], _tmp[2]
    datetime_obj = datetime.datetime.strptime(_m, '%m')
    _mm = datetime_obj.strftime('%b')
    return _mm + '-' + _y


def month_number_from_name(month_name):
    import datetime
    return datetime.datetime.strptime(month_name, '%B').month


if __name__ == '__main__':
    wf_client = WfClient(proxy_ip)
    # Since it's nested json we will use normalize to read data
    ver_dict = {}
    for metric_name in data:
        metric_name_wf = re.sub('-', '.', metric_name.lower())
        df = pd.json_normalize(data[metric_name])
        # Replace all NA/null values with zero for consistency
        df = df.replace('', '0')
        cols = list(df.columns)

        for row in df.iterrows():
            now = datetime.now()
            now_msec = convert_time_to_epoch_msec(now.strftime("%Y-%m-%d %H:%M:%S"))
            tags_dict = {}
            val = '0'
            for _row, col in zip(row[1].values, cols):
                if re.search('^[1-9]\\d*(\\.\\d+)?$', _row) and not re.search('[Yy]ear', col):
                    val = str(_row)
                tags_dict[col] = _row
            # print('%s, my.tableau.%s, %s, tags=%s' % (now_msec, metric_name_wf, val, tags_dict))
            # Aggregate functions
            if metric_name == 'CustomerReport.sheets.EnvironmentInformationReview':
                if tags_dict['Pivnet Slug'] == 'ops-manager':
                    ver = tags_dict['Max. Product Version Patch']
                    if ver in ver_dict.keys():
                        ver_dict[ver] += 1
                    else:
                        ver_dict[ver] = 1

            if metric_name == 'CustomerReport.sheets.MonthlyMaxAppInstancesbyFoundation':
                _date = tags_dict['Month of Date'].split('/')
                _date_msec = convert_time_to_epoch_msec("%s-%s-%s 01:01:01" % (_date[2], _date[0], _date[1]))
                # print('%s, my.tableau.agg.max.app.instances, %s, tags=%s' % (_date_msec,
                #                                                             tags_dict['Maximum App Instances'],
                #                                                             {'Environment': tags_dict['Environment']
                #                                                              }))
                wf_client.send_metric(name='my.tableau.agg.max.app.instances', value=tags_dict['Maximum App Instances'],
                                      timestamp=_date_msec, tags={'Environment': tags_dict['Environment']})

            if metric_name == 'CustomerReport.sheets.MonthlyMaxServiceInstancesbyFoundation':
                _month, _year = tags_dict['Month of Date'], tags_dict['Year of Date']
                _date_msec = convert_time_to_epoch_msec("%s-%s-01 01:01:01" % (_year, month_number_from_name(_month)))
                # print('%s, my.tableau.agg.max.service.instances, %s, tags=%s' % (_date_msec,
                #                                                                 tags_dict['Maximum Instances'],
                #                                                                 {'Environment':tags_dict['Environment']
                #                                                                  }))
                wf_client.send_metric(name='my.tableau.agg.max.service.instances', value=tags_dict['Maximum Instances'],
                                      timestamp=_date_msec, tags={'Environment': tags_dict['Environment']})

            wf_client.send_metric(name='my.tableau.%s' % metric_name_wf, value=val,
                                  timestamp=now_msec, tags=tags_dict)
            time.sleep(1)

        if metric_name == 'CustomerReport.sheets.EnvironmentInformationReview':
            for ver in ver_dict:
                # print('%s, my.tableau.agg.ops.manager.versions, %s, tags=%s' % (now_msec, ver_dict[ver],
                #                                                                {'version': ver}))
                wf_client.send_metric(name='my.tableau.agg.ops.manager.versions', value=ver_dict[ver],
                                      timestamp=now_msec, tags={'version': ver})

        if metric_name == 'CustomerReport.sheets.TileUpgrades-Last30Days':
            df['Month-Year'] = [month_year_from_date(date) for date in df['Installation Start Time']]
            grouped_pd_series = df.groupby(['Month-Year', 'Environment'])['Installation Status'].count()
            grouped_pd_dict = grouped_pd_series.to_dict()
            for key in grouped_pd_dict:
                # print('%s, my.tableau.agg.tileupgrades.count, %s, tags=%s' %(now_msec, grouped_pd_dict[key],
                #                                                             {'Month': key[0], 'Environment': key[1]}))
                wf_client.send_metric(name='my.tableau.agg.tileupgrades.count', value=grouped_pd_dict[key],
                                      timestamp=now_msec, tags={'Month': key[0], 'Environment': key[1]})
        print(df.shape)
        print('----')

