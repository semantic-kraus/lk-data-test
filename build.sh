# bin/bash

python scripts/enrich_person_indices.py
python scripts/make_rdf.py
python scripts/make_texts.py
python scripts/make_listwork.py
python curation/check_fackel_references.py
python scripts/owl_inverse_props.py