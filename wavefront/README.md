# Useful scripts when working with Wavefront SDKs or APIs.

The high level understanding of the Wavefront platform is that it can ingest data from any source in a time-series format:
> \<time-in-epoch\> \<metric-name\> \<metric-value\> \<tags\> \<source\>

Example:
> self.wf_sender.send_metric(name=name, value=value, timestamp=timestamp,
>                                       source=source, tags={})


Once the data is in Wavefront (verify from Browse -> Metrics), you can create Dashboards, Sections, Charts using the WQL/ts().


## wf_json_to_dashboard.py
```
- Example of how you can unpack JSON and translate it to time-series for wavefront
- Use wf-sdk to send data to wavefront
```

## common.py
```
 - Common methods/classes useful for other scripts
```

## wf_twitter_dashboard.py
```
- Example of fetching twitter data (using twitter API) based on hash-tag/topic, cleaning data and extracting sentiment (using NLTK libs)
- Translate to time-series 
- Use wf-sdk to send data to wavefront
```

## deploy_acme.py
```
 - Script to deploy the ACME fitness app 
```

## wf_query_dashboard.py
```
- ts/WQL analytics - time taken to run queries under dashboards/charts
- Use wavefront-api to query from wavefront
- Use wf-sdk to send data to wavefront
```

## wfcli_examples.txt
```
- Simple usage of wfcli/getting started. Refer:
  https://sysdef.xyz/article/wavefront-cli
```

## chaos.py
```
- Simple scheduler to create & clear chaos (trigger chaos-monkey)
```

NOTE - For wf-sdk reference see:
https://docs.wavefront.com/wavefront_sdks.html

