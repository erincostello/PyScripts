from __future__ import print_function
import csv
import os
import subprocess

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the header row as a list
    and the data as a nested dictionary"""
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

def  build_raster_list_from_csv(csvfile, path_col, name_col):
    """Read from a csv, and pull the path, year,
    and raster file names of each raster to be processed into a sorted list.
    csv must contain a fields titled Year, Path, and Name"""
    csv_list = read_csv(csvfile, skipheader = True)
    # Pull the path, year, and raster file name. 
    # The second name is a placeholder for a new name when there are duplicates
    raster_list = [[row[year_col],
                  row[path_col],
                  row[name_col],
                  row[new_name_col]]for row in csv_list]
    
    # sort the list by year and then NewName
    raster_list = sorted(raster_list, key=itemgetter(0, 3), reverse=False)        
    
    # Add a cols for processing status and the sort order
    raster_list = [["#", n] + raster_list[n] for n in range(0, len(raster_list))]
        
    return(raster_list)

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

# input parameters
walkpath = False
convrt_to_laz = True

csv_las = r"\\DEQWQNAS01\Lidar06\las_paths_Lidar06.csv"
workspaces = [r"\\DEQWQNAS01\Lidar06"]

#workspaces = [r"\\DEQWQNAS01\Lidar01",
    #r"\\DEQWQNAS01\Lidar02",
    #r"\\DEQWQNAS01\Lidar03",
    #r"\\DEQWQNAS01\Lidar04",
    #r"\\DEQWQNAS01\Lidar05",
    #r"\\DEQWQNAS01\Lidar06"]

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
                if f.endswith(".las"):
                    las_list.append(["#", f, os.path.join(dirpath, f)])
                    
    print("writing paths to csv")
    write_csv(las_list, csv_las)
    print("Done walking")

if convrt_to_laz is True:
    n = 0
    las_list = read_csv(csv_las, skipheader=False)
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
                            write_csv(las_list, csv_las)                  
            else:
                print("Error: " + inpath_temp + " does not exist")
                status = "E"
                las_list[n][0] = status
                write_csv(las_list, csv_las)
        n = n + 1
    print("Done converting to laz")
print("Done with script")