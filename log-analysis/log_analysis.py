import json
import sys
import os
import glob
from collections import defaultdict

log_directory=sys.argv[1]
proj_list = os.listdir(log_directory)
failure_type=[]
failure_name_count={}
failure_name_projName=defaultdict(list)
#print(proj_list)
for proj in proj_list:
    for file in glob.glob(log_directory+proj+"/*.json"):
        json_file=file
        #print('json_file='+json_file)
        with open(json_file) as user_file:
            file_contents = user_file.read()
            parsed_json = json.loads(file_contents)
            for i in range(len(parsed_json)-1): # This one is for each job
                jobs=parsed_json['jobs']
                #print('job len='+str(len(job_len)))
                for k in range(len(jobs)):
                    build_name=jobs[k]['name']
                    build_conclusion=jobs[k]['conclusion']
                    #print(build_name)
                    if build_conclusion=="failure" :
                        #print('proj_name='+proj)
                        steps_content=jobs[k]['steps']
                        #print('len='+str(len(steps_content)))

                        for j in range(len(steps_content)):
                            if (steps_content[j]['conclusion'] == "failure"):
                                if not steps_content[j]['name'] in failure_name_count: 
                                    failure_name_count[steps_content[j]['name']]=1
                                    failure_name_projName[steps_content[j]['name']].append(proj)
                                else:
                                    count=failure_name_count[steps_content[j]['name']]
                                    failure_name_count[ steps_content[j]['name'] ] = count + 1
                                    failure_name_projName[steps_content[j]['name']].append(proj)
                                break
print(failure_name_count)
print(failure_name_projName)
                #elif build_conclusion=="skipped" :
