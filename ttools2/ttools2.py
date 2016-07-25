from __future__ import division
from __future__ import print_function

class Blocks(object):
    """
    A block object is a specfic coordinate extent (a bounding box)
    with a collection of stream nodes that are contained
    within the extent.
    """
     
    def __init__(self, **kwargs):
        
        attrs = ["id", "xmin", "ymin", "xmax", "ymax", "nodes"]
        
        for attr in attrs:
            x = kwargs[attr] if attr in kwargs.keys() else None
            setattr(self, attr, x)       
                
        
class StreamReach(object):
    """
    A stream reach object is a collecton of stream nodes.
    """
      
    def __init__(self, **kwargs):

        attrs = ["nodes", "stream_km"]        
        
        for attr in attrs:
            x = kwargs[attr] if attr in kwargs.keys() else None
            setattr(self, attr, x)
         
    def get_node_data(self):
        data = {}
        for attr in self.__slots:
            data[attr] = getattr(self,attr)
        return data
                                    
    def make_nodes(self):
        print("making nodes")
        
        self.nodes = [1, 2, 3, 4]
        
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
        
        attrs = ["node_id",
                 "stream_id"
                 "stream_km", 
                 "point_x",
                 "point_y",
                 "elevation",
                 "gradient", 
                 "left", "right", "chanwid",
                 "topo",
                 "landcover"]
        
        for attr in attrs:
            x = kwargs[attr] if attr in kwargs.keys() else None
            setattr(self, attr, x)
             
    def measure_width(self):
        print("measureing channel width")
        
        self.lb_distance = 3
        self.rb_distance = 4
                
    def sample_elevation(self):
        print("get elevations")
        
        self.elevation = 99
        
        
    def measure_topo_angles(self):
        print("get topo angles")
        
        self.topo = {w: 33,
                s: 21,
                e: 9,}
        
    def sample_landcover(self):
        print("get landcover")
        
        self.landcover = {w: 1,
                s: 2,
                e: 3,}   