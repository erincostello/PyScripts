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

header = ["STATUS", "NAME", "PATH", "YEAR", "NAMECLEAN", "NAMENEW", "TYPE"]

status_col = 0
order_col = 1
year_col = 2
path_col = 3
name_col = 4
new_name_col = 5
type_col = 6

# To run the gdal commands you first have to set the path and GDAL_DATA variable in environments.
# C:\Python27\Lib\site-packages\osgeo
# GDAL_DATA C:\Python27\Lib\site-packages\osgeo\data\gdal

#in_gdbpath = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWilamette\LiDAR.gdb"
#in_gdb_fc = "VH_footprints"
in_csvfile = r"\\DEQWQNAS01\Lidar08\LiDAR\YEAR\Year_quad_list_input.csv"
#in_shp =  r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWilamette\VH_footprints_20150316.shp"
proj_final = 'EPSG:2992'
outpath_warp = r"N:\LiDAR\BE\new"
#outpath_reclass = r"\\DEQWQNAS01\Lidar08\LiDAR\YEAR\new"
out_vrt = r"N:\LiDAR\BE\new\BE.vrt"
outcsvfile = r"N:\LiDAR\BE\new\BE_quad_list_output_new.csv"
outtxtfile = r"N:\LiDAR\BE\new\BE_mosaic_list.txt"
outmosaic = r"N:\LiDAR\BE\BE_mosaic.img"
outmosaic_path = r"N:\LiDAR\BE"
outmosaic_name = r"BE_mosaic.img"
infile_type = "\\hdr.adf"
#infile_type = ""
out_format = "HFA"
out_ext = ".img"
overwrite_csv = False
buildwarp = False
buildreclass = False
buildvrt_list = True
buildvrt = True
buildmosaic = False
buildpyramids = False
rc_lower = -50000
rc_upper = 50000

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
        if skipheader == True: reader.next()
        csvlist = [row for row in reader]
    return(csvlist)

def write_csv(csvlist, csvfile):
    """write the input list to csv"""
    import csv
    with open(csvfile, "wb") as f:
        linewriter = csv.writer(f)
        for row in csvlist:
            linewriter.writerow(row)

def write_txt(txtlist, txtfile):
    """write the input list to txt"""
    with open(txtfile, "w") as f:
        for row in txtlist:
            f.write(row + '\n')
            
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False            

def build_raster_list_from_shp(in_shp):
    """Builds a sorted list of each raster to be processed.
    shp must contain fields titled Year, Path, and Name"""
    
    # Read the shapefile
    source = ogr.Open(in_shp, 1)
    fc = source.GetLayer()
    # Pull the path, year, and raster file name. 
    # The second name is a new name when there are duplicates
    raster_list = [[feature.GetField("Year"),
                  feature.GetField("Path"),
                  feature.GetField("Name"),
                  feature.GetField("NewName")]for feature in fc]
    source = None
    
    # sort the list by year and then NewName
    raster_list = sorted(raster_list, key=itemgetter(0, 3), reverse=False)
    
    # Add a cols for processing status, sort order, and raster format
    raster_list = [["#", n] + raster_list[n] + ["#"] for n in range(0, len(raster_list))]
    
    return(raster_list)

def  build_raster_list_from_gdb(in_gdb_path, in_gdb_fc):
    """Read a feature class from a ESRI GDB, and pull the path, year,
    and raster file names of each raster to be processed into a sorted list.
    GDB must contain a fields titled Year, Path, and Name"""
    # Does not work ??
    driver = ogr.GetDriverByName("OpenFileGDB")
    db = driver.Open(in_gdbpath, 0)
    fc = db.GetLayer(in_gdb_fc)
    # Pull the path, year, and raster file name. 
    # The second name is a new name when there are duplicates
    raster_list = [[feature.GetField("Year"),
                  feature.GetField("Path"),
                  feature.GetField("Name"),
                  feature.GetField("NewName")]for feature in fc]
    
    # sort the list by year and then NewName
    raster_list = sorted(raster_list, key=itemgetter(0, 3), reverse=False)
    
    # Add a cols for processing status and the sort order
    raster_list = [["#", n] + raster_list[n] for n in range(0, len(raster_list))]    
    
    return(raster_list)

def  build_raster_list_from_csv(csvfile, status_col, year_col, path_col, name_col, new_name_col):
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

def get_format(raster_list):
    """Returns the raster list with the output faster format"""
    n = 0
    for row in raster_list:
        out_raster = outpath_warp + "\\" + row[5] + out_ext        
        raster_list[n][6] = arcpy.Describe(out_raster).format
        n = n + 1
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

# get from csv file or build one from a feature class and export to csv
if overwrite_csv is True:
    #raster_list = build_raster_list_from_shp(in_shp)
    #raster_list = build_raster_list_from_gdb(in_gdb_path, in_gdb_fc)
    raster_list = build_raster_list_from_csv(in_csvfile, year_col=0, path_col=1, name_col=2, new_name_col=3)
    write_csv(raster_list, outcsvfile)
else:
    csv_exists = os.path.isfile(outcsvfile)   

    if csv_exists is False:
        raster_list = build_raster_list_from_shp(in_shp)
        #raster_list = build_raster_list_from_gdb(in_gdb_path, in_gdb_fc)
        write_csv(raster_list, outcsvfile)
    
    # Read the csv
    raster_list = read_csv(outcsvfile, skipheader = False)     

tot = len(raster_list)
n = 0
in_vrt_rasters = []

# -- Warp/reproject the rasters ----------------------------------------

for row in raster_list:
    status = row[0]
    inpath = row[3]
    inpath_server = inpath[:20]
    inpath_letter = pathletter_dict[inpath_server]
    inpath_temp = inpath.replace(inpath[:20], inpath_letter) + infile_type
    out_raster = outpath_warp + "\\" + row[5] + out_ext
    # check to see if the file already exists
    raster_exists = os.path.isfile(out_raster)
    
    #  Check if the raster already exists and status
    if raster_exists is True and status in ["X", "#"]:
        raster_list[n][0] = "X"
        in_vrt_rasters.append(out_raster) 
        write_csv(raster_list, outcsvfile)
        n = n + 1
    elif raster_exists is True and status == "E":
        buildvrt = False
        n = n + 1
    else:
        inraster_exists = os.path.isfile(inpath_temp)
        if inraster_exists is True:
            # Get the no data value
            nodatavalue , status = get_nodata_value(raster_path=inpath, band=1, status=status)
            cmd_list = ['gdalwarp -t_srs {0} -q -r near -srcnodata {1} -dstnodata {2} -of {3} -overwrite {4} {5}'.format(proj_final, nodatavalue, nodatavalue, out_format, inpath_temp, out_raster)]                
            print("warping "+str(n)+" of "+str(tot)+" "+inpath_temp)
            if status is not "E" and buildwarp is True:
                status = execute_cmd(cmd_list)
                in_vrt_rasters.append(out_raster)
                raster_list[n][0] = status
                write_csv(raster_list, outcsvfile)                
        else:
            print("Error: " + inpath_temp + " does not exist")
            status = "E"
            
        if status is "E":
            buildvrt = False
            print("gdalwarp Error")
        write_csv(raster_list, outcsvfile)                
        n = n + 1

print("done warping")


# -- Get the warped raster format for checking later ------------------
raster_list = get_format(raster_list)
write_csv(raster_list, outcsvfile)

# -- Reclass the rasters ----------------------------------------------
n = 0
if buildreclass is True:
    for row in raster_list:
        status = row[0]
        year = int(row[2])
        inpath = row[3]
        inpath_server = inpath[:20]
        inpath_letter = pathletter_dict[inpath_server]
        inpath_temp = inpath.replace(inpath[:20], inpath_letter) + infile_type
        out_raster = outpath_reclass + "\\" + row[5] + out_ext
        # check to see if the output file already exists
        raster_exists = os.path.isfile(out_raster)
        
        #  Check if the raster already exists and status
        if raster_exists is True and status in ["X", "#"]:
            raster_list[n][0] = "X"
            in_vrt_rasters.append(out_raster) 
            write_csv(raster_list, outcsvfile)
            n = n + 1
        elif raster_exists is True and status == "E":
            buildvrt = False
            n = n + 1
        else:
            inraster_exists = os.path.isfile(inpath_temp)
            if inraster_exists is True:
                print("reclass "+str(n)+" of "+str(tot)+" "+inpath_temp)
            else:
                print("Error: " + inpath_temp + " does not exist")
                status = "E"
                        
            # start reclass code
            try:
                data = gdal.Open(inpath_temp)  
                band = data.GetRasterBand(1)
                nodata = band.GetNoDataValue()
                
                block_sizes = band.GetBlockSize()  
                x_block_size = block_sizes[0]  
                y_block_size = block_sizes[1]  
                
                xsize = band.XSize  
                ysize = band.YSize  
                
                #max_value = band.GetMaximum()  
                #min_value = band.GetMinimum()  
                
                #if max_value == None or min_value == None:  
                #    stats = band.GetStatistics(0, 1)  
                #    max_value = stats[1]  
                #    min_value = stats[0]  
                 
                driver = gdal.GetDriverByName(out_format)  
                data_reclass = driver.Create(out_raster, xsize, ysize, 1, gdal.GDT_UInt32)
                data_reclass.SetGeoTransform(data.GetGeoTransform())  
                data_reclass.SetProjection(data.GetProjection())
                
                print("reclassifying {0}".format(out_raster))
                for i in range(0, ysize, y_block_size):  
                    if i + y_block_size < ysize:  
                        rows = y_block_size  
                    else:  
                        rows = ysize - i  
                    for j in range(0, xsize, x_block_size):  
                        if j + x_block_size < xsize:  
                            cols = x_block_size  
                        else:  
                            cols = xsize - j  
                
                        data_array = band.ReadAsArray(j, i, cols, rows)
                        
                        rc_array = numpy.zeros((rows, cols), numpy.uint16)
                        rc_array = year * numpy.logical_and(data_array > rc_lower, data_array < rc_upper)
                
                        data_reclass.GetRasterBand(1).WriteArray(rc_array,j,i)
                        data_reclass.GetRasterBand(1).SetNoDataValue(0)
                
                data_reclass = None
            except:
                status = "E"
            # end reclass code
                   
            if status is not "E":
                in_vrt_rasters.append(out_raster)
            raster_list[n][0] = status
            write_csv(raster_list, outcsvfile)
                
            if status is "E":
                buildvrt = False
                print("reclass error")
            write_csv(raster_list, outcsvfile)                
            n = n + 1
    print("done with reclass")

else:
    print("skipping reclass")
   
# -- Build the gdal VRT. -----------------------------------------------
# Must not have an error in status
if buildvrt is True:
    if buildvrt_list is True:
        write_txt(in_vrt_rasters, outtxtfile)
        
    cmd_list = ['gdalbuildvrt -resolution highest -hidenodata -addalpha -overwrite -q -input_file_list {0} {1}'.format(outtxtfile, out_vrt)]
    status = execute_cmd(cmd_list)
    if status is "E":
        buildmosaic = False
        print("gdalbuild Error")
    else:
        print("done building vrt")
else:
    print("skipping build vrt")

# Build the mosaic. Must not have an error in status
if buildmosaic is True:
    print("building mosaic")
    cmd_list = ['gdal_translate -of {0} -q -a_nodata none -stats {1} {2}'.format(out_format, out_vrt, outmosaic)]
    status = execute_cmd(cmd_list)

    if status is "E":
        print("gdal_translate Error")
    else:
        print("done mosaicing")
else:
    print("skipping mosaic")

if buildpyramids is True:
    print("building pyramids")
    arcpy.BuildPyramids_management(os.path.join(outmosaic_path, outmosaic_name), "-1", "NONE", "BILINEAR", "DEFAULT", "#", "OVERWRITE" )
print("script complete")

