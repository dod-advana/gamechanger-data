# `classifier` 

This is a framework of sorts for transfer learning using Hugging Face pre-trained models for sequence
classification, *e.g.*, text classification.

The `base_class` does most of the heavy lifting, however, it **must** be subclassed to provide a few
model and data loading methods. Implemented are models based on

- `bert-base-uncased`
- `roberta-base`
- `distilbert-base-uncased`

The Hugging Face models can be downloaded from their ['models' site](https://huggingface.co/models).

> If you do have a required model, the underlying library will attempt to 
>download the required files. These will be cached in `~/.cache`.

## Configuration
The classifier is driven entirely by a configuration file such as the ones
in the `examples/` directory. 

The schema for the YAML configuration is shown below. 

**NB**: *All* the 
configuration items must be present. If `None` is allowed as a value, use the
`~` character in the YAML to indicate `None`. Strict type checking is enforced as well as checking
for obvious errors. 

|Name | Type(s) | Description|
|:--- |:--- | :--- |
|log_id|`str`|Name of the log file|
|model_name|`str`|A valid Hugging Face model name|
|epochs|`int`|Number of epochs for model training|
|batch_size|`int`| Batch size; should be a power of 2|
|random_state|`int`|Sets the random number seed; can be `None`|
|checkpoint_path|`(str, None)`| Where to write the model file.|
|tensorboard_path|`(str, type_none)`|Directory for `tensorboard`'s `fevents` files.|
|num_labels|`int`|The number of unique labels|
|split|`float`|A number in (0, 1)|
|warmup_steps|`(float, None)`|Applied to the scheduler|
|lr|`float`|Learning rate|
|weight_decay|`float`|See the [AdamW documentation](https://huggingface.co/transformers/main_classes/optimizer_schedules.html)|
|eps|`float`|Stopping criteria for the optimizer|
|clip_grad_norm|`(float, None)`|Limits the gradient to a function of this value|
|drop_last|`bool`|If `True`, drop the last batch if it is incomplete|
|truncate|`bool`|If `True`, truncate to the max length. Recommend `False`|
|max_seq_len|`(int, None)`|If `None`, this value is computed from the encoded text. Otherwise, this value is used|

The schema is in `utils/config.py`. Changes to the schema are encouraged.

## Examples
The `examples/` directory contains sample CLI for training the CoLA data set.

General usage is

```
usage: python example_cola_cli

Trains the `bert-based` models on the CoLA data set

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_YAML, --config-yaml CONFIG_YAML
                        path to the `.yml` configuration file
  -d DATA_FILE, --data-file DATA_FILE
                        path the training data
  -m {bert,roberta,roberta-nd,bert-nd,distilbert}, --model-type {bert,roberta,roberta-nd,bert-nd,distilbert}
                        supported model type; default is `roberta'
  -t TRUNC, --truncate TRUNC
                        use rows up to this value; 0 indicates the entire data
                        set
```
If all goes well, you'll see a summary of the configuration parameters, and the training will begin:
```
[config.py:184 - log_config()], ------------------------------------------------------
[config.py:199 - log_config()],                class : DistilBertClassifier
[config.py:199 - log_config()],              version :  0.7.4  
[config.py:199 - log_config()],               config : sample_distilbert_gc_config.yml
[config.py:199 - log_config()],               log id : distilbert-gc-example-dodd.log
[config.py:199 - log_config()],           model name : distilbert-base-uncased
[config.py:196 - log_config()],               epochs :       1
[config.py:196 - log_config()],           batch size :       8
[config.py:196 - log_config()],         random state :      42
[config.py:193 - log_config()],      checkpoint path :   None  
[config.py:193 - log_config()],     tensorboard path :   None  
[config.py:196 - log_config()],           num labels :       2
[config.py:202 - log_config()],                split :   9.0E-01
[config.py:196 - log_config()],         warmup steps :       0
[config.py:202 - log_config()],                   lr :   1.0E-05
[config.py:202 - log_config()],         weight decay :   0.0E+00
[config.py:202 - log_config()],                  eps :   1.0E-08
[config.py:202 - log_config()],       clip grad norm :   1.0E+00
[config.py:196 - log_config()],            drop last :       0
[config.py:196 - log_config()],             truncate :       1
[config.py:196 - log_config()],          max seq len :     256
[config.py:199 - log_config()],           model type : distilbert
[config.py:199 - log_config()],               device :   cpu   
[config.py:199 - log_config()],        training data : dodd_resp_test.csv
[config.py:196 - log_config()],     training samples :   3,541
[config.py:196 - log_config()],   validation samples :     394
[config.py:199 - log_config()],            optimizer :  AdamW  
[config.py:196 - log_config()],          total steps :     443
[config.py:209 - log_config()], ------------------------------------------------------
[classifier.py:305 - train()], into the breach...
[classifier.py:310 - train()],          ==================== Epoch   1 /   1 ====================
[classifier.py:353 - _train_batch()], 	batch     1 /   443 	loss : 0.633	elapsed : 0:00:08
```

## Prediction
The commandline example `predict_cli.py` reads a model from a checkpoint directory and runs a user-supplied
`.csv` to effect predictions. Usage is documented in that script.

## TensorBoard
If `tensorboard_path` is a valid directory, events are logged for use in TensorBoard. Tensorboard
is started from the command line. If you've run the example
```
$ tensorboard --logdir=text_classif/examples/tensorboard/
```
You should see something very close to
```
Serving TensorBoard on localhost; to expose to the network, use a proxy or pass --bind_all
TensorBoard 2.4.1 at http://localhost:6006/ (Press CTRL+C to quit)
``` 
Point your browser to the TensorBoard URL to visualize various metrics. 
See the `torch` [recipe here](https://pytorch.org/tutorials/recipes/recipes/tensorboard_with_pytorch.html).

## Saving and Loading your Trained Models
The configuration file has the entry `checkpoint_path` and if this is not `None`, the model is written to 
a subdirectory suffixed by `_epoch_1`, etc., one for each epoch.

The example `examples/predict_cli.py` shows how to load a specific checkpoint and use it to classify a
set of texts. The `raw_text` of a document can be converted to a `.csv` of sentences using `utils/raw_text2csv.py`.
`predict_cli.py` will optionally write a `.csv` with predicted classes, its likelihood as well as all the
columns in the input `.csv`. 

See the documentation in `predict_cli.py` for usage. 

## Test Data
The benchmark test data is the *Corpus of Linguistic Acceptability* (CoLA) and is included in the `tests/test_data/cola_public`
directory. The full data set has 8,551 sentences labeled as 0 or 1 (*not grammatical*, *grammatical*).
See [Warstadt *et al*., (2019)](https://arxiv.org/pdf/1805.12471.pdf) for additional detail.

The directory `test_data/responsibility` has Gamechanger-specific data that can also be
used for testing purposes.

## Training
`example_cola_cli.py` will train a classification model on the CoLA data.

For `CONFIG_YAML`, the file `sample_distilbert_cola_config.yml` has the necessary configuration. The
`DATA_FILE` should point to `/tests/test_data/cola_public/raw/in_domain_train.tsv`. Finally, `-m distilbert`
will train a model using `distilbert-base-uncased`.

The sample configuration file should be updated if you wish to save a checkpoint or change the
model parameters such as the number of epochs.


## Logging and Metrics
Console and/or file logging is supported via `utills/initialize_logger()`. 
See `examples/example_gc_cli.py` for example usage. You'll need to alter the
configuration file to accommodate your paths and names.

At the end of each epoch, a `scikit-learn` classification report is logged as well
as a formatted confusion matrix.

## Subclassing
Since different models
require their own `transformers` class for tokenizing and sequence classification,
subclassing `Classifier` allows different models to be trained and tested. 

A subclass must implement the following method:

- `load_model_tokenizer()`

The modules `roberta_classifier.py`, `bert_classifier.py`, and `distilbert_classifier.py` are examples of subclasses. These
can be further subclassed for your custom methods.

## Example Metrics
```
[classifier.py:511 - _validate()], 

              precision    recall  f1-score   support

           0      0.789     0.418     0.546       268
           1      0.782     0.949     0.857       588

    accuracy                          0.783       856
   macro avg      0.785     0.683     0.702       856
weighted avg      0.784     0.783     0.760       856

[classifier.py:512 - _validate()], confusion matrix

	         pred: 0  pred: 1
true: 0      112      156
true: 1       30      558

[classifier.py:513 - _validate()], 	validation loss : 0.534
[classifier.py:514 - _validate()], 	            MCC : 0.457
[classifier.py:515 - _validate()], 	            AUC : 0.683
[classifier.py:516 - _validate()], 	 accuracy score : 0.783
[classifier.py:517 - _validate()], 	validation time : 0:01:48
[checkpoint_handler.py:30 - write_checkpoint()], saving model with loss : 0.534
```

## License
The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE