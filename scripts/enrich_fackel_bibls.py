# # see https://github.com/semantic-kraus/lk-data/issues/66
from acdh_tei_pyutils.tei import TeiReader
from lxml import etree as ET
import lxml.builder

listfackel_path = "./legalkraus-archiv/data/indices/listfackel.xml"
listfackel = TeiReader(listfackel_path)
fackel_texts = TeiReader("../fa-data/data/indices/fackelTexts_cascaded.xml")
nsmap = fackel_texts.nsmap
teiMaker = lxml.builder.ElementMaker(
    namespace="http://www.tei-c.org/ns/1.0", nsmap=nsmap
)
single_machtes = 0
multimatches = 0
nomatches = 0
nolinkmatches = 0


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
    global multimatches
    global nolinkmatches
    matches = []
    for key, val in weblinks_2_fackeltexts.items():
        if listfackel_bibl.corresp == key:
            matches += val
    if not matches:
        print(listfackel_bibl.corresp)
        nolinkmatches += 1
    linkmatches = matches if len(matches) == 2 else []
    if len(matches) > 1:
        if listfackel_bibl.bibl_scope_from:
            matches = [
                match
                for match in matches
                if match.get("startPage") == listfackel_bibl.bibl_scope_from
            ]
    if len(matches) > 1:
        if listfackel_bibl.bibl_scope_to:
            matches = [
                match
                for match in matches
                if match.get("endPage") == listfackel_bibl.bibl_scope_to
            ]
    if len(matches) > 1 and listfackel_bibl.title:
        matches = [
            match
            for match in matches
            if match.get("titleText").lower().strip(" .") == listfackel_bibl.title
        ]
    if len(matches) == 0 and linkmatches:
        if not [
            match
            for match in matches
            if match.get("titleText").lower().strip(" .") == listfackel_bibl.title
        ]:
            match1 = len(linkmatches[0].xpath("ancestor::tei:text", namespaces=nsmap))
            match2 = len(linkmatches[1].xpath("ancestor::tei:text", namespaces=nsmap))
            if match1 > match2:
                matches = linkmatches[:1]
            else:
                matches = linkmatches[1:]
    if len(matches) == 1:
        single_machtes += 1
        matched_id = matches[0].get("id")
        listfackel_bibl.element.insert(0, teiMaker.idno(matched_id, type="fackel"))
    elif len(matches) > 1:
        multimatches += 1
        print(f"{listfackel_bibl.corresp} unclear match, {len(matches)} matches")
    else:
        print(listfackel_bibl.corresp)
        print(f"{len(matches)} matches\n")
        nomatches += 1


def search_4_listfackel_issue_bibl(listfackel_bibl: BiblIf):
    global nomatches
    global single_machtes
    global multimatches
    global nolinkmatches
    matches = []
    for key, val in weblinks_2_fackelissues.items():
        if listfackel_bibl.corresp == key:
            matches += val
    if not matches:
        print(listfackel_bibl.corresp)
        nolinkmatches += 1
    if len(matches) == 1:
        single_machtes += 1
    elif len(matches) > 1:
        print(f"{listfackel_bibl.corresp} unclear match, {len(matches)} matches")
        multimatches += 1
    else:
        print(listfackel_bibl.corresp)
        print(f"{len(matches)} matches\n")
        nomatches += 1


if __name__ == "__main__":
    listfackel_bibls = []
    for bibl in listfackel.any_xpath("//tei:body/tei:listBibl/tei:bibl"):
        listfackel_bibls.append(BiblIf(bibl))
    for listfackel_bibl in listfackel_bibls:
        if not listfackel_bibl.issue:
            search_4_listfackel_bibl(listfackel_bibl)
        else:
            search_4_listfackel_issue_bibl(listfackel_bibl)

print(f"{single_machtes} exact matches, {multimatches} unclear matches, {nomatches} couldn't be matched at all.")
print("\n In {nolinkmatches} cases the link couldn't be matched.")
