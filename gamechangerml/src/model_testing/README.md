# Model Testing
The code in this directory relates to the training and evaluation of the sentence embedding transformers, question-answer transformer (has not been used on domain data) and sentence index similarity re-ranking model (deprecated). 

## API
In the ML dashboard, GAMECHANGER has a no-code interface for finetuning, building models with updated data, and evaluating models. For these non-search endpoints, the ML dashboard interacts with the MLAPI through `gamechangerml/api/fastapi/routers/controls.py`. The training, data creation, and evaluation functions in `controls.py` use the Pipeline class from `gamechangerml/src/train/pipeline.py`. The pipeline class imports training and evaluation scripts/classes from:

- `gamechangerml/scripts/make_training_data`
- `gamechangerml/scripts/update_eval_data`
- `gamechangerml/scripts/run_evaluation`
- `gamechangerml/src/search/sent_transformer/finetune`
- `gamechangerml/src/model_testing/evaluation`

## Sentence Index Pipeline Steps
The most developed model training/evaluation pipeline is for the sentence embeddings. The steps for running the entire model finetuning pipeline:
1. Update validation data
2. Update training data
3. Finetune the model
4. Evaluate the model
5. Build a full sentence index [not automated]

Because the full training/evaluation/indexing process takes a long time (1-6 hours for each step) there's a test script that will run the whole process of finetuning one of the base transformers (MODEL_NAME) on a subset of data and delete the test files after completing:

`python gamechangerml/src/model_testing/train_tests.py -m MODEL_NAME` 

### 1. Update validation data
We currently use three sources of data for validating the performance of the sentence index: 
- Matamo tracking data: this feedback comes from users clicking on thumbs up/thumbs down on search results in the application. Because this data comes directly from users, we have high confidence in this data
- User search history: this data comes from tracking documents opened by users after performing a search. Because this data isn't direct feedback, we have less trust in search-document pairs that don't appear multiple times. 
- Gold standard CSV: currently, this file is fairly dated but contains manually curated search-document pairs that are expected from users. **The easiest way to manually add searches and expected documents to the validation/evaluation pipeline is to update this file with the search phrase and expected filename (or a list of filenames separated by semi-colon)

To finetune the transformer models for sentence embeddings, we start by taking the most recent Matamo, User History, and gold standard data and combining them into three tiers of validation data based on confidence. The `SearchValidationData` class in `gamechangerml/src/model_testing/validation_data.py` preprocesses the raw user feedback/history data so unique searches can be consolidated and aggregated.

Configuration:
The configs for validation are in `gamechangerml/configs/config.py` -> `ValidationConfig`.
- "start_date": "2020-12-01",  # earliest date to include search hist/feedback data
- "end_date": "2025-12-01",  # last date to include search hist/feedback data from
- "exclude_searches": ["pizza", "shark"] # list of searches not to include in validation
- "min_correct_matches": {"gold": 3, "silver": 2, "any": 0}, # mapping of the minimum correct matches (search & doc opened) needed from the User History data to designate that pair to a tier -> the higher the number, the more times the doc has been opened for this search, the more confidence in the pair
- "max_results": {"gold": 7, "silver": 10, "any": 100}, # mapping of the maximum unique document results per search that can be added to each level -> the lower the number, the fewer results are relevant for the search, the more confidence there is in this pair

Input files (required for updating the validation data):
- `gamechangerml/data/user_data/search_history/SearchPdfMapping.csv` *
- `gamechangerml/data/user_data/matamo_feedback/matamo_feedback.csv` *

\*(the code will actually concat all csvs in these directories so the filenames shouldn't matter)

Output files:
Two validation data files are saved for each tier in a timestamped directory (TIMESTAMP), with a different subdir for each tier (ANY/SILVER/GOLD):
- `gamechangerml/data/validation/domain/sent_transformer/TIMESTAMP/LEVEL/intelligent_search_data.json`
- `gamechangerml/data/validation/domain/sent_transformer/TIMESTAMP/LEVEL/intelligent_search_metadata.json`

Other classes in `gamechangerml/src/model_testing/validation_data.py` relate to formatting the original data used for training the question-answer model (SQuAD), retriever morel (MSMARCO) and similarity re-ranking model (NLI) (used for creating an evaluation baseline).

### 2. Update training data
Once we have updated the validation data with the newest user data, we can re-create the training data. By default, we use the `silver` level data for training (due to not having many examples in the `gold` level). The training data gets made in `gamechangerml/scripts/make_training_data`:

1. Get the most recent validation data -> if no validation data exists (or if update_eval_data=True), makes the validation data. 
2. Create a new timestamped directory for the training data in `gamechangerml/data/training/sent_transformer`
3. Add the gold standard data to the intelligent search validation data (matamo + user history) \*This function also boosts the training data by creating a query-doc pair for every document name (ex. "query": "Title 10", "document": "Title 10")
4. Collect paragraphs from ES: because the only data we have for validation is the search and document name, we need to collect text to use for training. This step performs a search of the GAMECHANGER Elasticsearch index to retrieve the most relevant paragraphs for a search from the expected documents (positive matches) and from non-expected documents (neutral matches). A score is assigned to each retrieved paragraph based on a hardcoded mapping (0.95=match, 0.5=not a match)
5. Train/test split: each query and its matching/non-matching examples should be assigned to either the train or test set. 

Input Files:
- `gamechangerml/data/user_data/gold_standard.csv`
- `gamechangerml/data/validation/domain/sent_transformer/TIMESTAMP/silver/intelligent_search_data.json`

Output Files:
- `gamechangerml/data/training/sent_transformer/TIMESTAMP/training_data.json`
- `gamechangerml/data/training/sent_transformer/TIMESTAMP/training_metadata.json`
- `gamechangerml/data/training/sent_transformer/TIMESTAMP/not_found_search_pairs.json` -> for debugging/reference, contains all the search-doc pairs that didn't return positive matches from ES/weren't added to training data
- `gamechangerml/data/training/sent_transformer/TIMESTAMP/retrieved_paragraphs.csv` -> for easier reference, these are the 'best' paragraphs retrieved from the expected docs for each search from ES
- `gamechangerml/data/training/sent_transformer/TIMESTAMP/finetuning_data_TIMESTAMP.csv` -> for easier reference, lists out the search, paragraph ID, and score used for each training sample

### 3. Finetune the Model
1. Loads most recent training data -> if no training data exists or remake_train_data=True, remakes the training data
2. Loads the STFinetuner class from `gamechangerml/src/search/sent_transformer/finetune`. This is where the transformer params are set:
    - shuffle # default = True
    - batch_size # default = 8 -> if you get memory errors while finetuning, the batch size may be too high.
    - epochs # default = 10
    - warmup_steps # default = 100
3. Finetunes the model

Input Files:
- `gamechangerml/data/training/sent_transformer/TIMESTAMP/training_data.json`
- transformer model (ex. `gameechangerml/models/transformers/multi-qa-MiniLM-L6-cos-v1`)

Output Files:
- new model: `gamechangerml/models/transformers/TIMESTAMP_MODEL_NAME`
- metadata file: `gamechangerml/models/transformers/TIMESTAMP_MODEL_NAME/metadata.json`

### 4. Evaluate the Model
After finetuning, the evaluations are run automatically. Models can also be evaluated as a single step from the ML dashboard. A model's eval metrics should show up in the ML dashboard when model information is expanded. The `IndomainRetrieverEvaluator` class from `gamechangerml/src/model_testing/evaluation.py` creates a TEST sentence index for evaluating the model on a subset of the corpus (because making a full index takes a long time). The test index is made with docs that are mentioned in the training data (positive/negative samples); the evaluation step filters out search-doc pairs for docs that aren't present in the test index. The metrics are calculated by running the searches for each validation data level (silver, gold) and aggregating the true/false positives/negatives. Functions to calculate metrics are in `gamechangerml/src/model_testing/metrics.py`. Aggregate metrics are saved in the finetuned model metadata file.

Input Files:
- `gamechangerml/data/validation/domain/sent_transformer/TIMESTAMP/LEVEL/intelligent_search_data.json` -> for silver/gold tiers of validation data, runs eval
- new model

Output Files:
- `gamechangerml/models/MODEL_NAME/evals_gc/LEVEL/retriever_eval_TIMESTAMP.json` -> aggregate metrics used to display in the model info in ML dashboard
- `gamechangerml/models/MODEL_NAME/evals_gc/LEVEL/sent_index_TEST_TIMESTAMP.csv` -> dataframe has the expected docs and results for each query tested, and the query-level metrics.

### 5. Build the Sent Index [not automated]
This step isn't automated. If a model looks good to use for building an entire sent index, that process can be done by passing the finetuned model in as the model for re-building the sent index in the ML dashboard. 
