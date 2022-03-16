# Checkpoint Tool

Tool for handling file operations on checkpointed storage directories.

## Terminology

- **Checkpointed Base Directory** is a directory that uses a checkpoint (like timestamp) for its' subdirectories. For example, if `<data-root>/external-uploads/manual/` is a checkpointed base directory, we expect files in it to be organized under timestamped subdirectories - like `<data-root>/external-uploads/manual/2021-01-02T12:00:00`. It is called "checkpointed", because a checkpoint, like timestamp, can be maintained in a separate file like `<data-root>/external-uploads/manual/checkpoint.txt` to signify that only subdirectories with timestamp that is greater than the checkpoint should be considered for processing. - Typical scenario is an automated process that populates such timestamped directories and another process that periodically checks the base directories for new timestamped directories. Advancing the checkpoint stored in `<data-root>/external-uploads/manual/checkpoint.txt` is then used to avoid re-processing older directories without having to delete them.
- **Marker File** is a file that signifies that the process populating a given directory has finished what it was doing. For example, if marker file is `manifest.json`, then a web crawler uploading large set of documents to a checkpointed path on S3 would make sure it uploads `manifest.json` file last, so the downstream processors can use the fact of whether or not this file exists to determine whether it is okay to begin processing the batch of uploaded files. Checkpoint tool combines all such consideration and handling of checkpointed paths with marker files in its CLI/API.

## Usage

Can be used as a CLI (see cli.py) or programmatically (see utils.py). CLI usage information can be retrieved in canonical fashion by running the module and passing `--help` flag.