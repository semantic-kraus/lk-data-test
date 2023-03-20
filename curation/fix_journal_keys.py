from acdh_tei_pyutils.tei import TeiReader

source_tei = "./data/indices/listwork.xml"
doc = TeiReader(source_tei)
items = doc.any_xpath(f".//tei:listBibl/tei:bibl[./tei:bibl/tei:title[@level='j']]")
nsmap = doc.nsmap
print(len(nsmap))

pmb_id_dict = {}
for x in items:
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    sk_node = x.xpath('./tei:bibl[@type="sk"]', namespaces=nsmap)[0]
    child_nodes = sk_node.xpath('.//*')
    if len(child_nodes) == 1:
        print(child_nodes[0].text)
        key = child_nodes[0].attrib['key']
        pmb_id_dict[key] = xml_id
        # child_nodes[0].attrib["newkey"] = f"#{xml_id}"


for x in doc.any_xpath(".//*[@key]"):
    try:
        new_value = pmb_id_dict[x.attrib["key"]]
    except KeyError:
        continue
    x.attrib["key"] = f"#{new_value}"

doc.tree_to_file(source_tei)