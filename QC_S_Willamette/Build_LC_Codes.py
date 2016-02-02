""""
This script builds the landcover codes input csv for heat source based on
using the ttools nodes feature class
"""

from __future__ import print_function
import arcpy
import csv
from operator import itemgetter
from os.path import join
from os.path import exists


# ----------------------------------------------------------------------
# Start Fill in Data
# --- Current Conditons Settings
nodes_fc = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\TTools_Sim01_Current.gdb\Nodes_Current"
outputdir = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Landcover_Codes"
canopy_cover = 0.85
transsample_count = 15
trans_count = 8
lccode_filename = "lccodes_current.csv"
exclude_nodes = True
exclude_field = "EXCLUDE"
include_value = "False"  #  This value is what indicates the node is kept
lccode_colnames = ["NAME", "CODE", "HEIGHT", "CANOPY_COVER", "OVERHANG"]
# ----------------------------------------------------------------------


def ft2m(ft):
    """converts feet to meters"""
    return float(ft) * 0.3048

def setup_LC_data_headers(transsample_count, trans_count, heatsource8=False):
    """Generates a list of the landcover data file
    column header names and data types"""

    type = ["LC"]

    lcdataheaders =["STREAM_KM","LONGITUDE","LATITUDE","TOPO_W","TOPO_S","TOPO_E"]
    # a flag indicating the model should use the heat source 8 methods 
    # (same as 8 directions but no north)
    if heatsource8 is True:
        dirs = ["T{0}".format(x) for x in range(1, 8)]
    else:        
        dirs = ["T{0}".format(x) for x in range(1, trans_count + 1)]

    zones = range(1,int(transsample_count)+1)

    # Concatenate the type, dir, and zone and order in the correct way
    for t in type:
        for d, dir in enumerate(dirs):
            for z, zone in enumerate(zones):
                if t !="ELE" and d==0 and z==0:
                    #lcdataheaders.append(t+"_EMERGENT") # add emergent
                    lcdataheaders.append(t+"_T0_S0") # add emergent
                    lcdataheaders.append("{0}_{1}_S{2}".format(t, dir, zone))
                else:
                    lcdataheaders.append("{0}_{1}_S{2}".format(t, dir, zone))

    return lcdataheaders

def make_lc_codes(lcdata_in, canopy_cover, trans_count, transsample_count):
    """
    This function reads in landcover codes from the land cover
    data file and generates the landcover code file
    based on all the unique codes.
    """
    codes = set()
    
    for row in lcdata_in:
        for col in range(8, (trans_count * transsample_count) + 9):
            c = str(int(float(row[col])))
            codes.add(str(int(float(row[col]))))
            if float(c) > -9997:
                if float(c[-3:]) > 656:
                    nodes.add(str(row[1]))
    
    codes = list(codes)
    codes.sort()

    lccodes = []
    for code in codes:
        
        if float(code) < -9997:
            lccodes.append(["Current", float(code), 0, 0, 0])
        else:
            lccodes.append(["Current", float(code), ft2m(code[-3:]), canopy_cover, 0])
        
    return(lccodes)


def make_sp_codes(lcdata_in, input_geomorph, trans_count, transsample_count):
    """
    This function translates geomorphic codes into site potential
    vegetation codes as described in the Willamette Basin TMDL.
    The function is based on Brian Kasper's VB macro located here:
    \\deqhq1\TMDL\Library (weekly backup)\Willamette-Basinwide\Potential Veg\
    Subbasin System Potential Veg calc.xls
    """
    # read in the geomorhic codes and vegetation probabilities
    geodict = read_csv_dict(input_geomorph, key_col=1, val_col=[2, 8], skipheader=True)
    
    # set the random seed so this is repeatable
    random.seed(42)
    
    lcdata_out = []
    
    for row in lcdata_in:
        for col in range(8, (trans_count * transsample_count) + 9):
            rnd = random.randint(1, 100) / 100
            geocode = str(int(float(row[col])))
            param = geodict[geocode]
            
            if rnd <= float(param[0]):
                spc = param[3]
            elif rnd <= float(param[0]) + float(param[1]):
                spc = param[4]
            else:
                spc = param[5]
            row[col] = int(spc)
        lcdata_out.append(row)
    
    return lcdata_out

def read_nodes_fc(nodes_fc, readfields, wherecluase):
    """Reads an input point file and returns the fields as a
    list"""
    incursorFields = ["STREAM_ID","NODE_ID"] + readfields
    # Determine input point spatial units
    proj = arcpy.Describe(nodes_fc).spatialReference
    
    lcdata = []
            
    with arcpy.da.SearchCursor(nodes_fc, incursorFields, whereclause, proj) as Inrows:
        for row in Inrows:
            lcdata.append(row)  
    return(lcdata)

def write_csv(outputdir, filename, colnames, outlist):
    """write the output list to csv"""
    
    # insert column header names
    outlist.insert(0, colnames)
    
    with open(join(outputdir, filename), "wb") as file_object:
        writer = csv.writer(file_object,  dialect= "excel")
        writer.writerows(outlist) 

lcsample_headers = setup_LC_data_headers(transsample_count, trans_count)


# Build a query to retreive just the nodes that are needed
if exclude_nodes:
    whereclause = """{0} = '{1}'""".format(exclude_field, include_value)

lcdata_list = read_nodes_fc(nodes_fc, lcsample_headers, whereclause)
lccodes, nodes = make_lc_codes(lcdata_list, canopy_cover, trans_count, transsample_count)

write_csv(outputdir, lccode_filename, lccode_colnames, lccodes)
write_csv(outputdir, "9998_nodes.csv", ["NODE_ID"], nodes)




print("done")