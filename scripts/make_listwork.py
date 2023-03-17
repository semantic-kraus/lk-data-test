import os
from tqdm import tqdm
from acdh_cidoc_pyutils import normalize_string, make_e42_identifiers

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
entity_type = "work"
index_file = f"./data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap
items = doc.any_xpath(f".//tei:listBibl/tei:bibl")
if LIMIT:
    items = items[:LIMIT]
print(f"converting {entity_type}s derived from {index_file}")

main_title_type_uri = URIRef(f"{SK}types/title/main")
sub_title_type_uri = URIRef(f"{SK}types/title/sub")

g.add((main_title_type_uri, RDF.type, CIDOC["E55_Type"]))
g.add((sub_title_type_uri, RDF.type, CIDOC["E55_Type"]))
for x in tqdm(items, total=len(items)):
    try:
        xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    except Exception as e:
        print(x, e)
        continue
    item_id = f"{SK}{xml_id}"
    subj = URIRef(item_id)
    for title in x.xpath(
        './tei:bibl[@type="sk"]/tei:title[not(@type)]', namespaces=nsmap
    ):
        level_type = title.attrib["level"]
        if level_type == "a":
            label_value = title.text
            break
        elif level_type == "m":
            label_value = title.text
            break
        else:
            label_value = title.text
            break
    label_value = normalize_string(label_value)
    g.add((subj, RDF.type, CIDOC["F22_Self-Contained_Expression"]))
    g.add(
        (
            subj,
            RDFS.label,
            Literal(f"Expression: {label_value}", lang="en"),
        )
    )

    # creation
    expre_creation_uri = URIRef(f"{subj}/creation")
    g.add((
        expre_creation_uri, RDF.type, CIDOC["F28_Expression_Creation"]
    ))
    g.add((
        expre_creation_uri, RDFS.label, Literal(f"Creation of: {label_value}")
    ))
    g.add((
        expre_creation_uri, FRBROO["R17_created"], subj
    ))
    for author in x.xpath('.//tei:author/@key', namespaces=nsmap):
        author_uri = URIRef(f"{SK}{author}")
        g.add((
            expre_creation_uri, CIDOC["P14_carried_out_by"], author_uri
        ))
    # title
    title_uri = URIRef(f"{subj}/title/0")
    g.add((title_uri, RDF.type, CIDOC["E35_Title"]))
    g.add(
        (title_uri, RDF.value, Literal(f"{label_value}", lang="und"))
    )
    g.add((title_uri, CIDOC["P2_has_type"], main_title_type_uri))
    g.add((subj, CIDOC["P102_has_title"], title_uri))

    # subtitle
    for i, sub in enumerate(
        x.xpath('.//tei:title[@type="subtitle"]', namespaces=nsmap), start=1
    ):
        label_value = sub.text
        title_uri = URIRef(f"{subj}/title/{i}")
        g.add((title_uri, RDF.type, CIDOC["E35_Title"]))
        g.add(
            (
                title_uri,
                RDF.value,
                Literal(normalize_string(f"{label_value}"), lang="und"),
            )
        )
        g.add((title_uri, CIDOC["P2_has_type"], sub_title_type_uri))
        g.add((subj, CIDOC["P102_has_title"], title_uri))

    # identifiers
    g += make_e42_identifiers(
        subj, x, type_domain=f"{SK}types", default_lang="und", same_as=False
    )

    


print("writing graph to file")
g.serialize(f"{rdf_dir}/{entity_type}s.ttl")
