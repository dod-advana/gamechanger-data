from neo4j import GraphDatabase

# Credentials in app-config .json() from ./configure_repo.sh
# NEED TO BE CONNECTED TO BIG-IP Edge VPN

URI = "bolt://[ip]:[port]"
AUTH = ("[user]", "[pass]")

driver = GraphDatabase.driver(URI, auth=(AUTH))

with driver.session() as session:
    result = session.run("MATCH (n) RETURN n LIMIT 10")
    for record in result:
        node = record['n']
        print(f"Node ID: {node.id}")
        for key, value in node.items():
            print(f"{key}: {value}")
        print("-----------")

