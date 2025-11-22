import psycopg
import csv
from lxml import etree
import os
from concurrent.futures import ProcessPoolExecutor
import time
from datetime import datetime

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


def _format_seconds(sec: float) -> str:
    """Return H:MM:SS for seconds."""
    return time.strftime('%H:%M:%S', time.gmtime(sec))

def build_sql_filter(year):
    conditions = []
    for code in MATSCI_CPC_CODES:
        conditions.append(f"content LIKE '%<classification-cpc%>{code}%'")
        conditions.append(f"content LIKE '%<B51%>{code}%'")

    if year < 2013:
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
    start_monotonic = time.monotonic()
    start_ts = datetime.now().isoformat()
    print(f"[{year}] Starting worker at {start_ts}...")

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

            elapsed = time.monotonic() - start_monotonic
            print(f"[{year}] Finished! Saved {count} rows. Time taken: {_format_seconds(elapsed)}")
            return f"Year {year} Success: {count} rows in {_format_seconds(elapsed)}"

    except Exception as e:
        elapsed = time.monotonic() - start_monotonic
        print(f"[{year}] FAILED after {_format_seconds(elapsed)}: {e}")
        return f"Year {year} Failed after {_format_seconds(elapsed)}: {e}"


def main():
    # Range: 2002 to 2024
    # years_to_process = list(range(2002,2025))

    # Remaining years
    years_to_process = [2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2021, 2023, 2024]

    overall_start = time.monotonic()
    print(f"{datetime.now().isoformat()} - Starting pool with {MAX_WORKERS} workers for {len(years_to_process)} years...")

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

    overall_elapsed = time.monotonic() - overall_start
    print(f"All processing and merge complete. Total time: {_format_seconds(overall_elapsed)}")

if __name__ == "__main__":
    main()


# After matching with OpenAlex views, you can use this query to query specific patents
# uspto_xml.us_patents_raw has mostly empty patent_id column (97% empty) but the xml extracted result should have patent_id
# filled since we extract it from the xml content. 06387940 is example patent_id.

# SELECT * FROM uspto_xml.us_patents_raw
# WHERE content LIKE '%<doc-number>06387940</doc-number>%';
