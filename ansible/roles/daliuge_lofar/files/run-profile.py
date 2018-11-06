#!/bin/python
#
import psutil
import time
import subprocess
import requests
import json

# Collect statistics
p_sar = subprocess.Popen(["sar", "-A", "-o", "/local/run-profile.sar", "10"])
#dlg unroll-and-partition -L /local/daliuge-logical-graphs/LOFAR\ Pipelines/CALIB.json | dlg map | dlg submit -s daliuge-lofar
#p_dlg_unp = subprocess.Popen(["dlg", "unroll-and-partition", "-L", "/local/daliuge-logical-graphs/LOFAR Pipelines/CALIB.json"], stdout=subprocess.PIPE)
#p_dlg_map = subprocess.Popen(["dlg", "map"], stdin=p_dlg_unp.stdout, stdout=subprocess.PIPE)
#p_dlg_sub = subprocess.Popen(["dlg", "submit", "-s", "daliuge-lofar"], stdin=p_dlg_map.stdout)

# Unroll, partition, map and finally submit the LOFAR Pipeline CALIB.json logical graph.
output = subprocess.check_output("dlg unroll-and-partition -L /local/daliuge-logical-graphs/LOFAR\ Pipelines/CALIB.json | dlg map | dlg submit -s daliuge-lofar", shell=True)

# define some conditions
GRAPH_RUNNING = 3	# From daliuge/manager/session.py-SessionStates
GRAPH_FINISHED = 4	# From daliuge/manager/session.py-SessionStates
GRAPH_FAILED = 5
GRAPH_LEAF_FINISHED = 2	# From daliuge/dlg/ddap-protocol.py-DROPStates and AppDROPStates

url = 'http://localhost:8001/api/sessions/daliuge-lofar/status'
return_status = GRAPH_RUNNING

# While still running, can stop on FINISHED or on our own FAILED
while return_status == GRAPH_RUNNING:
    response = requests.get(url)
    # For successful API call, response code will be 200 (OK)
    if(response.ok):

        # Loading the response data into a dict variable
        jData = json.loads(response.content)

        for key in jData:
            print key + " : "
            print jData[key]
            if (jData[key] != GRAPH_RUNNING and jData[key] != GRAPH_FINISHED):
                return_status = GRAPH_FAILED
            else:
                return_status= jData[key]
    else:
        # If response code is not ok (200), print the resulting http error code with description
        response.raise_for_status()

    time.sleep(5)

print return_status

# Now check state of whole job, don't do anything with this yet though....
url = 'http://localhost:8001/api/sessions/daliuge-lofar/graph/status'
response = requests.get(url)
# For successful API call, response code will be 200 (OK)
if(response.ok):

    # Loading the response data into a dict variable
    jData = json.loads(response.content)

    print("The response contains {0} properties".format(len(jData)))
    print("\n")
    for key in jData:
        print key + " : "
        print jData[key]
else:
    # If response code is not ok (200), print the resulting http error code with description
    response.raise_for_status()


# Now dones, terminate the sar process started above after waiting for final stats
time.sleep(10)
p_sar.terminate()

# Terminante the sadc process started by sar
for process in psutil.process_iter():
    path = process.cmdline()
    if 'sadc' in path:
        print('Process sadc found, will now terminate.')
        process.terminate()
        break
else:
    print('Process sadc not found.')

# Delay before exit for everything to finish up
time.sleep(2)
