from acdh_tei_pyutils.tei import TeiReader

from work_type_mapping import work_types

list_work = './data/indices/listwork.xml'


doc = TeiReader(list_work)

all = 0
bibls = doc.any_xpath('.//tei:listBibl/tei:bibl')
for x in work_types:
    items = doc.any_xpath(x["type_xpath"])
    print(len(items))
    for sk_work in items:
        sk_work.attrib["subtype"] = x["type_value"]
    all += len(items)
print(f"caterogized: {all} items out of {len(bibls)}")

doc.tree_to_file("list_work")