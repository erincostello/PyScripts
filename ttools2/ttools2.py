from __future__ import division
from __future__ import print_function
from collections import defaultdict

class Blocks(object):
    """
    A block is a collection of stream nodes that are contained
    within a specfic coordinate extent (a bounding box). Organizing
    stream nodes into blocks makes it easier and more effceint to process
    a large number of stream nodes.
    """
    def __init__(self, **kwargs):
                
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        # order 0 left, 1 bottom, 2 right, 3 top
        self.block_extent = [xmin, ymin, xmax, ymax]
        self.nodes = nodes
        
class StreamReach(object):
    """
    A stream reach is a collecton of stream nodes organized
    in an upstream to downstream order.
    """
    def __init__(self, **kwargs):
        
        self.stream_id = stream_id
        self.nodes = nodes            
    
    def nested_dict(self): 
        """Build a nested dictionary"""
        return defaultdict(nested_dict)
            
    def get_stream_nodes(self):
        data = {}
        for attr in self.__slots:
            data[attr] = getattr(self,attr)
            
        return data
        
    def make_nodes(self):
        print("making nodes")
        
    def sort_nodes(self):
        print("sort nodes")
    
    def check_direction(self):
        print("checking direction")
        
    def calc_gradient(self):
        print("calculating gradient")
    

class StreamNode(object):
    """
    An individual stream segment defined as a stream node object.
    Stream nodes are a collection node attributes and methods to
    derive those attributes.
    
    """
    
    def __init__(self, **kwargs):
        
        __slots = ["node_id",
                   "stream_km", 
                   "point_x",
                   "point_y",
                   "elevation",
                   "gradient", 
                   "left", "right", "chanwid",
                   "topo",
                   "landcover", ]
        
        for attr in __slots:
            x = kwargs[attr] if attr in kwargs.keys() else None
            setattr(self, attr, x)
            self.__slots = __slots
            self.__slots.sort()
         
    def get_node_data(self):
        data = {}
        for attr in self.__slots:
            data[attr] = getattr(self,attr)
        return data
    
    def measure_width(self):
        print("measureing channel width")
        
        lb_distance = 3
        rb_distance = 4
        
        return lb_distance, rb_distance
        
    def sample_elevation(self):
        print("get elevations")
        
        z_node = 99
        
        return z_node
        
    def measure_topo_angles(self):
        print("get topo angles")
        
        topo = {w: 33,
                s: 21,
                e: 9,}
        
        return topo
        
    def sample_landcover(self):
        print("get landcover angles")
        
        topo = {w: 33,
                s: 21,
                e: 9,}
                
        return topo    