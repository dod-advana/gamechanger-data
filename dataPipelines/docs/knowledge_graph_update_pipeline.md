# Knowledge Graph Update - Design

At time of writing, gamechanger staff has been updating the knowledge graphs manually every so often to populate the databases. There should be a way of automating this process to ensure the databases (Neo4j and Postgres) stay up to data. This document details the design of processes that will update the knowledge graphs on a regular basis.

## 1. Goals

This process should be able to ...

* obtain the current data in parsed and ready for input into the knowledge graph on a nightly basis using a bash script
* Use the data API software to insert the data into both the Neo4J knowledge graph and the PostgreSQL knowledge graph ensuring both are up to date 
* Ensure that the inserts successfully updated both knowledge graphs before completing the task

## 2. Pipeline

The aforementioned goals will be accomplished through an additional streamsets pipeline, to run daily: . - Details as follows.

* **Purpose**: Obtain the locations for most current docs in s3 to update the knowledge graphs, creating insert statements for Neo4j and PostgreSQL.
* **Method**: Bash script that connects to data API to insert statements existing docs in S3
* **Frequency**: Daily
* **Input**: Environment Variables
* **Output**: Success or Failure of Insertion