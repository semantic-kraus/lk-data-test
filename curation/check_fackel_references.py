import glob
import os
from acdh_tei_pyutils.tei import TeiReader
from tqdm import tqdm
from collections import defaultdict, Counter
from acdh_cidoc_pyutils import normalize_string
import json


fackel_texts = "https://raw.githubusercontent.com/semantic-kraus/fa-data/main/data/indices/fackelTexts_cascaded.xml"
print(f"parsing {fackel_texts}")
fa_doc = TeiReader(fackel_texts)

files = sorted(glob.glob("./legalkraus-archiv/data/editions/*xml"))

page_text_dict = defaultdict(list)
page_text_list = []
for x in fa_doc.any_xpath(".//text[@range]"):
    text_id = x.attrib["textId"]
    for y in x.attrib["range"].split():
        page_id = y.lower()
        page_text_list.append(page_id)
        page_text_dict[page_id] = text_id


more_than_one = {x: count for x, count in Counter(page_text_list).items() if count > 1}
more_than_one_sorted = dict(
    sorted(more_than_one.items(), key=lambda x: x[1], reverse=True)
)
with open("./rdf/fackel_quotes_counter.json", "w") as f:
    json.dump(more_than_one_sorted, f, ensure_ascii=False)


d = defaultdict(list)
sources = []
for x in tqdm(files, total=len(files)):
    doc = TeiReader(x)
    _, tail = os.path.split(x)
    quotes = doc.any_xpath(".//tei:quote[@source]")
    for q in quotes:
        source = q.attrib["source"].lower()
        if "fackel" in source:
            texts = normalize_string(" ".join(q.xpath(".//text()")))
            value = f"{tail}||{texts}"
            d[source].append(value)
            sources.append(source)
# print(d)

more_than_one = {x: count for x, count in Counter(sources).items() if count > 1}
more_than_one_sorted = dict(
    sorted(more_than_one.items(), key=lambda x: x[1], reverse=True)
)
with open("./rdf/fackel_mentions.json", "w") as f:
    json.dump(more_than_one_sorted, f, ensure_ascii=False)


fa_texts = set(page_text_list)
mention_more_than_one = set()
for x in set(sources):
    try:
        more_than_one[x]
        mention_more_than_one.add(x)
    except:  # noqa:
        pass
print(len(mention_more_than_one))
print(len(set(sources)))

with open("./rdf/mention_more_than_one.txt", "w") as f:
    for x in mention_more_than_one:
        f.write(f"{x}\n")
