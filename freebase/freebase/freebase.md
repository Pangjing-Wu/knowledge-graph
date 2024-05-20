# Freebase
Freebase was a large collaborative knowledge base consisting of data composed mainly by its community members. It was an online collection of structured data harvested from many sources, including individual, user-submitted wiki contributions. It totally contains 1.9 billion triples stored in `N-Triples RDF` format. For example:
```rdf
<http://rdf.freebase.com/ns/g.11vjz1ynm> <http://rdf.freebase.com/ns/measurement_unit.dated_percentage.date> "2001-02"^^<http://www.w3.org/2001/XMLSchema#gYearMonth>  .
<http://rdf.freebase.com/ns/g.11vjz1ynm>  <http://rdf.freebase.com/ns/measurement_unit.dated_percentage.source> <http://rdf.freebase.com/ns/g.11x1gf2m6>  .
```

## Download
### Freebase
You can download the dump of freebase from [this data dump](https://developers.google.com/freebase/#freebase-rdf-dumps) provided by Google. The dump size is about 22GB, and decompressing it needs additional 250GB storage space. You can decompress it by:
```shell
gunzip -c freebase-rdf-latest.gz > freebase.nt
```
It is suggested to decompress the files on the backend and take a cup of coffee ☕️ for yourself since it needs a long time to complete the decompression.
```shell
nohup gunzip -c freebase-rdf-latest.gz 1>freebase.nt 2>unzip-freebase.log &
```
### Freebase/Wikidata Mappings
Due to the partial incompleteness of the data present in the freebase dump, some of the entities with missing partial relationships need to be mapped to wikidata. You can download the mapping relations from [this data dump](https://developers.google.com/freebase?hl=en#freebase-wikidata-mappings) provided by Google and decompress:
```shell
gunzip -c fb2w.nt.gz > fb2w.nt
```

## Preprocessing
### Clean Knowledge Triples
First, we need to clean the triples to remove non-English or non-digital triplets by running the Python script [remove-non-english.py](./remove-non-english.py) in the same folder:
```shell
nohup bash -c python -u remove-non-english.py 0<freebase.nt 1>filter-freebase.nt 2>remove-non-english.log 2>&1 >/dev/null&
```

## Load Data with OpenLink Virtuoso
OpenLink Virtuoso is a powerful RDF database that excels in managing and querying linked data. It is suitable for managing large-scale semantic data as it stores RDF triples efficiently and supports SPARQL for querying RDF data.

### Install OpenLink Virtuoso
You can find the latest version of OpenLink Virtuoso on [sourceforge](https://sourceforge.net/projects/virtuoso/files/virtuoso/) and download the one corresponding to your system platform. Decompress it and move it to `/usr/local`:
```shell
tar xvpfz virtuoso-opensource.x86_64-generic_glibc25-linux-gnu.tar.gz && mv virtuoso-opensource /usr/local/ && cd /usr/local/virtuoso-opensource
```
Rename the config file under `database` by:
```shell
mv ./database/virtuoso.ini.sample ./database/virtuoso.ini
```
Add Virtuoso path to your environment:
```shell
echo '
export VIRTUOSO_HOME=/usr/local/virtuoso-opensource
export PATH=.:${VIRTUOSO_HOME}/bin:$PATH' >> ~/.zshrc # or vi ~/.bashrc, depends on your shell.
source ~/.zshrc
```
To avoid the name collision of `isql`, it would be better to rename `./bin/isql` by:
```shell
mv ./bin/isql ./bin/isql-vt
```
Then, run `virtuoso-t -fd` in your terminal to test whether Virtuoso has been successfully installed. To run Virtuoso on the backend, you can use `virtuoso-t`.

### Start Service and Load Data
Before starting service and loading data, you should add your KG data directory to the virtuoso database config by appending `<your directory>` to the `DirsAllowed` in `./database/virtuoso.ini`. For example:
```text
AllowOSCalls                    = 0
SchedulerInterval               = 10
DirsAllowed                     = ., ../vad, /usr/share/proj
ThreadCleanupInterval           = 1
ThreadThreshold                 = 1
```
>[!NOTE]
>If you are already running the `virtuoso-t`, please remember to restart it after modification. 

Create a file, for example `load.vsql`, and copy [this script](https://vos.openlinksw.com/owiki/wiki/VOS/VirtBulkRDFLoaderScript#Bulk%20Loader%20Procedure%20and%20Sub-procedures%20creation%20SQL%20script) into the file in order to load the bulk loader procedure and sub-procedures into virtuoso.

Then we start the Virtuoso service.
```shell
virtuoso-t # start service in the backend.
isql-vt 1111 dba dba # run the database. args: isql-vt <HOST>[:<PORT>] <UID> <PWD>
```
We use `rdf_loader` to specific Freebase and Wiki and import them into database with `rdf_loader_run`.
```SQL
load load.vsql;
ld_dir('<your directory>', 'filter-freebase.nt', 'http://freebase.com'); 
ld_dir('<your directory>', 'fb2w.nt', 'http://www.wikidata.org'); 
rdf_loader_run();
```
ld_dir('/home/wupj/data/knowledge-graph/freebase/freebase', 'filter-freebase.nt', 'http://freebase.com');
>[!TIP]
>Loading Large Scale KG
>Note the default settings of Virtuoso will take very little memory but will not result in very good performance. You can accelerate the loading by modifying `NumberOfBuffers` and `MaxDirtyBuffers` in `./database/virtuoso.ini`. In addition, set `AsyncQueueMaxThreads = 1` and `ThreadThreshold = 1` can avoid the efficiency degradation caused by frequent thread switching. 

We can check the loading status of knowledge graph by:
```sql
SELECT * FROM DB.DBA.LOAD_LIST;
```
>[!NOTE]
>Loading Large Scale KG
>Even if you exit the `isql` and reopen, the data in `LOAD_LIST` will not disappear, so you should delete the data to avoid duplicated uploading:
>```sql
>DELETE FROM DB.DBA.LOAD_LIST;
>```

## Query Knowledge Graph in Python
After taking a long time to load knowledge graph in Virtuoso, now you can query knowledge graph in Python. `SPARQLWrapper` is required to run the test script and you can install it by:
```shell
pip install SPARQLWrapper
```

Here is an [example](./test-freebase.py) for you to test.
```python
import json
from SPARQLWrapper import SPARQLWrapper, JSON

SPARQLPATH = "http://localhost:8890/sparql"

sparql = SPARQLWrapper(SPARQLPATH)
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
print(results)
```

You can also perform other operations through SPARQL, such as: 

* Get number of triples in the DB.
````sql
SELECT COUNT(*) { 
  ?s ?p ?o
}
````
* Get all relations of a mention.
````sql
PREFIX ns: <http://rdf.freebase.com/ns/>
SELECT * WHERE {
   ns:m.014zcr ?p ?o
} 
LIMIT 10
````
* For multi-hop relations search:
````sql
PREFIX ns: <http://rdf.freebase.com/ns/>
SELECT * WHERE {
  ns:m.014zcr ns:film.actor.film ?film_performance .
  ?film_performance ns:film.performance.film ?film .
  ?film ns:type.object.name ?name .
  ?film ns:film.film.initial_release_date ?initial_release_date .
  FILTER(lang(?name) = 'en')
} 
LIMIT 1
````

For the complete reference, see Freebase types and relations, and [Virtuoso SPARQL service](http://virtuoso.openlinksw.com/dataspace/doc/dav/wiki/Main/VOSSparqlProtocol).


## Map entity ID to real name
Since the entities in Freebase are alphanumeric strings or URIs, such as `m.03_dwn`, that convey little information at a glance. To convert an entity ID into its human-readable name or type, you can query the knowledge graph by:
```python
from SPARQLWrapper import SPARQLWrapper, JSON

SPARQLPATH = "http://localhost:8890/sparql"

sparql = SPARQLWrapper(SPARQLPATH)

sparql_txt = """
    PREFIX ns: <http://rdf.freebase.com/ns/>
    SELECT DISTINCT ?tailEntity
    WHERE {
        {   
            ?entity ns:type.object.name ?tailEntity .
            FILTER(?entity = ns:%s)
        }
        UNION
        {
            ?entity <http://www.w3.org/2002/07/owl#sameAs> ?tailEntity .
            FILTER(?entity = ns:%s)
        }
    }
"""

entity_id = 'm.03_dwn'
sparql.setQuery(sparql_txt % (entity_id, entity_id))
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
print(results)
```