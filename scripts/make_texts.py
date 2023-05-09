import os
import glob
from tqdm import tqdm
from acdh_cidoc_pyutils import extract_begin_end, create_e52, normalize_string
from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO, NSMAP, SCHEMA, INT
from acdh_tei_pyutils.tei import TeiReader
from rdflib import Graph, Namespace, URIRef, Literal, XSD
from rdflib.namespace import RDF, RDFS


if os.environ.get("NO_LIMIT"):
    LIMIT = False
    print("no limit")
else:
    LIMIT = 500
domain = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(domain)


def create_mention_text_passage(subj, i, mention_wording, item_label):
    text_passage = URIRef(f"{subj}/passage/{i}")
    text_passage_label = Literal(f"Text passage from: {item_label}", lang="en")
    g.add((text_passage, RDF.type, INT["INT1_TextPassage"]))
    g.add((text_passage, RDFS.label, text_passage_label))
    g.add((text_passage, INT["R44_has_wording"], mention_wording))
    g.add((subj, INT["R10_has_Text_Passage"], text_passage))
    return text_passage


def create_mention_text_segment(
    subj, i, item_label, text_passage, mention_wording, arche_id_value
):
    text_segment = URIRef(f"{subj}/segment/{i}")
    text_segment_label = Literal(f"Text segment from: {item_label}", lang="en")
    g.add((text_segment, RDF.type, INT["INT16_Segment"]))
    g.add((text_segment, RDFS.label, text_segment_label))
    g.add((text_segment, INT["R16_incorporates"], text_passage))
    g.add((text_segment, INT["R44_has_wording"], mention_wording))
    try:
        pb_start = mention.xpath(".//preceding::tei:pb/@n", namespaces=NSMAP)[-1]
    except IndexError:
        pb_start = 1
    g.add((text_segment, INT["R41_has_location"], Literal(f"S. {pb_start}")))
    g.add((text_segment, INT["R41_has_location"], Literal(arche_id_value)))
    g.add((text_segment, SCHEMA["pagination"], Literal(f"S. {pb_start}")))
    return text_segment


def create_mention_intertex_relation(subj, i, text_passage, work_uri):
    intertext_relation = URIRef(f"{subj}/relation/{i}")
    g.add((intertext_relation, RDF.type, INT["INT3_IntertextualRelationship"]))
    g.add(
        (
            intertext_relation,
            RDFS.label,
            Literal("Intertextual relation", lang="en"),
        )
    )
    g.add((intertext_relation, INT["R13_has_referring_entity"], text_passage))
    g.add((intertext_relation, INT["R12_has_referred_to_entity"], work_uri))


# build uri lookup dict for listwork.xml

listwork = "./data/indices/listwork.xml"
doc = TeiReader(listwork)
items = doc.any_xpath(".//tei:listBibl/tei:bibl[./tei:bibl[@subtype]]")
nsmap = doc.nsmap
bibl_class_lookup_dict = {}
for x in tqdm(items, total=len(items)):
    try:
        xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    except Exception as e:
        print(x, e)
        continue
    item_sk_type = x.xpath("./tei:bibl/@subtype", namespaces=nsmap)[0]
    if item_sk_type == "journal":
        bibl_class_lookup_dict[xml_id] = f"{SK}{xml_id}/published-expression"
    else:
        bibl_class_lookup_dict[xml_id] = f"{SK}{xml_id}"


rdf_dir = "./rdf"
os.makedirs(rdf_dir, exist_ok=True)

title_type = URIRef(f"{SK}types/title/prov")
arche_text_type_uri = URIRef("https://sk.acdh.oeaw.ac.at/types/idno/URL/ARCHE")
g = Graph()
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
        # maybe process these too?
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
    subj_f4 = URIRef(f"{item_id}/carrier")
    item_label = normalize_string(doc.any_xpath(".//tei:title[1]/text()")[0])
    g.add((subj, RDF.type, CIDOC["E73_Information_Object"]))
    # DOC-ARCHE-IDs
    arche_id = URIRef(f"{SK}{xml_id}/identifier/0")
    arche_id_value = f"https://id.acdh.oeaw.ac.at/legalkraus/{xml_id}.xml"
    g.add((subj, CIDOC["P1_is_identified_by"], arche_id))
    g.add((arche_id, RDF.type, CIDOC["E42_Identifier"]))
    g.add((arche_id, RDF.value, Literal(arche_id_value, datatype=XSD.anyURI)))
    g.add((arche_id, RDFS.label, Literal(f"ARCHE-ID: {arche_id_value}", lang="en")))
    g.add((arche_id, CIDOC["P2_has_type"], arche_text_type_uri))
    # appellations
    title_uri = URIRef(f"{subj}/title/0")
    g.add((title_uri, RDF.type, CIDOC["E35_Title"]))
    g.add((title_uri, RDF.value, Literal(item_label, lang="de")))
    g.add((title_uri, RDFS.label, Literal(item_label, lang="de")))
    g.add((subj, CIDOC["P102_has_title"], title_uri))
    g.add((title_uri, CIDOC["P2_has_type"], title_type))

    # F4_Manifestation
    g.add((subj_f4, RDF.type, FRBROO["F4_Manifestation_Singleton"]))
    g.add((subj_f4, RDFS.label, Literal(f"Carrier of: {item_label}")))
    g.add((subj_f4, CIDOC["P128_carries"], subj))
    g.add((subj, RDFS.label, Literal(item_label, lang="de")))
    creation_uri = URIRef(f"{subj}/creation")
    g.add((creation_uri, RDF.type, CIDOC["E65_Creation"]))
    g.add((creation_uri, CIDOC["P94_has_created"], URIRef(item_id)))
    g.add((creation_uri, RDFS.label, Literal(f"Creation of: {item_label}")))
    # g.add((creation_uri, FRBROO["R17"], subj))
    # g.add((subj, FRBROO["R17i"], subj))

    # creation date:
    try:
        creation_date_node = doc.any_xpath('.//tei:date[@subtype="produced"]')[0]
        go_on = True
    except IndexError:
        go_on = False
    if go_on:
        begin, end = extract_begin_end(creation_date_node)
        creation_ts = URIRef(f"{creation_uri}/time-span")
        g.add((creation_uri, CIDOC["P4_has_time-span"], creation_ts))
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

    # # fun with mentions (persons, works, quotes)
    rs_xpath = ".//tei:body//tei:rs[@ref]"
    quote_xpath = "//tei:body//tei:quote[starts-with(@source, '#')]"
    for i, mention in enumerate(doc.any_xpath(f"{rs_xpath}|{quote_xpath}")):
        mention_wording = Literal(
            normalize_string(" ".join(mention.xpath(".//text()"))), lang="und"
        )
        text_passage = create_mention_text_passage(subj, i, mention_wording, item_label)
        text_segment = create_mention_text_segment(
            subj, i, item_label, text_passage, mention_wording, arche_id_value
        )
        g.add((subj_f4, CIDOC["P128_carries"], text_segment))
        # try:
        #     pb_end = mention.xpath('.//following::tei:pb/@n', namespaces=NSMAP)[0]
        # except IndexError:
        #     pb_end = pb_start
        if mention.get("type") == "person":
            person_id = mention.attrib["ref"][1:]
            person_uri = URIRef(f"{SK}{person_id}")
            mention_string = normalize_string(" ".join(mention.xpath(".//text()")))
            text_actualization = URIRef(f"{subj}/actualization/{i}")
            g.add((text_actualization, RDF.type, INT["INT2_ActualizationOfFeature"]))
            g.add(
                (
                    text_actualization,
                    RDFS.label,
                    Literal(f"Actualization on: {item_label}", lang="en"),
                )
            )
            g.add((text_passage, INT["R18_shows_actualization"], text_actualization))

            text_reference = URIRef(f"{subj}/reference/{i}")
            g.add((text_reference, RDF.type, INT["INT18_Reference"]))
            g.add(
                (
                    text_reference,
                    RDFS.label,
                    Literal(f"Reference on: {item_label}", lang="en"),
                )
            )
            g.add((text_actualization, INT["R17_actualizes_feature"], text_reference))
            g.add((text_reference, CIDOC["P67_refers_to"], person_uri))
        elif mention.get("type") == "work":
            if mention.get("subtype") == "pmb":
                work_id = mention.attrib["ref"][1:]
                try:
                    work_uri = URIRef(bibl_class_lookup_dict[work_id])
                except KeyError:
                    print(f"pmb: no uri for ref {work_id} found")
                    continue
                create_mention_intertex_relation(subj, i, text_passage, work_uri)
            elif mention.get("subtype") == "legal-doc":
                # # follwing test is used cause the ref val is defectiv in some cases
                if not mention.attrib["ref"].startswith("pmb") and not mention.attrib[
                    "ref"
                ].startswith("#"):
                    ref_val = mention.attrib["ref"]
                    work_id = ref_val.split("/")[-1].replace(".xml", "")
                    work_uri = URIRef(f"{SK}{work_id}")
                    create_mention_intertex_relation(subj, i, text_passage, work_uri)
        elif mention.xpath("local-name()='quote'"):
            work_id = mention.get("source").lstrip("#").replace(".xml", "")
            if work_id.isnumeric():
                work_id = "pmb" + work_id
                try:
                    work_uri = URIRef(bibl_class_lookup_dict[work_id])
                except KeyError:
                    print(f"quote: no uri for ref {work_id} found")
                    continue
            elif work_id.startswith("D"):
                work_uri = URIRef(f"{SK}{work_id}")
            else:
                continue
            create_mention_intertex_relation(subj, i, text_passage, work_uri)


# cases
print("lets process cases as E5 Events")

if LIMIT:
    files = sorted(glob.glob("legalkraus-archiv/data/cases_tei/*.xml"))[:LIMIT]
else:
    files = sorted(glob.glob("legalkraus-archiv/data/cases_tei/*.xml"))

for x in tqdm(files, total=len(files)):
    doc = TeiReader(x)
    xml_id = (
        doc.tree.getroot()
        .attrib["{http://www.w3.org/XML/1998/namespace}id"]
        .replace(".xml", "")
    )
    item_id = f"{SK}{xml_id}"
    subj = URIRef(item_id)
    item_label = normalize_string(doc.any_xpath(".//tei:title[1]/text()")[0])
    item_comment = normalize_string(
        doc.any_xpath(".//tei:abstract[1]/tei:p//text()")[0]
    )

    g.add((subj, RDF.type, CIDOC["E5_Event"]))
    g.add((subj, RDFS.label, Literal(item_label, lang="de")))
    g.add((subj, RDFS.comment, Literal(item_comment, lang="de")))
    # appellations
    app_uri = URIRef(f"{subj}/appellation/0")
    g.add((app_uri, RDF.type, CIDOC["E33_E41_Linguistic_Appellation"]))
    g.add((app_uri, RDF.value, Literal(item_label, lang="de")))
    g.add((app_uri, RDFS.label, Literal(item_label, lang="de")))
    g.add((subj, CIDOC["P1_is_identified_by"], app_uri))

    # DOC-ARCHE-IDs
    arche_id = URIRef(f"{SK}identifier/{xml_id}")
    arche_id_value = f"https://id.acdh.oeaw.ac.at/legalkraus/{xml_id}.xml"
    g.add((subj, CIDOC["P1_is_identified_by"], arche_id))
    g.add((arche_id, RDF.type, CIDOC["E42_Identifier"]))
    g.add((arche_id, RDF.value, Literal(arche_id_value, datatype=XSD.anyURI)))
    g.add((arche_id, RDFS.label, Literal(f"ARCHE-ID: {arche_id_value}", lang="en")))
    g.add((arche_id, CIDOC["P2_has_type"], arche_text_type_uri))

    # linked documents
    for y in doc.any_xpath('.//tei:list[@type="objects"]//tei:ref/text()'):
        doc_xml_id = y.replace(".xml", "")
        doc_uri = URIRef(f"{SK}{doc_xml_id}")
        g.add((doc_uri, CIDOC["P12i_was_present_at"], subj))
        g.add((subj, CIDOC["P12_occurred_in_the_presence_of"], doc_uri))


print("writing graph to file")
g.serialize(f"{rdf_dir}/texts.ttl")
