# Responsibility Parsing

## Directory Structure

```
gamechanger-data/common/document_parser/lib/responsibility_parse/
.
├── README.md
├── __init__.py
├── cli
│   └── responsibility_parser_cli.py
├── responsibility_parser.py
└── tests
    ├── __init__.py
    ├── data
    │   ├── input
    │   │   ├── DoDI\ 1000.04.json
    │   │   ├── DoDI\ 5000.94.json
    │   │   ├── DoDI\ 5000.94_expected.txt
    │   │   ├── DoDI\ 5000.94_resp_section.txt
    │   │   ├── DoDI\ 5000.94_resp_section_expected.txt
    │   │   ├── DoDI\ 6440.02\ CH\ 1.json
    │   │   ├── blank_file.json
    │   │   ├── expected_responsibility_results.xlsx
    │   │   └── file_missing_responsibilities.json
    │   └── output
    └── unit
        ├── __init__.py
        └── test_responsibility_parser.py
```

## ResponsibiltyParser Usage
The ResponsibilityParser can be imported and used in other scripts via:
```python
from common.document_parser.lib.responsibility_parse import ResponsibilityParser
responsibility_parser = ResponsibilityParser()
# all results will be saved off in responsibility_parser.results_df attribute
responsibility_parser.main(files_input_directory="directory/of/jsons")
# in order to save the results to a file
responsibility_parser.save_results_to_excel("directory/to/output/results.xlsx")
```

## CLI Usage
There is a CLI tool within that can be used to parse the responsibility results for a directory of GC jsons. 

### CLI Tool Usage/Params 
This CLI tool has the following CLI Usage/Params:
```
usage: responsibility_parser_cli.py [-h] --json-files-input-directory JSON_FILES_INPUT_DIRECTORY [--excel-save-filepath EXCEL_SAVE_FILEPATH] [--save-to-rds] [--postgres-user POSTGRES_USER]
                                    [--postgres-password POSTGRES_PASSWORD] [--postgres-db-name POSTGRES_DB_NAME] [--postgres-table-name POSTGRES_TABLE_NAME] [--postgres-hostname POSTGRES_HOSTNAME]
                                    [--postgres-port POSTGRES_PORT]

CLI tool for the Responsibility Section Parser

optional arguments:
  -h, --help            show this help message and exit
  --json-files-input-directory JSON_FILES_INPUT_DIRECTORY, -i JSON_FILES_INPUT_DIRECTORY
                        Directory to the input directory for Gamechanger JSONs. For multiple directories, semi-colon delimit the paths
  --excel-save-filepath EXCEL_SAVE_FILEPATH, -e EXCEL_SAVE_FILEPATH
                        Filepath (including diectory and filename) of the excel file that the responsibility explorer results shouldbe saved to
  --save-to-rds, -s     Flag for saving to RDS
  --postgres-user POSTGRES_USER, -u POSTGRES_USER
                        Username for Postgres Instance
  --postgres-password POSTGRES_PASSWORD, -p POSTGRES_PASSWORD
                        Password for Postgres Instance
  --postgres-db-name POSTGRES_DB_NAME, -d POSTGRES_DB_NAME
                        Database Name for RE results table to be stored
  --postgres-table-name POSTGRES_TABLE_NAME, -t POSTGRES_TABLE_NAME
                        Table Name for RE results table to be stored
  --postgres-hostname POSTGRES_HOSTNAME, -n POSTGRES_HOSTNAME
                        Hostname/IP for Postgres Instance
  --postgres-port POSTGRES_PORT, -o POSTGRES_PORT
                        Port for Postgres Instance

```

### CLI Tool Examples
An example of processing an input directory to create an output (excel spreadsheet) of the responsibility results
extracted from the directory of json files:
```commandline
python3 common/document_parser/lib/responsibility_parse/cli/responsibility_parser_cli.py 
-i "~/bah/advana_data/gc_jsons" 
-e "~/bah/advana_data/responsibility_results.xlsx"
```
If there are multiple input directories (of JSON files) that need to be parsed, these can be supplied to the `-i` param 
via a semicolon delimited list as follows:
```commandline
python3 common/document_parser/lib/responsibility_parse/cli/responsibility_parser_cli.py 
-i "~/bah/advana_data/gc_jsons1;~/bah/advana_data/gc_jsons2" 
-e "~/bah/advana_data/responsibility_results.xlsx"
```
In order to ingest directly into an RDS table, the CLI tool can be used as follows:
```commandline
python3 common/document_parser/lib/responsibility_parse/cli/responsibility_parser_cli.py 
-s 
-u db_username 
-p db_password 
-d db_name 
-t db_table 
-n db_hostname
-o db_port
```