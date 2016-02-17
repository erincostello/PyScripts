# This script will use the output from find_raster_path.py
# to generate a mosaic dataset.

# To run the gdal commands you first have to set the path and GDAL_DATA variable in environments.
# C:\Python27\Lib\site-packages\osgeo
# GDAL_DATA C:\Python27\Lib\site-packages\osgeo\data\gdal

from __future__ import print_function
import arcpy
import os
import csv
import subprocess
import string
import numpy
from collections import defaultdict
from operator import itemgetter
from osgeo import ogr
from osgeo import gdal
from osgeo import gdal_merge


# ouput csv header
header = ["STATUS", "NAME", "PATH", "PROJECT", "YEAR", "NAMECLEAN", "NAMENEW", "TYPE", "PATH_OUT"]

# output column assignments
status_col = 0
name_col = 1
path_col = 2
proj_col = 3
year_col = 4
clean_col = 5
new_name_col = 6
type_col = 7
pathout_col = 8

# in_csvfile
#csvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_new2_BE_rasters.csv"
#csvfile  = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_new2_HH_rasters.csv"
csvfile  = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_new2_VH_rasters.csv"

outpath_warp = r"F:\LiDAR\VH"

proj_final = 'EPSG:2992'
infile_type = "\\hdr.adf"
out_format = "HFA"
out_ext = ".img"

buildpyramids = True
buildmosaic = True
mdname = r"F:\LiDAR\MOSAICS.gdb\VH"

pathletter_dict = {r'\\DEQWQNAS01\Lidar01': r'G:',
                   r'\\DEQWQNAS01\Lidar02': r'H:',
                   r'\\DEQWQNAS01\Lidar03': r'I:',
                   r'\\DEQWQNAS01\Lidar04': r'J:',
                   r'\\DEQWQNAS01\Lidar05': r'K:',
                   r'\\DEQWQNAS01\Lidar06': r'L:',
                   r'\\DEQWQNAS01\Lidar07': r'M:',
                   r'\\DEQWQNAS01\Lidar08': r'N:'}

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the header row and data
    as a list"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader: reader.next()
        csvlist = [row for row in reader]
    return(csvlist)

def write_csv(csvlist, csvfile):
    """write the input list to csv"""
    import csv
    with open(csvfile, "wb") as f:
        linewriter = csv.writer(f)
        for row in csvlist:
            linewriter.writerow(row)
            
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False            

def get_nodata_value(raster_path, band, status):
    """Returns the no data value from a raster band"""
    try:
        raster = gdal.Open(raster_path)
        r_band = raster.GetRasterBand(band)
        nodatavalue = r_band.GetNoDataValue()
        raster = None
    except:
        nodatavalue = None
        status = "E"
    
    return(nodatavalue,status)

def get_format(raster_list, new_name_col, type_col):
    """Returns the raster list with the output faster format"""
    
    for n, row in enumerate(raster_list):
        out_raster = outpath_warp + "\\" + row[new_name_col] + out_ext
        raster_list[n][type_col] = arcpy.Describe(out_raster).format
        
    print("done with getting format")
    return(raster_list)

def execute_cmd(cmd_list):
    """Executes commands to the command prompt using subprocess module.
    Commands must be a string in a list"""
    for cmd in cmd_list:
        print(cmd)    
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
        stdout, stderr = proc.communicate()
        exit_code=proc.wait()
        if exit_code:       
            # Something went wrong
            status = "E"
            # Try to delete the temp drive for next iteration
            proc = subprocess.Popen(cmd[3], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
            print(stderr)
            return (status)
        else:
            print(stdout)
    # Yay! we've reached the end without errors
    status = "X"
    return (status)


# -- Build a list of rasters to itterate through -----------------------

raster_list = read_csv(csvfile, skipheader = False)
tot = len(raster_list)

# -- Warp/reproject the rasters ----------------------------------------

for n, row in enumerate(raster_list):
    
    if n > 0:
        status = row[status_col]
        inpath = row[path_col]
        inpath_server = inpath[:20]
        inpath_letter = pathletter_dict[inpath_server]
        inpath_temp = inpath.replace(inpath[:20], inpath_letter) + infile_type
        out_raster = outpath_warp + "\\" + row[new_name_col] + out_ext
        raster_list[n][pathout_col] = out_raster
        # check to see if the file already exists
        raster_exists = os.path.isfile(out_raster)
        
        #  Check if the raster already exists and status
        if raster_exists and status in ["X", "#"]:
            raster_list[n][status_col] = "X"
            write_csv(raster_list, csvfile)
    
        else:
            inraster_exists = os.path.isfile(inpath_temp)
            if inraster_exists:
                # Get the no data value
                nodatavalue , status = get_nodata_value(raster_path=inpath, band=1, status=status)
                cmd_list = ['gdalwarp -t_srs {0} -q -r bilinear -srcnodata {1} -dstnodata {2} -of {3} -overwrite {4} {5}'.format(proj_final, nodatavalue, nodatavalue, out_format, inpath_temp, out_raster)]                
                print("warping "+str(n)+" of "+str(tot)+" "+inpath_temp)
                if status is not "E":
                    status = execute_cmd(cmd_list)
                    raster_list[n][status_col] = status
                    write_csv(raster_list, csvfile)                
            else:
                print("Error: " + inpath_temp + " does not exist")
                status = "E"
                
            if status is "E":
                print("gdalwarp Error")
            write_csv(raster_list, csvfile)
            
# -- Build Pyramids/Mosaic ----------------------------------------
            
        if buildpyramids:
            print("Building pyramids")
            arcpy.BuildPyramidsandStatistics_management(out_raster, 'NONE', 'BUILD_PYRAMIDS', 'CALCULATE_STATISTICS',
                                                        '#', '#', '#', '#', '#', '#', '-1', '#', 'NEAREST', '#', '#', 'SKIP_EXISTING')
        
        if buildmosaic:
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
            arcpy.AddRastersToMosaicDataset_management(
                mdname,  rastype, out_raster, updatecs, updatebnd, updateovr,
                maxlevel, maxcs, maxdim, spatialref, inputdatafilter,
                subfolder, duplicate, buildpy, calcstats, 
                buildthumb, comments, forcesr)            

print("done warping")