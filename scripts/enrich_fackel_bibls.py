# # see https://github.com/semantic-kraus/lk-data/issues/66
from acdh_tei_pyutils.tei import TeiReader
from lxml import etree as ET
import lxml.builder

listfackel_path = "./data/indices/listfackel.xml"
listfackel = TeiReader(listfackel_path)
fackel_texts = TeiReader("https://raw.githubusercontent.com/semantic-kraus/fa-data/main/data/indices/fackelTexts_cascaded.xml")
nsmap = fackel_texts.nsmap
teiMaker = lxml.builder.ElementMaker()
single_machtes = 0
nomatches = 0
unmatched = []

def delete_old_matches():
    # # need to delete old matches, befor I create new ones
    # # be careful to only delete exact matches
    for idno in listfackel.any_xpath("//tei:idno[@type='fackel' and (@subtype='text' or subtype='issue')]"):
        idno.getparent().remove(idno)


class BiblIf:
    def __init__(self, element: ET.Element):
        self.element = element
        self.corresp = self.element.get("corresp").lower().strip()
        self.issue = True if self.corresp.endswith("0u1") else False
        bibl_scope = self.element.xpath("./tei:biblScope", namespaces=nsmap)
        self.bibl_scope_from = bibl_scope[0].get("from") if bibl_scope else None
        self.bibl_scope_to = bibl_scope[0].get("to") if bibl_scope else None
        try:
            self.title = (
                self.element.xpath("./tei:title[@level='a']", namespaces=nsmap)[0]
                .text.lower()
                .strip(" .")
            )
        except IndexError:
            self.title = None


weblinks_2_fackeltexts = {}
for text in fackel_texts.any_xpath("//text"):
    weblinks = text.get("webLink")
    if weblinks is not None:
        weblinks = weblinks.lower().strip()
        if weblinks in weblinks_2_fackeltexts:
            weblinks_2_fackeltexts[weblinks].append(text)
        else:
            weblinks_2_fackeltexts[weblinks] = [text]

weblinks_2_fackelissues = {}
for text in fackel_texts.any_xpath("//issue"):
    weblinks = text.get("webLink")
    if weblinks is not None:
        weblinks = weblinks.lower().strip()
        if weblinks in weblinks_2_fackelissues:
            weblinks_2_fackelissues[weblinks].append(text)
        else:
            weblinks_2_fackelissues[weblinks] = [text]


def search_4_listfackel_bibl(listfackel_bibl: BiblIf):
    global nomatches
    global single_machtes
    matches = []
    # # @corresp with //@webLink
    for key, val in weblinks_2_fackeltexts.items():
        if listfackel_bibl.corresp == key:
            matches += val
    # # and biblScope:
    # # biblScope/@from with text/@startPage
    matches = [
        match
        for match in matches
        if match.get("startPage") == listfackel_bibl.bibl_scope_from
    ]
    # # biblScope/@to with text/@endPage
    matches = [
        match
        for match in matches
        if match.get("endPage") == listfackel_bibl.bibl_scope_to
    ]
    # # If there is more than one corresponding text-element in fackelTexts_cascaded.xml, 
    # # compare listfackel.xml's title[@level="a"] with text/@titleText there. 
    # # Take the one that fits better.
    if len(matches) > 1 and listfackel_bibl.title:
        matches = [
            match
            for match in matches
            if match.get("titleText").lower().strip(" .") == listfackel_bibl.title
        ]
    
    # # if there is no corresponding text-element in fackelTexts_cascaded.xml, 
    # # look if the @corresp-value from listfackel can be found in a @range in 
    # # fackelTexts_cascaded.xml. If so, take that text's ID.
    if len(matches) == 0:
        matches = fackel_texts.any_xpath(f"//text[contains(translate(@range, 'F', 'f'), '{listfackel_bibl.corresp}')]")
        print(f"matches was 0 for {listfackel_bibl.corresp} but {len(matches)} by range.")
    matched = matches[0] if len(matches) >= 1 else None
    if matched is not None:
        matched_id = matched.get("id")
        listfackel_bibl.element.insert(0, teiMaker.idno(matched_id, type="fackel", subtype="text"))
        single_machtes += 1
    else:
        nomatches += 1
        print(listfackel_bibl.corresp)


def search_4_listfackel_issue_bibl(listfackel_bibl: BiblIf):
    global nomatches
    global single_machtes
    matches = []
    for key, val in weblinks_2_fackelissues.items():
        if listfackel_bibl.corresp == key:
            matches += val
    if len(matches) == 1:
        matched_id = matches[0].get("id")
        listfackel_bibl.element.insert(0, teiMaker.idno(matched_id, type="fackel", subtype="issue"))
        single_machtes += 1
    else:
        print(f"bibl with corresp '{listfackel_bibl.corresp}' couldn't be matched at all.")
        nomatches += 1


if __name__ == "__main__":
    listfackel_bibls = []
    delete_old_matches()
    for bibl in listfackel.any_xpath("//tei:body/tei:listBibl/tei:bibl"):
        listfackel_bibls.append(BiblIf(bibl))
    for listfackel_bibl in listfackel_bibls:
        if not listfackel_bibl.issue:
            search_4_listfackel_bibl(listfackel_bibl)
        else:
            # # If @corresp in listfackel.xml ends with "0u1", 
            # # the @corresp should match an issue-element in 
            # # fackelTexts_cascaded.xml - take that id instead.
            search_4_listfackel_issue_bibl(listfackel_bibl)
    listfackel.tree_to_file(listfackel_path)

print(f"{single_machtes} matches, {nomatches} couldn't be matched at all.")
