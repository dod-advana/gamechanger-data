![Alt text](../../img/tags/GAMECHANGER-NoPentagon_CMYK@3x.png)

# 

# PDF Document Processor 

Document is a Python library for processing PDF documents into Json structures

* Reads OCR'ed PDF documents and creates a flexible data structure that can be exported.


## Usage

### From the command line
Document.py can be run as a module to process a folder or single file
from the project root:
```python -m common.document_parser pdf-to-json -s "./common/data/Test_files/" -d "./out/"```

reads in Test_files and puts the json output in ./out

#### Optional Flags/Options
```-c clean```
Flag cleans special characters and extra spaces


```-p multiprocessing ```
Option enables multiprocessing with -p 0 using max threads and -p x numbers specifying the core count


### Processing a single document
The processing of a single document can be done with the `clean` flag set to true or false. True indicates that the text is being cleaned from special characters and extra spaces.

```python
import Document

doc = Document.Issuance('filename.pdf') # processes and returns a single issuance.
print(doc) # prints the document name with the number of pages.
doc.json_write(clean=True, out_dir="./") # writes the object to a json files
```

### Processing a directory of files
Processing a directory will only read `.pdf` files inside folder specified `dir_path`. It does not go deeper in the file tree. 

```python
import Document

Document.process_dir(dir_path = 'FMR', out_dir= './FMR_out/', clean=True)
# processes an entire directory of pdf documents.
```


### Create csv meta data file from a directory of json files
For simple database purposes this reads a directory of json files and creates a csv file of all the meta data items and everything that can be stored in a simple csv file.

```python
import Document

Document.Issuance.create_csv_data("Json_directory", out_dir="Json_directory/")
# creates a csv in the same directory of all meta.
```

### Rewriting Json files
Without changes to the code this will one for one rewrite the directory. This function can be useful when adding new elements to this class, which we want to apply to older versions of the json structures. 

```python
import Document

Document.Issuance.rewrite_dir("Json_directory","Json_directory_new/")
# reads jsons and writes jsons back to a new directory. 
```

### Entity Extraction 
To extract entities from pages, you can call the extract_entities function on a json. It will read the json, run spaCy NER on the text of each page, and append a list of entities organized by entity type to each paragraph json (NER is run on full page text because the model benefits from the extra context, but the entities are appended on a per-paragraph basis). Types of entities extracted: ORG, GPE, NORP, LOC, LAW, PERSON.

``` python
import Document

# To run on a single document:
doc = Document.Issuance('filename.pdf')
doc.extract_entities()

# To run on a directory:
Document.extract_entities_dir(dir_path, dest)
```
