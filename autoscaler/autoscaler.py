#!/usr/bin/python
import requests
import json
import math
import time
import datetime

marathonAddress = 'http://localhost:8080'
influxdbAddress = 'http://influxdb.domain:8086'
influxdbUsername = 'r'
influxdbPassword = ''
influxdbDatabase = ''

events = {}

# Check all apps and apply scaling if necessary to apps which have autoscaling enabled
def get_apps():
    response=requests.get(marathonAddress + '/v2/apps').json()
    for app in response['apps']:
        if 'autoscale' in app['env']:
            if app['env']['autoscale'] == 'true':
                print ' Considering',app['id']
                minInstances = int(app['env']['autoscale_min_instances'])
                maxInstances = int(app['env']['autoscale_max_instances'])
                for env in app['env']:
                    if 'autoscale_rule' in env:
                        name = env.replace('autoscale_rule_','')
                        apply_scale_rule(name, app['id'], minInstances, maxInstances, app['env'][env])
 
# Apply autoscale rule
def apply_scale_rule(name, app, minInstances, maxInstances, rule):
    rule = rule.replace(" ", "").split("|")

    currentInstances = get_app(app)
    dbMeasurement = rule[0]
    dbValue = rule[1]
    if rule[2] == 'target':
        target = int(rule[3])
        trigger = rule[4]
        backoff = int(rule[5])
        factor = int(rule[6])

        currentValue = query_db(dbMeasurement, dbValue, app, trigger)
        ideal = int(round(currentValue*currentInstances/target))

        if ideal < minInstances:
            ideal = minInstances
        if ideal > maxInstances:
            ideal = maxInstances

        if app not in events:
            events[app] = 0

        if currentInstances < ideal and time.time() - events[app] > backoff:
            print ' ',app,': Scaling up to',ideal,'instances from',currentInstances,'instances','due to target from rule',name,'( target=',target,'current=',currentValue,')'
            events[app] = time.time()
            scale_app(app, ideal)
        elif currentInstances > ideal and time.time() - events[app] > backoff*factor:
            print ' ',app,': Scaling down to',ideal,'instances from',currentInstances,'instances','due to target from rule',name,'( target=',target,'current=',currentValue,')'
            events[app] = time.time()
            scale_app(app, ideal)
        else:
            print ' ',app,': Not scaling'

# Query InfluxDB
def query_db(measurement, value, app, trigger):
    appName = gen_name(app)
    query = "/query?db=" + influxdbDatabase + "&q=SELECT MEAN(" + value + ") FROM " + measurement + " WHERE app = '" + appName + "' AND time > now() - " + trigger + "s fill(0)"
    try:
        r = requests.get(influxdbAddress + query, auth=(influxdbUsername, influxdbPassword))
        data = r.json()
        results = data['results']
    except:
        print 'Unable to query InfluxDB'
    return results[0]['series'][0]['values'][0][1]

# Generate application name to be consistent with task name
# (app name in InfluxDB is based on the task name)
def gen_name(app):
    app = app.split('/')
    if len(app) > 2:
       app = app[2] + '.' + app[1]
    else:
       app  = app[1]
    return app

# Get current number of instances
def get_app(marathon_app):
    response=requests.get(marathonAddress + '/v2/apps/' + marathon_app).json()
    app_instances=response['app']['instances']
    return app_instances

# Scale application
def scale_app(marathon_app, instances):
    data = {'instances': instances}
    json_data = json.dumps(data)
    headers = {'Content-type': 'application/json'}
    response = requests.put(marathonAddress + '/v2/apps/'+ marathon_app, json_data, headers=headers)

if __name__ == "__main__":
    while 1 == 1:
        print datetime.datetime.now(),'Checking apps'
        get_apps()
        time.sleep(60)

