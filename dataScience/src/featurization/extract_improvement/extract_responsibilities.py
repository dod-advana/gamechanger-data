import os
try:
    os.chdir(os.path.join(os.getcwd(), 'c:\\Users\\602870\\Desktop\\gamechanger\\gamechanger'))
except:
    pass

import pandas as pd
import numpy as np
import re
import spacy as sp
import en_core_web_sm
import time

from dataScience.src.utilities.text_utils import simple_clean
from dataScience.src.featurization.extract_improvement import extract_entities, create_list_from_dict
import dataScience.src.utilities.spacy_model as spacy_

spacy_model = spacy_.get_lg_nlp()

data = pd.read_csv('dataScience/src/featurization/extract_improvement/data/pipe.csv')
combined_cols = pd.DataFrame(data[data.columns[1:]].apply(lambda x: ','.join(x.dropna().astype(str)), axis=1), columns=['text'])
combined_cols_list = combined_cols['text'].tolist()

start = time.time()
per_doc_list = []
all_docs = []

for i in range(len(combined_cols_list)):
    sentence = combined_cols_list[i]
    entities = extract_entities(sentence, spacy_model)
    flat_entities = create_list_from_dict(entities)
    flat_entities = '|'.join(i for i in flat_entities)
    all_docs.append(flat_entities)

data['new_entities'] = all_docs
print('Elapsed seconds:', time.time() - start)

data.to_csv('dataScience/src/featurization/extract_improvement/model_outputs/full_pipe_w_new_entities_022321_test.csv')