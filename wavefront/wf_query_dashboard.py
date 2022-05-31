import pdb
import re
import wavefront_api_client as wave_api

from common import WfClient, convert_time_to_epoch_msec
from datetime import datetime

base_url = ''
api_key = ''
proxy_ip = '10.212.155.104'
HOUR_MSEC = 60 * 60 * 1000
config = wave_api.Configuration()
config.host = base_url
client = wave_api.ApiClient(configuration=config, header_name='Authorization', header_value='Bearer ' + api_key)


# Driver code
if __name__ == "__main__":
    query_api = wave_api.QueryApi(client)

    # Pull wql from chart/dashboard
    dash_api = wave_api.DashboardApi(client)
    dashboard_id = 'Prediction-AD'

    get_dashboard = dash_api.get_dashboard(dashboard_id)

    # Setup a wf client using wf-sdk
    wf_client = WfClient(proxy_ip)

    for section in get_dashboard.response.sections:
        for row in section.rows:
            for chart in row.charts:
                # Create a db with chart vars and ts queries
                ts_db = {}
                for src in chart.sources:
                    api_response = None
                    now = datetime.now()
                    epoch_msec = convert_time_to_epoch_msec(now.strftime("%Y-%m-%d %H:%M:%S"))
                    # Sequence assumes first query is always ts() - not scoping for
                    # derived metrics, in which case first query is a variable
                    if re.search('ts', src.query):
                        print('Making query: %s %s %s' % (src.query, epoch_msec - HOUR_MSEC, 'm'))
                        api_response = query_api.query_api(src.query, epoch_msec - HOUR_MSEC, 'm')
                        ts_db[src.name] = src.query
                    else:
                        # Replace the var with ts()
                        for var in ts_db:
                            if re.search('\\${%s}' % var, src.query):
                                src_query = src.query.replace('${%s}' % var, ts_db[var])
                                print('Making query: %s %s %s' % (src_query, epoch_msec - HOUR_MSEC, 'm'))
                                api_response = query_api.query_api(src_query, epoch_msec - HOUR_MSEC, 'm')
                                ts_db[src.name] = src_query
                                break
                    if api_response is not None:
                        # Send metric
                        print('\t Send metric for chart: %s, query: %s, value: %s to wavefront' % (chart.name, src.query,
                                                                                                api_response.stats.latency))
                        wf_client.send_metric(name='my.query.stats.latency', value=api_response.stats.latency,
                                              timestamp=epoch_msec, tags={'query': src.query, 'chart': chart.name})
