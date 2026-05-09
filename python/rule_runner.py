import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "governance"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_rules(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT rule_id, rule_name, rule_sql, severity
            FROM governance.rule_catalog
            ORDER BY rule_id
        """)
        return cur.fetchall()


def run_rule(conn, rule):
    with conn.cursor() as cur:
        cur.execute(rule["rule_sql"])
        rows = cur.fetchall()
        rows_failed = len(rows)
        rows_checked = None  # optional metric

        status = "pass" if rows_failed == 0 else "fail"

        cur.execute("""
            INSERT INTO governance.rule_runs
            (rule_id, rows_checked, rows_failed, status)
            VALUES (%s,%s,%s,%s)
            RETURNING run_id
        """, (rule["rule_id"], rows_checked, rows_failed, status))

        run_id = cur.fetchone()[0]

        if rows_failed > 0:
            for r in rows[:50]:  # store up to 50 failing samples
                cur.execute("""
                    INSERT INTO governance.rule_failures
                    (run_id, failed_value, failure_reason)
                    VALUES (%s,%s,%s)
                """, (run_id, str(r), rule["rule_name"]))

        conn.commit()


def main():
    conn = psycopg2.connect(**DB_CONFIG)

    rules = get_rules(conn)

    print(f"Running {len(rules)} governance rules")

    for rule in rules:
        print("Running:", rule["rule_name"])
        run_rule(conn, rule)

    conn.close()
    print("All rules executed")


if __name__ == "__main__":
    main()