import os
from tqdm import tqdm
from acdh_cidoc_pyutils import (
    make_appellations,
    make_e42_identifiers,
    make_birth_death_entities,
    make_occupations,
    make_entity_label,
)
from acdh_cidoc_pyutils.namespaces import CIDOC
from acdh_tei_pyutils.tei import TeiReader
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS

if os.environ.get("NO_LIMIT"):
    LIMIT = False
    print("no limit")
else:
    LIMIT = 100

rdf_dir = "./rdf"
os.makedirs(rdf_dir, exist_ok=True)
domain = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(domain)
g = Graph()
entity_type = "person"
index_file = f"./data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap
items = doc.any_xpath(f".//tei:{entity_type}")
if LIMIT:
    items = items[:LIMIT]

g.add((URIRef(f"{SK}types/place/placename"), RDF.type, CIDOC["E55_Type"]))
g.add((URIRef(f"{SK}types/idno/xml-id"), RDF.type, CIDOC["E55_Type"]))

print(f"converting {entity_type}s derived from {index_file}")
for x in tqdm(items, total=len(items)):
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    item_id = f"{SK}{xml_id}"
    subj = URIRef(item_id)
    name_node = x.xpath(".//tei:persName", namespaces=nsmap)[0]
    item_label = make_entity_label(name_node)[0]
    g.add((subj, RDF.type, CIDOC["E21_Person"]))
    g += make_e42_identifiers(
        subj, x, type_domain=f"{SK}types", default_lang="und", same_as=False
    )
    g += make_appellations(subj, x, type_domain=f"{SK}types", default_lang="und")
    try:
        gender = x.xpath(".//tei:sex/@value", namespaces=doc.nsmap)[0]
    except IndexError:
        gender = None
    if gender is not None:
        type_uri = f"{SK}types/person/persname/{gender}"
        for appellation_uri in g.objects(
            subject=subj, predicate=CIDOC["P1_is_identified_by"]
        ):
            if "/appellation/" in appellation_uri:
                g.add((appellation_uri, CIDOC["P2_has_Type"], URIRef(f"{type_uri}")))
    g += make_occupations(subj, x, default_lang="de", special_label="works for: ")[0]
    # g += make_affiliations(
    #     subj,
    #     x,
    #     domain,
    #     person_label=item_label,
    #     org_id_xpath="./tei:orgName[1]/@key",
    #     org_label_xpath="./tei:orgName[1]//text()",
    # )
    if x.xpath("./tei:birth", namespaces=nsmap):
        birth_g, birth_uri, birth_timestamp = make_birth_death_entities(
            subj,
            x,
            domain=SK,
            event_type="birth",
            verbose=False,
            date_node_xpath="/tei:date[1]",
            place_id_xpath="//tei:settlement[1]/@key",
        )
        g += birth_g
    if x.xpath("./tei:birth[./tei:settlement]", namespaces=nsmap):
        try:
            birth_place_node = x.xpath(
                "./tei:birth/tei:settlement", namespaces=nsmap
            )[0]
        except IndexError:
            birth_place_node = None
        if birth_place_node is not None:
            try:
                birth_place_id = birth_place_node.attrib["key"]
            except KeyError:
                birth_place_id = None
            if birth_place_id is not None:
                birth_place_uri = URIRef(f"{SK}{birth_place_id}")
                g.add((birth_place_uri, RDF.type, CIDOC["E53_Place"]))
                place_label = birth_place_node.xpath("./tei:placeName/text()", namespaces=nsmap)[0]
                g.add((birth_place_uri, RDFS.label, Literal(place_label, lang="en")))
                place_appellations = URIRef(f"{birth_place_uri}/appellations/0")
                g.add((birth_place_uri, CIDOC["P1_is_identified_by"], place_appellations))
                g.add((place_appellations, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
                g.add((place_appellations, RDFS.label, Literal(place_label, lang="en")))
                g.add((place_appellations, CIDOC["P2_has_type"], URIRef(f"{SK}types/place/placename")))
                g.add((place_appellations, RDF.value, Literal(place_label)))
                for i, idno in enumerate(birth_place_node.xpath("./tei:idno", namespaces=nsmap)):
                    idno_uri = URIRef(f"{birth_place_uri}/identifier/idno/{i}")
                    g.add((birth_place_uri, CIDOC["P1_is_identified_by"], idno_uri))
                    g.add((idno_uri, RDF.type, CIDOC["E42_Identifier"]))
                    g.add((idno_uri, RDFS.label, Literal(f"Identifier: {idno.text}", lang="en")))
                    g.add((idno_uri, CIDOC["P2_has_type"], URIRef(f"{SK}types/idno/URL/{idno.attrib['type']}")))
                    g.add((idno_uri, RDF.value, Literal(idno.text, lang="en")))
                birth_place_identifier_uri = URIRef(f"{birth_place_uri}/identifier/{birth_place_id}")
                g.add((birth_place_uri, CIDOC["P1_is_identified_by"], birth_place_identifier_uri))
                g.add((birth_place_identifier_uri, RDF.type, CIDOC["E42_Identifier"]))
                g.add((birth_place_identifier_uri, RDFS.label, Literal(f"Identifier: {birth_place_id}", lang="und")))
                g.add((birth_place_identifier_uri, CIDOC["P2_has_type"], URIRef(f"{SK}types/idno/xml-id")))
                g.add((birth_place_identifier_uri, RDF.value, Literal(birth_place_id)))
    if x.xpath("./tei:death", namespaces=nsmap):
        death_g, death_uri, death_timestamp = make_birth_death_entities(
            subj,
            x,
            domain=SK,
            event_type="death",
            default_prefix="Tod von",
            verbose=False,
            date_node_xpath="/tei:date[1]",
            place_id_xpath="//tei:settlement[1]/@key",
        )
        g += death_g
    if x.xpath("./tei:death[./tei:settlement]", namespaces=nsmap):
        try:
            death_place_node = x.xpath(
                "./tei:death/tei:settlement", namespaces=nsmap
            )[0]
        except IndexError:
            death_place_node = None
        if death_place_node is not None:
            try:
                death_place_id = death_place_node.attrib["key"]
            except KeyError:
                death_place_id = None
            if death_place_id is not None:
                death_place_uri = URIRef(f"{SK}{death_place_id}")
                g.add((death_place_uri, RDF.type, CIDOC["E53_Place"]))
                place_label = death_place_node.xpath("./tei:placeName/text()", namespaces=nsmap)[0]
                g.add((death_place_uri, RDFS.label, Literal(place_label, lang="en")))
                place_appellations = URIRef(f"{death_place_uri}/appellations/0")
                g.add((death_place_uri, CIDOC["P1_is_identified_by"], place_appellations))
                g.add((place_appellations, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
                g.add((place_appellations, RDFS.label, Literal(place_label, lang="en")))
                g.add((place_appellations, CIDOC["P2_has_type"], URIRef(f"{SK}types/place/placename")))
                g.add((place_appellations, RDF.value, Literal(place_label)))
                for i, idno in enumerate(death_place_node.xpath("./tei:idno", namespaces=nsmap)):
                    idno_uri = URIRef(f"{death_place_uri}/identifier/idno/{i}")
                    g.add((death_place_uri, CIDOC["P1_is_identified_by"], idno_uri))
                    g.add((idno_uri, RDF.type, CIDOC["E42_Identifier"]))
                    g.add((idno_uri, RDFS.label, Literal(f"Identifier: {idno.text}", lang="en")))
                    g.add((idno_uri, CIDOC["P2_has_type"], URIRef(f"{SK}types/idno/URL/{idno.attrib['type']}")))
                    g.add((idno_uri, RDF.value, Literal(idno.text, lang="en")))
                death_place_identifier_uri = URIRef(f"{death_place_uri}/identifier/{death_place_id}")
                g.add((death_place_uri,
                       CIDOC["P1_is_identified_by"],
                       death_place_identifier_uri))
                g.add((death_place_uri, CIDOC["P1_is_identified_by"], death_place_identifier_uri))
                g.add((death_place_identifier_uri, RDF.type, CIDOC["E42_Identifier"]))
                g.add((death_place_identifier_uri, RDFS.label, Literal(f"Identifier: {death_place_id}", lang="und")))
                g.add((death_place_identifier_uri, CIDOC["P2_has_type"], URIRef(f"{SK}types/idno/xml-id")))
                g.add((death_place_identifier_uri, RDF.value, Literal(death_place_id)))

# ORGS
entity_type = "org"
index_file = f"./data/indices/list{entity_type}.xml"
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
    g += make_appellations(subj, x, type_domain=f"{SK}types/", default_lang="und")
    g += make_e42_identifiers(
        subj, x, type_domain=f"{SK}types", default_lang="und", same_as=False
    )

# # PLACES
# entity_type = "place"
# index_file = f"./data/indices/list{entity_type}.xml"
# doc = TeiReader(index_file)
# nsmap = doc.nsmap
# items = doc.any_xpath(f".//tei:{entity_type}")
# if LIMIT:
#     items = items[:LIMIT]
# print(f"converting {entity_type}s derived from {index_file}")
# for x in tqdm(items, total=len(items)):
#     xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
#     item_id = f"{SK}{xml_id}"
#     subj = URIRef(item_id)
#     g.add((subj, RDF.type, CIDOC["E53_Place"]))
#     g += coordinates_to_p168(subj, x)
#     g += make_appellations(subj, x, type_domain=f"{SK}types/", default_lang="und")
#     g += make_e42_identifiers(
#         subj, x, type_domain=f"{SK}types", default_lang="und", same_as=False
#     )
#     try:
#         pmb = x.xpath('.//tei:idno[@type="pmb"]/text()', namespaces=nsmap)[0]
#     except IndexError:
#         pmb = None
#     if pmb:
#         pmb_uri = URIRef(pmb)
#         g.add((subj, OWL["sameAs"], pmb_uri))
#         g.add((pmb_uri, RDF.type, CIDOC["E42_Identifier"]))

print("writing graph to file: data.trig")
g.serialize(f"{rdf_dir}/data.trig", format="trig")
