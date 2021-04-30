from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import torch
from collections import OrderedDict

# import wikipedia as wiki


class DocumentReader:
    def __init__(
        self, pretrained_model_name_or_path="bert-large-uncased", use_gpu=False
    ):
        self.READER_PATH = pretrained_model_name_or_path
        self.tokenizer = AutoTokenizer.from_pretrained(self.READER_PATH)
        self.model = AutoModelForQuestionAnswering.from_pretrained(
            self.READER_PATH)
        self.max_len = self.model.config.max_position_embeddings
        self.chunked = False
        self.use_gpu = use_gpu

        if use_gpu:
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                self.use_gpu = use_gpu
            else:
                self.use_gpu = False

    def tokenize(self, question, text):
        self.inputs = self.tokenizer.encode_plus(
            question, text, add_special_tokens=True, return_tensors="pt"
        )
        self.input_ids = self.inputs["input_ids"].tolist()[0]
        if len(self.input_ids) > self.max_len:
            self.inputs = self.chunkify()
            self.chunked = True

    def chunkify(self):
        """
        Break up a long article into chunks that fit within the max token
        requirement for that Transformer model.

        Calls to BERT / RoBERTa / ALBERT require the following format:
        [CLS] question tokens [SEP] context tokens [SEP].
        """

        # create question mask based on token_type_ids
        # value is 0 for question tokens, 1 for context tokens
        qmask = self.inputs["token_type_ids"].lt(1)
        qt = torch.masked_select(self.inputs["input_ids"], qmask)
        chunk_size = self.max_len - qt.size()[0] - 1  # the "-1" accounts for
        # having to add an ending [SEP] token to the end

        # create a dict of dicts; each sub-dict mimics the structure of pre-chunked model input
        chunked_input = OrderedDict()
        for k, v in self.inputs.items():
            q = torch.masked_select(v, qmask)
            c = torch.masked_select(v, ~qmask)
            chunks = torch.split(c, chunk_size)

            for i, chunk in enumerate(chunks):
                if i not in chunked_input:
                    chunked_input[i] = {}

                thing = torch.cat((q, chunk))
                if i != len(chunks) - 1:
                    if k == "input_ids":
                        thing = torch.cat((thing, torch.tensor([102])))
                    else:
                        thing = torch.cat((thing, torch.tensor([1])))

                chunked_input[i][k] = torch.unsqueeze(thing, dim=0)
        return chunked_input

    def _get_answer(self):
        if self.chunked:
            answer = ""
            for k, chunk in self.inputs.items():
                if self.use_gpu:
                    chunk = {key: value.cuda() for key, value in chunk.items()}
                answer_start_scores, answer_end_scores = self.model(**chunk)

                answer_start = torch.argmax(
                    self.model(**chunk)["start_logits"])
                answer_end = torch.argmax(
                    self.model(**chunk)["end_logits"]) + 1

                ans = self.convert_ids_to_string(
                    chunk["input_ids"][0][answer_start:answer_end]
                )
                if ans != "[CLS]":
                    answer += ans + " / "
            return answer
        else:
            if self.use_gpu:
                self.inputs = {key: value.cuda() for key, value in inputs}
            answer_start_scores, answer_end_scores = self.model(**self.inputs)

            # get the most likely beginning of answer with the argmax of the score
            answer_start = torch.argmax(answer_start_scores)
            # get the most likely end of answer with the argmax of the score
            answer_end = torch.argmax(answer_end_scores) + 1

            return self.convert_ids_to_string(
                self.inputs["input_ids"][0][answer_start:answer_end]
            )

    def convert_ids_to_string(self, input_ids):
        return self.tokenizer.convert_tokens_to_string(
            self.tokenizer.convert_ids_to_tokens(input_ids)
        )

    def answer(self, question: str, wiki_results):
        print(f"Question: {question}")
        # wiki_results = wiki.search(question)
        # page = wiki.page(wiki_results[0])
        # print(f"Top wiki result: {page}")
        self.tokenize(question, wiki_results)
        answer = self._get_answer()
        return answer
