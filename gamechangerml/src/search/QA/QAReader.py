"""
Based on original code sourced from Cloudera's Fast Forward Labs (https://qa.fastforwardlabs.com/)
Authors: Melanie R. Beck, PhD; Andrew Reed
Accessed: May 2021
Availability: https://qa.fastforwardlabs.com/pytorch/hugging%20face/wikipedia/bert/transformers/2020/05/19/Getting_Started_with_QA.html,
https://qa.fastforwardlabs.com/no%20answer/null%20threshold/bert/distilbert/exact%20match/f1/robust%20predictions/2020/06/09/Evaluating_BERT_on_SQuAD.html
"""
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import torch
from collections import OrderedDict
import collections
import numpy as np
from typing import List, NamedTuple, Tuple, Dict, Union, Any
import os

question_words = {
    "what's": "what is",
    "when's": "when is",
    "why's": "why is",
    "who's": "who is",
    "where's": "where is",
    "how's": "how is"
}

def to_list(tensor: torch.Tensor) -> List[float]:
    """ Converts tensor to list """

    return tensor.detach().cpu().tolist()

def clean_query(query: str, question_words=question_words) -> str:
    """ Cleans queries so they are standard """
    for key in question_words.keys():
        query = query.replace(key, question_words[key])

    if query.upper() == query:
        query = query.lower()

    return query.strip('?')

def prediction_probabilities(predictions: NamedTuple) -> float:
    """ Calculates probabilities of answers (optional, not used) """

    def softmax(x):
        """Compute softmax values for each sets of scores in x."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    all_scores = [pred.start_logit + pred.end_logit for pred in predictions]
    return softmax(np.array(all_scores))

def compute_score_difference(predictions: NamedTuple) -> float:
    """ Calculates difference in scores from null answer and best answer """
    # assumes that the null answer is always the last prediction
    score_null = predictions[-1].start_logit + predictions[-1].end_logit
    score_non_null = predictions[0].start_logit + predictions[0].end_logit

    return score_null - score_non_null

def sort_answers(answers: List[Tuple]) -> List[Dict[str, Union[str, float]]]:
    """ Sorts the answers of all context based on null score difference (scored_answer only) """
    sorted_answers = sorted(answers, key=lambda x: x[2], reverse=False)
    app_answers = []
    for ans in sorted_answers:
        if ans[0].lstrip().split(" ")[0] != "[CLS]": # ignore these non-answers
            mydict = {}
            mydict['text'] = ans[0]
            mydict['probability'] = ans[1] # if getting probability
            mydict['null_score_diff'] = ans[2]
            mydict['status'] = ans[3]
            mydict['context'] = ans[4]
            app_answers.append(mydict)

    return app_answers

class DocumentReader:
    def __init__(self, transformer_path: str, model_name: str, qa_type: str, nbest: int, null_threshold: float, use_gpu: bool=False):

        self.model_name = model_name
        self.READER_PATH = os.path.join(transformer_path, model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.READER_PATH)
        self.model = AutoModelForQuestionAnswering.from_pretrained(self.READER_PATH)
        self.max_len = self.model.config.max_position_embeddings
        self.use_gpu = use_gpu
        self.qa_type = qa_type
        self.nbest = nbest
        self.null_threshold = null_threshold

        if use_gpu:
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                self.use_gpu = use_gpu
            else:
                self.use_gpu = False

    def tokenize(self, question: str, context: List[str]) -> Tuple[List[Dict[str, torch.Tensor]], List[int]]:
        """Takes in a question and context and creates tokenized inputs for each chunk/context."""
        all_inputs = []
        context_flag = 0 # which piece of context in list of context produced the input
        context_tracker = [] # keeps track of where inputs came from
        for i in context:
            inputs = self.tokenizer.encode_plus(question, i, add_special_tokens=True, return_tensors="pt")
            input_ids = inputs["input_ids"].tolist()[0]
            if len(input_ids) > self.max_len: # if the context paragraph is too long, break it up
                inputs = self.chunkify(inputs)
                all_inputs.extend(inputs)
                context_tracker.extend([context_flag] * len(inputs))
            else:
                all_inputs.append(inputs)
                context_tracker.append(context_flag)
            context_flag += 1

        return all_inputs, context_tracker

    def chunkify(self, inputs: Dict[str, torch.Tensor]) -> List[Dict[str, torch.Tensor]]:
        """
        Break up a long article into chunks that fit within the max token
        requirement for that Transformer model.

        Calls to BERT / RoBERTa / ALBERT require the following format:
        [CLS] question tokens [SEP] context tokens [SEP].
        """
        # create question mask based on token_type_ids
        # value is 0 for question tokens, 1 for context tokens
        qmask = inputs["token_type_ids"].lt(1)
        qt = torch.masked_select(inputs["input_ids"], qmask)
        chunk_size = self.max_len - qt.size()[0] - 1  # the "-1" accounts for
        # having to add an ending [SEP] token to the end

        # create a dict of dicts; each sub-dict mimics the structure of pre-chunked model input
        chunked_input = OrderedDict()
        for k, v in inputs.items():
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

        new_inputs = [i for i in chunked_input.values()]

        return new_inputs

    def get_clean_text(self, input_ids: List[int]) -> str:
        """ Convert tokens back to text """
        text = self.tokenizer.convert_tokens_to_string(self.tokenizer.convert_ids_to_tokens(input_ids))
        return " ".join(text.strip().split())

    def preliminary_predictions(self, start_logits: torch.Tensor, end_logits: torch.Tensor, input_ids: List[int]) -> NamedTuple:
        """ Get possible predicted pairs """

        # convert tensors to lists
        start_logits = to_list(start_logits)[0]
        end_logits = to_list(end_logits)[0]

        # sort our start and end logits from largest to smallest, keeping track of the index
        start_idx_and_logit = sorted(enumerate(start_logits), key=lambda x: x[1], reverse=True)
        end_idx_and_logit = sorted(enumerate(end_logits), key=lambda x: x[1], reverse=True)

        start_indexes = [idx for idx, logit in start_idx_and_logit[:self.nbest]]
        end_indexes = [idx for idx, logit in end_idx_and_logit[:self.nbest]]

        # question tokens are between the CLS token (101, at position 0) and first SEP (102) token
        question_indexes = [i + 1 for i, token in enumerate(input_ids[1 : input_ids.index(102)])]

        # keep track of all preliminary predictions
        PrelimPrediction = collections.namedtuple(  # pylint: disable=invalid-name
            "PrelimPrediction", ["start_index", "end_index", "start_logit", "end_logit"]
        )
        prelim_preds = []
        for start_index in start_indexes:
            for end_index in end_indexes:
                # throw out invalid predictions
                if start_index in question_indexes:
                    continue
                if end_index in question_indexes:
                    continue
                if end_index < start_index:
                    continue
                prelim_preds.append(
                    PrelimPrediction(
                        start_index=start_index,
                        end_index=end_index,
                        start_logit=start_logits[start_index],
                        end_logit=end_logits[end_index],
                    )
                )
        # sort prelim_preds in descending score order
        prelim_preds = sorted(prelim_preds, key=lambda x: (x.start_logit + x.end_logit), reverse=True)

        return prelim_preds

    def best_predictions(self, prelim_preds: NamedTuple, start_logits: torch.Tensor, end_logits: torch.Tensor, input_ids: List[int]) -> NamedTuple:
        """Get nbest predictions from the preliminary predictions"""
        # keep track of all best predictions
        start_logits = to_list(start_logits)[0]
        end_logits = to_list(end_logits)[0]

        # This will be the pool from which answer probabilities are computed
        BestPrediction = collections.namedtuple(
            "BestPrediction", ["text", "start_logit", "end_logit"]
        )
        nbest_predictions = []
        seen_predictions = []
        
        for pred in prelim_preds:
            if len(nbest_predictions) >= self.nbest:
                break
            if pred.start_index > 0:  # non-null answers have start_index > 0

                begin = pred.start_index
                end = pred.end_index + 1

                toks = input_ids[begin:end]
                text = self.get_clean_text(toks)

                # if this text has been seen already - skip it
                if text in seen_predictions:
                    continue

                # flag text as being seen
                seen_predictions.append(text)

                # add this text to a pruned list of the top nbest predictions
                nbest_predictions.append(
                    BestPrediction(
                        text=text, start_logit=pred.start_logit, end_logit=pred.end_logit
                    )
                )

        # Add the null prediction
        nbest_predictions.append(
            BestPrediction(text="", start_logit=start_logits[0], end_logit=end_logits[0])
        )

        return nbest_predictions

    def one_passage_answers(self, start_logits: torch.Tensor, end_logits: torch.Tensor, input_ids: List[int]) -> Tuple[str, float]:
        """ Get best (scored) answers for one context input """
        prelim_preds = self.preliminary_predictions(start_logits, end_logits, input_ids)
        nbest_preds = self.best_predictions(prelim_preds, start_logits, end_logits, input_ids)
        probabilities = prediction_probabilities(nbest_preds)
        score_difference = compute_score_difference(nbest_preds)
        # if score difference > threshold, return the null answer
        if score_difference > self.null_threshold:
            return nbest_preds[0].text, probabilities[0], score_difference, "failed"
        else:
            return nbest_preds[0].text, probabilities[0], score_difference, "passed"

    def get_argmax_answer(self, inputs: Dict[str, torch.Tensor]) -> str:
        """ Simple Answer: retrieves the start/end pair with the highest score."""
        answer_start = torch.argmax(self.model(**inputs)["start_logits"])
        answer_end = torch.argmax(self.model(**inputs)["end_logits"]) + 1
        
        ans = self.get_clean_text(inputs["input_ids"][0][answer_start:answer_end])
        if ans.lstrip().split(" ")[0] != "[CLS]":
            return ans
        else:
            return ""

    def get_robust_prediction(self, inputs: Dict[str, torch.Tensor]) -> Tuple[str, float]:
        """ Score Answer: retrieves up to nbest answers per context input and their difference from the null score."""
        start_logits = self.model(**inputs)["start_logits"]
        end_logits = self.model(**inputs)["end_logits"]
        input_ids = inputs["input_ids"].tolist()[0]
        return self.one_passage_answers(start_logits, end_logits, input_ids)

    def answer(self, question: str, context: List[str]) -> List[Dict[str, Union[str, float, int]]]:
        """
        Main function called by mlapp to query QA model.
        
        Args:
            - question (str)
            - context (List[str])
        Returns:
            - answers (List[Dict]): each answer is a dictionary including text, context index, and score (if scored)
        """
        question = clean_query(question)
        #print(f"Question: {question}")

        inputs, tracker = self.tokenize(question, context)
        all_answers = []
        if self.qa_type == 'scored_answer':
            for idx, inp in enumerate(inputs):
                if self.use_gpu:
                    inp = {key: value.cuda() for (key, value) in inp.items()}
                answer, prob, diff, status = self.get_robust_prediction(inp)
                all_answers.append((answer, prob, diff, status, tracker[idx]))
            all_answers = sort_answers(all_answers)
        elif self.qa_type == 'simple_answer':
            for idx, inp in enumerate(inputs):
                if self.use_gpu:
                    inp = {key: value.cuda() for (key, value) in inp.items()}
                answer = self.get_argmax_answer(inp)
                all_answers.append({"text": answer, "context": tracker[idx]})
        
        return all_answers