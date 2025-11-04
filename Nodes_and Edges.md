# Node and Edge Tables (Including Attributes)

## Node Types

| Node Type | Attributes |
|-----------|------------|
| Work | doi, title, type, publication_date, cited_by_count, open_access, host_venue_id |
| Concept | display_name, level, display_name, wikidata, works_count |
| Author | orcid, display_name |
| Institution | ror, display_name, country_code |
| Publisher | display_name, hierarchy_level |
| Source | issn_I, issn, display_name |
| Topic | display_name, field, subfield |
| Inventor | name |
| Patent | Number? Date? (unsure with the db) |
| Classification | Name, field/subfield |
| Person | name |

## Edge Types

| Edge Type | Node Type 1 | Node Type 2 | Bidirectional | Attributes |
|-----------|-------------|-------------|---------------|------------|
| Co-authors | Author | Author | Yes | |
| Authored | Author | Work | No | position |
| Affiliated_with | Author | Institution | No | |
| Discussed | Work | Concept | No | score |
| Cited | Work/Patent | Work/Patent | No | count |
| Tagged | Work | Topic | No | score |
| Published_in | Source | Work | No | volume |
| Parented | Publisher | Publisher | No | |
| Published_by | Source | Publisher | No | |
| Associated | Institution | Institution | Yes | relationship |
| Assigned_to | Patent | Institution | No | |
| Classified_by | Patent | Classification | No | |
| Maps_to | Topic/Concept | Classification | Yes | |
| Invented | Inventor | Patent | No | |