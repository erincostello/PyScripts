import imp
import os
from collections import defaultdict


#ttools2_path = r"C:\WorkSpace\GitHub\TTools\ttools2.py"

ttools2_path = r"/Users/rmichie/Documents/GitHub/PyScripts/ttools2/ttools2.py"

ttools = imp.load_source("ttools2", ttools2_path)

def nested_dict(): 
    """Build a nested dictionary"""
    return defaultdict(nested_dict)

def read_nodes_fc1(overwrite_data = True , addFields = None):
    """Reads the input point feature class and returns the STREAM_ID, NODE_ID, and X/Y coordinates as a nested dictionary"""
    
    node = nested_dict()
    stream = nested_dict()

    incursorFields = ["STREAM_ID","NODE_ID", "STREAM_KM", "SHAPE@X","SHAPE@Y"]
    
    arcobject = [["sid1", 1, 0.00, -122.3, 45.3 ],
                 ["sid1", 2, 0.05, -122.3, 45.3 ],
                 ["sid1", 3, 0.10, -122.3, 45.3 ],
                 ["sid2", 4, 0.00, -122.3, 45.3 ],
                 ["sid2", 5, 0.00, -122.3, 45.3 ],
                 ]

    if overwrite_data:
        for row in arcobject:
            stream1 = ttools.StreamReach(stream_id = row[0], 
                                        node_id = row[1])
            
            stream[row[0]] = stream1
        
            node1 = ttools.StreamNode(node_id = row[1],
                                     stream_km = row[2], 
                                     point_x = row[3],
                                     point_y = row[4])
            node[row[1]] = node1
    else:
        for row in arcobject:
            # if the data is null or zero (0 = default for shapefile),
            # it is retreived and will be overwritten.
            if row[5] is None or row[5] == 0 or row[5] < -9998:
                stream1 = ttools.StreamReach(stream_id = row[0], 
                                            node_id = row[1])
                
                stream[row[0]] = stream1
            
                node = ttools.StreamNode(node_id = row[1],
                                         stream_km = row[2], 
                                         point_x = row[3],
                                         point_y = row[4])
                node[row[1]] = node1
                    
    if len(node) == 0:
        sys.exit("The fields checked in the input point feature class "+
                 "have existing data. There is nothing to process. Exiting")
            
    return(stream, node)


stream, node = read_nodes_fc1()
print("blah")

