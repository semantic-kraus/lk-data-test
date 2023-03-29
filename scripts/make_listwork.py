import os
from tqdm import tqdm
from acdh_cidoc_pyutils import normalize_string, extract_begin_end, create_e52

from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO
from acdh_tei_pyutils.tei import TeiReader
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS

if os.environ.get("NO_LIMIT"):
    LIMIT = False
else:
    LIMIT = False

rdf_dir = "./rdf"
os.makedirs(rdf_dir, exist_ok=True)
domain = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(domain)
g = Graph()
entity_type = "work"
index_file = f"./data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap
items = doc.any_xpath(".//tei:listBibl/tei:bibl[./tei:bibl[@subtype]]")
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
    item_sk_type = x.xpath("./tei:bibl/@subtype", namespaces=nsmap)[0]
    if (
        item_sk_type == "standalone_publication"
        or item_sk_type == "article"
        or item_sk_type == "standalone_text"
    ):
        item_id = f"{SK}{xml_id}"
        subj = URIRef(item_id)
        g.add((subj, RDF.type, FRBROO["F22_Self-Contained_Expression"]))
    elif item_sk_type == "journal":
        item_id = f"{SK}{xml_id}/published-expression"
        subj = URIRef(item_id)
        g.add((subj, RDF.type, FRBROO["F24_Publication_Expression"]))
    else:
        item_id = f"{SK}{xml_id}"
        subj = URIRef(item_id)
        g.add((subj, RDF.type, FRBROO["F22_Self-Contained_Expression"]))
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

    # g.add(
    #     (
    #         subj,
    #         RDFS.label,
    #         Literal(f"Expression: {label_value}", lang="en"),
    #     )
    # )
    # add more classes
    if item_sk_type == "standalone_publication":
        pub_expr_uri = URIRef(f"{subj}/published-expression")
        g.add((pub_expr_uri, RDF.type, FRBROO["F24_Publication_Expression"]))
        g.add(
            (
                pub_expr_uri,
                RDFS.label,
                Literal(
                    normalize_string(f"Published Expression: {label_value}"), lang="en"
                ),
            )
        )
        g.add((pub_expr_uri, CIDOC["P165_incorporates"], subj))

    if item_sk_type in ["journal", "issue", "article"]:
        try:
            title_j = x.xpath("./tei:bibl[@type='sk']/tei:title[@level='j' and @key]", namespaces=nsmap)[0]
            good_to_go = True
        except IndexError:
            print(f"missing @key in: {xml_id}")
            good_to_go = False
        if good_to_go:
            title_j_key = title_j.attrib["key"][1:]
            title_j_text = normalize_string(title_j.text)
            periodical_uri = URIRef(f"{SK}{title_j_key}/published-expression")
            g.add((
                periodical_uri, RDF.type, FRBROO["F24_Publication_Expression"]
            ))
            g.add((
                periodical_uri, RDFS.label, Literal(f"Periodical: {title_j_text}", lang="en")
            ))
            try:
                title_date = x.xpath("./tei:bibl[@type='sk']/tei:date", namespaces=nsmap)[0]
            except IndexError:
                continue
            try:
                title_date_key = title_date.attrib["key"]
            except KeyError:
                print(xml_id)
                continue
            title_date_key = title_date_key[1:]
            issue_uri = URIRef(f"{SK}{title_date_key}")
            g.add((
                issue_uri, RDF.type, FRBROO["F22_Self-Contained_Expression"]
            ))
            g.add((
                issue_uri, RDFS.label, Literal(f"Expression: {label_value}", lang="en")
            ))
            issue_uri_f24 = URIRef(f"{issue_uri}/published-expression")
            g.add((
                issue_uri_f24, RDF.type, FRBROO["F24_Publication_Expression"]
            ))
            g.add((
                issue_uri_f24, RDFS.label, Literal(f"Issue: {label_value}", lang="en")
            ))
            g.add((
                issue_uri_f24, CIDOC["P165_incorporates"], issue_uri
            ))
            g.add((
                periodical_uri, FRBROO["R5_has_component"], issue_uri_f24
            ))
            issue_uri_pub_event_uri = URIRef(f"{issue_uri}/publication")
            g.add((
                issue_uri_pub_event_uri, RDF.type, FRBROO["F30_Publication_Event"]
            ))
            g.add((
                issue_uri_pub_event_uri, RDFS.label, Literal(f"Publication: {label_value}")
            ))
            g.add((
                issue_uri_pub_event_uri, FRBROO["R24_created"], issue_uri_f24
            ))
            start, end = extract_begin_end(title_date)
            g += create_e52(issue_uri_pub_event_uri, begin_of_begin=start, end_of_end=end)

    # authors
    uebersetzt = x.xpath('./tei:author[@role="hat-ubersetzt"]', namespaces=nsmap)
    if not uebersetzt:
        uebersetzt = x.xpath(
            './tei:author[@role="hat-anonym-veroffentlicht" or @role="hat-geschaffen"]',
            namespaces=nsmap,
        )
    if uebersetzt:
        creation = URIRef(f"{subj}/creation")
        g.add((creation, RDF.type, FRBROO["F28_Expression_Creation"]))
        g.add(
            (
                creation,
                RDFS.label,
                Literal(normalize_string(f"Creation of: {label_value}"), lang="en"),
            )
        )
        g.add((creation, FRBROO["R17_created"], subj))
        for a in uebersetzt:
            author_id = a.attrib["key"]
            author_uri = URIRef(f"{SK}{author_id}")
            g.add((creation, CIDOC["P14_carried_out_by"], author_uri))

    try:
        pub_date = x.xpath('./tei:bibl[@type="sk"]/tei:date/@when', namespaces=nsmap)[0]
    except IndexError:
        try:
            pub_date = x.xpath("./tei:date/text()", namespaces=nsmap)[0]
        except IndexError:
            pub_date = False
    if pub_date:
        pub_event_uri = URIRef(f"{subj}/publication")
        g.add((pub_event_uri, RDF.type, FRBROO["F30_Publication_Event"]))
        g.add((pub_event_uri, RDFS.label, Literal(f"Publication of: {label_value}")))
        if item_sk_type == "standalone_publication":
            g.add(
                (
                    pub_event_uri,
                    FRBROO["R24_created"],
                    URIRef(f"{subj}/published-expression"),
                )
            )
        else:
            g.add((pub_event_uri, FRBROO["R24_created"], subj))
        time_span_uri = URIRef(f"{pub_event_uri}/time-span")
        g.add((pub_event_uri, CIDOC["P4_has_time-span"], time_span_uri))
        g += create_e52(time_span_uri, begin_of_begin=pub_date, end_of_end=pub_date)

    # # creation
    # expre_creation_uri = URIRef(f"{subj}/creation")
    # g.add((expre_creation_uri, RDF.type, CIDOC["F28_Expression_Creation"]))
    # g.add((expre_creation_uri, RDFS.label, Literal(f"Creation of: {label_value}")))
    # g.add((expre_creation_uri, FRBROO["R17_created"], subj))
    # for author in x.xpath(".//tei:author/@key", namespaces=nsmap):
    #     author_uri = URIRef(f"{SK}{author}")
    #     g.add((expre_creation_uri, CIDOC["P14_carried_out_by"], author_uri))
    #     g.add((author_uri, CIDOC["P14i_performed"], expre_creation_uri))
    # # title
    # title_uri = URIRef(f"{subj}/title/0")
    # g.add((title_uri, RDF.type, CIDOC["E35_Title"]))
    # g.add((title_uri, RDF.value, Literal(f"{label_value}", lang="und")))
    # g.add((title_uri, CIDOC["P2_has_type"], main_title_type_uri))
    # g.add((subj, CIDOC["P102_has_title"], title_uri))

    # # F24 Publication Expression
    # if len(x.xpath(".//tei:date", namespaces=nsmap)) > 0:
    #     publ_expr_uri = URIRef(f"{subj}/publication")

    # # subtitle
    # for i, sub in enumerate(
    #     x.xpath('.//tei:title[@type="subtitle"]', namespaces=nsmap), start=1
    # ):
    #     label_value = sub.text
    #     title_uri = URIRef(f"{subj}/title/{i}")
    #     g.add((title_uri, RDF.type, CIDOC["E35_Title"]))
    #     g.add(
    #         (
    #             title_uri,
    #             RDF.value,
    #             Literal(normalize_string(f"{label_value}"), lang="und"),
    #         )
    #     )
    #     g.add((title_uri, CIDOC["P2_has_type"], sub_title_type_uri))
    #     g.add((subj, CIDOC["P102_has_title"], title_uri))

    # # identifiers
    # g += make_e42_identifiers(
    #     subj, x, type_domain=f"{SK}types", default_lang="und", same_as=False
    # )

print("writing graph to file")
g.serialize(f"{rdf_dir}/{entity_type}s.ttl")
