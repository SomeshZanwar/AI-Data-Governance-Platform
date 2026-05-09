from fastapi import FastAPI
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Data Governance API")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "governance")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

@app.get("/datasets")
def get_datasets():
    cur = conn.cursor()
    cur.execute("""
        SELECT dataset_id, table_name
        FROM governance.dataset_registry
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


@app.get("/rules")
def get_rules():
    cur = conn.cursor()
    cur.execute("""
        SELECT rule_id, rule_name, severity
        FROM governance.rule_catalog
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


@app.get("/incidents")
def get_incidents():
    cur = conn.cursor()
    cur.execute("""
        SELECT incident_id, rule_id, severity, status, opened_at
        FROM governance.incidents
        WHERE status='open'
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


@app.get("/health")
def get_dataset_health():
    cur = conn.cursor()
    cur.execute("""
        SELECT dataset_id, health_score, status
        FROM governance.dataset_health_scores
    """)
    rows = cur.fetchall()
    cur.close()
    return rows