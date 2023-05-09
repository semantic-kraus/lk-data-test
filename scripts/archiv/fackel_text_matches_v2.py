from acdh_tei_pyutils.tei import TeiReader
from glob import glob

# # script searching for mentioned fackel-texts that are nested
matchstring = "https://facke"
files_dir = (
    "/home/zorg/Dokumente/kraus/semantic/lk-data/legalkraus-archiv/data/editions/*"
)
element_results = {"note": [], "rs": [], "quote": []}
# index_file = "/home/zorg/Dokumente/kraus/semantic/fa-data/data/indices/fackelTexts_cascaded.xml"
index_file = "/home/zorg/Downloads/fackelTexts_cascaded.xml"
index_doc = TeiReader(index_file)

print(f"searching for attributes containing {matchstring}")
for filepath in glob(files_dir):
    print(f"searching in '{filepath}'")
    doc = TeiReader(filepath)
    for element_name in element_results:
        element_results[element_name] += [
            link.lower()
            for link in doc.any_xpath(
                f".//tei:body//tei:{element_name}/@*[contains(., '{matchstring}')]"
            )
        ]

existing_source_vals = [value.lower() for value in index_doc.any_xpath("//*/@range")]
for element_name, links in element_results.items():
    counter_dict = {}
    for link in links:
        matches = 0
        for existing in existing_source_vals:
            if link in existing:
                matches += 1
        counter_dict[link] = matches

    with open(f"{element_name}_results.txt", "w") as outfile:
        for key, amount in counter_dict.items():
            if amount > 1:
                outfile.write(f"{key}\t:{amount}\n")
