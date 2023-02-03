import os
import glob
from tqdm import tqdm
from acdh_cidoc_pyutils import extract_begin_end, create_e52, normalize_string
from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO
from acdh_tei_pyutils.tei import TeiReader
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS

rdf_dir = "./rdf"
os.makedirs(rdf_dir, exist_ok=True)
domain = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(domain)
g = Graph()
LIMIT = False
entity_type = "documents"
if LIMIT:
    files = sorted(glob.glob('legalkraus-archiv/data/editions/*.xml'))[:LIMIT]
else:
    files = sorted(glob.glob('legalkraus-archiv/data/editions/*.xml'))
to_process = []
print("filtering documents without transcriptions")
for x in tqdm(files, total=len(files)):
    doc = TeiReader(x)
    try:
        doc.any_xpath('.//tei:div[@type="no-transcription"]')[0]
    except IndexError:
        to_process.append(x)
print(f"continue processing {len(to_process)} out of {len(files)} Documents")

for x in tqdm(to_process, total=len(to_process)):
    doc = TeiReader(x)
    xml_id = doc.tree.getroot().attrib["{http://www.w3.org/XML/1998/namespace}id"].replace('.xml', '')
    item_id = f"{SK}{xml_id}"
    subj = URIRef(item_id)
    item_label = normalize_string(doc.any_xpath(".//tei:title[1]/text()")[0])
    g.add((subj, RDF.type, FRBROO["F22"]))
    g.add((subj, RDFS.label, Literal(item_label, lang="de")))
    creation_uri = URIRef(f"{subj}/creation")
    g.add((creation_uri, RDF.type, FRBROO["F28"]))
    g.add((creation_uri, RDFS.label, Literal(f"Creation Event of {item_label}")))
    g.add((creation_uri, FRBROO["R17"], subj))
    g.add((subj, FRBROO["R17i"], subj))

    # creation date:
    try:
        creation_date_node = doc.any_xpath('.//tei:date[@subtype="produced"]')[0]
        go_on = True
    except IndexError:
        go_on = False
    if go_on:
        begin, end = extract_begin_end(creation_date_node)
        creation_ts = URIRef(f"{creation_uri}/timestamp")
        g += create_e52(creation_ts, begin_of_begin=begin, end_of_end=end)
    
    # creator Brief:
    try:
        creator = doc.any_xpath(".//tei:correspAction/tei:persName/@ref")[0]
        go_on = True
    except IndexError:
        go_on = False
    if go_on:
        creator_uri = URIRef(f"{SK}{creator[1:]}")
        g.add((creation_uri, CIDOC["P14_carried_out_by"], creator_uri))
print("writing graph to file")
g.serialize(f"{rdf_dir}/texts.ttl")