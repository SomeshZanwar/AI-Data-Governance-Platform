"""
Run once: python sample_data/generate_governance_data.py
Generates all sample CSVs for the Data Reliability Control Center demo.
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

os.makedirs("sample_data", exist_ok=True)
np.random.seed(42)
now = datetime.utcnow()

# ── Dataset registry ───────────────────────────────────────────────────────────
datasets = pd.DataFrame([
    {"dataset_id":"DS001","name":"sales_metrics",         "owner":"analytics-team",  "tier":"Gold",  "tags":"revenue,finance",   "created_at":str(now-timedelta(days=180))},
    {"dataset_id":"DS002","name":"user_events",           "owner":"data-engineering","tier":"Silver","tags":"users,behavior",     "created_at":str(now-timedelta(days=90))},
    {"dataset_id":"DS003","name":"inventory_data",        "owner":"ops-team",        "tier":"Silver","tags":"ops,inventory",      "created_at":str(now-timedelta(days=60))},
    {"dataset_id":"DS004","name":"experiment_results",    "owner":"product-team",    "tier":"Bronze","tags":"experiments,product","created_at":str(now-timedelta(days=30))},
    {"dataset_id":"DS005","name":"customer_profiles",     "owner":"marketing-team",  "tier":"Gold",  "tags":"customers,PII",      "created_at":str(now-timedelta(days=120))},
    {"dataset_id":"DS006","name":"pipeline_log",          "owner":"data-engineering","tier":"Bronze","tags":"ops,logs",           "created_at":str(now-timedelta(days=14))},
])

# ── Rules catalog ──────────────────────────────────────────────────────────────
rules = pd.DataFrame([
    {"rule_id":"R001","dataset_id":"DS001","rule_name":"row_count_check",     "rule_type":"completeness","threshold":10000, "severity":"critical"},
    {"rule_id":"R002","dataset_id":"DS001","rule_name":"null_check_revenue",  "rule_type":"validity",    "threshold":0.01,  "severity":"high"},
    {"rule_id":"R003","dataset_id":"DS001","rule_name":"freshness_check",     "rule_type":"timeliness",  "threshold":24,    "severity":"high"},
    {"rule_id":"R004","dataset_id":"DS002","rule_name":"null_check_user_id",  "rule_type":"validity",    "threshold":0.0,   "severity":"critical"},
    {"rule_id":"R005","dataset_id":"DS002","rule_name":"duplicate_user_check","rule_type":"uniqueness",  "threshold":0.01,  "severity":"medium"},
    {"rule_id":"R006","dataset_id":"DS002","rule_name":"schema_validation",   "rule_type":"conformity",  "threshold":0,     "severity":"critical"},
    {"rule_id":"R007","dataset_id":"DS003","rule_name":"row_count_check",     "rule_type":"completeness","threshold":500,   "severity":"medium"},
    {"rule_id":"R008","dataset_id":"DS004","rule_name":"experiment_id_check", "rule_type":"validity",    "threshold":0.0,   "severity":"high"},
    {"rule_id":"R009","dataset_id":"DS005","rule_name":"pii_mask_check",      "rule_type":"security",    "threshold":0.0,   "severity":"critical"},
    {"rule_id":"R010","dataset_id":"DS005","rule_name":"freshness_check",     "rule_type":"timeliness",  "threshold":48,    "severity":"high"},
    {"rule_id":"R011","dataset_id":"DS006","rule_name":"log_completeness",    "rule_type":"completeness","threshold":100,   "severity":"low"},
])

# ── Rule runs (7 days of history) ─────────────────────────────────────────────
runs = []
for _, rule in rules.iterrows():
    for day_offset in range(7, 0, -1):
        run_time = now - timedelta(days=day_offset)
        if rule["rule_id"] in ["R004", "R006"] and day_offset <= 2:
            status, actual, msg = "FAILED", 0.05, "Null/schema check failed"
        elif rule["rule_id"] == "R002" and day_offset == 4:
            status, actual, msg = "FAILED", 0.023, "Revenue null rate spike"
        else:
            status, actual, msg = "PASSED", round(rule["threshold"] * 0.1, 4), "Check passed"
        runs.append({
            "run_id":     f"{rule['rule_id']}-D{day_offset}",
            "rule_id":    rule["rule_id"],
            "dataset_id": rule["dataset_id"],
            "run_at":     str(run_time),
            "status":     status,
            "actual":     actual,
            "message":    msg,
        })
runs_df = pd.DataFrame(runs)

# ── Health scores ──────────────────────────────────────────────────────────────
health = []
for _, ds in datasets.iterrows():
    ds_runs = runs_df[runs_df["dataset_id"] == ds["dataset_id"]]
    total   = len(ds_runs)
    passed  = (ds_runs["status"] == "PASSED").sum()
    score   = round(passed / total, 2) if total > 0 else 1.0
    health.append({
        "dataset_id":   ds["dataset_id"],
        "dataset_name": ds["name"],
        "health_score": score,
        "total_runs":   total,
        "passed_runs":  int(passed),
        "failed_runs":  int(total - passed),
    })
health_df = pd.DataFrame(health)

# ── Incidents ──────────────────────────────────────────────────────────────────
incidents = pd.DataFrame([
    {
        "incident_id": "INC001",
        "dataset_id":  "DS002",
        "rule_id":     "R004",
        "detected_at": str(now - timedelta(hours=18)),
        "status":      "OPEN",
        "severity":    "critical",
        "title":       "Null user_id values detected in user_events",
        "explanation": (
            "The null_check_user_id rule failed. Approximately 5% of rows "
            "have null user_id values. This breaks downstream attribution models "
            "and experiment analysis pipelines. Immediate investigation required."
        ),
    },
    {
        "incident_id": "INC002",
        "dataset_id":  "DS002",
        "rule_id":     "R006",
        "detected_at": str(now - timedelta(hours=16)),
        "status":      "OPEN",
        "severity":    "critical",
        "title":       "Schema validation failure in user_events",
        "explanation": (
            "Schema validation failed — the 'session_id' column type changed "
            "from VARCHAR to INTEGER. This is a breaking change affecting 3 "
            "downstream dbt models. Rollback or schema migration needed."
        ),
    },
    {
        "incident_id": "INC003",
        "dataset_id":  "DS001",
        "rule_id":     "R002",
        "detected_at": str(now - timedelta(days=4, hours=2)),
        "status":      "RESOLVED",
        "severity":    "high",
        "title":       "Revenue null rate spike in sales_metrics (resolved)",
        "explanation": (
            "Revenue null rate reached 2.3% on Jan 22, caused by a pipeline "
            "ingestion gap during a scheduled maintenance window. Pipeline "
            "restarted at 14:30 UTC and backfill completed. Resolved."
        ),
    },
])

# ── Save ───────────────────────────────────────────────────────────────────────
datasets.to_csv("sample_data/datasets.csv",      index=False)
rules.to_csv("sample_data/rules.csv",            index=False)
runs_df.to_csv("sample_data/rule_runs.csv",      index=False)
health_df.to_csv("sample_data/health_scores.csv",index=False)
incidents.to_csv("sample_data/incidents.csv",    index=False)

for f in ["datasets","rules","rule_runs","health_scores","incidents"]:
    print(f"✓ sample_data/{f}.csv")
print("Done.")