from lxml.etree import Element
from rdflib import Graph, Literal, URIRef, RDF, RDFS
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
    default_lang="de",
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
