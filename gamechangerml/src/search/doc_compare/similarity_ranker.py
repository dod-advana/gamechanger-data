
from os.path import join
from txtai.pipeline import Similarity

class SimilarityRanker:
    def __init__(self, sim_model_name, transformer_path):

        self.sim_model = join(transformer_path, sim_model_name)
        self.similarity = Similarity(self.sim_model)

    def re_rank(self, query, top_docs):
        results = []
        texts = [x["text"] for x in top_docs]
        scores = self.similarity(query, texts)
        for idx, score in scores:
            doc = {}
            doc["score"] = score
            doc["id"] = top_docs[idx]["id"]
            doc["text"] = top_docs[idx]["text"]
            results.append(doc)
        return results
