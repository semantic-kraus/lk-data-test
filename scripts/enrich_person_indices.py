from acdh_tei_pyutils.tei import TeiEnricher
import lxml.etree as ET

listplace_path = "./data/indices/listplace.xml"
listplace = TeiEnricher(listplace_path)
listperson_path = "./data/indices/listperson.xml"
listperson = TeiEnricher(listperson_path)
nsmap = listperson.nsmap

place_id_lookup = {}
for place in listplace.any_xpath(".//tei:listPlace/tei:place"):
    if place.xpath("./tei:idno[@subtype]", namespaces=nsmap):
        place_id = place.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        place_id_lookup[place_id] = {}
        print("created key", place_id)
        for i, idno in enumerate(place.xpath("./tei:idno[@subtype]", namespaces=nsmap)):
            place_id_lookup[place_id][f"{idno.get('subtype')}__{i}"] = idno.text
print("place lookup dict created", len(place_id_lookup))


def enrich_settlements(node):
    try:
        settlement_key = node.get("key")
    except IndexError:
        settlement_key = None
        return "no key found"
    if settlement_key:
        try:
            settlement = place_id_lookup[settlement_key]
        except KeyError:
            settlement = None
        if settlement:
            for key, value in settlement.items():
                idno = ET.Element("{http://www.tei-c.org/ns/1.0}idno")
                idno.attrib["type"] = key.split("__")[0]
                idno.text = value
                node.append(idno)
            print(f"added place ids to {settlement_key}")


for person in listperson.any_xpath(".//tei:listPerson/tei:person"):
    if person.xpath("./tei:birth[./tei:settlement]", namespaces=nsmap):
        settlement_node = person.xpath("./tei:birth/tei:settlement", namespaces=nsmap)[0]
        enrich_settlements(settlement_node)
    if person.xpath("./tei:death[./tei:settlement]", namespaces=nsmap):
        settlement_node = person.xpath("./tei:death/tei:settlement", namespaces=nsmap)[0]
        enrich_settlements(settlement_node)
listperson.tree_to_file(file=listperson_path)
print("finished adding place ids to person/settlement nodes")
