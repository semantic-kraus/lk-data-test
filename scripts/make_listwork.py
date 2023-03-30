import os
from tqdm import tqdm
from acdh_cidoc_pyutils import normalize_string, extract_begin_end, create_e52

from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO
from acdh_tei_pyutils.tei import TeiReader
from rdflib import Graph, Namespace, URIRef, Literal, plugin, ConjunctiveGraph
from rdflib.namespace import RDF, RDFS, DCTERMS, VOID

# from rdflib.void import generateVoID
from rdflib.store import Store

LK = Namespace("https://sk.acdh.oeaw.ac.at/project/legal-kraus")

store = plugin.get("Memory", Store)()
project_store = plugin.get("Memory", Store)()

if os.environ.get("NO_LIMIT"):
    LIMIT = False
else:
    LIMIT = False

rdf_dir = "./rdf"
os.makedirs(rdf_dir, exist_ok=True)
domain = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(domain)

project_uri = URIRef(f"{SK}project/legal-kraus")
g_prov = Graph(store=project_store, identifier=URIRef(f"{SK}provenance"))
g_prov.bind("dct", DCTERMS)
g_prov.bind("void", VOID)
g_prov.bind("sk", SK)
g_prov.bind("lk", LK)
g_prov.bind("cidoc", CIDOC)
g_prov.bind("frbroo", FRBROO)
g_prov.parse("./data/about.ttl")


g = Graph(identifier=project_uri, store=project_store)
g.bind("cidoc", CIDOC)
g.bind("frbroo", FRBROO)
g.bind("sk", SK)
g.bind("lk", LK)
entity_type = "work"
index_file = f"./data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap
items = doc.any_xpath(".//tei:listBibl/tei:bibl[./tei:bibl[@subtype]]")
if LIMIT:
    items = items[:LIMIT]
print(f"converting {entity_type}s derived from {index_file}")

main_title_type_uri = URIRef(f"{SK}types/appellation/title/main")
sub_title_type_uri = URIRef(f"{SK}types/appellation/title/sub")
num_volume_type_uri = URIRef(f"{SK}types/appellation/num/volume")
num_issue_type_uri = URIRef(f"{SK}types/appellation/num/issue")


g.add((main_title_type_uri, RDF.type, CIDOC["E55_Type"]))
g.add((sub_title_type_uri, RDF.type, CIDOC["E55_Type"]))
for x in tqdm(items, total=len(items)):
    try:
        xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    except Exception as e:
        print(x, e)
        continue
    item_sk_type = x.xpath("./tei:bibl/@subtype", namespaces=nsmap)[0]
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
        elif level_type == "j":
            label_value = title.text
            break
        else:
            label_value = xml_id
    label_value = normalize_string(label_value)
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

    if item_sk_type == "standalone_text":
        g.add((subj, RDFS.label, Literal(f"Expression: {label_value}")))
    if item_sk_type == "article":
        g.add((subj, RDFS.label, Literal(f"Text: {label_value}", lang="en")))
    if item_sk_type == "standalone_publication":
        g.add((subj, RDFS.label, Literal(f"Expression: {label_value}")))
        pub_expr_uri = URIRef(f"{subj}/published-expression")
        g.add((pub_expr_uri, RDF.type, FRBROO["F24_Publication_Expression"]))
        if pub_expr_uri != subj:
            g.add(
                (
                    pub_expr_uri,
                    RDFS.label,
                    Literal(
                        normalize_string(f"Published Expression: {label_value}"),
                        lang="en",
                    ),
                )
            )
            g.add((pub_expr_uri, CIDOC["P165_incorporates"], subj))
            pub_expr_appellation_uri = URIRef(f"{subj}/appellation/0")
            g.add(
                (
                    pub_expr_appellation_uri,
                    RDF.type,
                    CIDOC["E33_E41_Linguistic_Appellation"],
                )
            )
            g.add(
                (
                    pub_expr_appellation_uri,
                    RDFS.label,
                    Literal(
                        normalize_string(f"Appellation for: {label_value}"), lang="en"
                    ),
                )
            )
            g.add(
                (pub_expr_uri, CIDOC["P1_is_identified_by"], pub_expr_appellation_uri)
            )
            g.add((pub_expr_appellation_uri, CIDOC["P1i_identifies"], pub_expr_uri))
            for i, num in enumerate(x.xpath("./tei:bibl/tei:num", namespaces=nsmap)):
                num_type = num.attrib["type"]
                if num_type == "volume":
                    appellation_type = num_volume_type_uri
                else:
                    appellation_type = num_issue_type_uri
                cur_num_text = normalize_string(num.text)
                pub_expr_appellation_e90 = URIRef(f"{subj}/appellation-num/{i}")
                g.add(
                    (pub_expr_appellation_e90, RDF.type, CIDOC["E90_Symbolic_Object"])
                )
                g.add(
                    (
                        pub_expr_appellation_uri,
                        CIDOC["P106_is_composed_of"],
                        pub_expr_appellation_e90,
                    )
                )
                g.add(
                    (
                        pub_expr_appellation_e90,
                        CIDOC["P106i_forms_part_of"],
                        pub_expr_appellation_uri,
                    )
                )
                g.add(
                    (
                        pub_expr_appellation_e90,
                        RDFS.label,
                        Literal(f"Appellation Part: {cur_num_text}", lang="en"),
                    )
                )
                g.add(
                    (pub_expr_appellation_e90, CIDOC["P2_has_type"], appellation_type)
                )
            for i, title in enumerate(
                x.xpath('./tei:bibl/tei:title[@level="m"]', namespaces=nsmap)
            ):
                try:
                    title.attrib["type"]
                    appellation_type = sub_title_type_uri
                except KeyError:
                    appellation_type = main_title_type_uri
                cur_title_text = normalize_string(title.text)
                pub_expr_appellation_e90 = URIRef(f"{subj}/appellation-title/{i}")
                g.add(
                    (pub_expr_appellation_e90, RDF.type, CIDOC["E90_Symbolic_Object"])
                )
                g.add(
                    (
                        pub_expr_appellation_uri,
                        CIDOC["P106_is_composed_of"],
                        pub_expr_appellation_e90,
                    )
                )
                g.add(
                    (
                        pub_expr_appellation_e90,
                        CIDOC["P106i_forms_part_of"],
                        pub_expr_appellation_uri,
                    )
                )
                g.add(
                    (
                        pub_expr_appellation_e90,
                        RDFS.label,
                        Literal(f"Appellation Part: {cur_title_text}", lang="en"),
                    )
                )
                g.add(
                    (
                        pub_expr_appellation_e90,
                        RDF.value,
                        Literal(f"{cur_title_text}", lang="en"),
                    )
                )
                g.add(
                    (pub_expr_appellation_e90, CIDOC["P2_has_type"], appellation_type)
                )

    if item_sk_type in ["journal", "issue", "article"]:
        try:
            title_j = x.xpath(
                "./tei:bibl[@type='sk']/tei:title[@level='j' and @key]",
                namespaces=nsmap,
            )[0]
            good_to_go = True
        except IndexError:
            print(f"missing @key in: {xml_id}")
            good_to_go = False
        if good_to_go:
            bibl_sk = x.xpath('./tei:bibl[@type="sk"]', namespaces=nsmap)[0]
            title_j_key = title_j.attrib["key"][1:]
            title_j_text = normalize_string(title_j.text)
            periodical_uri = URIRef(f"{SK}{title_j_key}/published-expression")
            g.add((periodical_uri, RDF.type, FRBROO["F24_Publication_Expression"]))
            g.add(
                (
                    periodical_uri,
                    RDFS.label,
                    Literal(f"Periodical: {title_j_text}", lang="en"),
                )
            )
            try:
                title_date = x.xpath(
                    "./tei:bibl[@type='sk']/tei:date", namespaces=nsmap
                )[0]
            except IndexError:
                continue
            try:
                title_date_key = title_date.attrib["key"]
            except KeyError:
                print(xml_id)
                continue
            title_date_key = title_date_key[1:]
            issue_uri = URIRef(f"{SK}{title_date_key}")
            g.add((issue_uri, RDF.type, FRBROO["F22_Self-Contained_Expression"]))
            g.add(
                (
                    issue_uri,
                    RDFS.label,
                    Literal(f"Expression: {title_j_text}", lang="en"),
                )
            )
            issue_uri_f24 = URIRef(f"{issue_uri}/published-expression")
            g.add((issue_uri_f24, RDF.type, FRBROO["F24_Publication_Expression"]))
            g.add(
                (
                    issue_uri_f24,
                    RDFS.label,
                    Literal(f"Issue: {title_j_text}", lang="en"),
                )
            )
            g.add((issue_uri_f24, CIDOC["P165_incorporates"], issue_uri))
            issue_uri_appellation = URIRef(f"{issue_uri}/appellation/0")
            g.add(
                (
                    issue_uri_appellation,
                    RDF.type,
                    CIDOC["E33_E41_Linguistic_Appellation"],
                )
            )
            g.add(
                (
                    issue_uri_appellation,
                    RDFS.label,
                    Literal(f"Appellation for: {title_j_text}", lang="en"),
                )
            )
            g.add((issue_uri_appellation, CIDOC["P1i_identifies"], issue_uri_f24))
            g.add((issue_uri_f24, CIDOC["P1_is_identified_by"], issue_uri_appellation))
            if issue_uri_f24 != subj:
                for i, title in enumerate(
                    bibl_sk.xpath('.//tei:title[not(@level="a")]', namespaces=nsmap)
                ):
                    cur_title_text = normalize_string(title.text)
                    pub_expr_appellation_e90 = URIRef(
                        f"{issue_uri}/appellation-title/{i}"
                    )
                    g.add(
                        (
                            pub_expr_appellation_e90,
                            RDF.type,
                            CIDOC["E90_Symbolic_Object"],
                        )
                    )
                    g.add(
                        (
                            issue_uri_appellation,
                            CIDOC["P106_is_composed_of"],
                            pub_expr_appellation_e90,
                        )
                    )
                    g.add(
                        (
                            pub_expr_appellation_e90,
                            CIDOC["P106i_forms_part_of"],
                            issue_uri_appellation,
                        )
                    )
                    g.add(
                        (
                            pub_expr_appellation_e90,
                            RDFS.label,
                            Literal(f"Appellation Part: {cur_title_text}", lang="en"),
                        )
                    )
                    g.add(
                        (
                            pub_expr_appellation_e90,
                            RDF.value,
                            Literal(f"{cur_title_text}", lang="en"),
                        )
                    )
            if issue_uri != subj:
                g.add((issue_uri, CIDOC["P165_incorporates"], subj))
                g.add((periodical_uri, FRBROO["R5_has_component"], issue_uri_f24))
            issue_uri_pub_event_uri = URIRef(f"{issue_uri}/publication")
            g.add((issue_uri_pub_event_uri, RDF.type, FRBROO["F30_Publication_Event"]))
            g.add(
                (
                    issue_uri_pub_event_uri,
                    RDFS.label,
                    Literal(f"Publication: {title_j_text}"),
                )
            )
            g.add((issue_uri_pub_event_uri, FRBROO["R24_created"], issue_uri_f24))
            start, end = extract_begin_end(title_date)
            ts_uri = URIRef(f"{issue_uri_pub_event_uri}/time-span")
            g += create_e52(ts_uri, begin_of_begin=start, end_of_end=end)
            g.add((issue_uri_pub_event_uri, CIDOC["P4_has_time-span"], ts_uri))

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
    if item_sk_type not in ["journal", "issue", "article"]:
        try:
            pub_date = x.xpath(
                './tei:bibl[@type="sk"]/tei:date[@when or @notBefore]', namespaces=nsmap
            )[0]
            from_sk = True
        except IndexError:
            from_sk = False
            try:
                pub_date = x.xpath("./tei:date", namespaces=nsmap)[0]
            except IndexError:
                pub_date = None
        if pub_date is not None:
            pub_event_uri = URIRef(f"{subj}/publication")
            g.add((pub_event_uri, RDF.type, FRBROO["F30_Publication_Event"]))
            g.add(
                (pub_event_uri, RDFS.label, Literal(f"Publication of: {label_value}"))
            )
            if item_sk_type == "standalone_publication":
                g.add(
                    (
                        pub_event_uri,
                        FRBROO["R24_created"],
                        URIRef(f"{subj}/published-expression"),
                    )
                )
                if URIRef(f"{subj}/published-expression") != subj:
                    g.add(
                        (
                            URIRef(f"{subj}/published-expression"),
                            CIDOC["P165_incorporates"],
                            subj,
                        )
                    )
            else:
                g.add((pub_event_uri, FRBROO["R24_created"], subj))
            time_span_uri = URIRef(f"{pub_event_uri}/time-span")
            g.add((pub_event_uri, CIDOC["P4_has_time-span"], time_span_uri))
            if from_sk:
                begin, end = extract_begin_end(pub_date)
            else:
                if " – " in pub_date.text:
                    begin, end = pub_date.text.split(" – ")
                else:
                    begin = pub_date.text
                    end = begin
            g += create_e52(time_span_uri, begin_of_begin=begin, end_of_end=end)
            g.add((pub_event_uri, CIDOC["P4_has_time-span"], time_span_uri))
print("writing graph to file")
# g_prov, g = generateVoID(g, dataset=project_uri, res=g_prov)
g_all = ConjunctiveGraph(store=project_store)
g_all.serialize(f"{rdf_dir}/{entity_type}.trig", format="trig")
