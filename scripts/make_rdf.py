import os
from tqdm import tqdm
from acdh_cidoc_pyutils import (
    make_appelations,
    make_ed42_identifiers,
    coordinates_to_p168
)
from acdh_cidoc_pyutils.namespaces import CIDOC
from acdh_tei_pyutils.tei import TeiReader
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, OWL

rdf_dir = "./rdf"
os.makedirs(rdf_dir, exist_ok=True)
domain = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(domain)
g = Graph()

entity_type = "person"
index_file = f"./legalkraus-archiv/data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap
items = doc.any_xpath(f".//tei:{entity_type}")
print(f"converting {entity_type}s derived from {index_file}")
for x in tqdm(items, total=len(items)):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
    item_id = f"{SK}{xml_id}"
    subj = URIRef(item_id)
    g.add((subj, RDF.type, CIDOC["E21_Person"]))
    g += make_ed42_identifiers(subj, x, type_domain=f"{SK}types", default_lang="und")
    g += make_appelations(subj, x, type_domain=f"{SK}types", default_lang="und")

# ORGS
entity_type = "org"
index_file = f"./legalkraus-archiv/data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap
items = doc.any_xpath(f".//tei:{entity_type}")
print(f"converting {entity_type}s derived from {index_file}")
for x in tqdm(items, total=len(items)):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
    item_id = f"{SK}{xml_id}"
    subj = URIRef(item_id)
    g.add((subj, RDF.type, CIDOC["E74_Group"]))
    g += make_appelations(subj, x, type_domain=f"{SK}types/", default_lang="und")
    g += make_ed42_identifiers(subj, x, type_domain=f"{SK}types", default_lang="und")

# PLACES
entity_type = "place"
index_file = f"./legalkraus-archiv/data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap
items = doc.any_xpath(f".//tei:{entity_type}")
print(f"converting {entity_type}s derived from {index_file}")
for x in tqdm(items, total=len(items)):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
    item_id = f"{SK}{xml_id}"
    subj = URIRef(item_id)
    g.add((subj, RDF.type, CIDOC["E53_Place"]))
    g += coordinates_to_p168(subj, x)
    g += make_appelations(subj, x, type_domain=f"{SK}types/", default_lang="und")
    g += make_ed42_identifiers(subj, x, type_domain=f"{SK}types", default_lang="und")
    try:
        pmb = x.xpath('.//tei:idno[@type="pmb"]/text()', namespaces=nsmap)[0]
    except IndexError:
        pmb = None
    if pmb:
        pmb_uri = URIRef(pmb)
        g.add((subj, OWL["sameAs"], pmb_uri))
        g.add((pmb_uri, RDF.type, CIDOC["E42_Identifier"]))
print("writing graph to file")
g.serialize(f"{rdf_dir}/data.ttl")