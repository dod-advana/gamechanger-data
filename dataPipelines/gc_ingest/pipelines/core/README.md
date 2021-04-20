# Core Pipelines

CLI/API for running core pipelines 

## Code Structure
CLI is defined in `cli.py` and full pipelines can, at this time, only run from the CLI.

The API of the pipelines is broken up into configuration classes used to define which parameters must be specified to run the given pipeline and classes that define steps that are required to run a particular pipeline; within `configs.py` and `steps.py`, respectively. The prescribed order in which these steps should run for a given pipeline scenario and some higher level conditional logic is found in the `cli.py`. Although there is no principal reason why such recommended logic cannot be moved to `steps.py` classes to simplify non-CLI use-cases.

The configuration classes in `config.py` not only define which parameters the CLI's and API's accept, but they also provide Click option/argument decorators that are used in `cli.py` to define the CLI option names/types/defaults. In this fashion, configuration classes accommodate both CLI and API usage concerns in one place and suggest that any changes to one require changes to the other; e.g. if parameter is added to config class, a corresponding option should be added to list of option decorators in the same class.

## Pipelines

### Checkpoint Ingest
cli entrypoint - `gc_ingest.pipelines core ingest checkpoint ...`

This pipeline is meant to ingest raw pdf documents (with metadata) from the next-in-line checkpointed (see terminology) S3 location. Which specific S3 path is picked to be processed is determined based on timestamp and (optionally) whether the timestamped subpath features a marker file (see README of the checkpoint tool for more details). This is meant to run on recurring basis, as it uses the checkpoint file to keep track of what directories should not be processed again. - Flagship use case is automatically picking up and processing uploads from the web crawlers.

### Local Ingest
cli entrypoint - `gc_ingest.pipelines core ingest local ...`

This pipeline is meant to ingest raw pdf documents (with metadata) from a local directory. Useful for certain manual ingest scenarios and local testing.

### S3 Ingest
cli entrypoint - `gc_ingest.pipelines core ingest s3 ...`

This pipeline is meant to ingest raw and (optionally) parsed documents from specific s3 paths. Useful for certain manual ingest scenarios.

## Terminology

- More in README files within `dataPipelines/gc_ingest/tools/...`

## Usage

Can be used as a CLI (see cli.py) or programmatically (see utils.py). CLI usage information can be retrieved in canonical fashion by running the module and passing `--help` flag.