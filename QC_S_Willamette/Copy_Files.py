'''
Copies files into the model folders

'''

import os
import shutil
import csv

copy_file = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Site_Potential\lccodes_site_potential.csv"
model_dir = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Heat_Source\02_SitePotential\model_directory.csv"

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the data as a list"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader is True: reader.next()
        csvlist = [row for row in reader]
    return(csvlist)

model_list = read_csv(model_dir, skipheader=False)

for i, model in enumerate(model_list):
    if i == 0:
        continue
    
    dir_model = model[1]
    dir_inputs = os.path.join(dir_model, "inputs")

    shutil.copy(copy_file, dir_inputs)
    
print "done"