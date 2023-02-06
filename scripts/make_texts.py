import os
import glob
from tqdm import tqdm
from acdh_cidoc_pyutils import extract_begin_end, create_e52, normalize_string
from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO, NSMAP
from acdh_tei_pyutils.tei import TeiReader
from rdflib import Graph, Namespace, URIRef, Literal, XSD
from rdflib.namespace import RDF, RDFS

INT = Namespace("https://w3id.org/lso/intro/beta202001#")

rdf_dir = "./rdf"
os.makedirs(rdf_dir, exist_ok=True)
domain = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(domain)
g = Graph()
LIMIT = False
entity_type = "documents"
if LIMIT:
    files = sorted(glob.glob("legalkraus-archiv/data/editions/*.xml"))[:LIMIT]
else:
    files = sorted(glob.glob("legalkraus-archiv/data/editions/*.xml"))
to_process = []
print("filtering documents without transcriptions")
for x in tqdm(files, total=len(files)):
    doc = TeiReader(x)
    try:
        doc.any_xpath('.//tei:div[@type="no-transcription"]')[0]
        os.remove(x)
    except IndexError:
        to_process.append(x)
print(f"continue processing {len(to_process)} out of {len(files)} Documents")

for x in tqdm(to_process, total=len(to_process)):
    doc = TeiReader(x)
    xml_id = (
        doc.tree.getroot()
        .attrib["{http://www.w3.org/XML/1998/namespace}id"]
        .replace(".xml", "")
    )
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

    # fun with mentions
    for i, mention in enumerate(doc.any_xpath('.//tei:body//tei:rs[@ref and @type="person"]')):
        try:
            pb_start = mention.xpath('.//preceding::tei:pb/@n', namespaces=NSMAP)[-1]
        except IndexError:
            pb_start = 1
        try:
            pb_end = mention.xpath('.//following::tei:pb/@n', namespaces=NSMAP)[0]
        except IndexError:
            pb_end = pb_start
        person_id = mention.attrib["ref"][1:]
        person_uri = URIRef(f"{SK}{person_id}")
        mention_string = normalize_string(" ".join(mention.xpath(".//text()")))
        mention_event_uri = URIRef(f"{subj}/mention-event/{person_id}/{i}")
        mention_singleton_uri = URIRef(f"{subj}/mention-event/{person_id}/{i}/f4")
        mention_segment = URIRef(f"{mention_event_uri}/int16")
        g.add((mention_event_uri, RDF.type, CIDOC["E5_Event"]))
        g.add(
            (
                mention_event_uri,
                RDFS.label,
                Literal(f"Event: {item_label} erwähnt {mention_string}", lang="de"),
            )
        )
        g.add((mention_event_uri, CIDOC["P11_had_participant"], person_uri))
        g.add(
            (
                mention_event_uri,
                CIDOC["P12_occurred_in_the_presence_of"],
                mention_singleton_uri,
            )
        )
        g.add((mention_singleton_uri, RDF.type, FRBROO["F4"]))
        g.add((mention_singleton_uri, CIDOC["P128_carries"], mention_segment))
        g.add((mention_segment, RDF.type, INT["INT16_PublicationExpressionSection"]))
        g.add((mention_segment, INT["pageEnd"], Literal(pb_end)))
        g.add((mention_segment, INT["pageStart"], Literal(pb_start)))
        g.add((mention_segment, CIDOC["P165_incorporates"],subj ))

print("writing graph to file")
g.serialize(f"{rdf_dir}/texts.ttl")
