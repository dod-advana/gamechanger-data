# US Code Pipelines - Design

At time of writing, US Code publications consist of 54 distinct documents (not counting appendices) that are available for download at `uscode.house.gov/download/download.shtml`. This document details the design of processes meant to automate the discovery and downloading of these publications and subsequent updates.

## 1. Goals

US Code Pipelines should be able to ...

* obtain latest pdf files for US Code publications
* obtain new versions of pub files without re-downloading old/existing pubs
* provide stable HDFS/S3 URL to a manifest of latest versions of the pubs and their HDFS/S3 locations
* automatically push updated pubs and summary/keyword-tag information to the App's document database (SOLR).

## 2. Pipelines

Five distinct pipelines will accomplish aforementioned goals: Crawler Pipeline, Download Pipeline, Metadata Enrichment Pipeline, Manifest Pipeline, and Publish Pipeline. - Details as follows.

### 2.1. Crawler Pipeline

* **Purpose**: Enumerate all download links and metadata for US Code publications at expected web locations.
* **Method**: Python web scraping program that runs via StreamSets SDC
* **Frequency**: Daily
* **Input**: (ENV VARS) Expected URL's where US Code pub download links are found.
* **Output**: (HDFS/S3) JSON-formatted records containing download URI's and metadata such as pub title and versioning info.

### 2.2. Download Pipeline

* **Purpose**: Obtain PDF versions of the US Code publications
* **Method**: Shell script that downloads PDF files from their web url's
* **Frequency**: every 30m (if new records are available)
* **Input**: (HDFS/S3) JSON-formatted records containing download URI's and pub metadata + full US Code JSON manifest (if exists) to avoid downloading existing files
* **Output**: (HDFS/S3) PDF pub files packaged with their JSON metadata and JSON update events referring to processed files (with HDFS/S3 locations) for the downstream pipelines.

### 2.3. Metadata Enrichment Pipeline

* **Purpose**: Enrich pub metadata with summaries and keyword tags
* **Method**: Python program that parses PDF pub files for summary and keyword information.
* **Frequency**: Daily (if new records are available)
* **Input**: (HDFS/S3) JSON update event records and the JSON metadata/manifest + PDF files produced by the Download Pipeline
* **Output**: (HDFS/S3) Enriched JSON metadata and JSON update events referring to processed files (with HDFS/S3 locations) for the downstream pipelines.

### 2.4. Manifest Pipeline

* **Purpose**: Update a JSON manifest of all US Code pubs with latest metadata and S3/HDFS locations of each pub.
* **Method**: Python program that updates a JSON manifest of pubs based on files available since last run.
* **Frequency**: Daily
* **Input**: (HDFS/S3) US Code JSON manifest (if exists) and JSON manifest update events produced by the Metadata Enrichment Pipeline.
* **Output**: (HDFS/S3) Updated US Code JSON manifest (the path/name of manifest stays the same for benefit of pub consumers)

### 2.5. Publish Pipeline

* **Purpose**: Publish enriched metadata and files to SOLR cluster, so new docs are accessible from the App.
* **Method**: Python program that converts manifest to expected format and uses SOLR API to publish it.
* **Frequency**: Daily
* **Input**: (HDFS/S3) US Code JSON manifest with enriched summary/keyword data.
* **Output**: (SOLR) Document index is updated with new pubs and associated metadata.
