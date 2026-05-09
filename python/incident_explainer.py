import os
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "governance"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_open_incidents(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                i.incident_id,
                i.rule_id,
                i.severity,
                i.status,
                i.opened_at,
                rc.rule_name,
                rc.rule_type,
                rc.rule_sql
            FROM governance.incidents i
            JOIN governance.rule_catalog rc
              ON i.rule_id = rc.rule_id
            WHERE i.status = 'open'
            ORDER BY i.opened_at DESC
        """)
        return cur.fetchall()


def explain_incident(incident):

    explanation = f"""
INCIDENT {incident['incident_id']}

Rule Failed: {incident['rule_name']}
Severity: {incident['severity']}

Explanation:
This governance rule detected a data quality issue.

The rule SQL indicates a constraint violation in the dataset.

Possible causes:
- upstream ingestion failure
- incomplete dimension loads
- delayed pipeline dependencies
- duplicate or missing keys

Recommended action:
1. inspect the affected dataset
2. validate upstream pipelines
3. reload the affected tables if necessary
"""

    return explanation.strip()

    return response.output_text.strip()


def main():
    conn = psycopg2.connect(**DB_CONFIG)

    incidents = get_open_incidents(conn)

    if not incidents:
        print("No open incidents found.")
        conn.close()
        return

    output_dir = Path("docs/incident_explanations")
    output_dir.mkdir(parents=True, exist_ok=True)

    for incident in incidents:
        explanation = explain_incident(incident)

        out_file = output_dir / f"incident_{incident['incident_id']}.md"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(f"# Incident {incident['incident_id']} Explanation\n\n")
            f.write(explanation)
            f.write("\n")

        print(f"Wrote {out_file}")

    conn.close()


if __name__ == "__main__":
    main()