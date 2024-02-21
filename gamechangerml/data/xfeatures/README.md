#Features:

### Abbreviations.csv
Contains information to translate military acronyms and abbreviations to their expanded format. Ex) DoD expands to Department of Defense 
	
WHERE IS IT USED?

* _Abbrevations.csv_ (can't find usage)
	
* _Abbreviations.json_
  - Abbeviation.py where it is used to find abbreviations and their expansions to create dictionaries of counts and expansions
	
### Agencies.csv
Contains information on government agencies including Alias, name, website, address, email, phone numbers, government branch, parent agency, related agency, and seal.
	
WHERE IS IT USED?

* _Responsibilities.py_
    - Used to extract agencies from text where a simultaneously extracted responsibility is mapped to the agencies individually.
	
* _Pipeline.py_
    - Is used to make the  combined entities data
    
* _Combine_entities.py_
    -Agencies csv is stack on top of topics_wiki_csv derive the combined entities csv
	
* _init.py_
    - Is mapped to AGENCY_DATA_PATH
	
* _Abbreviations_utils.py_
    - Leverages agencies.csv to create a dictionary for use in the abbreviations pipeline

* _Update_orgs.py_
    - Updating the DoD Orgs reference table the updated_dod_orgs.txt
		

### Classifier_entities.csv
Contains an entity, it's alias and a classification category (person, organization,  
	
WHERE IS IT USED? (not found in code base)
	

### Combined_entities.csv
Is a concatenation of agencies.csv and topics_wiki created by the make_combined_entities function in src/featurization/make_meta.py
	
WHERE IS IT USED?
* _Combine_entities.py_
  - Leveraged in a script to combine agencies(orgs) and topics into a single csv for ingestion and use in [TODO].
* _get_wiki_descriptions_
  - Modifies combined_entities.csv to contain an information element, along with 
a information source element and a timestamp in the main function.
	

### Corpus_doctypes.csv
Contains information about government document types, their Acronymn expansion, source, and group. Note there seems to be a strong correlation between source and group. (is this duplication?)
	
WHERE IS IT USED?
* _profile_corpus.py_
  - maps sources_path and used in combination with ____ to create a stats file for the corpus [TODO]
	

### Enwiki_vocab_min200.txt 
A document that contains either a tokenization mapping or word count of a subset of words in the english language. (check for duplicate numbers to test possibility of tokenization)
	
WHERE IS IT USED? [TODO]
* _Word_wt.py_
* _Conftest.py_
* _Build_qe_model_
	

### Graph_relations.xls
An xls file containing the name of an organization, it's aliases, parent organization, the type of organization, DoDcomponent, OSD component, and department/organization head

WHERE IS IT USED?
(not used in this repo)



### Popular_documents.csv
A table mapping documents in the corpus to a popularity score
	
WHERE IS IT USED?

* _Features.py_
  - in order to retrieve a popularity score for a document.
	

### Topics_wiki.csv
A csv file containing DoD related topics with a description of the topic along with the web crawlers used to derive the description.
	
WHERE IS IT USED?

* _Combine_entities.py_
  - Leveraged in a script to combine agencies(orgs) and topics into a single csv for ingestion and use in [Fill].
* _Pipeline.py_
  - Leveraged in pipeline.py as an argument to functionality defined in combine_entities.py

	

### Word-freq-corpus-20201101.txt
It looks like a document containing the count of words found in the corpus
	
	
WHERE IS IT USED?
* _Embed_titles_ 
  - Used to get word weights.



	
