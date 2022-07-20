import gensim
import traceback
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords

stemmer = PorterStemmer()


class WordSim:
    def __init__(self, model_dir):
        self.model_dir = model_dir
        try:
            self.model = gensim.models.KeyedVectors.load_word2vec_format(
                self.model_dir, binary=True)
        except Exception as e:
            print(e)
            self.model = None
            print("Cannot load pretrained vector for Word Similarity")

    def tokenize(self, text: str):
        text = remove_stopwords(text)
        return list(gensim.utils.tokenize(text))

    def most_similiar_tokens(self, text: str, sim_thresh=0.7, top_n=2):
        tokens = self.tokenize(text)
        similar_tokens = {}
        for word in tokens:
            try:
                max_count = 0
                if word.isalpha():
                    word = word.lower()
                    sim_words = self.model.most_similar(word)
                    sim_word_thresh = [x[0]
                                       for x in sim_words if x[1] > sim_thresh]
                    cleaned = self.clean_tokens(word, sim_word_thresh)
                    # get top 2 even after threshold
                    similar_tokens[word] = cleaned[:top_n]
            except Exception as e:
                print("Could not get similar token for ", word)
                print(traceback.format_exc())
        return similar_tokens

    def clean_tokens(self, orig, tokens):
        clean = []
        for idx, word in enumerate(tokens):
            if stemmer.stem(word) != stemmer.stem(orig) and orig not in word:
                clean.append(word)
        return clean
