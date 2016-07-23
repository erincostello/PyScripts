import imp
import os


ttools2_path = r"C:\WorkSpace\GitHub\TTools\ttools2.py"

ttools = imp.load_source("ttools2", ttools2_path)


def nested_dict(self): 
    """Build a nested dictionary"""
    return defaultdict(nested_dict)   

def read_nodes_fc(nodes_fc, overwrite_data, addFields):
    """Reads the input point feature class and returns the
    STREAM_ID, NODE_ID, and X/Y coordinates as a nested dictionary"""
    
    nodeDict = nested_dict()
    incursorFields = ["STREAM_ID","NODE_ID", "STREAM_KM", "SHAPE@X","SHAPE@Y"]

    # Get a list of existing fields
    existingFields = []
    for f in arcpy.ListFields(nodes_fc):
        existingFields.append(f.name)     

    # Check to see if the 1st field exists if yes add it.
    if overwrite_data is False and (addFields[0] in existingFields) is True:
        incursorFields.append(addFields[0])
    else:
        overwrite_data = True

    # Determine input point spatial units
    proj_nodes = arcpy.Describe(nodes_fc).spatialReference

    with arcpy.da.SearchCursor(nodes_fc,incursorFields,"",proj_nodes) as Inrows:
        if overwrite_data is True:
            for row in Inrows:
                StreamNode(node_id=row[1], 
                           stream_km = row[2],
                           point_x = row[3],
                           point_y = row[4])
        else:
            for row in Inrows:
                # if the data is null or zero (0 = default for shapefile),
                # it is retreived and will be overwritten.
                if row[5] is None or row[5] == 0 or row[5] < -9998:
                    StreamNode(node_id=row[1], 
                               stream_km = row[2],
                               point_x = row[3],
                               point_y = row[4])
    if len(nodeDict) == 0:
        sys.exit("The fields checked in the input point feature class "+
                 "have existing data. There is nothing to process. Exiting")
            
    return(nodeDict)


node = ttools.StreamNode()
block = ttools.Blocks()




print("blah")

