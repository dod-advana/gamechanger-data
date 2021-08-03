from pathlib import Path
import filetype
import typing as t
import json


class ManualMetadata:

    def __init__(self, input_directory, document_group):
        self.input_directory = input_directory
        self.document_group = document_group
        p = Path(self.input_directory).glob("**/*")
        self.files = [x for x in p if x.is_file() and (str(x).endswith("pdf") or str(x).endswith("html")
                                                       or (filetype.guess(str(x)) is not None and (
                                                           filetype.guess(str(x)).mime == "pdf" or filetype.guess(str(x)).mime == "application/pdf")))]
        self.metadata_files = [Path(x).stem for x in p if x.is_file() and filetype.guess(str(x)) is not None and (
            filetype.guess(str(x)).mime == "metadata")]

    def create_document(self, file) -> t.Optional[t.Dict[str, t.Any]]:
        doc = None
        if self.document_group == "Memo":
            pdi = dict(doc_type="pdf", web_url="manual.ingest")
            version_hash_fields = {"filename": Path(file).name}
            doc = dict(
                doc_name=Path(file).stem,
                doc_title=Path(file).stem,
                doc_num="",
                doc_type="Memo",
                publication_date="N/A",
                cac_login_required=True,
                crawler_used="Memo",
                source_page_url="manual.ingest",
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdi]
            )
        elif self.document_group == "NGA":
            pdi = dict(doc_type="pdf", web_url="manual.ingest")
            version_hash_fields = {"filename": Path(file).name}
            doc = dict(
                doc_name=Path(file).stem,
                doc_title=Path(file).stem,
                doc_num="",
                doc_type="pdf",
                publication_date="N/A",
                cac_login_required=False,  # TODO check this
                crawler_used="nga",
                source_page_url="manual.ingest",
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdi]
            )
        elif self.document_group == "pdf":
            pdi = dict(doc_type="pdf", web_url="manual.ingest")
            version_hash_fields = {"filename": Path(file).name}
            doc = dict(
                doc_name=Path(file).stem,
                doc_title=Path(file).stem,
                doc_num="",
                doc_type="pdf",
                publication_date="N/A",
                cac_login_required=True,
                crawler_used="pdf",
                source_page_url="manual.ingest",
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdi]
            )
        else:
            pdi = dict(doc_type=Path(file).suffix[1:],
                       web_url="manual.ingest")
            version_hash_fields = {"filename": Path(file).name}
            doc = dict(
                doc_name=Path(file).stem,
                doc_title=Path(file).stem,
                doc_num="",
                doc_type=str.upper(self.document_group),
                publication_date="N/A",
                cac_login_required=True,
                crawler_used=str.upper(self.document_group),
                source_page_url="manual.ingest",
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdi],
                display_doc_type="Document",
                display_org=str.upper(self.document_group),
                display_source=str.upper(self.document_group) + " Publications"
            )

        return doc

    def create_metadata(self):
        if self.document_group:
            for file in self.files:
                print(self.metadata_files)
                if Path(file).stem not in self.metadata_files:
                    doc = self.create_document(file)

                    outname = str(file) + '.metadata'
                    print(outname)
                    if doc:
                        with open(outname, "w") as f:
                            f.write(json.dumps(doc))
