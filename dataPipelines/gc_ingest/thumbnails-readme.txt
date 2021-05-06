### DELETE AFTER NEW PERSON TAKES OVER TASK ###
Sanjana Thirumalai, 5/7/2021

This branch contains the logic for creating and uploading pdf thumbnails to s3.
Creating thumbnails:
    -In document_parser, created a cli option generate_thumbnails that dictates whether or not to generate the pngs
    -In document_parser/lib, created generate_png.py that uses fitz to create png of the first page of a pdf
    -created thumbnail_dir config option that says where to save the thumbnail pngs to

Uploading thumbnails to s3:
    -in gc_ingest/tools/load, added a thumbnail extension/doc/archive type to facilitate uploading
    -also created folder for the thumbnails to be uploaded in s3 (should be "thumbnails" in the main dir)