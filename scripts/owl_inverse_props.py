# import os
import glob
import requests
import json
from slugify import slugify
from tqdm import tqdm
from lxml.etree import XMLParser
from lxml import etree as ET
# from collections import defaultdict
from rdflib import Graph, URIRef, Namespace, Dataset
# from rdflib.store import Store
# from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO


NSMAP_RDF = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "xml:base": "https://sk.acdh.oeaw.ac.at/model#",
    "frbroo": "https://cidoc-crm.org/frbroo/sites/default/files/FRBR2.4-draft.rdfs#",
    "crm": "http://www.cidoc-crm.org/cidoc-crm/",
    "intro": "https://w3id.org/lso/intro/beta202304#",
    "schema": "https://schema.org/",
    "prov": "http://www.w3.org/ns/prov#",
    "dcterms": "http://purl.org/dc/terms/"
}
SK_MODEL_URL = "https://raw.githubusercontent.com/semantic-kraus/sk_general/main/sk_model.owl"
DOMAIN = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(DOMAIN)
LK = Namespace("https://sk.acdh.oeaw.ac.at/project/legal-kraus")

project_uri = URIRef(f"{SK}project/legal-kraus")
# store = plugin.get("Memory", Store)()
# project_store = plugin.get("Memory", Store)()


def parse_xml(url):
    p = XMLParser(huge_tree=True)
    response = requests.get(url)
    doc = ET.fromstring(response.content, parser=p)
    return doc


def get_inverse_of(model_doc):
    inverse_of_dict = []
    inverse = model_doc.xpath(".//*[owl:inverseOf]", namespaces=NSMAP_RDF)
    for i, x in tqdm(enumerate(inverse), total=len(inverse)):
        value = x.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"]
        inverseOf = x.xpath("./owl:inverseOf", namespaces=NSMAP_RDF)[0] \
            .attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]
        inverse_of_dict.append([inverseOf, value])
    return inverse_of_dict


def parse_rdf_trig(file):
    print(f"parsing file: {file}")
    d = Dataset()
    d.parse(file, format="trig")
    return d


def parse_rdf_ttl(file):
    print(f"parsing file: {file}")
    g = Graph()
    g.parse(file, format="ttl")
    return g


def query_for_inverse(ttl_input, prop):
    prop = f"<{prop}>"
    query = f"""
    PREFIX ns1: <http://www.cidoc-crm.org/cidoc-crm/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?sbj ?p ?obj
    WHERE {{
        ?sbj {prop} ?obj .
        ?obj ?p ?o .
    }}"""
    qres = ttl_input.query(query)
    print(len(qres))
    return qres


def create_inverse_dict(query_result):
    props_with_inverse = {}
    for row in tqdm(query_result, total=len(query_result)):
        sbj = row[0]
        p = slugify(row[1])
        obj = row[2]
        try:
            props_with_inverse[p].append({sbj: obj})
        except KeyError:
            props_with_inverse[p] = []
            props_with_inverse[p].append({sbj: obj})
    # print(props_with_inverse)
    return props_with_inverse


def save_dict(dict, file):
    with open(file, "w") as f:
        json.dump(dict, f)
    print(f"saved dict {file}")


def create_triples(dict_result, output):
    for key, value in dict_result.items():
        # inverse_inverse_of = f"{inverse_of}--{inverse}"
        print("length values", len(value))
        pred = inverse
        for v in value:
            sbj = list(v.keys())[0]
            obj = list(v.values())[0]
            output.append(
                {"sbj": obj, "pred": pred, "obj": sbj}
            )


rdf_files = sorted(glob.glob("./rdf/*.ttl"))
lookup_dict = get_inverse_of(parse_xml(SK_MODEL_URL))
# print(lookup_dict)

for file in rdf_files:
    ttl = parse_rdf_ttl(file)
    missing_inverse_triples = []
    found_inverse_triples = []
    for x in tqdm(lookup_dict, total=len(lookup_dict)):
        # print(x)
        inverse_of = x[0]
        inverse = x[1]
        qres = query_for_inverse(ttl, inverse_of)
        dict_result = create_inverse_dict(qres)
        if dict_result is not None:
            try:
                test = dict_result[slugify(inverse)]
            except KeyError:
                test = False
            if test is False:
                print(f"no inverse found for {inverse_of}--{inverse}")
                create_triples(dict_result, missing_inverse_triples)
            else:
                print(f"inverse found for {inverse_of}--{inverse}")
                create_triples(dict_result, found_inverse_triples)
    if len(found_inverse_triples) != 0:
        unique_triples = [dict(t) for t in {tuple(d.items()) for d in found_inverse_triples}]
        save_dict(unique_triples, f"{file.replace('.ttl', '')}_inv_ok.json")
    if len(missing_inverse_triples) != 0:
        # trig_path = file.replace(".ttl", ".trig")
        # ds = parse_rdf_trig(trig_path)
        # g = ds.graph(project_uri)
        unique_triples = [dict(t) for t in {tuple(d.items()) for d in missing_inverse_triples}]
        # for triple in unique_triples:
        #     s = URIRef(triple["sbj"])
        #     p = URIRef(triple["pred"])
        #     o = URIRef(triple["obj"])
        #     ds.add((s, p, o, g))
        # # g_all = ConjunctiveGraph(store=project_store)
        # ds.serialize(trig_path, format="trig")
        save_dict(unique_triples, f"{file.replace('.ttl', '')}.json")
