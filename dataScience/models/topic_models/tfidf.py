from gensim.models.phrases import Phraser
from dataScience.src.featurization.topic_modeling import Topics
import os

base = os.path.dirname(os.path.realpath(__file__))
model_dir = os.path.join(base, 'models')
# this needs to be redone 
try:
    tfidf_model = Topics(model_dir, False)
    bigrams = Phraser.load(os.path.join(model_dir, 'bigrams.phr'))
except Exception as e:
    print(e)
    print("cannot load tfidf")

