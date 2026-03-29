# AI Data Governance Platform

**Analytics Reliability System for Monitoring Data Quality, Detecting Incidents, and Explaining Failures**

An end-to-end data governance platform built using PostgreSQL, dbt, Python, and Power BI.
This system enables analytics teams to proactively monitor dataset health, detect failures, and understand root causes using AI-assisted explanations.

---

# Business Problem

Modern data stacks rely on multiple pipelines and derived datasets.
Without governance controls, data quality issues can silently propagate and break downstream dashboards, ML models, and decision-making.

When data quality breaks:

Dashboards show incorrect metrics
ML models degrade silently
Stakeholders lose trust

Most teams detect issues after damage is done.

---

# System Architecture

The system follows a layered data platform architecture.

![Architecture](docs/architecture_diagram.png)

### Data Flow


GitHub Archive Dataset
↓
Python Ingestion Pipeline
↓
PostgreSQL Raw Storage
↓
dbt Transformation Layer
↓
Analytics Layer (fact & dimension tables)
↓
Governance Engine (rules, incidents, health scoring)
↓
AI Explanation Layer
↓
Power BI Monitoring Dashboard


---

# Core Features

### Data Ingestion
- Python pipeline ingests GitHub Archive events into PostgreSQL
- Handles large-scale event data for analytics processing

### Analytics Modeling (dbt)
Structured transformation layer with fact and dimension models:
- `fact_commits`
- `fact_pull_requests`
- `fact_issues`
- `dim_repository`
- `dim_user`
- `dim_date`

### Governance Metadata Layer
Central system to track datasets, rules, and incidents.

Core Tables:

- `dataset_registry`
- `rule_catalog`
- `rule_runs`
- `dataset_health_scores`
- `incidents`

### Automated Rule Engine
Python-based rule execution framework:

- Runs data quality checks across datasets
- Logs rule outcomes and failures
- Enables scalable rule definitions

Example rules include:

- Duplicate commit detection
- Null commit checks
- Foreign key validation
- Duplicate issue detection

### Dataset Health Scoring
Each dataset is assigned a reliability score:

health_score = 1 - (failed_rules / total_rules)

Enables quick identification of unstable datasets.

### Incident Detection

- Rule failures automatically generate incidents
- Tracks severity, status, and timestamps
- Provides structured monitoring of data issues
Example:

incident_id | rule_id | severity | status | opened_at


### AI Incident Explanation

- Uses LLM-based scripts to explain data quality failures
- Converts technical errors into interpretable insights
- Reduces debugging time for analysts and engineers

### Governance Monitoring Dashboard
Power BI dashboard visualizes:


- Dataset health trends
- Rule failure patterns
- Active governance incidents
- System reliability metrics


---

# Tech Stack

| Component | Technology |
|--------|-------------|
| Data Source | GitHub Archive |
| Ingestion | Python |
| Storage | PostgreSQL |
| Transformation | dbt |
| Governance Engine | Python + SQL |
| AI Layer | OpenAI API |
| Monitoring | Power BI |



---

# Project Structure

```text
ai-data-governance-platform
│
├── dashboard
│ └── governance_dashboard.png
│
├── docs
│ ├── architecture_diagram.png
│ ├── governance_architecture.md
│ ├── rule_dictionary.md
│ ├── scalability.md
│ └── incident_explanations
│
├── github_governance_dbt
│ ├── models
│ ├── macros
│ ├── seeds
│ └── dbt_project.yml
│
├── python
│ ├── ingest_github_archive.py
│ ├── rule_runner.py
│ ├── incident_explainer.py
│ ├── governance_assistant.py
│ └── rag_assistant.py
│
├── sql
│ └── governance_schema.sql
│
├── requirements.txt
└── README.md
```

---

# Example Governance Rule

Ensuring commit SHA uniqueness:


SELECT commit_sha
FROM mart_mart.fact_commits
GROUP BY commit_sha
HAVING COUNT(*) > 1


---

# Example Incident Output

When a rule fails, the system logs an incident:


incident_id | rule_id | severity | status | opened_at


This enables teams to track governance issues and prioritize fixes.

---

# Why This Project Matters

This project shifts governance from manual debugging → automated monitoring.

It demonstrates how analytics teams can:

- Treat datasets as production systems
- Detect failures early
- Quantify data reliability
- Improve trust in analytics outputs

# Future Improvements

Potential enhancements:

- Workflow orchestration (Airflow / Dagster)
- Real-time anomaly detection
- Alerting system (Slack / email)
- Integration with data catalogs
- RAG-based governance assistant

---

# License

For portfolio and educational use.
