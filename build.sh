rm -rf html
mkdir html
touch html/.nojekyll

python scripts/enrich_person_indices.py
python scripts/make_rdf.py
python scripts/make_texts.py
python scripts/make_listwork.py
python curation/check_fackel_references.py
python scripts/owl_inverse_props.py

# python scripts/make_index.py
# cp rdf/* html/
# echo "rdf dir content copied to html dir"
# echo "list directory"
# ls -l html
# ls -l rdf