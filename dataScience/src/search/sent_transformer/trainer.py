from transformers import AutoModelForSequenceClassification, AutoTokenizer
from transformers import AdamW

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader

from dataScience.src.search.sent_transformer.corpus import SentenceCorpus

from tqdm import tqdm

import matplotlib.pyplot as plt

class GCDataset(TensorDataset):
    def __init__(self, fpath, tokenizer, iter_len = 1_000):
        self.corp = SentenceCorpus(fpath, iter_len = iter_len)
        self.tokenizer = tokenizer
        self.iter_len = iter_len

    def preprocess(self, text_a, text_b):
        text_a = text_a[0] + " " + " ".join(text_a[2])
        text_b = text_b[0] + " " + " ".join(text_b[2])
        text = text_a + " [SEP] " + text_b + " "
        tokens = self.tokenizer(text, return_tensors = 'pt')["input_ids"]
        return tokens

    def __len__(self):
        return self.iter_len

    def __getitem__(self, index):
        text_a, text_b, sim_score = self.corp._get_item_sample()
        input_ids = self.preprocess(text_a, text_b)
        return input_ids, sim_score

def collate_fn(batch):
    tokens = [a[0].view(-1)[:512] for a in batch]
    labels = [a[1] for a in batch]
    tokens = nn.utils.rnn.pad_sequence(tokens, padding_value = 1).T
    tokens = tokens
    labels = torch.Tensor(labels).view(-1, 1)
    attention_id = torch.where(tokens == 1, 0, 1)
    new_batch = (tokens, attention_id, labels)
    return new_batch


def train_model(
    corpus_directory,
    save_path,
    pretrained_model = "valhalla/distilbart-mnli-12-3",
    label_count = 9,
    use_gpu = False,
    batch_size = 4,
    sample_count = 5_000,
    epochs = 4,
    ):

    if pretrained_model:
        model = AutoModelForSequenceClassification.from_pretrained(pretrained_model)
        model.num_labels = label_count
        num_ftrs = model.classifier.in_features
        model.classifier = nn.Linear(num_ftrs, label_count)
        tokenizer = AutoTokenizer.from_pretrained(pretrained_model, model_max_length = 500)
    else:
        # Write appropriate error log
        assert 1 == 2

    if use_gpu:
        if torch.cuda.is_available():
            if torch.cuda.device_count() > 1:
                model = nn.DataParallel(model)
            model = model.cuda()
        else:
            print("Error")
            use_gpu = False

    dataset = GCDataset(corpus_directory, tokenizer, iter_len = sample_count)
    dataloader = DataLoader(dataset, batch_size = batch_size, collate_fn = collate_fn)

    max_grad_norm = 1.0

    param_optimizer = list(model.named_parameters())
    no_decay = ['bias', 'gamma', 'beta']
    optimizer_grouped_parameters = [{'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
                                    'weight_decay_rate': 0.01},
                                    {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)],
                                    'weight_decay_rate': 0.0}]

    optimizer = AdamW(optimizer_grouped_parameters,
                    lr = 2e-5,
                    weight_decay = 0.01,
                    correct_bias = False)

    train_loss = []
    window_error = []
    model = model.train()
    for epoch in range(epochs):
        for idx, (a, b, c) in tqdm(enumerate(dataloader)):
            if use_gpu:
                a, b, c = a.cuda(), b.cuda(), c.cuda()

            optimizer.zero_grad()
            loss, output = model(
                input_ids = a.long(), 
                attention_mask = b.long(), 
                labels = c.long(),
                return_dict = False
            )

            loss.backward()
            torch.nn.utils.clip_grad_norm_(parameters = model.parameters(), max_norm = max_grad_norm)
            optimizer.step()

            if (idx % 4 == 0) and (idx != 0):
                train_loss.append(sum(window_error)/4)
                window_error = []
            else:

                window_error.append(loss.item())

    if use_gpu:
        model = model.cpu()
    model.save_pretrained(save_path)    
    
    plt.plot(train_loss)
    plt.savefig("./../../../../../test.png")

    

if __name__ == "__main__":
    train_model("./../../../../../sentparse", "./../../../../../gc-bert-sim", pretrained_model = "bert-base-uncased", use_gpu = True)
