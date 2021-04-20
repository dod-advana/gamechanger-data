# Enity Matching/Resolution - Design

At time of writing, gamechanger has been relying on the filename of stored artifacts to updated revised documents. This is not the best way because these filenames will not always be stable. This document details the design of processes that reliably replaces stored publications in AWS S3 and ES.

## 1. Goals

This process should be able to ...

* obtain latest ocr'd pdf files from all currently crawled sites from PaaS team running the crawler, downloader, and OCR jobs
* obtain output of the PaaS job and store the document metadata and file locations in a database
* use the new file manifest from the database to determine which files to run document parser on and automatically push updated pubs and summary/keyword-tag information to the App's document database (ES)

## 2. Pipelines

Three main jobs will accomplish aforementioned goals: Crawler-Download-OCR Pipeline, Manifest/Download-Helper Pipeline, and Parser-Publish Pipeline. - Details as follows.

### 2.1. Crawler-Download-OCR Pipeline

* **Purpose**: Enumerate download links and metadata, download, and run OCR for publications at expected web locations.
* **Method**: Python web scraping program that runs via container in PaaS team environment
* **Frequency**: Daily
* **Input**: (ENV VARS) Expected URL's where publication download links are found.
* **Output**: (HDFS/S3) Enriched JSON metadata and OCR processed PDF files (with HDFS/S3 locations) for the downstream pipelines.

### 2.2. Manifest/Download-Helper Pipeline

* **Purpose**: Obtain OCR processed PDF and JSON file staging locations
* **Method**: Python script that obtain output of previous job and stores infromation in SQLite/PostgreSQL 
* **Frequency**: Daily
* **Input**: (HDFS/S3) Enriched JSON metadata and OCR processed PDF files (with HDFS/S3 locations).
* **Output**: (HDFS/S3/DB) DB with history of pdf/json file locations and metadata. Interim HDFS/S3 locations for the most current documents in the manifest.

### 2.3. Parser-Publish Pipeline

* **Purpose**: Enrich pub metadata with summaries and keyword tags/set final locations of pdf and jsons
* **Method**: Python program that parses PDF pub files for summary and keyword information using the DB manifest, sets new pdf/json s3 final locations, and creates a new ES index active.
* **Frequency**: Daily (if new records are available)
* **Input**: (HDFS/S3/DB) DB with history of pdf/json file locations and metadata. Interim HDFS/S3 locations for the most current documents in the manifest.
* **Output**: (HDFS/S3/ES) Final locations for most current docs in s3 and updated document index is updated with new pubs and associated metadata.

