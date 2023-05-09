from acdh_tei_pyutils.tei import TeiReader

# # check if authors (listwork) are registerd in listperson #47

listwork = TeiReader("./data/indices/listwork.xml")
listperson = TeiReader("./data/indices/listperson.xml")
author_pmb_ids = listwork.any_xpath("//tei:body//tei:author/@key")
existing_people = listperson.any_xpath("//tei:body/tei:listPerson/tei:person/@xml:id")
found = 0
non_existing = []
for author_pmb_id in author_pmb_ids:
    if author_pmb_id not in existing_people:
        non_existing.append(author_pmb_id)
    else:
        found += 1
non_existing_log = '\n'.join(non_existing)
print(f"{found} where found, {len(non_existing)} are missing: \n{non_existing_log}")