import json
import os
from pathlib import Path
import psycopg2
from psycopg2.extras import Json, execute_batch
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path("data_raw/github_archive")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "governance"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "")
}

BATCH_SIZE = 5000


def parse_event(line):
    # Remove null bytes that break PostgreSQL
    line = line.replace("\x00", "").replace("\\u0000", "")

    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None

    actor = obj.get("actor") or {}
    repo = obj.get("repo") or {}
    org = obj.get("org") or {}

    payload = obj.get("payload")
    raw = obj

    # extra protection
    payload = json.dumps(payload).replace("\x00", "")
    raw = json.dumps(raw).replace("\x00", "")

    return (
        str(obj.get("id")),
        obj.get("type"),
        actor.get("id"),
        actor.get("login"),
        repo.get("id"),
        repo.get("name"),
        obj.get("created_at"),
        obj.get("public"),
        Json(json.loads(payload)),
        org.get("id"),
        org.get("login"),
        Json(json.loads(raw)),
    )


def main():

    files = sorted(DATA_DIR.glob("*.json"))

    if not files:
        raise Exception("No JSON files found")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    insert_sql = """
    INSERT INTO raw.github_events (
        event_id,
        event_type,
        actor_id,
        actor_login,
        repo_id,
        repo_name,
        created_at,
        is_public,
        payload,
        org_id,
        org_login,
        raw_json
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    batch = []
    total = 0

    for file in files:
        print("Processing:", file)

        with open(file, "r", encoding="utf8") as f:
            for line in f:

                record = parse_event(line)

                if record:
                    batch.append(record)

                if len(batch) >= BATCH_SIZE:
                    execute_batch(cur, insert_sql, batch)
                    conn.commit()
                    total += len(batch)
                    batch = []
                    print("Inserted", total)

    if batch:
        execute_batch(cur, insert_sql, batch)
        conn.commit()
        total += len(batch)

    print("Done. Total rows:", total)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()