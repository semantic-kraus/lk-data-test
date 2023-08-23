from acdh_tei_pyutils.tei import TeiReader

sb_url = "https://schnitzler-briefe.acdh.oeaw.ac.at/"
entity_type = "person"
index_file = f"./data/indices/list{entity_type}.xml"
doc = TeiReader(index_file)
nsmap = doc.nsmap

for x in doc.any_xpath(".//tei:idno[@type='schnitzler-briefe']"):
    pmb_id = x.text.split("=")[-1]
    new_url = f"{sb_url}{pmb_id}.html"
    x.text = new_url

for x in doc.any_xpath(".//tei:idno[@subtype='schnitzler-briefe']"):
    pmb_id = x.text.split("=")[-1]
    new_url = f"{sb_url}{pmb_id}.html"
    x.text = new_url

doc.tree_to_file(index_file)