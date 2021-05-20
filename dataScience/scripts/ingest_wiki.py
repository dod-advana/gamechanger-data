from datetime import datetime
from elasticsearch import Elasticsearch

from gensim.corpora.wikicorpus import WikiCorpus
wiki_dump = 'simplewiki-20170820-pages-meta-current.xml.bz2'

corpus = WikiCorpus(wiki_dump)

es = Elasticsearch()
for i in corpus.get_texts():
    print(i)
    wiki_doc = " ".join(i)
    doc = {"text": wiki_doc, "timestamp": datetime.now()}
    es.index(index="simple-wiki", body=doc)
