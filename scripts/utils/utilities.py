from lxml.etree import Element
from rdflib import Graph, Literal, URIRef, RDF, RDFS, OWL
from rdflib.namespace import Namespace
from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO, NSMAP
from acdh_cidoc_pyutils import (
    normalize_string,
    create_e52,
    extract_begin_end
)
from acdh_tei_pyutils.utils import make_entity_label


def make_occupations_type_req(
    subj: URIRef,
    node: Element,
    prefix="occupation",
    id_xpath=False,
    default_lang="en",
    not_known_value="undefined",
    special_label=None,
    type_required=False,
):
    g = Graph()
    occ_uris = []
    base_uri = f"{subj}/{prefix}"
    occupations = node.xpath(".//tei:occupation", namespaces=NSMAP)
    for i, x in enumerate(occupations):
        try:
            lang = x.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        except KeyError:
            lang = default_lang
        occ_text = normalize_string(" ".join(x.xpath(".//text()")))
        if id_xpath:
            try:
                occ_id = x.xpath(id_xpath, namespaces=NSMAP)[0]
            except IndexError:
                pass
        else:
            occ_id = f"{i}"
        if occ_id.startswith("#"):
            occ_id = occ_id[1:]
        occ_uri = URIRef(f"{base_uri}/{occ_id}")
        occ_uris.append(occ_uri)
        g.add((occ_uri, RDF.type, FRBROO["F51_Pursuit"]))
        if special_label:
            try:
                occ_type = x.attrib["type"]
            except KeyError:
                occ_type = None
            if type_required and occ_type == type_required:
                g.add((occ_uri, RDFS.label, Literal(f"{special_label}{occ_text}", lang=lang)))
            else:
                g.add((occ_uri, RDFS.label, Literal(occ_text, lang=lang)))
        else:
            g.add((occ_uri, RDFS.label, Literal(occ_text, lang=lang)))
        g.add((subj, CIDOC["P14i_performed"], occ_uri))
        begin, end = extract_begin_end(x, fill_missing=False)
        if begin or end:
            ts_uri = URIRef(f"{occ_uri}/time-span")
            g.add((occ_uri, CIDOC["P4_has_time-span"], ts_uri))
            g += create_e52(
                ts_uri,
                begin_of_begin=begin,
                end_of_end=end,
                not_known_value=not_known_value,
            )
    return g


def make_e42_identifiers_utils(
    subj: URIRef,
    node: Element,
    type_domain="https://foo-bar/",
    default_lang="en",
    set_lang=False,
    same_as=True,
    default_prefix="Identifier: ",
) -> Graph:
    g = Graph()
    try:
        lang = node.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
    except KeyError:
        lang = default_lang
    xml_id = node.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    label_value = normalize_string(f"{default_prefix}{xml_id}")
    if not type_domain.endswith("/"):
        type_domain = f"{type_domain}/"
    app_uri = URIRef(f"{subj}/identifier/{xml_id}")
    type_uri = URIRef(f"{type_domain}idno/xml-id")
    approx_uri = URIRef(f"{type_domain}date/approx")
    g.add((approx_uri, RDF.type, CIDOC["E55_Type"]))
    g.add((approx_uri, RDFS.label, Literal("approx")))
    g.add((type_uri, RDF.type, CIDOC["E55_Type"]))
    g.add((subj, CIDOC["P1_is_identified_by"], app_uri))
    g.add((app_uri, RDF.type, CIDOC["E42_Identifier"]))
    g.add((app_uri, RDFS.label, Literal(label_value, lang=lang)))
    g.add((app_uri, RDF.value, Literal(normalize_string(xml_id))))
    g.add((app_uri, CIDOC["P2_has_type"], type_uri))
    events_types = {}
    for i, x in enumerate(node.xpath(".//tei:event[@type]", namespaces=NSMAP)):
        events_types[x.attrib["type"]] = x.attrib["type"]
    if events_types:
        for i, x in enumerate(events_types.keys()):
            event_type_uri = URIRef(f"{type_domain}event/{x}")
            g.add((event_type_uri, RDF.type, CIDOC["E55_Type"]))
            g.add((event_type_uri, RDFS.label, Literal(x, lang=default_lang)))
    for i, x in enumerate(node.xpath("./tei:idno", namespaces=NSMAP)):
        idno_type_base_uri = f"{type_domain}idno"
        if x.text:
            idno_uri = URIRef(f"{subj}/identifier/idno/{i}")
            g.add((subj, CIDOC["P1_is_identified_by"], idno_uri))
            idno_type = x.get("type")
            if idno_type:
                idno_type_base_uri = f"{idno_type_base_uri}/{idno_type}"
            idno_type = x.get("subtype")
            if idno_type:
                idno_type_base_uri = f"{idno_type_base_uri}/{idno_type}"
            g.add((idno_uri, RDF.type, CIDOC["E42_Identifier"]))
            g.add((idno_uri, CIDOC["P2_has_type"], URIRef(idno_type_base_uri)))
            g.add((URIRef(idno_type_base_uri), RDF.type, CIDOC["E55_Type"]))
            label_value = normalize_string(f"{default_prefix}{x.text}")
            g.add((idno_uri, RDFS.label, Literal(label_value, lang=lang)))
            g.add((idno_uri, RDF.value, Literal(normalize_string(x.text))))
            if same_as:
                if x.text.startswith("http"):
                    g.add(
                        (
                            subj,
                            OWL.sameAs,
                            URIRef(
                                x.text,
                            ),
                        )
                    )
    return g


def create_triple_from_node(
    node: Element,
    subj: URIRef,
    subj_suffix: str | bool = False,
    pred: Namespace = CIDOC["P2_has_type"],
    sbj_class: Namespace | bool = False,
    obj_class: Namespace | bool = False,
    obj_node_xpath: str | bool = False,
    obj_node_value_xpath: str | bool = False,
    obj_node_value_alt_xpath_or_str: str | bool = False,
    obj_prefix: Namespace = Namespace("https://foo-bar/"),
    obj_process_condition: str | bool = False,
    skip_value: str | bool = False,
    default_lang: str | bool = False,
    value_literal: bool = False,
    label_prefix: str = "",
    node_attribute: str | bool = False,
    identifier: Namespace | bool = False,
    date: bool = False,
) -> Graph:
    g = Graph()
    predicate = pred
    node_name = node.tag.split("}")[-1]
    if subj_suffix:
        subject = URIRef(f"{subj}/{subj_suffix}")
    else:
        subject = subj
    if node_attribute:
        try:
            node_attrib_value = node.attrib[node_attribute]
        except KeyError:
            node_attrib_value = None
        if node_attrib_value is not None:
            subject = URIRef(f"{subject}/{node_attrib_value}")
    if obj_node_xpath:
        obj_node = node.xpath(obj_node_xpath, namespaces=NSMAP)
        if isinstance(obj_node, list):
            for i, obj in enumerate(obj_node):
                subject_uri = URIRef(f"{subject}/{i}")
                if identifier:
                    g.add((subj, identifier, subject_uri))
                if sbj_class:
                    g.add((subject_uri, RDF.type, sbj_class))
                obj_name = obj.tag.split("}")[-1]
                if label_prefix:
                    try:
                        xpath = obj_process_condition.split("'")[0].replace("=", "")
                        xpath_condition = obj_process_condition.split("'")[1]
                        obj_type = obj.xpath(xpath, namespaces=NSMAP)[0]
                        if obj_type == xpath_condition:
                            l_prefix = label_prefix
                        else:
                            l_prefix = ""
                    except IndexError:
                        l_prefix = ""
                else:
                    l_prefix = ""
                if default_lang:
                    try:
                        lang = node.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
                    except KeyError:
                        lang = default_lang
                    if len(obj.xpath("./*")) < 1 and obj.text:
                        object_literal = Literal(f"{l_prefix}{normalize_string(obj.text)}", lang=lang)
                        g.add((subject_uri, RDFS.label, object_literal))
                    elif len(obj.xpath("./*")) > 1:
                        entity_label_str, cur_lang = make_entity_label(obj, default_lang=lang)
                        object_literal = Literal(f"{l_prefix}{normalize_string(entity_label_str)}", lang=lang)
                        g.add((subject_uri, RDFS.label, object_literal))
                if value_literal:
                    if len(obj.xpath("./*")) < 1 and obj.text:
                        object_literal = Literal(f"{l_prefix}{normalize_string(obj.text)}")
                        g.add((subject_uri, RDF.value, object_literal))
                    elif len(obj.xpath("./*")) > 1:
                        entity_label_str, cur_lang = make_entity_label(obj, default_lang=lang)
                        object_literal = Literal(f"{l_prefix}{normalize_string(entity_label_str)}")
                        g.add((subject_uri, RDF.value, object_literal))
                if obj_node_value_xpath:
                    try:
                        obj_node_value = obj.xpath(obj_node_value_xpath, namespaces=NSMAP)[0]
                    except IndexError:
                        try:
                            obj_node_value = obj.xpath(obj_node_value_alt_xpath_or_str, namespaces=NSMAP)[0]
                        except IndexError:
                            if obj_node_value_alt_xpath_or_str == "iterator":
                                obj_node_value = i
                            else:
                                obj_node_value = obj_node_value_alt_xpath_or_str
                    if obj_node_value == skip_value:
                        continue
                    object_uri = URIRef(f"{obj_prefix}/{node_name}/{obj_name}/{obj_node_value}")
                    g.add((subject_uri, predicate, object_uri))
                    if obj_class:
                        g.add((object_uri, RDF.type, obj_class))
                if date:
                    not_known_value = "undefined"
                    begin, end = extract_begin_end(obj, fill_missing=False)
                    if begin or end:
                        ts_uri = URIRef(f"{object_uri}/time-span")
                        g.add((object_uri, CIDOC["P4_has_time-span"], ts_uri))
                        g += create_e52(
                            ts_uri,
                            begin_of_begin=begin,
                            end_of_end=end,
                            not_known_value=not_known_value,
                        )
    else:
        subject_uri = subject
        object_uri = obj_class
        g.add((subject_uri, predicate, object_uri))
    return g
