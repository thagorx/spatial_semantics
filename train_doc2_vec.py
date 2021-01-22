#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from gensim.corpora.wikicorpus import WikiCorpus
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from pprint import pprint
import multiprocessing
import pickle


# In[ ]:


#https://markroxor.github.io/gensim/static/notebooks/doc2vec-wikipedia.html


# In[ ]:


wiki = WikiCorpus("../data/en_wikipedia_corpus/enwiki-latest-pages-articles.xml.bz2")


# In[ ]:


import pickle
pickle.dump(wiki, open( "../data/en_wikipedia_corpus/corpus.pickel", "wb" ))


# In[ ]:


class TaggedWikiDocument(object):
    def __init__(self, wiki):
        self.wiki = wiki
        self.wiki.metadata = True
    def __iter__(self):
        for content, (page_id, title) in self.wiki.get_texts():
            yield TaggedDocument([c for c in content], [title])


# In[ ]:


wiki = pickle.load(open( "../data/en_wikipedia_corpus/corpus.pickel", "rb"))


# In[ ]:


documents = TaggedWikiDocument(wiki)
pickle.dump(documents, open( "../data/en_wikipedia_corpus/TaggedWikiDocument.pickel", "wb" ))


# In[ ]:


documents = pickle.load(open( "../data/en_wikipedia_corpus/TaggedWikiDocument.pickel", "rb" ))


# In[ ]:


doc2vec_model = Doc2Vec(dm=0, dbow_words=1, vector_size=200, window=8, min_count=19, epochs=20, workers=8)


# In[ ]:


doc2vec_model.build_vocab(documents)
doc2vec_model.train(documents)
doc2vec_model.save("../data/en_wikipedia_corpus/doc2vec_eng.pickel")
print('done')


# In[ ]:




