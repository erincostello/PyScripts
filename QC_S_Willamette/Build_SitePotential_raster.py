"""
Build_Geomorph_Raster.py

This script builds a raster of the geomorphic and site potential codes
described in the Willamette Basin TMDL.

The site potential vegetation scenario and related vegetation classes
were developed using the same methods described in the 2006 TMDL.

Python scripts were developed to process the geomorphic raster
and translate geomorphic codes into site potential vegetation codes 

The original geomorphic feature class used in the 2006 TMDL had two 
limitations that needed to be addressed for modeling in the southern Willamette.

The limitations concern two land cover classes for water: open water
and general water. 

 General water (code 3011) are areas which include natural river
channels, lakes, ponds, or wetland areas. Under the site potential
vegetation scenario these features continued to stay as water. The 2006 effort
 mapped these areas using aerial photos and digitized them into a landcover
feature class only at locations that were modeled. For this
project water features that would have code 3011 needed to be
mapped across the entire study area. The National Wetland Inventory
(USFWS 2004) and the National Hydrography Dataset high resolution
v2.2 databases contain extensive inventories of water features and
were incorporated into geomorphic  raster. 

NWI's classification system (Cowardin et al 2013) allowed the removal of
most anthropogenic related water areas such as impounded reservoirs
and gravel mining ponds. Water's classified as Lacustrine (L),
Palustrine (P), Marine (M), or Estuarine (E) that are NOT forested (FO),
scrub/shrub (SS), diked/impounded (h), a spoil (s), or excavated (x) were
coded as general water. Forested and scrub/shrub classes were removed
because they have emergent or overhanging vegetation. The NHD high
channel areas were used to map the riverine reaches because in some areas
it was a little more accurate than NWI where the channel has migrated
in recent years, mostly in portions of the Willamette River.

Open water (code 2000) are areas representing the ACOE reservoirs
within the boundaries of the original geomorphic feature class and other
anthropogenic related water areas that did not meet the criteria for
general water. Under the classification rules for site potential
vegetation these areas were treated as prairie or savanna vegetation
types. In the upland forest zone impounded reservoirs were not mapped.
They were classified as upland forest (code 1900). The intent was that
these site potential vegetation types would be present along the
natural unimpouned channel (rather than actually present in the
river channel). The reservoirs were not modeled so no effort was made
to map the location of the natural (unimpounded) water channel.

"""
from __future__ import print_function

from operator import itemgetter
import csv
import random
import numpy

import arcpy
from arcpy import env

from arcpy.sa import *
#from arcpy.sa import Con
#from arcpy.sa import Nibble
#from arcpy.sa import SetNull
arcpy.CheckOutExtension("Spatial")

working_dir = r"F:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Site_Potential_Geomorph.gdb"
env.workspace = working_dir

# This csv file contains the probability of occurrence for each vegetation 
# type within each geomorphic unit. 
# This comes from Table 1 on page C-18 in the TMDL Appendix C
input_geomorph = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Site_Potential\geomorph_probability_table.csv"

# This is the geomorph fc from the Willamette TMDL project files 
# clipped to the S. Willamette and reprojected into lambert (ogic)
geomorph_fc1 = r"geomorph_fc_s01_from_TMDL"
arcpy.env.extent = geomorph_fc1

# This is nhd high areas v 2.20 cliped to the S. Willamette and 
# reprojected into lambert (ogic). They are being used to identify
# riverine channel areas because they correspond to 
# the flowlines used to generate the stream nodes.
# These areas will be coded as water (3011)
nhd_fc = r"NHDH_Area_v220_s01"

# This is nwi v 20141006 cliped to the S. Willamette and 
# reprojected into lambert (ogic). It is being used to identify the 
# impounded open water (OW) areas, such as ACOE reserovirs and also 
# wetlands, lakes, or ponds which will be coded as general water (3011).
nwi_fc1 = r"NWI_v20141006_s01"

# outputs
nhd_fc2 = r"NHDH_Area_v220_s02"
nwi_fc2 = r"NWI_v20141006_s02"
nwi_fc3 = r"NWI_v20141006_s03"

geomorph_fc2 = r"geomorph_fc_s02"
geomorph_fc3 = r"geomorph_fc_s03_final"

water_fc1 = r"water_features_s01"

out_raster1 = r"geomorph_codes_s01"
out_raster2 = r"geomorph_codes_s02"
out_raster3 = r"geomorph_codes_s03_final"
out_raster4 = r"site_pot_codes_s04_final"

def read_csv_dict(csvfile, key_col, val_col, skipheader=True):
    """Reads an input csv file and returns a dictionary with
    one of the columns as the dictionary keys and another as the values"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader == True: reader.next()
        csvdict = dict((row[key_col], row[val_col[0]:val_col[1]]) for row in reader)
    return csvdict

# This is the rex SQL query to select NWI attribute codes that will be coded as 
# water - 3011. It corresponds to Lacustrine (L), Palustrine (P), Marine (M),
# or Estuarine (E) waters that are not forested (FO), scrub/shrub (SS),
# diked/impounded (h), spoil (s), or excavated (x).
# Note Riverine (R) waters are excluded because those are covered 
# by the NHD.
# Refer to NWI documentation for meaning of the codes
# http://www.fws.gov/wetlands/Documents/NWI_Wetlands_and_Deepwater_Map_Code_Diagram.pdf
nwi_to_water = ('''(ATTRIBUTE LIKE ('%L%') OR 
                ATTRIBUTE LIKE ('%P%') OR
                ATTRIBUTE LIKE ('%E%') OR
                ATTRIBUTE LIKE ('%M%')) AND
                (ATTRIBUTE NOT LIKE ('%FO%') AND
                ATTRIBUTE NOT LIKE ('%SS%') AND
                ATTRIBUTE NOT LIKE ('%h%') AND
                ATTRIBUTE NOT LIKE ('%x%') AND
                ATTRIBUTE NOT LIKE ('%s%'))''')

# This is the rex SQL query to select NWI attribute codes that 
# correspond to Lacustrine (L) limnetic or littoral systems 
# that are diked/impounded (h). 
# These codes will be reclassed as open water (OW), which is 
# geomorph code 2000.
nwi_to_ow = '''ATTRIBUTE LIKE ('%L%h%')'''

# Make a new copy of the NWI
if not arcpy.Exists(nwi_fc2):
    arcpy.FeatureClassToFeatureClass_conversion(nwi_fc1, out_path=working_dir, 
                                               out_name=nwi_fc2)

    # outdent <----

    # Add a new fields into the NWI and NHD for the reclass code
    arcpy.AddField_management(nwi_fc2, "TYPE", "TEXT", "", "", "",
                              "", "NULLABLE", "NON_REQUIRED")
    arcpy.AddField_management(nhd_fc, "TYPE", "TEXT", "", "", "",
                              "", "NULLABLE", "NON_REQUIRED")
    
    arcpy.AddField_management(nwi_fc2, "GEOMORPH", "DOUBLE", "", "", "",
                              "", "NULLABLE", "NON_REQUIRED")
    arcpy.AddField_management(nhd_fc, "GEOMORPH", "DOUBLE", "", "", "",
                              "", "NULLABLE", "NON_REQUIRED")
    
    # select NHD features, code as 3011
    update_fields = ["TYPE", "GEOMORPH"]
    with arcpy.da.UpdateCursor(nhd_fc, update_fields) as cursor:  
        for row in cursor:
                row[0] = "Wa"
                row[1] = 3011
                cursor.updateRow(row)
    
    # select NWI water features, code as 3011
    query_field =  ["ATTRIBUTE"]
    with arcpy.da.UpdateCursor(nwi_fc2, query_field + update_fields, 
                               nwi_to_water) as cursor:  
        for row in cursor:
                row[1] = "Wa"
                row[2] = 3011
                cursor.updateRow(row)
    
    # select NWI open water features, code as 2000
    with arcpy.da.UpdateCursor(nwi_fc2, query_field + update_fields, 
                               nwi_to_ow) as cursor:  
        for row in cursor:
                row[1] = "OW"
                row[2] = 2000
                cursor.updateRow(row)
            
# Copy only the NWI features that were just changed
if not arcpy.Exists(nwi_fc3):
    nwi2_sql_query = """GEOMORPH IN (2000, 3011)"""
    arcpy.FeatureClassToFeatureClass_conversion(nwi_fc2, working_dir,
                                                nwi_fc3, nwi2_sql_query)

# Erase overlapping NWI features in the NHD  
if not arcpy.Exists(nhd_fc2):
    arcpy.Erase_analysis(nhd_fc, nwi_fc3, nhd_fc2)

# merge the nwi and nhd
if not arcpy.Exists(water_fc1):
    arcpy.Merge_management([nwi_fc3, nhd_fc2], water_fc1)


if not arcpy.Exists(geomorph_fc2):
    arcpy.Erase_analysis(geomorph_fc1, water_fc1, geomorph_fc2)

# merge the water fc and geomorph
if not arcpy.Exists(geomorph_fc3):
    arcpy.Merge_management([geomorph_fc2, water_fc1], geomorph_fc3)

# convert to raster
if not arcpy.Exists(out_raster1):
    arcpy.PolygonToRaster_conversion(geomorph_fc3, "GEOMORPH", out_raster1, "CELL_CENTER", "NONE" , 9)
else:
    raster1 = arcpy.Raster(out_raster1)

# make a null mask for the areas to use in the nibble
if not arcpy.Exists(out_raster2):
    print("set null")
    raster2 = arcpy.sa.SetNull(out_raster1,out_raster1,"VALUE IN (900, 2000, 3011)")
    raster2.save(out_raster2)
else:
    raster2 = arcpy.Raster(out_raster2)
        
# implement nearest neighbor on Qg2 (900) but keep water (2000, 3011) the same
if not arcpy.Exists(out_raster3):
    print("nearest neighbor nibble")
    raster3 = arcpy.sa.Con(out_raster1, out_raster1,
                           Nibble(out_raster1,
                                  out_raster2,
                                  "DATA_ONLY"),
                           "VALUE IN (2000, 3011)")
    raster3.save(out_raster3)
else:
    raster3 = arcpy.Raster(out_raster3)
    
# Now implement the the site potential rules
if not arcpy.Exists(out_raster4):
    print("Apply site potential rules")
    
    arcpy.env.extent = raster3
    arcpy.env.snapRaster = raster3
    
    # get the coordinate system
    coord_sys = arcpy.Describe(raster3).spatialReference
    arcpy.env.outputCoordinateSystem = coord_sys
    
    # read in the geomorhic codes and vegetation probabilities
    geodict = read_csv_dict(input_geomorph, key_col=1, val_col=[2, 8], skipheader=True)    
    
    # may need blocking here
    
    lowerLeft = arcpy.Point(raster3.extent.XMin, raster3.extent.YMin)
    cell_size = raster3.meanCellWidth    
    
    # in feet
    block_size = 45000
    
    block_cells = int(block_size / cell_size)
    
    # cols/rows
    x_width = raster3.width
    y_width = raster3.height
    
    x_min = raster3.extent.XMin
    y_min = raster3.extent.YMin
    
    x_max = raster3.extent.XMax
    y_max = raster3.extent.YMax
    
    na_value = raster3.noDataValue
    
    if na_value is None:
        na_value = 0
    
    raster4_names = []
    
    x_n = len(range(0, x_width, block_cells))
    y_n = len(range(0, y_width, block_cells))
    n_total = x_n * y_n
    block_n = 0
    
    # Build data blocks
    for x in range(0, x_width, block_cells):
        for y in range(0, y_width, block_cells):
            
            print("Processing block {0} of {1}".format(block_n+1, n_total))
            
            # Name the temp raster
            raster4_name = r"temp_block_{0}".format(block_n)
            
            # Lower left coordinate of block (in map units)
            block0_x_min = x_min + (x * cell_size)
            block0_y_min = y_min + (y * cell_size)
            # Upper right coordinate of block (in map units)
            block0_x_max = min([block0_x_min + block_size, x_max])
            block0_y_max = min([block0_y_min + block_size, y_max])
    
            block_array = arcpy.RasterToNumPyArray(raster3,
                                                     lower_left_corner=arcpy.Point(block0_x_min, block0_y_min),
                                                     ncols=block_cells , nrows=block_cells)
    
            # Continue to next block if there are no values
            if block_array.max() <= 0:
                del block_array
                block_n += 1
                continue
            
            # Continue to next block if it already exists 
            # but add to names list
            if arcpy.Exists(raster4_name):
                del block_array
                raster4_names.append(raster4_name)
                block_n += 1
                continue                
            
            # Get the count of unique values
            block_unique = numpy.unique(block_array, return_counts=False)
            
            for geocode in block_unique:
                
                if geocode in [na_value, 3011]: continue
                
                geocode_index = numpy.where(numpy.in1d(block_array.ravel(), [geocode]).reshape(block_array.shape))
                
                # Count the number of array elements equal to the geocode
                geocode_len = len(geocode_index[0])
                
                # Generate an equal number of site potential codes 
                # where the count of each site potential code is equal 
                # to the distribution established in the TMDL                
                param = geodict[str(geocode)]
                forest = [int(param[3])] * int(round(float(param[0]) * geocode_len))
                savanna = [int(param[4])] * int(round(float(param[1]) * geocode_len))
                prairie = [int(param[5])] * int(round(float(param[2]) * geocode_len))
                
                spc = forest + savanna + prairie
                
                m = geocode_len - len(spc)
                
                if m > 0:
                    # need to add some values
                    random.seed(33)
                    spc = spc + [int(param[random.randint(3, 5)]) for i in range(m)]
                    
                
                #  set the random seed so this is repeatable
                random.seed(42)
                # shuffle the order
                random.shuffle(spc)
                
                # replace array values with the site potential codes
                for i in range(0, geocode_len):
                    
                    r = geocode_index[0][i]
                    c = geocode_index[1][i]
                    block_array[r, c] = spc[i]
                    
                
                del geocode_index
            
            # Convert data block back to raster
            arcpy.env.extent = arcpy.Extent(block0_x_min, block0_y_min, block0_x_max, block0_y_max)
            raster4_block = arcpy.NumPyArrayToRaster(block_array,
                                                     arcpy.Point(block0_x_min, block0_y_min),
                                                         cell_size,
                                                         cell_size, na_value)
            # output the temp raster
            raster4_block.save(raster4_name)
            
            raster4_names.append(raster4_name)
            block_n += 1
            
            del block_array
            del raster4_block
                    
    #arcpy.MosaicToNewRaster_management(input_rasters=raster4_names,
    #                                   output_location=working_dir,
    #                                   raster_dataset_name_with_extension=out_raster4,
    #                                   pixel_type='16_BIT_UNSIGNED',
    #                                   number_of_bands=1)
    
    # Rebuild the attribute table because it does not seem to 
    # get compleated in the process above
    #arcpy.BuildRasterAttributeTable_management(in_raster=out_raster4, overwrite="Overwrite")
        
    # Remove temporary files
    if arcpy.Exists(out_raster4):
        for raster4_name in raster4_names:
            if arcpy.Exists(raster4_name):
                arcpy.Delete_management(raster4_name)

print("done")