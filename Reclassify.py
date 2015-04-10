# http://geoexamples.blogspot.com/2013/06/gdal-performance-raster-classification.html
from __future__ import print_function
import numpy
from numpy import zeros  
from numpy import logical_and  
from osgeo import gdal  



inpath_temp = r"\\DEQWQNAS01\Lidar08\LiDAR\VH\vh44122b1a.img"
out_raster = r"\\DEQWQNAS01\Lidar08\LiDAR\YEAR\yr44122b1a.img"
year = 2009

rc_lower = -5000
rc_upper = 5000

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

format = "HFA"  
driver = gdal.GetDriverByName( format )  
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
        
        r = zeros((rows, cols), numpy.uint16)
        r = year * logical_and(data_array > -50000, data_array < 50000)

        data_reclass.GetRasterBand(1).WriteArray(r,j,i)
        data_reclass.GetRasterBand(1).SetNoDataValue(0)

data_reclass = None

print("done")

if buildreclass is True:
    for row in raster_list:
        status = row[0]
        year = row[2]
        inpath = row[3]
        inpath_server = inpath[:20]
        inpath_letter = pathletter_dict[inpath_server]
        inpath_temp = inpath.replace(inpath[:20], inpath_letter) + infile_type
        out_raster = outpath_warp + "\\" + row[5] + ".img"
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
                    
                    r = zeros((rows, cols), numpy.uint16)
                    r = year * logical_and(data_array > rc_lower, data_array < rc_upper)
            
                    data_reclass.GetRasterBand(1).WriteArray(r,j,i)
                    data_reclass.GetRasterBand(1).SetNoDataValue(0)
            
            data_reclass = None            
            # end reclass code
                   
            if status is not "E":
                status = execute_cmd(cmd_list)
                in_vrt_rasters.append(out_raster)
            raster_list[n][0] = status
            write_csv(raster_list, outcsvfile)
                
            if status is "E":
                buildvrt = False
                print("reclass Error")
            write_csv(raster_list, outcsvfile)                
            n = n + 1
    print("done with reclass")