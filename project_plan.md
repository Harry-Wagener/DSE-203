# Knowledge Graph ETL Project Requirements
## Material Science Publications & Patents

**Course**: ETL & Data Management  
**Target Database**: Neo4j  
**Domain**: Material Science (subset of OpenAlex + USPTO data)

---

## 1. Project Overview

### 1.1 Objective
Build a knowledge graph integrating academic publications (OpenAlex) and patent data (USPTO) focused on Material Science, enabling cross-domain analysis of research and innovation.

### 1.2 Scope
- Extract and filter Material Science publications from OpenAlex database
- Extract and process USPTO patent data with Material Science classifications
- Transform data to graph-compatible format
- Load data into Neo4j with proper relationships
- Enable entity resolution between inventors and authors (Person unification)
- Map academic topics/concepts to patent classifications

---

## 2. Data Sources

### 2.1 OpenAlex Database
**Schema**: `openalex.*`  
**Key Tables**:
- `authors` - Author profiles and metadata
- `works` - Publications (articles, papers, etc.)
- `works_authorships` - Author-Work relationships with positions
- `institutions` - Academic/research institutions
- `concepts` - Legacy concept taxonomy
- `topics` - Modern hierarchical topic system (topic → subfield → field → domain)
- `sources` - Journals, conferences, repositories
- `publishers` - Publishing organizations
- `works_referenced_works` - Citation network
- `works_related_works` - Related work connections

**Filtering Criteria**: 
- Material Science domain/field/subfield (TBD: specific topic IDs)
- Date range: TBD (recommend: last 10-20 years for manageability)

### 2.2 USPTO Patent Database
**Schema**: `uspto.*`  
**Key Tables**:
- `target_patent` - Patent documents and metadata
- `inventors_raw` - Inventor information
- `institute_match` / `new_institute_match` - Institution affiliations
- `patent_cite_pubs` - Patents citing publications
- `topic_match` / `subfield_match` / `field_match` / `domain_match` - Classification to topic mappings
- Various aggregated tables (`*_patent`, `*_patent1`, `*_patent2`)

**Filtering Criteria**:
- CPC/IPC classifications related to Material Science (TBD: specific symbols)
- Date range: TBD (align with OpenAlex date range)

---

## 3. Graph Schema

### 3.1 Node Types

| Node Label | Key Properties | Unique Identifier |
|------------|----------------|-------------------|
| Person | name, orcid (optional), type (author/inventor/both) | composite or generated ID |
| Work | id, doi, title, type, publication_date, year, cited_by_count, is_oa | OpenAlex ID |
| Patent | id, patent_document_id, country, year, application_date, issue_date, title, section_symbol, class_symbol, subclass_symbol, group_symbol | USPTO ID |
| Institution | id, ror, display_name, country_code, type | ROR ID or OpenAlex ID |
| Concept | id, display_name, level, wikidata, works_count | OpenAlex ID |
| Topic | id, display_name, field, subfield, domain | OpenAlex ID |
| Source | id, issn_l, issn, display_name | OpenAlex ID |
| Publisher | id, display_name, hierarchy_level | OpenAlex ID |
| Classification | id, symbol, name, type (section/class/subclass/group), description | CPC/IPC symbol |

### 3.2 Relationship Types

| Relationship | From → To | Direction | Properties | Notes |
|--------------|-----------|-----------|------------|-------|
| COAUTHORED_WITH | Person → Person | Bidirectional | work_count, works[] (optional) | Derived from shared works |
| AUTHORED | Person → Work | Directed (reverse: AUTHORED_BY) | position (first/middle/last) | From authorships |
| INVENTED | Person → Patent | Directed (reverse: INVENTED_BY) | - | From inventors |
| AFFILIATED_WITH | Person → Institution | Directed | year, context (author/inventor) | Time-sensitive affiliation |
| CITED | Work → Work | Directed (reverse: CITED_BY) | - | Academic citations |
| CITED | Patent → Patent | Directed (reverse: CITED_BY) | - | Patent citations |
| CITED | Patent → Work | Directed (reverse: CITED_BY) | - | Cross-domain citations |
| DISCUSSED | Work → Concept | Directed | score | Legacy concept tagging |
| TAGGED_WITH | Work → Topic | Directed | score | Modern topic tagging |
| PUBLISHED_IN | Work → Source | Directed | volume, issue | Publication venue |
| PUBLISHED_BY | Source → Publisher | Directed | - | Source-publisher relationship |
| PARENT_OF | Publisher → Publisher | Directed (reverse: CHILD_OF) | - | Publisher hierarchy |
| ASSOCIATED_WITH | Institution → Institution | Bidirectional | relationship_type | Institutional relationships |
| ASSIGNED_TO | Patent → Institution | Directed | - | Patent assignee |
| CLASSIFIED_BY | Patent → Classification | Directed | role (primary/secondary) | Patent classification |
| MAPS_TO | Topic → Classification | Bidirectional | confidence, method | Topic-classification alignment |
| MAPS_TO | Concept → Classification | Bidirectional | confidence, method | Concept-classification alignment |

**Note**: All directed relationships have implicit reverse edges for traversal optimization.

### 3.3 Indexes and Constraints
- **Unique constraints** on all node IDs
- **Indexes** on:
  - Person.name, Person.orcid
  - Work.doi, Work.year
  - Patent.patent_document_id, Patent.year
  - Institution.ror, Institution.country_code
  - Topic/Concept/Classification IDs and names
  - All timestamp/year fields for temporal queries

---

## 4. ETL Pipeline Requirements

### 4.1 Extract Phase

#### 4.1.1 Material Science Filtering
- **Objective**: Identify Material Science publications and patents
- **Method**: 
  - OpenAlex: Filter by Topic/Concept IDs in Material Science domain
  - USPTO: Filter by relevant CPC/IPC classification symbols
- **Deliverable**: SQL queries or scripts to extract relevant subsets
- **Output**: Intermediate tables or CSV exports

#### 4.1.2 Data Extraction
- **Source**: PostgreSQL databases (openalex, uspto schemas)
- **Approach**: 
  - Local testing: Small subset (e.g., 10K works, 1K patents)
  - Production: Batch processing for full Material Science subset
- **Tools**: Python (psycopg3), pandas for data handling
- **Output Format**: Parquet or CSV files for intermediate storage

### 4.2 Transform Phase

#### 4.2.1 Entity Resolution
**Person Unification Challenge**:
- **Problem**: Match inventors (USPTO) with authors (OpenAlex)
- **Approach Options**:
  1. Exact name matching + institution matching
  2. Fuzzy name matching with similarity scoring
  3. ORCID linking where available
  4. External disambiguation service (if available)
- **Deliverable**: Person entity resolution module
- **Output**: Unified Person entities with source tracking (author/inventor/both)

#### 4.2.2 Institution Matching
- **Problem**: Align USPTO institution names with OpenAlex ROR IDs
- **Approach**: 
  - Use existing `institute_match` table
  - Apply fuzzy matching for unmatched institutions
  - Manual curation for high-value ambiguous cases
- **Deliverable**: Institution mapping table

#### 4.2.3 Cross-Domain Topic Mapping
**Classification ↔ Topic/Concept Mapping Challenge**:
- **Problem**: Map patent CPC/IPC classifications to OpenAlex Topics/Concepts
- **Approach Options**:
  1. Use existing `*_match` tables (topic_match, subfield_match, etc.)
  2. Semantic similarity using embeddings (title/abstract/claims)
  3. Manual expert mapping for top-level categories
  4. Hybrid approach
- **Deliverable**: Topic-Classification mapping module with confidence scores
- **Output**: MAPS_TO relationships with confidence and method attributes

#### 4.2.4 Data Cleaning & Validation
- **Tasks**:
  - Handle missing values (DOIs, ORCIDs, dates)
  - Normalize dates to year granularity
  - Validate citation networks (no self-loops, valid IDs)
  - Deduplicate entities
  - Validate cross-references between tables
- **Deliverable**: Data validation reports and cleaned datasets

#### 4.2.5 Graph Formatting
- **Tasks**:
  - Convert relational data to node/edge lists
  - Generate unique IDs where needed (Person entities)
  - Create reverse relationships
  - Format properties as Neo4j-compatible types
- **Output**: 
  - Node CSV files (one per label)
  - Relationship CSV files (one per type)
  - Neo4j import headers

### 4.3 Load Phase

#### 4.3.1 Neo4j Setup
- **Environment**: Local Neo4j instance for testing, cloud/server for production
- **Configuration**:
  - Memory settings for large imports
  - Batch import configuration
  - Index and constraint definitions

#### 4.3.2 Data Import
- **Method**: 
  - `neo4j-admin import` for initial bulk load (preferred for large datasets)
  - `LOAD CSV` for incremental updates
  - Python driver (neo4j-python) for programmatic control
- **Batching Strategy**: 
  - Batch size: 10K-100K records per transaction
  - Parallel loading where possible
- **Error Handling**: 
  - Logging of failed imports
  - Rollback strategy for partial failures
  - Validation queries post-import

#### 4.3.3 Post-Load Processing
- **Tasks**:
  - Create indexes and constraints
  - Compute derived properties (e.g., citation counts)
  - Generate COAUTHORED_WITH relationships from AUTHORED
  - Validate graph integrity (orphaned nodes, broken relationships)
  - Performance testing of key queries

---

## 5. Code Requirements

### 5.1 Code Organization
```
project/
├── config/
│   ├── database.yaml          # DB connection configs
│   ├── filters.yaml            # Material Science filter criteria
│   └── neo4j.yaml              # Neo4j connection & settings
├── extract/
│   ├── openalex_extractor.py   # OpenAlex extraction
│   ├── uspto_extractor.py      # USPTO extraction
│   └── filters.sql             # SQL filter queries
├── transform/
│   ├── person_resolver.py      # Person entity resolution
│   ├── institution_matcher.py  # Institution matching
│   ├── topic_mapper.py         # Topic-Classification mapping
│   ├── graph_formatter.py      # Convert to graph format
│   └── validators.py           # Data validation
├── load/
│   ├── neo4j_loader.py         # Neo4j import scripts
│   ├── schema_setup.py         # Create constraints/indexes
│   └── post_load.py            # Post-load processing
├── utils/
│   ├── db_utils.py             # Database connection helpers
│   ├── logging.py              # Logging configuration
│   └── helpers.py              # Common utilities
├── tests/
│   ├── test_extract.py
│   ├── test_transform.py
│   └── test_load.py
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_filtering_analysis.ipynb
│   ├── 03_person_resolution.ipynb
│   └── 04_graph_analysis.ipynb
├── scripts/
│   ├── run_local_test.sh       # Local subset processing
│   └── run_production.sh       # Full batch processing
├── requirements.txt
├── README.md
└── main.py                     # Orchestration script
```

### 5.2 Local Testing vs Production
- **Local Mode**:
  - Subset size: ~10K works, ~1K patents
  - Single-threaded processing
  - Verbose logging
  - Intermediate checkpoint files
- **Production Mode**:
  - Full Material Science subset
  - Parallel/batch processing
  - Progress bars and monitoring
  - Optimized for performance

### 5.3 Code Quality
- **Documentation**: Docstrings for all modules and functions
- **Type Hints**: Use Python type annotations
- **Error Handling**: Comprehensive try-except blocks with logging
- **Testing**: Unit tests for critical functions
- **Version Control**: Git with meaningful commit messages
- **Dependencies**: Pinned versions in requirements.txt

---

## 6. Deliverables

### 6.1 Code Deliverables
1. **ETL Pipeline Code**: Modular, documented, tested
2. **Configuration Files**: Database connections, filter criteria
3. **Neo4j Schema Scripts**: Cypher queries for schema setup
4. **Documentation**: README with setup instructions, architecture docs
5. **Jupyter Notebooks**: Exploratory analysis and validation

### 6.2 Data Deliverables
1. **Filtered Datasets**: Intermediate CSV/Parquet files
2. **Entity Resolution Tables**: Person mappings, institution mappings
3. **Neo4j Database**: Populated knowledge graph
4. **Data Quality Report**: Statistics on nodes, relationships, coverage

### 6.3 Analysis Deliverables
1. **Graph Statistics**: Node counts, relationship distributions, degree distributions
2. **Sample Queries**: Cypher queries demonstrating graph capabilities
3. **Visualization**: Example graph visualizations (Neo4j Bloom or Python)
4. **Documentation**: Final report describing decisions, challenges, results

---

## 7. Technical Challenges & Mitigation

### 7.1 Person Entity Resolution
**Challenge**: Matching inventors to authors across databases  
**Mitigation**:
- Start with exact matches (ORCID, name+institution)
- Use fuzzy matching with manual review for high-impact entities
- Accept some ambiguity; document resolution confidence
- Consider iterative refinement

### 7.2 Cross-Domain Topic Mapping
**Challenge**: Aligning patent classifications with academic topics  
**Mitigation**:
- Leverage existing USPTO topic_match tables
- Use semantic embeddings for unmapped classifications
- Create confidence scores for all mappings
- Manual expert review for top-level mappings

### 7.3 Scale & Performance
**Challenge**: Large dataset processing and graph traversal performance  
**Mitigation**:
- Use batch processing with checkpoints
- Optimize Neo4j indexes early
- Use `neo4j-admin import` for bulk loading
- Profile and optimize slow queries
- Consider graph projection for intensive analyses

### 7.4 Data Quality
**Challenge**: Missing data, inconsistencies, duplicates  
**Mitigation**:
- Comprehensive validation at each stage
- Document data quality issues
- Impute or flag missing critical fields
- Provide data quality metrics in final report

### 7.5 Temporal Alignment
**Challenge**: Aligning publication dates with patent dates  
**Mitigation**:
- Standardize to year granularity
- Use application_date for patents (vs issue_date) for fairer comparison
- Document temporal assumptions

---

## 8. Success Criteria

### 8.1 Minimum Viable Product (MVP)
- [ ] Material Science subset extracted from both databases
- [ ] Neo4j graph populated with core nodes (Work, Patent, Person, Institution)
- [ ] Core relationships established (AUTHORED, INVENTED, CITED, AFFILIATED_WITH)
- [ ] Basic entity resolution for Persons
- [ ] Documentation of pipeline

### 8.2 Target Goals
- [ ] All node types and relationships implemented
- [ ] Person entity resolution with >70% precision
- [ ] Topic-Classification mappings with confidence scores
- [ ] Comprehensive data quality report
- [ ] 10+ example Cypher queries demonstrating insights
- [ ] Performance-optimized graph (queries <1s for common patterns)

### 8.3 Stretch Goals
- [ ] Advanced person disambiguation using ML
- [ ] Real-time incremental updates
- [ ] Graph embeddings for similarity search
- [ ] Interactive visualization dashboard
- [ ] Published insights or analysis from the graph

---


## 9. Dependencies & Tools

### 10.1 Python Libraries
```
# Database & Data Processing
psycopg==3.2.11        # PostgreSQL driver (from your notebook)
psycopg-binary==3.2.11
pandas>=2.0.0
pyarrow>=12.0.0        # Parquet support
numpy>=1.24.0

# Neo4j
neo4j>=5.14.0          # Python driver
py2neo>=2021.2.3       # Alternative driver (optional)

# Entity Resolution & Matching
fuzzywuzzy>=0.18.0     # String matching
python-Levenshtein>=0.21.0
rapidfuzz>=3.0.0       # Faster fuzzy matching

# NLP & Embeddings (if using semantic matching)
sentence-transformers>=2.2.0
scikit-learn>=1.3.0

# Utilities
python-dotenv>=1.0.0   # Environment variables
pyyaml>=6.0            # Config files
tqdm>=4.65.0           # Progress bars
loguru>=0.7.0          # Better logging

# Visualization (optional)
matplotlib>=3.7.0
seaborn>=0.12.0
networkx>=3.1          # Graph analysis

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
```

### 9.2 External Tools
- **PostgreSQL 13+**: Source databases
- **Neo4j 5.x**: Target graph database
- **Jupyter**: Notebooks for exploration

### 9.3 Hardware Recommendations
- **Local Testing**: 8GB RAM, 50GB disk
- **Production**: 16GB+ RAM, 200GB+ disk, multi-core CPU

---

## 10. Risk Management

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Material Science filtering too restrictive/broad | High | High | Iterative refinement; start conservative |
| Person entity resolution low precision | High | Medium | Accept ambiguity; focus on high-confidence matches |
| Neo4j performance issues at scale | Medium | High | Early optimization; consider graph projections |
| Topic-Classification mapping intractable | Medium | Medium | Use existing mappings; manual curation for gaps |
| Timeline overrun | Medium | High | Prioritize MVP; defer stretch goals |
| Data quality issues | High | Medium | Validation at each stage; document limitations |

---

## 11. Open Questions

1. **Material Science Scope**: Specific OpenAlex Topic IDs or CPC symbols to define "Material Science"?
2. **Date Range**: What years for publications and patents?
3. **Subset Size**: Target number of nodes/relationships for production graph?
4. **Person Resolution**: What precision/recall tradeoff is acceptable?
5. **Topic Mapping**: Should we focus on coarse-grained (field/domain) or fine-grained (topic/classification) mappings?
6. **Citation Networks**: Should we include only direct citations or follow chains?
7. **Collaboration**: Are there domain experts available for validation?
8. **Deployment**: Is the final Neo4j database for local analysis or shared access?

---

## Notes

- This is a living document; update as project evolves
- Prioritize decisions that unblock downstream work
- Document all major decisions and rationale
- Maintain flexibility for pivots based on data realities