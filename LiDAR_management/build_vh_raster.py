'''
Walks directories looking for bare earth (BE), 
hightest hit (HH), or vegetation height (VH) raster data. Groups
rasters based on quad and project name attributes (not overlapping extent)
and generates a vegetation height raster and pyramids if they do
not exist. A geo filter function is used to limit processing to specfic
areas of interest.

Outputs are a comma delimited text file of the raster inventory and
any vegetation height rasters.
'''
from __future__ import print_function
import os
import csv
import string
from osgeo import ogr
from osgeo import gdal
from collections import defaultdict
from operator import itemgetter

import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

build_vh = True

# dirctory and file name of the output raster inventory
out_csv_file = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\North_Coast_paths.txt"

# input csv file containting project names and which year the area was flown
csv_year =  r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_by_year_20150825.csv"

# list of directories to walk
workspaces = [r"\\DEQWQNAS01\Lidar01\PDX-MTHood",
              r"\\DEQWQNAS01\Lidar01\WillametteValley",
              r"\\DEQWQNAS01\Lidar01\SouthCoast",
              r"\\DEQWQNAS01\Lidar03\Central_Coast_Range",
              r"\\DEQWQNAS01\Lidar04\NorthCoast",
              r"\\DEQWQNAS01\Lidar05\OLC_SCAPPOOSE_2013",
              r"\\DEQWQNAS01\Lidar05\OLC_TILLAMOOK_YAMHILL_2012",
              r"\\DEQWQNAS01\Lidar05\OLC_YAMBO_2010",
              r"\\DEQWQNAS01\Lidar06\OLC_LANE_COUNTY_2014"]

workspaces = [r"\\DEQWQNAS01\Lidar04\NorthCoast"]

# attribute field name to query for geo filter
#geo_field_name = "HUC_8"
geo_field_name = "STATE"

# attribute values to query # Mid Coast
#geo_area = "'17100204','17100205','17100206','17100207'"
geo_area = "'OR','OR WA','WA OR'"

# Disregard any folder with the name in the ignore list
ignore = ["POINT", "REPORT", "LAS", "LAZ", "VEC", "SHAP", "ASC", "TIN","INTEN",
          "DEN","HILLS","HL", "HILSD", "HS", "ORTHO", "PHOTO","TRAJ", "RECYCLER",
          "System Volume Information","Lower_Columbia","USFS_Original",
          "Yamhill_DEQ","Deschutes_from_USFS_old", "XXX", ".bnd"]

def nested_dict(): 
    """Build a nested dictionary"""
    return defaultdict(nested_dict)
        
def clean_name(filename):
    '''Cleans up the filename putting everything in lower case, removes
    underscores, and strips raster prefix and unique alpha letters from
    the end of ohio code quad names'''
    
    name_mod = filename.lower()
    name_mod = name_mod.replace("_", "")
    # remove these raster prefix
    for this_string in ["vh", "veght", "veg_height",
                        "be", "bare",
                        "hh", "high", "q"]:
        
        name_mod = name_mod.replace(this_string, "")
        
    # This removes a file extension e.g. .img
    name_mod = name_mod.split('.',1)[0]
    
    # Identify if the name is an ohio code          
    if (len(name_mod) == 7 and
        name_mod[0:4].isdigit() and
        name_mod[5].isalpha() and
        name_mod[6].isdigit()):
        
        isOhiocode = True
        quad_key = name_mod
        
    elif (len(name_mod) == 8 and
          name_mod[0:4].isdigit() and
          name_mod[5].isalpha() and
          name_mod[6].isdigit() and
          name_mod[7].isalpha()):
            
        isOhiocode = True
        # Remove letter at end e.g. "45123d4"
        quad_key = name_mod[:-1]
        
    else:
        # Note an Ohio code
        isOhiocode = False
        quad_key = name_mod
        
    return name_mod, quad_key, isOhiocode
                    
def geo_filter(geo_field_name, geo_area):
    '''Returns a sorted list of ohio code quad names that are within
    the specified geo area'''
    
    # Read in the data
    driver = ogr.GetDriverByName("OpenFileGDB")
    db = driver.Open(r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\QUADS.gdb", 0)
    fc = db.GetLayer("WBD_HU06_HUC12_Quadindex7_5")
    
    # Pull the feature with the query
    fc.SetAttributeFilter("{0} IN ({1})".format(geo_field_name, geo_area))
    
    # Pull the quads
    quads = [feature.GetField("OHIOCODE") for feature in fc]
    
    # Get all the unique values
    myquads = sorted(set(quads), reverse=False)
    
    return myquads

def read_csv_dict(csvfile, key_col, value_col, skipheader = True):
    """Reads an input csv file and returns a dictionary with
    one of the columns as the dictionary keys and another as the values"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader == True: reader.next()
        csvdict = dict((row[key_col],row[value_col]) for row in reader)
    return csvdict

def write_csv(csvlist, csvheader, csvfile):
    """write the input list to csv"""
    with open(csvfile, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(csvheader)        
        for row in csvlist:
            writer.writerow(row)
            

#--Main ---------------------------

# get a list of the ohio code quads in the geo area
myquads = geo_filter(geo_field_name, geo_area)

# build a dictionary of project names
pjctdict = read_csv_dict(csv_year, key_col=0, value_col=1, skipheader=True)

# initialize the quad dictionary
quad_dict = nested_dict()

# strings to identify different raster types
keep_be = ["be", "bare", "bare_earth"]
keep_hh = ["hh", "high", "highest_hit"]
keep_vh = ["vh", "veght", "veg_height"]

# walk workspace directories
for workspace in workspaces:
    for dirpath, dirnames, filenames in arcpy.da.Walk(workspace,
                                                      topdown=True,
                                                      datatype="RasterDataset"):                
        remove_list = []
        print(dirpath)
        for d in dirnames:
            if any(word.lower() in d.lower() for word in ignore):
                remove_list.append(d)
        
        for r in remove_list:
            dirnames.remove(r)        
        
        # -- BARE EARTH rasters            
        if any(word.lower() in dirpath.lower() for word in keep_be):    
            for filename in filenames:
                if all(word.lower() not in filename.lower() for word in ignore):
                    pjct = [value for key, value in pjctdict.items() if dirpath.startswith(key)][0]
                    raster_path = os.path.join(dirpath, filename)
                    if not pjct:
                        year = "NA"
                    
                    name_mod, quad_key, isOhiocode = clean_name(filename)
                    
                    # filter by geo area
                    if isOhiocode:
                        if any(quad.lower() == quad_key for quad in myquads):
                            quad_dict[pjct][name_mod]["BE"] = raster_path
                    else:
                        # not an ohio code, can't filter geoarea, keep anyway
                        quad_dict[pjct][name_mod]["BE"] = raster_path
                    
        # -- HIGHEST HIT rasters       
        if any(word.lower() in dirpath.lower() for word in keep_hh):   
            for filename in filenames:
                if all(word.lower() not in filename.lower() for word in ignore):
                    pjct = [value for key, value in pjctdict.items() if dirpath.startswith(key)][0]
                    raster_path = os.path.join(dirpath, filename)
                    if not pjct:
                        pjct = "NA"
                    
                    name_mod, quad_key, isOhiocode = clean_name(filename)
                    
                    # filter by geo aarea
                    if isOhiocode:
                        if any(quad.lower() == quad_key for quad in myquads):
                            quad_dict[pjct][name_mod]["HH"] = raster_path
                    else:
                        # not an ohio code, can't filter geoarea, keep anyway
                        quad_dict[pjct][name_mod]["HH"] = raster_path
                    
        # -- VEGETATION HEIGHT rasters
        if any(word.lower() in dirpath.lower() for word in keep_vh):   
            for filename in filenames:
                if all(word.lower() not in filename.lower() for word in ignore):
                    pjct = [value for key, value in pjctdict.items() if dirpath.startswith(key)][0]
                    raster_path = os.path.join(dirpath, filename)
                    if not pjct:
                        pjct = "NA"
                        
                    name_mod, quad_key, isOhiocode = clean_name(filename)
                    
                    # filter by geo aarea
                    if isOhiocode:
                        if any(quad.lower() == quad_key for quad in myquads):
                            quad_dict[pjct][name_mod]["VH"] = raster_path
                    else:
                        # not an ohio code, can't filter geoarea, keep anyway
                        quad_dict[pjct][name_mod]["VH"] = raster_path
out_csv = []

# Create vegetation height rasters
for project_area, quad_keys in quad_dict.items():
    for quad_key, types in quad_keys.items():
        row = ['Error', quad_key, None, None, None]
        for type, raster_path in types.items():
            if type == "VH":
                row[2] = raster_path
            elif type == "BE":
                row[3] = raster_path
            elif type == "HH":
                row[4] = raster_path        
        
        if ('BE' in types.keys() and
            'HH' in types.keys() and
            'VH' not in types.keys()):
            
            be_path = types["BE"]
            hh_path = types["HH"]
            
            # Check to see if the file is a folder (ESRI grid format), if not we have to move up three directories
            if os.path.isdir(hh_path):
                vh_dir = os.path.dirname(os.path.dirname(hh_path))+ "\\VH"
            else:
                vh_dir = os.path.dirname(os.path.dirname(os.path.dirname(hh_path)))+ "\\VH"
            
            # check to see if the directory exists already, if not create it
            if not os.path.isdir(vh_dir):
                os.mkdir(vh_dir)            
                
            # make veg height file name
            filename = "vh" + quad_key
            vh_path = os.path.join(vh_dir, filename)
                
            print("creating {0}".format(vh_path))
            
            # Set snap raster environment
            arcpy.env.snapRaster = be_path            
                  
            if build_vh:
                try:
                    vh = Minus(hh_path, be_path)
                    vh.save(vh_path)
                    arcpy.BuildPyramids_management(vh_path, "-1", "NONE", "BILINEAR",
                                                   "DEFAULT", "75", "SKIP_EXISTING")
                    row[2] = vh_path
                    row[0] = 'Complete'
                except:
                    row[0] = 'Error'
        
        elif ('BE' in types.keys() and
            'HH' in types.keys() and
            'VH' in types.keys()):
            
            row[0] = 'Complete'
        
        out_csv.append(row)
        
# write to output
header = ["STATUS", "QUAD", "VH_PATH", "BE_PATH", "HH_PATH"]
write_csv(out_csv, header, out_csv_file)
print('Done')