from SPARQLWrapper import SPARQLWrapper, JSON

SPARQLPATH = "http://localhost:8890/sparql"

sparql = SPARQLWrapper(SPARQLPATH)


# count triples.
sparql_txt = """
SELECT COUNT(*) { 
    ?s ?p ?o
}
"""
sparql.setQuery(sparql_txt)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

for binding in results['results']['bindings']:
    for key in binding:
        print(f"Total triples: {binding[key]['value']}")


# find the individuals who are married to the person (ns:m.02pbp9). 
sparql_txt = """PREFIX ns: <http://rdf.freebase.com/ns/>
    SELECT distinct ?name3
    WHERE {
    ns:m.0k2kfpc ns:award.award_nominated_work.award_nominations ?e1.
    ?e1 ns:award.award_nomination.award_nominee ns:m.02pbp9.
    ns:m.02pbp9 ns:people.person.spouse_s ?e2.
    ?e2 ns:people.marriage.spouse ?e3.
    ?e2 ns:people.marriage.from ?e4.
    ?e3 ns:type.object.name ?name3
    MINUS{?e2 ns:type.object.name ?name2}
    }
"""
sparql.setQuery(sparql_txt)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

print('Spouses:')
for binding in results['results']['bindings']:
    for key in binding:
        print(binding[key]['value'])