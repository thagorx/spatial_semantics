import parse_osm
import tag_handler
from shapely.geometry import Polygon
import pandas as pd
import geopandas as gpd
from gensim.corpora.wikicorpus import WikiCorpus
from gensim.models.doc2vec import Doc2Vec, TaggedDocument


class Spatial_Semantic_Vector:
    
    def __init__(self, tag_df_path, tag_median_size_df_path):
        self.tag_df =  pd.read_pickle(tag_df_path)
        self.tag_median_size_df = pd.read_pickle(tag_median_size_df_path).set_index(['key','value']).sort_index()
        # replace pd nan with None
        self.tag_median_size_df = self.tag_median_size_df.where(pd.notnull(self.tag_median_size_df), None)
        self.filtertags_handler = tag_handler.filtertags(self.tag_df)
        # from here on out we want key value in the tag_df as the index because it makes
        # the look up faster
        # we sort the index to handle the "1: PerformanceWarning: indexing past lexsort 
        # depth may impact performance." Warning
        self.tag_df = self.tag_df.set_index(['key','value']).sort_index()
        self.doc2vec_model = Doc2Vec.load("../data/en_wikipedia_corpus/doc2vec_eng.pickel")

    def _compose_document(self, element):
        # example element:
        # {'leisure pitch': {'area': 373.27528143301606}, 'sport basketball': {'area': 373.27528143301606}}
        doc_shard = ''
        for key in element.keys():
            group, sub_type =  key.split(' ')
            # we lookup the combination in the tag_df
            row = self.tag_df.loc[group, sub_type]
            # and retrieve both the wikidata and the wikipedia text from it
            wikidata_desc = row.iloc[0].wikidata_desc
            wikipedia_desc = row.iloc[0].en_text

            # now we test if we aktualy have wikipedia text
            if wikipedia_desc:
                text = wikipedia_desc
            # if not we take the wikidata description instead
            else:
                text = wikidata_desc

            # now we test if we have an area or a lenght for the group sub_type combo
            if element[key]:
                # this is uqly and needs restructuring:
                if element[key].get('area'):
                    area = element[key].get('area')
                    # now we need to get the median area for this group sub_type combo
                    try:
                        m_area = self.tag_median_size_df.loc[group,sub_type].median_area
                    except:
                        m_area = None

                    if m_area:
                        doc_shard += self._text_weigher(text,area/m_area)
                    else:
                        # if we dont have an median we wiegh with 0
                        doc_shard += self._text_weigher(text,0)  

                if element[key].get('length'):
                    length = element[key].get('length')
                    # now we need to get the median area for this group sub_type combo
                    try:
                        m_length = self.tag_median_size_df.loc[group,sub_type].median_length
                    except:
                        m_length = None

                    if m_length:
                        doc_shard += self._text_weigher(text,length/m_length)
                    else:
                        # if we dont have an median we wiegh with 0
                        doc_shard += self._text_weigher(text,0)                

            else:
                # else is the case when the element is just a node thus it does not
                # have an area or length
                doc_shard += self._text_weigher(text,0)

        return doc_shard

    def _text_weigher(self, text, weight):
        # for the time beeing we just round the weight to the next intiger
        weight = round(weight)

        if weight <= 1 :
            # we want the text atleast once 
            w_text = text

        else:
            text += ' '
            w_text = text*weight

        return w_text

    def _clip_2d_features(self, feature):
        feature_cliped = {}
        for geometry in ['line','polygon', 'multipolygon', 'multiline', 'multipoint']:
            if feature.get(geometry):
                # if we found a geometry we clip it to the extent of the bounding box
                intersection = self.boundingbox.intersection(feature.get(geometry).buffer(0))
                if intersection:
                    feature_cliped[geometry] = intersection
        if 'point' in feature:
            # points are simply copied over
            feature_cliped['point'] = feature['point']

        return feature_cliped

    def generate_vec(self, boundingbox):
        self.boundingbox = boundingbox
        # first we fetch for the given boundingbox features from OSM:
        osm_handle = parse_osm.disect_osm(parse_osm.json_from_osm(boundingbox))
        # from these features we filter out the features with tags that we have documents for 
        selected_tags_df = osm_handle.feature_df[osm_handle.feature_df.apply(self.filtertags_handler.filter_them, axis = 1)]
        # we then cast these features to a list so that in the next step we generate thier geometry
        type_id_list = selected_tags_df.index.tolist()
        # for the selected features we calculate the geometry:
        [osm_handle.get_geometry(f_type,osm_id) for f_type, osm_id in type_id_list]
        #then we have to reslect the dataframe and make a copy of it for further proccesing
        selected_tags_df = osm_handle.feature_df[osm_handle.feature_df.apply(self.filtertags_handler.filter_them, axis = 1)].copy()
        # we need to clip the 2 dimensional feautres to the extent of the $boundingbox
        selected_tags_df['geometry'] = selected_tags_df['geometry'].apply(self._clip_2d_features)
        # filter out feauters who no longer have a geometry after clipping
        selected_tags_df = selected_tags_df.loc[selected_tags_df['geometry']!={}]
        # lastly for the found featres with tags that intresst us we wiegh thier size 
        # (if ther is one) and combine them into a meta document
        combined_document = ''
        for element in selected_tags_df[['geometry','tags']].apply(self.filtertags_handler.calcualte_size_for_tags, axis=1).tolist():
            # and then we add the document shard for a given element
            combined_document += self._compose_document(element)
            # some padding
            combined_document += ' '
        # the combinded document we feed into ou doc2vec model and generate a vector
        vec = self.doc2vec_model.infer_vector(combined_document.split(' '))

        return vec