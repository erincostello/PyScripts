# -----------------------------------------------------------------------
# This script generates heat source landcover data inputs for all 
# combinations of supplied stream azimuth, vegetation height, density, 
# sky gap width, and left and right buffer widths.

# It is setup to generate different north/south side buffer widths at different stream azimuths.
# See model specfic scenarios

# Ryan Michie
# Oregon Dept. Enivironmental Quality
# 7/1/2015
# -----------------------------------------------------------------------

from __future__ import print_function
from __future__ import division
from numpy import * 
import numpy as np
from math import degrees, radians, sin, cos
import matplotlib.path as mppath
import itertools
import csv

# Designate outfile path and name
outpathfile = r"C:\WorkSpace\ODF_Riparian_Rulemaking\Modeling\North_Side_Topo\Heat_Source\lcdata_python_output.csv"
sim1path = r"C:\WorkSpace\ODF_Riparian_Rulemaking\Modeling\North_Side_Topo\Heat_Source\lcdata_python_sim1_.csv"
sim2path = r"C:\WorkSpace\ODF_Riparian_Rulemaking\Modeling\North_Side_Topo\Heat_Source\lcdata_python_sim2_.csv"
sim3path = r"C:\WorkSpace\ODF_Riparian_Rulemaking\Modeling\North_Side_Topo\Heat_Source\lcdata_python_sim3_.csv"
sim4path = r"C:\WorkSpace\ODF_Riparian_Rulemaking\Modeling\North_Side_Topo\Heat_Source\lcdata_python_sim4_.csv"

trans_count = 32
transsample_distance = 3
transsample_count = 12 # does not include a sample at the stream node

type = ["LC"]
vgp_list = [0]
vht_list = [1]
vdn_list = [.60]

# buffers in feet = [20, 40, 60, 70, 80, 90, 100, 110]
# south side
vwd_right_list = [6.096, 12.192, 18.288, 21.336, 24.384, 27.432, 30.48, 33.528]

# north side
vwd_left_list = [6.096, 12.192, 18.288, 21.336, 24.384, 27.432, 30.48, 33.528, 0]
azimuth_list = [45, 50, 60, 70, 80, 90, 100, 110, 120, 130, 135]

node_x = 0
node_y = 0

def expandgrid(varnames, *itrs):
    """Creates an array from all combinations of the supplied vectors.
    Same as expand.grid() function in R"""
    product = list(itertools.product(*itrs))
    return {'{0}'.format(varnames[i]):[x[i] for x in product] for i in range(len(itrs))}

def setup_LC_data_headers(transsample_count, trans_count,
                          canopy_data_type, stream_sample, type):
    """Generates a list of the landcover data file
    column header names and data types"""

    lcdataheaders =[]
     
    dir = ['T' + str(x) for x in range(1, trans_count + 1)]

    zone = range(1,int(transsample_count)+1)

    # Concatenate the type, dir, and zone and order in the correct way
    for t in type:
        for d in range(0,len(dir)):
            for z in range(0,len(zone)):
                if stream_sample is True and t !="ELE" and d==0 and z==0:
                    #lcdataheaders.append(t+"_EMERGENT") # add emergent
                    lcdataheaders.append(t+"_T0_S0") # add emergent
                    lcdataheaders.append(t+"_"+dir[d]+"_S"+str(zone[z]))
                else:
                    lcdataheaders.append(t+"_"+dir[d]+"_S"+str(zone[z]))

    return lcdataheaders

lcdataheaders = setup_LC_data_headers(transsample_count, trans_count, 
                                     "CanopyCover", 
                                     True, type)
varnames = ["vht", "vdn", "azimuth", "vgp", "vwd_left", "vwd_right"]
lc_combos = expandgrid(varnames, vht_list,vdn_list, azimuth_list,vgp_list,vwd_left_list, vwd_right_list)
lc_combos['node'] = range(1,len(lc_combos['vht'])+1)
 
dir = [x * 360.0 / trans_count for x in range(1,trans_count+ 1)]

# calculate the xy coordinates of each sample
lc_xy = []
for d in range(0,len(dir)):                       
    for s in range(1,int(transsample_count+1)):
        # Calculate the x and y coordinate of the 
        # landcover sample location
        lc_x = (s * transsample_distance *
                sin(radians(dir[d])) + node_x)
        lc_y = (s * transsample_distance *
                cos(radians(dir[d])) + node_y)
        lc_xy.append((lc_x, lc_y))

# these are static multiplier values to get perpendicular to the stream 
# azimuth and contruct the buffer polygons
line1 = array([1, -1, -1, 1, 1])
line2 = array([-90, -90, 90, 90, -90])
line3 = array([1, 1, 0, 0, 1])
buffer_l_line = array([1, 1, -1, -1, 1])
buffer_r_line = array([-1, -1, 1, 1, -1])
centerline_dis = array(transsample_distance * (transsample_count + 1) * line1)

#varnames = ["vht", "vdn", "azimuth", "vgp", "vwd"]
for node in xrange(0, len(lc_combos['node'])):
    
    vht0 = lc_combos["vht"][node]
    vdn0 = lc_combos["vdn"][node]
    azm0 = lc_combos["azimuth"][node]
    vgp0 = lc_combos["vgp"][node]
    vwdl = lc_combos["vwd_left"][node]
    vwdr = lc_combos["vwd_right"][node]

    centerline_x = array(centerline_dis * sin(radians(azm0)) + node_x)
    centerline_y = array(centerline_dis * cos(radians(azm0)) + node_y)
    
    # Calculate x and y vertex coordinates of the stream polygon 
    stream_x = array((vgp0/2 * sin(radians(azm0+vgp0))) + centerline_x)
    stream_y = array((vgp0/2 * cos(radians(azm0+vgp0))) + centerline_y)
    stream_xy = zip(stream_x,stream_y)
    stream_poly = mppath.Path(stream_xy)
       
    buffer_l_dis = array(buffer_l_line*abs((vgp0/2) + (vwdl*line3)))
    buffer_r_dis = array(buffer_r_line*abs((vgp0/2) + (vwdr*line3)))
    
    # calculate x/y vertex coordindates of the left/right buffer
    buffer_l_x = array(buffer_l_dis * np.sin(np.radians(azm0+line2)) + centerline_x)
    buffer_l_y = array(buffer_l_dis * np.cos(np.radians(azm0+line2)) + centerline_y)
    buffer_r_x = array(buffer_r_dis * np.sin(np.radians(azm0+line2)) + centerline_x)
    buffer_r_y = array(buffer_r_dis * np.cos(np.radians(azm0+line2)) + centerline_y)
    
    buffer_l_xy = zip(buffer_l_x,buffer_l_y)
    buffer_l_poly = mppath.Path(buffer_l_xy)
    
    buffer_r_xy = zip(buffer_r_x,buffer_r_y)
    buffer_r_poly = mppath.Path(buffer_r_xy)
    
    lc_r = buffer_r_poly.contains_points(lc_xy)
    lc_l = buffer_l_poly.contains_points(lc_xy)
    
    # Put the Left and Right together
    # logic works like this:  
    # True + True = True, 
    # True + False = True, 
    # False + False = False        
    lc = lc_r + lc_l
    print(lc)
    
    
    # True = inside the veg buffer, replace w/ veght
    veghtcode = array([vht0 if x==True else 0 for x in lc])
    
    # north/south string in feet
    ns_str = str(int(vwdl*3.28084)) +" | "+str(int(vwdr*3.28084))
    node_sample = [0]
    ttools_header = hstack(("node", varnames, "north_south", lcdataheaders))
    ttools_node = hstack((node,vht0,vdn0,azm0,vgp0,vwdl,vwdr,ns_str, 
                          node_sample,veghtcode))  
    
    # add the the header on the first loop or the results from previous loops
    if node == 0:
        ttools = vstack((ttools_header,ttools_node)) 
    else: 
        ttools = vstack((ttools,ttools_node))        

# This subsets the data for each specfic scenario
# Sim 01 - equal side buffers
sim1 = [node for node in ttools if node[5] == node[6]]
sim1.insert(0, ttools[0])

# Sim 02 - 20 foot northside buffers
sim2 = [node for node in ttools if node[5] == '6.096']
sim2.insert(0, ttools[0])

# Sim 03 - 40 foot northside buffers
sim3 = [node for node in ttools if node[5] == '12.192']
sim3.insert(0, ttools[0])

# Sim 04 - 0 foot northside buffers
sim4 = [node for node in ttools if node[5] == '0']
sim4.insert(0, ttools[0])

# write to csv output
with open(outpathfile, 'wb') as file_object:
    writer = csv.writer(file_object, dialect= "excel")
    writer.writerows(ttools)

with open(sim1path, 'wb') as file_object:
    writer = csv.writer(file_object, dialect= "excel")
    writer.writerows(sim1)
    
with open(sim2path, 'wb') as file_object:
    writer = csv.writer(file_object, dialect= "excel")
    writer.writerows(sim2)

with open(sim3path, 'wb') as file_object:
    writer = csv.writer(file_object, dialect= "excel")
    writer.writerows(sim3)
    
with open(sim4path, 'wb') as file_object:
    writer = csv.writer(file_object, dialect= "excel")
    writer.writerows(sim4)

print("done")