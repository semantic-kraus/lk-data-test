from lxml.etree import Element
from rdflib import Graph, Literal, URIRef, RDF, RDFS, OWL
from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO, NSMAP
from acdh_cidoc_pyutils import (
    normalize_string,
    create_e52,
    extract_begin_end
)


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
