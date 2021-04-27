from shapely.geometry import Polygon, LineString, Point, MultiPolygon, MultiLineString, MultiPoint
from shapely.ops import transform
import random
import pyproj
import pandas as pd


class filtertags:
    
    def __init__(self, df_filter_tags):
        self.filter_tags_df = df_filter_tags
        self.tag_list = []
        self.generate_tag_list()
        
        
    def generate_tag_list(self,):
        # this takes a dataframe and appends the tags pressent in it 
        # to the tag list
        for row in self.filter_tags_df.iterrows():
            self.tag_list.append(f"{row[1]['key']} {row[1]['value']}")
        
    def filter_them(self,row):
        # this function looks if key,value are present in the tag_list 
        # if so it returns true
        r_value = False

        if row['tags']:
            for key in row['tags'].keys():
                if f"{key} {row['tags'][key]}" in self.tag_list:
                     r_value = True
    
        return r_value
    
    def calcualte_size_for_tags(self,row):
    
        geometry, tags, name  = row['geometry'], row['tags'] , row.name
        sizes_dict = {}
        # it seems that sometimes the geometry for a featuer can not be resolved
        try:
            for key in geometry.keys():
                if 'line' in key:
                    sizes_dict['length'] = line_length(geometry[key])
                elif 'poly' in key:
                    sizes_dict['area'] = poly_area(geometry[key])
        except:
            print(f'geometry could not be resolved for {name}')
            sizes_dict['area'] = None

        # we only keep tag key combinations that are part of tag_list     
        key_val_list = [f'{key} {tags[key]}' for key in tags.keys() if f'{key} {tags[key]}' in self.tag_list]

        return_dict = {}

        # a geometry might have more than one relevant tag
        # {'tag_key':{'length':,'area':},'tag_key2':{'length':,'area':}}
        for key_val in key_val_list:
            return_dict[key_val] = sizes_dict

        return return_dict
        
        
def random_bb(size,constrain=None):
    # size has to be in degrees since to BB for osm is in degrees
    # constrain has to be a shapely (multi-)polygon and can be used to limit the area
    
    # if a constrain exist we shrink the possibility space donw to the bounds of it 
    if constrain:
        minx, miny, maxx, maxy = constrain.bounds
    else:
        minx, miny, maxx, maxy = -180,-90,180,90
    
    # we generate first the lower left corner of the bounding box
    if constrain:
        # when an constrain exist we make shure the point is within it
        ll_x,ll_y =-9999999,-9999999
        while not constrain.contains(Point(ll_x, ll_y)):
            ll_x,ll_y = random.uniform(minx, maxx),random.uniform(miny, maxy)
    else:
        ll_x,ll_y = random.uniform(minx, maxx),random.uniform(miny, maxy)

    return Polygon([(ll_x,ll_y),(ll_x+size,ll_y),(ll_x+size,ll_y+size),(ll_x,ll_y+size)])


def line_length(line):
    
    geod = pyproj.Geod(ellps='WGS84')
    line_length = geod.geometry_length(line)

    return abs(line_length)


def poly_area(poly):

    geod = pyproj.Geod(ellps='WGS84')
    poly_area = geod.geometry_area_perimeter(poly)[0]
    
    return abs(poly_area)