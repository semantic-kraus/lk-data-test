# bin/bash

echo "delete namedgraphs"
curl -D- -X DELETE \
    "${R_ENDPOINT_V}?c=<https://sk.acdh.oeaw.ac.at/project/legal-kraus>"
sleep 300

echo "add namedgraph data.trig"
curl $R_ENDPOINT_V \
    -H 'Content-Type: application/x-trig; charset=UTF-8' \
    -H 'Accept: text/boolean' \
    -d @rdf/data.trig
sleep 600

echo "add namedgraph texts.trig"
curl $R_ENDPOINT_V \
    -H 'Content-Type: application/x-trig; charset=UTF-8' \
    -H 'Accept: text/boolean' \
    -d @rdf/texts.trig
sleep 600

echo "add namedgraph work.trig"
curl $R_ENDPOINT_V \
    -H 'Content-Type: application/x-trig; charset=UTF-8' \
    -H 'Accept: text/boolean' \
    -d @rdf/work.trig
