Readme for neo4j publisher

Currently, this reads from a csv of entities (scraped from USAGOV site) and inputs them with their information into the
neo4j database. Then, it goes to the gc_assists db in postgres and adds verified entities (ones that users have
verified as accurately tagged).

There is also a wikipedia scraper that will find the wiki page of the verified entities and scrape the infobox for
relevant information (key people, address, headquarters, etc.)

The actual NER tagging is done with spacy's entity extraction algorithm in the dataScience folder.