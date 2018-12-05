#!/usr/bin/python
__author__ = 'nitishgoyal13'

import sys
import requests
import json
import math
import time

#marathon_host = input("Enter the DNS hostname or IP of your Marathon Instance : ")
#marathon_app = input("Enter the Marathon Application Name to Configure Autoscale for from the Marathon UI : ")
#max_request_p95_time = int(input("Enter the Max percent of Mem Usage averaged across all Application Instances to trigger Autoscale out(ie. 80) : "))
#max_threadpool_utilization = int(input("Enter the Max percent of CPU Usage averaged across all Application Instances to trigger Autoscale out(ie. 80) : "))
#out_trigger_mode = input("Enter which metric(s) to trigger Autoscale out('and', 'or') : ")
#down_trigger_mode = input("Enter which metric(s) to trigger Autoscale down('and', 'or') : ")
#autoscale_multiplier = float(input("Enter Autoscale multiplier for triggered Autoscale (ie 1.5) : "))
#max_instances = int(input("Enter the Max instances that should ever exist for this application (ie. 20) : "))
#min_request_p95_time = int(input("Enter the Min percent of Mem Usage averaged across all Application Instances to trigger Autoscale down(ie. 40) : "))
#min_threadpool_utilization = int(input("Enter the Min percent of CPU Usage averaged across all Application Instances to trigger Autoscale down(ie. 40) : "))
#min_instances = int(input("Enter the Min instances that should ever less for this application (ie. 2) : "))
#check_sec = int(input("Enter the check second (ie. 30) : "))

marathon_host = '10.84.199.144'
marathon_app = 'foxtrot-0-5-4-6-query-67'  #http://marathon_host:8080/v2/apps
max_request_p95_time = 0.300
max_threadpool_utilization = 0.7
out_trigger_mode = 'or'
down_trigger_mode = 'or'
autoscale_multiplier = 1.5
max_instances = 8
min_request_p95_time = 0.100
min_threadpool_utilization = 0.3
min_instances = 3
check_sec = 30


class Marathon(object):

    def __init__(self, marathon_host):
        self.name = marathon_host
        self.uri=("http://"+marathon_host+":8080")

    def get_all_apps(self):
        response = requests.get(self.uri + '/v2/apps').json()
        if response['apps'] ==[]:
            print ("No Apps found on Marathon")
            sys.exit(1)
        else:
            apps=[]
            for i in response['apps']:
                appid = i['id'].strip('/')
                apps.append(appid)
            print ("Found the following App LIST on Marathon =", apps)
            self.apps = apps # TODO: declare self.apps = [] on top and delete this line, leave the apps.append(appid)
            return apps

    def get_app_details(self, marathon_app):
        response = requests.get(self.uri + '/v2/apps/'+ marathon_app).json()
        if (response['app']['tasks'] ==[]):
            print ('No task data on Marathon for App !', marathon_app)
        else:
            app_instances = response['app']['instances']
            self.appinstances = app_instances
            print(marathon_app, "has", self.appinstances, "deployed instances")
            app_task_dict={}
            adminPort_dict={}
            for i in response['app']['tasks']:
                taskid = i['id']
                hostid = i['host']
                adminPort = i['ports'][1]
                print ('DEBUG - taskId=', taskid +' running on '+ hostid)
                app_task_dict[str(taskid)] = str(hostid) + ":" + str(adminPort)
                adminPort_dict[str(taskid)] = str(adminPort)
            return app_task_dict

    def scale_out_app(self,marathon_app,autoscale_multiplier):
        target_instances_float=self.appinstances * autoscale_multiplier
        target_instances=math.ceil(target_instances_float)
        if (target_instances > max_instances):
            print("Reached the set maximum instances of", max_instances)
            target_instances=max_instances
        else:
            target_instances=target_instances
        data ={'instances': target_instances}
        json_data=json.dumps(data)
        headers = {'Content-type': 'application/json'}
        response=requests.put(self.uri + '/v2/apps/'+ marathon_app,json_data,headers=headers)
        print ('Scale_out_app return status code =', response.status_code)
        
    def scale_down_app(self,marathon_app,autoscale_multiplier):
        target_instances_float=self.appinstances / autoscale_multiplier
        target_instances=math.ceil(target_instances_float)
        if (target_instances < min_instances):
            print("Reached the set minmum instances of", min_instances)
            target_instances=min_instances
        else:
            target_instances=target_instances
        data ={'instances': target_instances}
        json_data=json.dumps(data)
        headers = {'Content-type': 'application/json'}
        response=requests.put(self.uri + '/v2/apps/'+ marathon_app,json_data,headers=headers)
        print ('Scale_down_app return status code =', response.status_code)

def get_task_agentstatistics(task, host):
    # Get the performance Metrics for all the tasks for the Marathon App specified
    # by connecting to the Mesos Agent and then making a REST call against Mesos statistics
    # Return to Statistics for the specific task for the marathon_app
    response = requests.get('http://'+host + ':5051/monitor/statistics.json').json()
    #print ('DEBUG -- Getting Mesos Metrics for Mesos Agent =',host)
    for i in response:
        executor_id = i['executor_id']
        #print("DEBUG -- Printing each Executor ID ", executor_id)
        if (executor_id == task):
            task_stats = i['statistics']
            # print ('****Specific stats for task',executor_id,'=',task_stats)
            return task_stats


def get_task_metrics(host):
    # Get the performance Metrics for all the tasks for the Marathon App specified
    # by connecting to the Mesos Agent and then making a REST call against Mesos statistics
    # Return to Statistics for the specific task for the marathon_app
    return requests.get('http://'+host + '/metrics.json').json()

def timer():
    print("Successfully completed a cycle, sleeping for ",check_sec," seconds...")
    time.sleep(check_sec)
    return

if __name__ == "__main__":
    print ("This application tested with Python3 only")
    running=1
    while running == 1:
        # Initialize the Marathon object
        aws_marathon = Marathon(marathon_host)
        # Call get_all_apps method for new object created from aws_marathon class and return all apps
        marathon_apps = aws_marathon.get_all_apps()
        print ("The following apps exist in Marathon...", marathon_apps)
        # Quick sanity check to test for apps existence in MArathon.
        if (marathon_app in marathon_apps):
            print ("  Found your Marathon App=", marathon_app)
        else:
            print ("  Could not find your App =", marathon_app)
            sys.exit(1)
        # Return a dictionary comprised of the target app taskId and hostId.
        app_task_dict = aws_marathon.get_app_details(marathon_app)
        print ("    Marathon  App 'tasks' for", marathon_app, "are=", app_task_dict)

        app_threadpool_values = []
        app_request_p95_values = []
        for task,host in app_task_dict.items():
            #cpus_time =(task_stats['cpus_system_time_secs']+task_stats['cpus_user_time_secs'])
            #print ("Combined Task CPU Kernel and User Time for task", task, "=", cpus_time)

            # Compute Threads Usage
            task_metrics = get_task_metrics(host)
            thread_pool_utilization = (task_metrics['gauges']['org.eclipse.jetty.util.thread.QueuedThreadPool.dw.utilization']['value'])

            time.sleep(1)

            requests_p95 = (task_metrics['timers']['io.dropwizard.jetty.MutableServletContextHandler.requests']['p95'])

            # Thread pool percentage usage
            app_threadpool_values.append(thread_pool_utilization)

            # Requests time value
            app_request_p95_values.append(requests_p95)

            print ("task", task, "thread_pool_utilization Utilization=", thread_pool_utilization)
            print ("task", task, "requests_p95 Utilization=", requests_p95)
            print()

        # Normalized data for all tasks into a single value by averaging
        app_avg_threadpool_utilization = (sum(app_threadpool_values) / len(app_threadpool_values))
        print ('Current Average  CPU Time for app', marathon_app, '=', app_avg_threadpool_utilization)
        app_avg_requests_p95_time=(sum(app_request_p95_values) / len(app_request_p95_values))
        print ('Current Average Mem Utilization for app', marathon_app,'=', app_avg_requests_p95_time)
        #Evaluate whether an autoscale trigger is called for
        print('\n')
        if (out_trigger_mode == "and"):
            if (app_avg_threadpool_utilization > max_threadpool_utilization) and (app_avg_requests_p95_time > max_request_p95_time):
                print ("Autoscale out triggered based on 'both' Mem & CPU exceeding threshold")
                aws_marathon.scale_out_app(marathon_app, autoscale_multiplier)
            else:
                print ("Both values were not greater than autoscale up targets")
        elif (out_trigger_mode == "or"):
            if (app_avg_threadpool_utilization > max_threadpool_utilization) or (app_avg_requests_p95_time > max_request_p95_time):
                print ("Autoscale out triggered based Mem 'or' CPU exceeding threshold")
                aws_marathon.scale_out_app(marathon_app, autoscale_multiplier)
            else:
                print ("Neither Mem 'or' CPU values exceeding threshold")
        
        if (down_trigger_mode == "and"):
            if (app_avg_threadpool_utilization < min_threadpool_utilization) and (app_avg_requests_p95_time < min_request_p95_time):
                print ("Autoscale out triggered based Mem 'or' CPU exceeding threshold")
                aws_marathon.scale_down_app(marathon_app, autoscale_multiplier)
            else:
                print ("Neither Mem 'or' CPU values exceeding threshold")
        elif(down_trigger_mode == "or"):
            if (app_avg_threadpool_utilization < min_threadpool_utilization) or (app_avg_requests_p95_time < min_request_p95_time):
                print ("Autoscale out triggered based Mem 'or' CPU exceeding threshold")
                aws_marathon.scale_down_app(marathon_app, autoscale_multiplier)
            else:
                print ("Neither Mem 'or' CPU values exceeding threshold")
        timer()
