"""
Walks directories looking for for .las or .laz files. Outputs a comma
delimited text file with the path to the files it finds. Converts the
files using LASzip and deletes the .las or .laz file after conversion.
Logs progress in the comma delimited text file so you can track progress.
"""

from __future__ import print_function
import csv
import os
import subprocess

# -- Start Inputs ------------------------------------------------------

walkpath = True
LASzip_conversion = True

# Extension/s to search for. This is always a tuple and
# either .las, or .laz
extensions_to_find = (".las")

csv_output = r"\\DEQWQNAS01\Lidar06\las_paths_Lidar06.csv"

# The top level directory or directories where the searching starts. 
# Always a list
workspaces = [r"\\DEQWQNAS01\Lidar06"]
#workspaces = [r"\\DEQWQNAS01\Lidar01",
    #r"\\DEQWQNAS01\Lidar02",
    #r"\\DEQWQNAS01\Lidar03",
    #r"\\DEQWQNAS01\Lidar04",
    #r"\\DEQWQNAS01\Lidar05",
    #r"\\DEQWQNAS01\Lidar06"]

# On windows you need to map server paths to a network drive letter :(
pathletter_dict = {r'\\DEQWQNAS01\Lidar01': r'G:',
                   r'\\DEQWQNAS01\Lidar02': r'H:',
                   r'\\DEQWQNAS01\Lidar03': r'I:',
                   r'\\DEQWQNAS01\Lidar04': r'J:',
                   r'\\DEQWQNAS01\Lidar05': r'K:',
                   r'\\DEQWQNAS01\Lidar06': r'L:',
                   r'\\DEQWQNAS01\Lidar07': r'M:',
                   r'\\DEQWQNAS01\Lidar08': r'N:'}

# directories to ignore when walking
ignore = ["REPORT", "VEC", "SHAP", "ASC", "TIN", "INTEN", "RASTER",
          "BE", "BARE", "HH", "HIGH", "VH", "VEGHT", "DEN",
          "HILLS","HL", "HILSD", "HS", "ORTHO", "PHOTO","TRAJ",
          "RECYCLER", "System Volume Information","Lower_Columbia",
          "USFS_Original","Yamhill_DEQ","Deschutes_from_USFS_old", "XXX"]

# -- End Inputs --------------------------------------------------------

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the data as a list"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader is True: reader.next()
        csvlist = [row for row in reader]
    return(csvlist)

def write_csv(csvlist, csvfile):
    """write the input list to csv"""
    with open(csvfile, "wb") as f:
        writer = csv.writer(f)
        for row in csvlist:
            writer.writerow(row)
            
def execute_cmd(cmd_list, exe, shel):
    """Executes commands to the command prompt using subprocess module.
    Commands must be a string in a list"""
    for cmd in cmd_list:
        print(cmd)    
        proc = subprocess.Popen(cmd, executable=exe, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=shel)
        stdout, stderr = proc.communicate()
        exit_code=proc.wait()
        if exit_code:       
            # Something went wrong
            status = "E"
            print(stderr)
            return (status)
        else:
            print(stdout)
    # Yay! we've reached the end without errors
    status = "X"
    return (status)

if walkpath is True:
    las_list = []
    print("starting to walk")
    for workspace in workspaces:
        for dirpath, dirnames, filenames in os.walk(workspace, topdown=True):
            
            remove_ = []
            print(dirpath)
            for d in dirnames:
                if any(word.upper() in d.upper() for word in ignore):
                    remove_.append(d)
        
            for r in remove_:
                dirnames.remove(r)            
            
            for f in filenames:
                if f.endswith(extensions_to_find):
                    las_list.append(["#", f, os.path.join(dirpath, f)])
                    
    print("writing paths to csv")
    write_csv(las_list, csv_output)
    print("Done walking")

if LASzip_conversion is True:
    n = 0
    las_list = read_csv(csv_output, skipheader=False)
    for row in las_list:
        status = row[0]
        file_name = row[1]
        inpath = row[2]
        inpath_server = inpath[:20]
        inpath_letter = pathletter_dict[inpath_server]
        inpath_temp = inpath.replace(inpath[:20], inpath_letter)
        exe = inpath_letter + "\\laszip.exe"
        # check to see if the file already exists
        las_exists = os.path.isfile(inpath_temp)
        if status is not "X":
            if las_exists is True and status in ["E", "#"]:
                # change to correct drive
                cmd_list = ['{0}'.format(inpath_letter)]
                status = execute_cmd(cmd_list, exe=None, shel=True)
                if status is "E":
                    print("Drive letter error")
                else:
                    # execute laszip
                    cmd_list = ['laszip {0}'.format(inpath_temp)]
                    status = execute_cmd(cmd_list, exe,  shel=False)
                    if status is "E":
                        print("laszip Error")
                    else:
                        # delete the .las file
                        cmd_list = ['del {0}'.format(inpath_temp)]
                        status = execute_cmd(cmd_list, exe=None, shel=True)
                        if status is "E":
                            print("delete error")
                        else:
                            # update the csv file
                            las_list[n][0] = status
                            write_csv(las_list, csv_output)
            else:
                print("Error: " + inpath_temp + " does not exist")
                status = "E"
                las_list[n][0] = status
                write_csv(las_list, csv_output)
        n = n + 1
    print("Done converting from {0}".format(extensions_to_find))
print("Done with script")