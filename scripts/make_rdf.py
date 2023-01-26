import os
from lxml.etree import Element
from tqdm import tqdm
from acdh_cidoc_pyutils import (
    make_appelations,
    make_ed42_identifiers,
    coordinates_to_p168
)
from acdh_cidoc_pyutils.namespaces import CIDOC, NSMAP
from acdh_tei_pyutils.tei import TeiReader
from acdh_tei_pyutils.utils import make_entity_label
from rdflib import Graph, Namespace, URIRef, Literal, RDFS
from rdflib.namespace import RDF, OWL


def make_birth_death_entities(subj: URIRef, node: Element, event_type="birth", verbose=False, default_prefix="Geburt von", default_lang="de"):
    g = Graph()
    name_node = node.xpath('.//tei:persName[1]', namespaces=NSMAP)[0]
    label, label_lang = make_entity_label(name_node, default_lang=default_lang)
    if event_type not in ["birth", "death"]:
        return (g, None, None)
    if event_type == "birth":
        cidoc_property = CIDOC["P98_brought_into_life"]
        cidoc_class = CIDOC[f"E67_Birth"]
    else:
        cidoc_property = CIDOC["P100_was_death_of"]
        cidoc_class = CIDOC[f"E69_Death"]
    xpath_expr = f".//tei:{event_type}[1]"
    try:
        event_node = node.xpath(xpath_expr, namespaces=NSMAP)[0]
    except IndexError as e:
        if verbose:
            print(subj, e)
            return (g, None, None)
    event_uri = URIRef(f"{subj}/{event_type}")
    time_stamp_uri = URIRef(f"{event_uri}/timestamp")
    g.set((
        event_uri, cidoc_property, subj
    ))
    g.set((
        event_uri, RDF.type, cidoc_class
    ))
    g.add((
        event_uri, RDFS.label, Literal(f"{default_prefix} {label}", lang=default_lang)
    ))
    g.set((
        event_uri, CIDOC["P4_has_time-span"], time_stamp_uri
    ))
    return (g, event_uri, time_stamp_uri)

rdf_dir = "./rdf"
os.makedirs(rdf_dir, exist_ok=True)
domain = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(domain)
g = Graph()
LIMIT = 250
entity_type = "person"
index_file = f"./legalkraus-archiv/data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap
items = doc.any_xpath(f".//tei:{entity_type}")
if LIMIT:
    items = items[:LIMIT]
print(f"converting {entity_type}s derived from {index_file}")
for x in tqdm(items, total=len(items)):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    item_id = f"{SK}{xml_id}"
    subj = URIRef(item_id)
    g.add((subj, RDF.type, CIDOC["E21_Person"]))
    g += make_ed42_identifiers(subj, x, type_domain=f"{SK}types", default_lang="und")
    g += make_appelations(subj, x, type_domain=f"{SK}types", default_lang="und")
    birth_g, birth_uri, birth_timestamp = make_birth_death_entities(subj, x, event_type="birth", verbose=True)
    g += birth_g
    death_g, death_uri, death_timestamp = make_birth_death_entities(subj, x, event_type="death", default_prefix="Tod von", verbose=True)
    g += death_g


# ORGS
entity_type = "org"
index_file = f"./legalkraus-archiv/data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap
items = doc.any_xpath(f".//tei:{entity_type}")
if LIMIT:
    items = items[:LIMIT]
print(f"converting {entity_type}s derived from {index_file}")
for x in tqdm(items, total=len(items)):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
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
if LIMIT:
    items = items[:LIMIT]
print(f"converting {entity_type}s derived from {index_file}")
for x in tqdm(items, total=len(items)):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
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