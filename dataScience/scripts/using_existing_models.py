from dataScience.src.search.semantic.models import D2V
from dataScience.src.text_handling.entity import Phrase_Detector
from dataScience.src.text_handling.process import preprocess

model_dir = "dataScience/src/modelzoo/semantic/models"
model_name = "2020072720_model.d2v"


phrase_detector = Phrase_Detector("id")
phrase_detector.load(model_dir)

model = D2V("id")
model.load(f"{model_dir}/{model_name}")

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
