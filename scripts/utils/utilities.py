from lxml.etree import Element
from lxml import etree as ET
from rdflib import Graph, Literal, URIRef, RDF, RDFS, OWL
from rdflib.namespace import Namespace
from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO, NSMAP
from acdh_cidoc_pyutils import (
    normalize_string,
    create_e52,
    extract_begin_end
)
from acdh_tei_pyutils.utils import make_entity_label


GEO = Namespace("http://www.opengis.net/ont/geosparql#")


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


def create_object_literal_graph(
    node: Element,
    subject_uri: URIRef,
    l_prefix: str,
    default_lang: str,
    predicate: Namespace,
    enforce_default_lang: bool = False,
) -> Graph:
    g = Graph()
    if enforce_default_lang:
        lang = default_lang
    else:
        try:
            lang = node.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        except KeyError:
            lang = default_lang
    if len(node.xpath("./*")) < 1 and node.text:
        if predicate == RDFS.label:
            object_literal = Literal(f"{l_prefix}{normalize_string(node.text)}",
                                     lang=lang)
        else:
            object_literal = Literal(f"{l_prefix}{normalize_string(node.text)}")
    elif len(node.xpath("./*")) >= 1:
        entity_label_str, cur_lang = make_entity_label(node, default_lang=lang)
        if predicate == RDFS.label:
            object_literal = Literal(f"{l_prefix}{normalize_string(entity_label_str)}",
                                     lang=lang)
        else:
            object_literal = Literal(f"{l_prefix}{normalize_string(entity_label_str)}")
    else:
        object_literal = Literal("undefined", lang="en")
    g.add((subject_uri, predicate, object_literal))
    return g


def create_obj_value_graph(
    node: Element,
    subject_uri: URIRef,
    parent_node_name: str | bool = False,
    xpath: str | bool = False,
    xpath_alt_or_str: str | bool = False,
    iterator: str | bool = False,
    namespaces: dict = NSMAP,
    skip_value: str | bool = False,
    prefix: str | bool = False,
    predicate: Namespace | bool = False,
    obj_class: Namespace | bool = False,
    custom_obj_uri: str | bool = False,
) -> tuple[Graph, URIRef]:
    g = Graph()
    obj_name = node.tag.split("}")[-1]
    try:
        obj_node_value = node.xpath(xpath, namespaces=namespaces)[0]
    except IndexError:
        try:
            obj_node_value = node.xpath(xpath_alt_or_str, namespaces=namespaces)[0]
        except IndexError:
            if xpath_alt_or_str == "iterator":
                obj_node_value = iterator
            else:
                obj_node_value = xpath_alt_or_str
    if obj_node_value == skip_value:
        return (None, None)
    if custom_obj_uri:
        object_uri = URIRef(f"{prefix}/{custom_obj_uri}")
    else:
        object_uri = URIRef(f"{prefix}/{parent_node_name}/{obj_name}/{obj_node_value}")
    if obj_class:
        g.add((object_uri, RDF.type, obj_class))
    g.add((subject_uri, predicate, object_uri))
    return (g, object_uri)


def create_triple_from_node(
    node: Element,
    subj: URIRef,
    subj_suffix: str | bool = False,
    pred: Namespace | bool = False,
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
        try:
            obj_node = node.xpath(obj_node_xpath, namespaces=NSMAP)
        except (ET.XPathSyntaxError, ET.XPathEvalError) as err:
            print("##################################")
            print(f"{err} in xpath: {obj_node_xpath}")
            print("##################################")
            obj_node = None
        if isinstance(obj_node, list):
            for i, obj in enumerate(obj_node):
                subject_uri = URIRef(f"{subject}/{i}")
                if identifier:
                    g.add((subj, identifier, subject_uri))
                if sbj_class:
                    g.add((subject_uri, RDF.type, sbj_class))
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
                    g += create_object_literal_graph(
                        node=obj,
                        subject_uri=subject_uri,
                        l_prefix=l_prefix,
                        default_lang=default_lang,
                        predicate=RDFS.label
                    )
                if value_literal:
                    g += create_object_literal_graph(
                        node=obj,
                        subject_uri=subject_uri,
                        l_prefix=l_prefix,
                        default_lang=default_lang,
                        predicate=RDF.value
                    )
                if obj_node_value_xpath:
                    g1, obj_uri = create_obj_value_graph(
                        node=obj,
                        subject_uri=subject_uri,
                        parent_node_name=node_name,
                        xpath=obj_node_value_xpath,
                        xpath_alt_or_str=obj_node_value_alt_xpath_or_str,
                        iterator=i,
                        skip_value=skip_value,
                        prefix=obj_prefix,
                        predicate=predicate,
                        obj_class=obj_class
                    )
                    if g1:
                        g += g1
                if date and obj_uri:
                    not_known_value = "undefined"
                    begin, end = extract_begin_end(obj, fill_missing=False)
                    if begin or end:
                        ts_uri = URIRef(f"{obj_uri}/time-span")
                        g.add((obj_uri, CIDOC["P4_has_time-span"], ts_uri))
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


def create_e42_or_custom_class(
    subj: URIRef,
    node: Element,
    subj_suffix: str = "identifier/idno",
    default_lang: str = "und",
    uri_prefix: str = "https://foo-bar/",
    xpath: str | bool = False,
    attribute: str | bool = False,
    label: str | bool = False,
    label_prefix: str | bool = "Identifier: ",
    value: str | bool = False,
    value_datatype: Namespace | bool = False,
    type_suffix: str | bool = "types/any",
    custom_identifier: Namespace | bool = False,
    custom_identifier_class: Namespace | bool = False
) -> Graph | tuple[Graph, URIRef]:
    g = Graph()
    if xpath:
        try:
            identifier = node.xpath(xpath, namespaces=NSMAP)
        except (ET.XPathSyntaxError, ET.XPathEvalError) as err:
            print("##################################")
            print(f"{err} in xpath: {xpath}")
            print("##################################")
            identifier = None
        if isinstance(identifier, list):
            for i, ident in enumerate(identifier):
                identifier_uri = URIRef(f"{subj}/{subj_suffix}/{i}")
                if custom_identifier:
                    g.add((subj, custom_identifier, identifier_uri))
                else:
                    g.add((subj, CIDOC["P1_is_identified_by"], identifier_uri))
                if custom_identifier_class:
                    g.add((identifier_uri, RDF.type, custom_identifier_class))
                else:
                    g.add((identifier_uri, RDF.type, CIDOC["E42_Identifier"]))
                if attribute:
                    g.add((identifier_uri, CIDOC["P2_has_type"],
                           URIRef(f"{uri_prefix}{type_suffix}/{ident.attrib[attribute]}")))
                else:
                    g.add((identifier_uri, CIDOC["P2_has_type"], URIRef(f"{uri_prefix}{type_suffix}")))
                g += create_object_literal_graph(
                    node=ident,
                    subject_uri=identifier_uri,
                    l_prefix=label_prefix,
                    default_lang=default_lang,
                    predicate=RDFS.label
                )
                g += create_object_literal_graph(
                    node=ident,
                    subject_uri=identifier_uri,
                    l_prefix="",
                    default_lang=default_lang,
                    predicate=RDF.value
                )
        return g
    else:
        identifier_uri = URIRef(f"{subj}/{subj_suffix}")
        if custom_identifier:
            g.add((subj, custom_identifier, identifier_uri))
        else:
            g.add((subj, CIDOC["P1_is_identified_by"], identifier_uri))
        if custom_identifier_class:
            g.add((identifier_uri, RDF.type, custom_identifier_class))
        else:
            g.add((identifier_uri, RDF.type, CIDOC["E42_Identifier"]))
        g.add((identifier_uri, CIDOC["P2_has_type"], URIRef(f"{uri_prefix}{type_suffix}")))
        if label:
            g.add((identifier_uri, RDFS.label, Literal(f"{label_prefix}{label}", lang=default_lang)))
        if value and not value_datatype:
            g.add((identifier_uri, RDF.value, Literal(label)))
        elif value and value_datatype:
            g.add((identifier_uri, RDF.value, Literal(label, datatype=value_datatype)))
        return (g, identifier_uri)


def create_birth_death_settlement_graph(
    node: Element,
    namespaces: dict = NSMAP,
    uri_prefix: Namespace = Namespace("https://foo-bar/"),
    node_attrib: str | bool = False,
) -> Graph:
    g = Graph()
    try:
        place_id = node.attrib[node_attrib]
    except KeyError:
        place_id = None
    if place_id is not None:
        place_uri = URIRef(f"{uri_prefix}{place_id}")
        g.add((place_uri, RDF.type, CIDOC["E53_Place"]))
        # from string no xpath
        g1, identifier_uri = create_e42_or_custom_class(
            node=node,
            subj=place_uri,
            subj_suffix="appellations/0",
            uri_prefix=uri_prefix,
            type_suffix="types/place/placename",
            custom_identifier_class=CIDOC["E33_E41_Linguistic_Appellation"]
        )
        g += g1
        # literals from node
        place_node = node.xpath(normalize_string("./tei:placeName"), namespaces=namespaces)[0]
        g += create_object_literal_graph(
            node=place_node,
            subject_uri=place_uri,
            l_prefix="",
            default_lang="en",
            predicate=RDFS.label
        )
        g += create_object_literal_graph(
            node=place_node,
            subject_uri=identifier_uri,
            l_prefix="",
            default_lang="en",
            predicate=RDFS.label
        )
        g += create_object_literal_graph(
            node=place_node,
            subject_uri=identifier_uri,
            l_prefix="",
            default_lang="en",
            predicate=RDF.value
        )
        # from node via xpath
        g += create_e42_or_custom_class(
            node=node,
            subj=place_uri,
            subj_suffix="identifier/idno",
            default_lang="en",
            uri_prefix=uri_prefix,
            xpath="./tei:idno",
            attribute="type",
            label_prefix="Identifier: ",
            type_suffix="types/idno/URL"
        )
        # from string no xpath
        g2, identifier_uri2 = create_e42_or_custom_class(
            node=node,
            subj=place_uri,
            subj_suffix=f"identifier/{place_id}",
            default_lang="en",
            uri_prefix=uri_prefix,
            label=place_id,
            type_suffix="types/idno/xml-id",
            label_prefix="Identifier: "
        )
        g += g2
        try:
            coordinates = node.xpath("./tei:location/tei:geo", namespaces=namespaces)[0]
        except IndexError:
            coordinates = None
        if coordinates is not None:
            long = coordinates.text.split()[0]
            lat = coordinates.text.split()[1]
            g.add((place_uri, CIDOC["P168_place_is_defined_by"],
                   Literal(f"Point({long} {lat})", datatype=GEO["wktLiteral"])))
    return g
