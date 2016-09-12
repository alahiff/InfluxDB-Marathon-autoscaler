# InfluxDB-Marathon-autoscaler
Simple preliminary version of an autoscaler for Marathon using metrics from InfluxDB. Inspired by https://github.com/tendrilinc/marathon-autoscaler.
Resource metrics (CPU, memory, network, diskio etc) as well as application metrics from cAdvisor can be used.

How it works:
* A metrics collector is run on each Mesos agent. This queries cAdvisor and the local Mesos agent API and inserts metrics into InfluxDB tagged by the Mesos application name and task ID. Any labels which have been added to applications are also included as tags.
* An autoscaling script regularly queries Marathon and searches for any applications which have special environment variables defined which specify autoscaling rules. It then makes use of metrics from InfluxDB in order to decide whether to scale each application.

Prerequisites:
* Requires cAdvisor to be running on each Mesos agent.

Setup:
* Put `metrics-collector/metrics-influxdb-mesos-tasks` into `/usr/local/bin` on each Mesos agent
* Put `metrics-collector/influxdb-mesos-tasks.config` into `/usr/local/etc` on each Mesos agent and update the InfluxDB connection details as appropriate
* Setup a cron on each Mesos agent to run `/usr/local/bin/metrics-influxdb-mesos-tasks` every minute on each Mesos agent
* Adjust the InfluxDB and Marathon connection details in `autoscaler/autoscaler.py` and run the script on a host with access to the Marathon API

Environment variables are used in the Marathon application specification to specify autoscaling rules (Marathon labels are not used because they appear on the main page of the Marathon UI). Example environment variables:
* "autoscale": "true"
* "autoscale_min_instances": "2"
* "autoscale_max_instances": "8"
* "autoscale_rule_requests": "http | requests | target | 1000 | 180 | 120 | 4"

In this example autoscaling is enabled with a minimum of 2 instances and maximum of 8 instances.
The metrics for the rule `requests` are obtained from the field `requests` from the `http` measurement in the InfluxDB database.
A target value of `1000` averaged across all instances over the past `180s` is used. After scaling it backs off for at least `120s` - it can scale up again after `120s` but will only scale down after 480s (`120s` multiplied by `4`). This additional backoff time before downscaling is to ensure that the autoscaler won't scale up and down too frequently if the metric is varying frequently.

Multiple rules can be specified for each application but in each iteration an application can only be scaled once and cannot be scaled again until the backoff time period expires.
