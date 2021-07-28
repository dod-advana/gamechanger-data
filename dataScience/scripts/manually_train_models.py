from dataScience.src.search.semantic.models import D2V
from dataScience.src.text_handling.corpus import LocalCorpus, LocalTaggedCorpus
from dataScience.src.text_handling.entity import Phrase_Detector
from dataScience.src.text_handling.process import preprocess
from dataScience.configs.D2V_Config import Config

corp_dir = Config.CORPUS_DIR
model_dir = Config.MODEL_DIR

corpus = LocalCorpus(corp_dir)
print("Training Phrase_Detector")
phrase_detector = Phrase_Detector(Config.MODEL_ID)
phrase_detector.train(corpus)
phrase_detector.save(model_dir)

print("Training D2V")
tagged_corpus = LocalTaggedCorpus(corp_dir, phrase_detector)
model = D2V(Config.MODEL_ID)
model.train(Config.MODEL_ARGS, tagged_corpus)
model.save(model_dir, False)

tokens = preprocess(
    "National Park",
    min_len=1,
    phrase_detector=phrase_detector,
    remove_stopwords=True,
)
print(model.infer(tokens))

tokens = preprocess(
    "National Parks",
    min_len=1,
    phrase_detector=phrase_detector,
    remove_stopwords=True,
)
print(model.infer(tokens))

tokens = preprocess(
    "taxes", min_len=1, phrase_detector=phrase_detector, remove_stopwords=True
)
print(model.infer(tokens))
