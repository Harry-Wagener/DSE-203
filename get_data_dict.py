import psycopg
import os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

q_text = """
SELECT 
    cols.table_schema,
    cols.table_name,
    cols.column_name,
    cols.ordinal_position,
    cols.data_type,
    cols.character_maximum_length,
    cols.is_nullable,
    cols.column_default,
    CASE 
        WHEN pk.column_name IS NOT NULL THEN 'YES'
        ELSE 'NO'
    END AS is_primary_key,
    fk.foreign_table_schema,
    fk.foreign_table_name,
    fk.foreign_column_name
FROM information_schema.columns AS cols
LEFT JOIN (
    -- Primary keys
    SELECT 
        tc.table_schema,
        tc.table_name,
        kcu.column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'PRIMARY KEY'
) AS pk
  ON cols.table_schema = pk.table_schema
 AND cols.table_name = pk.table_name
 AND cols.column_name = pk.column_name
LEFT JOIN (
    -- Foreign keys
    SELECT 
        tc.table_schema,
        tc.table_name,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
     AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
) AS fk
  ON cols.table_schema = fk.table_schema
 AND cols.table_name = fk.table_name
 AND cols.column_name = fk.column_name
WHERE cols.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY cols.table_schema, cols.table_name, cols.ordinal_position;"""

with conn.cursor() as cur:
    cur.execute(q_text)
    rows = cur.fetchall()
    # Save results to a text file instead of printing
    out_path = os.path.join(os.path.dirname(__file__), "open_Alex_schema_tables.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            # If the row contains a single column (table_name) write that, else write the full row repr
            if len(row) == 1:
                f.write(f"{row[0]}\n")
            else:
                f.write(f"{row}\n")

conn.close()

