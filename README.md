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

Environment variables are used in the Marathon application specification to specify autoscaling rules. Example environment variables:
* "autoscale": "true"
* "autoscale_min_instances": "2"
* "autoscale_max_instances": "8"
* "autoscale_rule_memory": "memory | total | target | 1000 | 180 | 120"

In this example autoscaling is enabled with a minimum of 2 instances and maximum of 8 instances.
The metrics for the rule `memory` are obtained from the field `total` from the `memory` measurement in the InfluxDB database.
A target value of `1000` averaged across all instances over the past 180s is used. After scaling it backs off for 120s.
