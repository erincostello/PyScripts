"""
This script initiates mulitple heat source solar models
"""

import subprocess
import csv
from os.path import dirname, exists, join, realpath, abspath
from heatsource9 import BigRedButton

# This is the csv file that summarize the path 
# to each model simulation folder
model_dir = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Heat_Source\02_SitePotential\model_directory.csv"

def write_csv(csvlist, csvfile):
    """Write the input list to csv"""

    with open(csvfile, "wb") as f:
        writer = csv.writer(f)
        for row in csvlist:
            writer.writerow(row)

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the data as a list"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader is True: reader.next()
        csvlist = [row for row in reader]
    return(csvlist)

def execute_cmd(cmd_list, exe, shel):
    """Executes commands to the command prompt using subprocess module.
    Commands must be a string in a list"""
    for cmd in cmd_list:
        print(cmd)    
        proc = subprocess.Popen(cmd, executable=exe, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=shel)
        stdout, stderr = proc.communicate()
        exit_code=proc.wait()
        
        if exit_code or "Synopsis:" in stdout:       
            # Something went wrong
            status = "Error"
            print(stderr)
            return (status)
        else:
            print(stdout)
    # Yay! we've reached the end without errors
    status = "Complete"
    return (status)


model_list = read_csv(model_dir, skipheader=False)
control_file = 'HeatSource_Control.csv'

for i, model in enumerate(model_list):
    if i == 0 or model[2] == "Complete":
        continue
    
    inputdir = model[1]
    python_script = inputdir + '\HS9_Run_Solar_Only.py'
    model_name = model[0]
    
    # change to correct drive
    cmd_list = ['{0}'.format('C:')]
    status = execute_cmd(cmd_list, exe=None, shel=True)
    
    if status == "Error":
        print("Drive letter error")
    else:        
        # run model
        cmd_list = ['python {0}'.format(python_script)]
        status = execute_cmd(cmd_list, exe=None,  shel=True)
        if status == "Error":
            print("Model error in {0}".format(model_name))    
        
    model_list[i][2] = status
    write_csv(model_list, model_dir)


