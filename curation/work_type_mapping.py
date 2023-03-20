work_types = [
    {
        "type_value": "journal",
        "type_xpath": '//tei:bibl[@type="sk"][./tei:title[@level="j"] and not(./tei:title[@level="a"]) and not(./tei:date)]',
    },
    {
        "type_value": "issue",
        "type_xpath": '//tei:bibl[@type="sk"][./tei:title[@level="j"] and not(./tei:title[@level="a"]) and ./tei:date[@key]]'
    },
    {
        "type_value": "article",
        "type_xpath": '//tei:bibl[@type="sk"][./tei:title[@level="j"] and ./tei:title[@level="a"] and ./tei:date[@key]]',
    },
    {
        "type_value": "standalone publication",
        "type_xpath": '//tei:bibl[@type="sk"][./tei:title[@level="m"] and not(./tei:date)]',
    },
]
