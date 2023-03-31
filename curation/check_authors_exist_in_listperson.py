from acdh_tei_pyutils.tei import TeiReader

doc = TeiReader("./data/indices/listwork.xml")
authors = set()
for x in doc.any_xpath(".//tei:author/@key"):
    if x.startswith("#"):
        a_key = x[1:]
    else:
        a_key = x
    authors.add(a_key)

print(len(authors))

bauthors = set()
doc = TeiReader("./data/indices/listperson.xml")
authors = set()
for x in doc.any_xpath(".//tei:person/@xml:id"):
    bauthors.add(x)
print(len(bauthors))

for x in authors:
    if x in bauthors:
        continue
    else:
        print(x)
