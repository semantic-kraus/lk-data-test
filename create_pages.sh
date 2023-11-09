rm -rf html
mkdir html
touch html/.nojekyll

python scripts/make_index.py
cp rdf/*.trig html/
cp rdf/*.ttl html/
cd html
zip -r texts.zip texts.*
rm texts.t*
