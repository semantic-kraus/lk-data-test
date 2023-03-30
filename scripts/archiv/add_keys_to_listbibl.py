from collections import defaultdict
from acdh_tei_pyutils.tei import TeiReader


file = "./data/indices/listwork.xml"

doc = TeiReader(file)
nsmap = doc.nsmap
d = defaultdict(list)
for x in doc.any_xpath(".//tei:bibl/tei:bibl"):
    try:
        date_str = x.xpath("./tei:date/text()", namespaces=nsmap)[0]
    except IndexError:
        continue
    try:
        title_key = x.xpath("./tei:title[@level='j']/@key", namespaces=nsmap)[0]
    except IndexError:
        continue
    print(date_str, title_key)
    d[f"{date_str}___{title_key}"].append(x)

n = 130
for key, value in d.items():
    n += 1
    new_key = f"#sk_lk{n:05}"
    print(len(value), new_key)
    for item in value:
        date = item.xpath("./tei:date", namespaces=nsmap)[0]
        date.attrib['key'] = new_key

doc.tree_to_file(file)
