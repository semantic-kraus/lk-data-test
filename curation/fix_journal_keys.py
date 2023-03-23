from acdh_tei_pyutils.tei import TeiReader

source_tei = "./data/indices/listwork.xml"
doc = TeiReader(source_tei)
items = doc.any_xpath(".//tei:listBibl/tei:bibl[./tei:bibl/tei:title[@level='j']]")
nsmap = doc.nsmap

pmb_id_dict = {}
for x in items:
    xml_id = x.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    sk_node = x.xpath('./tei:bibl[@type="sk"]', namespaces=nsmap)[0]
    child_nodes = sk_node.xpath(".//*")
    if len(child_nodes) == 1:
        key = child_nodes[0].attrib["key"]
        pmb_id_dict[key] = xml_id

for x in doc.any_xpath(".//*[@key]"):
    try:
        new_value = pmb_id_dict[x.attrib["key"]]
    except KeyError:
        continue
    x.attrib["key"] = f"#{new_value}"

doc.tree_to_file(source_tei)

print("and now to #6 https://github.com/semantic-kraus/lk-data/issues/6")

doc = TeiReader(source_tei)
items = doc.any_xpath(
    './/tei:bibl[@type="sk"]/tei:title[@level="j" and not(parent::tei:bibl/tei:title[not(@level="j")][2]) and not(parent::tei:bibl/tei:date) and not(parent::tei:bibl/tei:num)]' # noqa:
)
nsmap = doc.nsmap
print(len(items))
replace_dict = {}
for x in items:
    journal_key = x.attrib["key"]
    bibl = x.getparent().getparent()
    bibl_id = bibl.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    print(journal_key, bibl_id)
    x.attrib["key"] = f"#{bibl_id}"
    replace_dict[journal_key] = f"#{bibl_id}"
for x in doc.any_xpath(".//*[@key]"):
    try:
        new_key = replace_dict[x.attrib["key"]]
    except KeyError:
        continue
    x.attrib["key"] = new_key
doc.tree_to_file(source_tei)

