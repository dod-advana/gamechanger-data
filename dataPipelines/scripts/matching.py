import os
import sys
import shutil
from pathlib import Path

raw_docs_dir = Path(os.environ["RAW_DOCS"]).absolute()
parsed_docs_dir = Path(os.environ["PARSED_DOCS"]).absolute()
output_base_dir = Path(os.environ["OUTPUT_BASE"]).absolute()
output_unparsed = Path(output_base_dir, "unparsed")
output_raw = Path(output_base_dir, "raw")
output_parsed = Path(output_base_dir, "parsed")
output_base_dir.mkdir(exist_ok=True)
output_unparsed.mkdir(exist_ok=True)
output_raw.mkdir(exist_ok=True)
output_parsed.mkdir(exist_ok=True)
raw_docs = [x for x in raw_docs_dir.iterdir() if x.name.lower().endswith("pdf") or x.name.lower().endswith("html")]
crawler_output_file = Path(raw_docs_dir, "crawler_output.json")

for raw_file in raw_docs:
    metadata_file = Path(raw_docs_dir, raw_file.name + ".metadata")
    parsed_file = Path(parsed_docs_dir, raw_file.with_suffix(".json").name)
    if parsed_file.exists():
        shutil.copy(parsed_file, output_parsed)
        shutil.copy(raw_file, output_raw)
        shutil.copy(metadata_file, output_raw)
    else:
        shutil.copy(raw_file, output_unparsed)
        shutil.copy(metadata_file, output_unparsed)

if crawler_output_file.exists():
    shutil.copy(crawler_output_file, output_unparsed)
    shutil.copy(crawler_output_file, output_raw)

