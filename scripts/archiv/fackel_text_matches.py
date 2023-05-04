from acdh_tei_pyutils.tei import TeiReader
from glob import glob

# # script searching for mentioned fackel-texts that are nested
matchstring = "https://facke"
files_dir = "/home/zorg/Dokumente/kraus/semantic/lk-data/legalkraus-archiv/data/editions/*"
#index_file = "/home/zorg/Dokumente/kraus/semantic/fa-data/data/indices/fackelTexts_cascaded.xml"
index_file = "/home/zorg/Downloads/fackelTexts_cascaded.xml"
index_doc = TeiReader(index_file)

links = []
print(f"searching for attributes containing {matchstring}")
for filepath in glob(files_dir):
    print(f"searching in '{filepath}'")
    doc = TeiReader(filepath)
    links += [link.lower() for link in doc.any_xpath(f".//tei:body//*/@*[contains(., '{matchstring}')]")]

links = dict.fromkeys(links)
print(f"{len(links)} unique attribute-values conataining {matchstring} where found")

existing_source_vals = [value.lower() for value in index_doc.any_xpath("//*/@range")]

for key in links:
    matches = 0
    for existing in existing_source_vals:
        if key in existing:
            matches += 1
    links[key] = matches

with open("results.txt", "w") as outfile:
    for key, amount in links.items():
        if amount > 1:
            outfile.write(f"{key}\t:{amount}\n")
