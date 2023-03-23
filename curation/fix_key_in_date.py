from acdh_tei_pyutils.tei import TeiReader

print("working on https://github.com/semantic-kraus/lk-data/issues/7")

source_tei = "./data/indices/listwork.xml"
doc = TeiReader(source_tei)
items = doc.any_xpath('//tei:bibl[@type="sk" and @subtype="issue"]')
nsmap = doc.nsmap
key_map = {}
for x in items:
    bibl = x.getparent()
    bibl_xmlid = bibl.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    date = x.xpath('./tei:date[@key]', namespaces=nsmap)[0]
    date_key = date.attrib["key"]
    key_map[date_key] = bibl_xmlid
    print(date_key, bibl_xmlid)
    date_key = f"#{bibl_xmlid}"
doc.tree_to_file(source_tei)
