from wavefront_sdk import WavefrontProxyClient


class WfClient(object):
    """
    Class for wavefront-client to send-metrics
    """
    def __init__(self, _proxy_ip):
        self.wf_sender = WavefrontProxyClient(
            host=_proxy_ip,
            metrics_port=2878,
            distribution_port=2878,
            tracing_port=30000,
            event_port=2878
        )

    def send_metric(self, name, value, timestamp, source='ssharat-a02',
                    tags=None):
        if tags:
            print('Sending to wf: name=%s, value=%s, timestamp=%s, source=%s,'
                  'tags=%s' % (name, value, timestamp, source, tags))
            self.wf_sender.send_metric(name=name, value=value, timestamp=timestamp,
                                       source=source, tags=tags)
        else:
            print('Sending to wf: name=%s, value=%s, timestamp=%s, source=%s' % (name, value,
                                                                                 timestamp, source))
            self.wf_sender.send_metric(name=name, value=value, timestamp=timestamp,
                                       source=source, tags={})


def convert_time_to_epoch_msec(_datetime):
    import datetime
    date = _datetime.split(' ')[0].split('-')
    time = _datetime.split(' ')[1].split(':')
    yy, mm, dd = int(date[0]), int(date[1]), int(date[2])
    h, m, s = int(time[0]), int(time[1]), int(time[2])
    return int(datetime.datetime(yy, mm, dd, h, m, s).strftime('%s')) * 1000