# This script builds a vegetation height raster and mosaics it into an
# ESRI mosaic dataset
#
# 'csv_vh' is an input csv file with the following col headers:
#    STATUS,   VH_NAME,  VH_PATH,  BE_PATH,   HH_PATH
#    blank,    blank,    blank,    not blank, not blank


from __future__ import print_function
import os
import csv
import ntpath
import arcpy
from collections import defaultdict
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

# if this is False it means csv_vh already exists
walk_directory = True
mosaic = False

workspaces = [r"\\DEQWQNAS01\Lidar03\OLC_SOUTH_WARNER_2014"]

csv_vh = r"\\DEQWQNAS01\Lidar03\OLC_SOUTH_WARNER_2014\path_build_VH_rasters.csv"
mdname = r"\\DEQWQNAS01\Lidar07\Willamette.gdb\VH"

# input csv file indicating which year the project was flown
csv_year =  r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_by_year_20150825.csv"


# Disregard any folder with the name in the ignore list
ignore = ["POINT", "3_FT", "3FT,""REPORT", "LAS", "LAZ", "VEC", "SHAP", "ASC", "TIN","INTEN",
          "DEN","HILLS","HL", "HILSD", "HS", "ORTHO", "PHOTO","TRAJ", "RECYCLER",
          "System Volume Information", "XXX"]

def nested_dict(): 
    """Build a nested dictionary"""
    return defaultdict(nested_dict)

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the header row as a list and the data as a nested dictionary"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader: reader.next()
        csvlist = [row for row in reader]
    return csvlist

def read_csv_dict(csvfile, key_col, value_col, skipheader = True):
    """Reads an input csv file and returns a dictionary with
    one of the columns as the dictionary keys and another as the values"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader: reader.next()
        csvdict = dict((row[key_col],row[value_col]) for row in reader)
    return csvdict

def write_csv(csvlist, csvfile):
    """write the input list to csv"""
       
    with open(csvfile, "wb") as f:
        writer = csv.writer(f)
        for row in csvlist:
            writer.writerow(row)  

def get_file_name(inpath):
    head, tail = ntpath.split(inpath)
    return tail or ntpath.basename(head)

def walk_dir(workspaces, projdict, yeardict, ignore):
    
    rasterDict = nested_dict()
    
    # strings to identify different rasters types
    keep_be = ["be", "bare", "bare_earth"]
    keep_hh = ["hh", "high", "highest_hit"]
    keep_vh = ["vh", "veght", "veg_height"]    
    
    for workspace in workspaces:
        for dirpath, dirnames, filenames in arcpy.da.Walk(workspace,
                                                          topdown=True,
                                                          datatype="RasterDataset"):                
            remove_ = []
            print(dirpath)
            for d in dirnames:
                if any(word.lower() in d.lower() for word in ignore):
                    remove_.append(d)
            
            for r in remove_:
                dirnames.remove(r)        
                        
            if any(word.lower() in dirpath.lower() for word in keep_be):    
                for filename in filenames:
                    if all(word.lower() not in filename.lower() for word in ignore):
                        
                        try:
                            year = [value for key, value in yeardict.items() if dirpath.startswith(key)][0]
                        except:
                            year = "NA"
                        
                        try:
                            proj = [value for key, value in projdict.items() if dirpath.startswith(key)][0]
                        except:
                            proj = "NA"
                        
                        file_key = filename.lower()    
                        for this_string in keep_be:
                            file_key = file_key.replace(this_string, "")
                        
                        rasterDict[proj][year][file_key]["be"] = os.path.join(dirpath, filename)
                    
            if any(word.lower() in dirpath.lower() for word in keep_hh):   
                for filename in filenames:
                    if all(word.lower() not in filename.lower() for word in ignore):
                        
                        try:
                            year = [value for key, value in yeardict.items() if dirpath.startswith(key)][0]
                        except:
                            year = "NA"
                        
                        try:
                            proj = [value for key, value in projdict.items() if dirpath.startswith(key)][0]
                        except:
                            proj = "NA"
                        
                        file_key = filename.lower() 
                        for this_string in keep_hh:
                            file_key = file_key.replace(this_string, "")
                        
                            rasterDict[proj][year][file_key]["hh"] = os.path.join(dirpath, filename)
                            
            if any(word.lower() in dirpath.lower() for word in keep_vh):
                for filename in filenames:
                    if all(word.lower() not in filename.lower() for word in ignore):
                        try:
                            year = [value for key, value in yeardict.items() if dirpath.startswith(key)][0]
                        except:
                            year = "NA"
                        
                        try:
                            proj = [value for key, value in projdict.items() if dirpath.startswith(key)][0]
                        except:
                            proj = "NA"
                            
                        file_key = filename.lower()            
                        for this_string in keep_vh:
                            file_key = file_key.replace(this_string, "")
            
                            rasterDict[proj][year][file_key]["vh"] = os.path.join(dirpath, filename)            
    
    csvlist = [["STATUS", "VH_NAME", "VH_PATH", "BE_PATH", "HH_PATH"]]
    projects = rasterDict.keys()
    projects.sort()
    for p in projects:
        years = rasterDict[p].keys()
        years.sort()
        for y in years:
            file_key = rasterDict[p][y].keys()
            file_key.sort()
            for f in file_key:
                be = rasterDict[p][y][f]["be"]
                hh = rasterDict[p][y][f]["hh"]
                vh = rasterDict[p][y][f]["vh"]
                if ((be and hh) and not vh):
                    csvlist.append(["", "", "", be, hh])
                     
    return csvlist

yeardict = read_csv_dict(csv_year, key_col=0, value_col=2, skipheader=True)
projdict = read_csv_dict(csv_year, key_col=0, value_col=1, skipheader=True)

if walk_directory:
    csvlist = walk_dir(workspaces, projdict, yeardict, ignore)
    write_csv(csvlist, csv_vh)

# read csv
csvlist = read_csv(csv_vh, skipheader=False)

rastype = "Raster Dataset"
updatecs = "UPDATE_CELL_SIZES"
updatebnd = "NO_BOUNDARY"
updateovr = "NO_OVERVIEWS"
maxlevel = "-1"
maxcs = "#"
maxdim = "#"
spatialref = "#"
inputdatafilter = "#"
subfolder = "NO_SUBFOLDERS"
duplicate = "EXCLUDE_DUPLICATES"
buildpy = "NO_PYRAMIDS"
calcstats = "CALCULATE_STATISTICS"
buildthumb = "NO_THUMBNAILS"
comments = "#"
forcesr = "#"

tot = len(csvlist) - 1

for n, row in enumerate(csvlist):
    
    if n == 0:
        # skip the header row
        continue
    
    bepath = row[3]
    hhpath = row[4]
    
    # Check to see if the file is a folder (ESRI grid format), if not we have to move up three directories
    if os.path.isdir(hhpath):
        vhpath = os.path.dirname(os.path.dirname(hhpath))+ "\\VEG_HEIGHT"
    else:
        vhpath = os.path.dirname(os.path.dirname(os.path.dirname(hhpath)))+ "\\VEG_HEIGHT"
        
    # check to see if the veght directory exists already, if not create it
    if not os.path.isdir(vhpath):
        os.mkdir(vhpath)
        
    # make veg height file name by using name of bare earth grid
    bename = get_file_name(bepath)
    mod_name1 = bename.lower()
    mod_name1 = mod_name1.replace("_", "")
    mod_name1 = mod_name1.replace("be", "vh")
    mod_name1 = mod_name1.replace("bare", "vh")
    mod_name1 = mod_name1.replace("bareearth", "vh")  
    vhname = mod_name1
    
    csvlist[n][1] = vhname
        
    vhpath = vhpath + "\\" +vhname
    csvlist[n][2] = vhpath
    
    # check to see if the raster exists
    if not os.path.isdir(vhpath):
        print("creating "+str(n)+" of "+str(tot)+" "+vhpath)
        vh = Minus(hhpath, bepath)
        vh.save(vhpath)
        arcpy.BuildPyramids_management(vhpath, "-1", "NONE", "BILINEAR",
                                       "DEFAULT", "75", "SKIP_EXISTING")
        
    if (row[0] != "X" and mosaic): 
        # Add to a mosaic datset, assumes one already exists
        print("mosaicing "+str(n)+" of "+str(tot)+" "+vhpath)
        arcpy.AddRastersToMosaicDataset_management(
                     mdname, rastype, vhpath, updatecs, updatebnd, updateovr,
                     maxlevel, maxcs, maxdim, spatialref, inputdatafilter,
                     subfolder, duplicate, buildpy, calcstats, 
                     buildthumb, comments, forcesr)        
        csvlist[n][0] = "X"
    else:
        csvlist[n][0] = "X"
    write_csv(csvlist, csv_vh)
    
print("done")