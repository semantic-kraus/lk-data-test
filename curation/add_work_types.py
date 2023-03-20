from acdh_tei_pyutils.tei import TeiReader

from work_type_mapping import work_types

list_work = './data/indices/listwork.xml'


doc = TeiReader(list_work)

all = 0
bibls = doc.any_xpath('.//tei:listBibl/tei:bibl')
print("deleting existing tpyes")
for x in doc.any_xpath('.//tei:bibl[@type="sk"]'):
    x.attrib["subtype"] = "no_type"
for x in work_types:
    items = doc.any_xpath(x["type_xpath"])
    print(f"typed {len(items)} bibls with type: {x['type_value']}")
    for sk_work in items:
        sk_work.attrib["subtype"] = x["type_value"]
    all += len(items)
print(f"caterogized: {all} items out of {len(bibls)}")

doc.tree_to_file(list_work)