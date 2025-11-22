import psycopg
import csv
from lxml import etree
import os
from concurrent.futures import ProcessPoolExecutor

# --- CONFIGURATION ---
DB_CONFIG = {
    "dbname": "postgres",
    "user": "",      # CHANGE THIS
    "password": "",  # CHANGE THIS
    "host": "awesome-compute.sdsc.edu",          # CHANGE THIS
    "port": "5432"
}

# How many years to process in parallel?
# Set this to the number of CPU cores you have (e.g., 4, 8, 16)
MAX_WORKERS = 30

MATSCI_CPC_CODES = ['C01', 'C03', 'C04', 'C08', 'C21', 'C22', 'C30', 'B82']
MATSCI_USPC_CLASSES = ['29', '75', '148', '420', '423', '427', '428']

def build_sql_filter(year):
    conditions = []
    for code in MATSCI_CPC_CODES:
        conditions.append(f"content LIKE '%<classification-cpc%>{code}%'")
        conditions.append(f"content LIKE '%<B51%>{code}%'")

    if year < 2015:
        for cls in MATSCI_USPC_CLASSES:
            conditions.append(f"content LIKE '%<classification-us>%{cls}/%'")
            conditions.append(f"content LIKE '%<class>{cls}</class>%'")
            conditions.append(f"content LIKE '%<B52%>{cls}%'")
    return " OR ".join(conditions)

def parse_patent_xml(xml_content, year):
    # ... (Same parsing logic as before) ...
    extracted_rows = []
    try:
        if isinstance(xml_content, str):
            xml_content = xml_content.encode('utf-8')

        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(xml_content, parser=parser)

        patent_id = root.findtext('.//publication-reference/document-id/doc-number')
        if not patent_id:
            patent_id = root.findtext('.//B110/DNUM/PDAT')

        if not patent_id: return []

        # Inventors
        inventors = root.xpath('//inventor | //B721')
        for inv in inventors:
            first = inv.findtext('.//first-name') or inv.findtext('.//NAM/FNM/PDAT')
            last = inv.findtext('.//last-name') or inv.findtext('.//NAM/SNM/STEXT/PDAT')
            city = inv.findtext('.//city') or inv.findtext('.//ADR/CITY/PDAT')
            state = inv.findtext('.//state')
            country = inv.findtext('.//country') or inv.findtext('.//ADR/CTRY/PDAT')

            extracted_rows.append({
                'patent_id': patent_id, 'patent_year': year, 'role': 'inventor',
                'entity_name': f"{first} {last}" if first and last else None,
                'first_name': first, 'last_name': last, 'org_name': None,
                'city': city, 'state': state, 'country': country
            })

        # Assignees
        assignees = root.xpath('//assignee | //B731')
        for ass in assignees:
            org_name = ass.findtext('.//orgname') or ass.findtext('.//NAM/ONM/STEXT/PDAT')
            city = ass.findtext('.//city') or ass.findtext('.//ADR/CITY/PDAT')
            country = ass.findtext('.//country') or ass.findtext('.//ADR/CTRY/PDAT')

            extracted_rows.append({
                'patent_id': patent_id, 'patent_year': year, 'role': 'assignee',
                'entity_name': org_name, 'first_name': None, 'last_name': None,
                'org_name': org_name, 'city': city, 'state': None, 'country': country
            })

    except Exception:
        return []
    return extracted_rows

def process_year(year):
    """
    This function runs in its own separate process.
    It opens its OWN database connection and writes its OWN csv file.
    """
    output_filename = f"patents_part_{year}.csv"
    print(f"[{year}] Starting worker...")

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            filter_sql = build_sql_filter(year)
            query = f"SELECT content FROM uspto_xml.us_patents_raw WHERE year = {year} AND ({filter_sql})"

            with open(output_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['patent_id', 'patent_year', 'role', 'entity_name',
                              'first_name', 'last_name', 'org_name', 'city', 'state', 'country']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                # Server-side cursor for this specific year
                with conn.cursor(name=f"cursor_parallel_{year}") as cur:
                    cur.execute(query)
                    count = 0
                    while True:
                        rows = cur.fetchmany(2000)
                        if not rows: break

                        batch_data = []
                        for (xml_content,) in rows:
                            if not xml_content: continue
                            batch_data.extend(parse_patent_xml(xml_content, year))

                        if batch_data:
                            writer.writerows(batch_data)
                            count += len(batch_data)

            print(f"[{year}] Finished! Saved {count} rows.")
            return f"Year {year} Success: {count} rows"

    except Exception as e:
        print(f"[{year}] FAILED: {e}")
        return f"Year {year} Failed: {e}"

def main():
    # Range: 2002 to 2024
    years_to_process = list(range(2002, 2025))

    print(f"Starting pool with {MAX_WORKERS} workers for {len(years_to_process)} years...")

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(process_year, years_to_process)

    for res in results:
        print(res)

    print("All years done. Now merging files...")

    # Merge all parts into one file
    with open("material_science_patents_FINAL.csv", "w", encoding="utf-8") as outfile:
        # Write header once
        outfile.write("patent_id,patent_year,role,entity_name,first_name,last_name,org_name,city,state,country\n")
        for year in years_to_process:
            fname = f"patents_part_{year}.csv"
            if os.path.exists(fname):
                with open(fname, "r", encoding="utf-8") as infile:
                    next(infile) # Skip header of part file
                    for line in infile:
                        outfile.write(line)
                os.remove(fname) # Cleanup

if __name__ == "__main__":
    main()
