# Text Classification

This provides an evolving framework for configuration and benchmarking text classifiers.
The idea revolves around being to configure, train, test, and evaluate a classifier without
too much trouble.

## Quick Start
The easiest way to start is to look at the example `example_single_clf_cola.py`. This runs
the *best* of the statistical classifiers using the 
[Corpus of Linguistic Acceptability](https://nyu-mll.github.io/CoLA/), or COLA data set.

## Benchmark Data
The data set is included in the `tests/` directory. For reference, the data can be
downloaded [here](http://nyu-mll.github.io/cola). 

Each sentence is labeled as 0 (not grammatical) or 1 (grammatical). Two sentences can be
very similar, however, one of them may be *not grammatical*. This makes it a challenge
for a binary text classifier.

## Logging
If `initialize_logger()` from `utils/log_init.py` is called, both console and
file logging will be started. The log file is written to the content root directory.
The log file name is prefixed with a user-supplied `data_name`.

---

## 'Bag of Words'-based Classifiers
#### Simple and Easy to Beat

---

Out of 15 standard classifiers, Stochastic Gradient Descent with an `l1` penalty performed
the best, but it's accuracy was a dismal 0.6830. The reasons for this can be seen in
the classification report:

```
              precision    recall  f1-score   support

          NG       0.35      0.11      0.16       271
           G       0.69      0.91      0.78       584

    accuracy                           0.65       855
   macro avg       0.52      0.51      0.47       855
weighted avg       0.58      0.65      0.59       855
``` 

The classifier has high recall for `G` (grammatical), but as the
confusion matrix shows, it classifies the majority of sentences as
`NG` (not grammatical), hence its overall precision is quite low.

```
 NG   29  242
  G   53  531
```

*Bag-of-words*-based methods make for **poor classifiers** for such sentences, and probably a lot of 
sentences exhibiting subtle differences. Such poor performance is well-documented.

Nevertheless, it provides a lower bound.