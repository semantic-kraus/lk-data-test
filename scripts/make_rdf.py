import os
from tqdm import tqdm
from acdh_cidoc_pyutils import (
    create_e52,
    normalize_string,
    extract_begin_end,
    make_appelations,
    make_ed42_identifiers
)
from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO
from acdh_tei_pyutils.tei import TeiReader
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL

rdf_dir = "./rdf"
os.makedirs(rdf_dir, exist_ok=True)
domain = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(domain)
g = Graph()

doc = TeiReader("./legalkraus-archiv/data/indices/listplace.xml")
nsmap = doc.nsmap
items = doc.any_xpath(".//tei:place")

print("converting places")
for x in tqdm(items, total=len(items)):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"].lower()
    item_id = f"{SK}{xml_id}"
    subj = URIRef(item_id)
    g.add((subj, RDF.type, CIDOC["E53_Place"]))
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