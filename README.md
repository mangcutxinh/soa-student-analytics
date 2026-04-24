# 🎓 SOA Student Analytics

> **Medallion Architecture** on Databricks — CSV ingestion → Bronze → Silver → Gold (Delta Lake)
> Microservices backend (WIP – Week 13)

---

## 📁 Project Structure

```
soa-student-analytics/
├── databricks/
│   ├── notebooks/
│   │   ├── 01_data_ingestion.py   ← Read CSV, validate schema
│   │   ├── 02_bronze_layer.py     ← Raw data → Delta Bronze
│   │   ├── 03_silver_layer.py     ← Clean / enrich → Delta Silver
│   │   ├── 04_gold_analytics.py   ← GPA, stats, ML features → Gold
│   │   └── 05_pipeline_runner.py  ← Orchestrator (used by Job)
│   └── jobs/
│       └── etl_pipeline_job.json  ← Databricks Job config
├── data/
│   └── mock/
│       └── student_score_dataset.csv   ← 300 students, 12 columns
├── services/                           ← Microservices (WIP – Week 13)
│   ├── student-service/
│   ├── score-service/
│   ├── analytics-service/
│   └── notification-service/
├── docs/
│   └── architecture/
│       └── soa_architecture_diagram.png
└── README.md
```

---

## ⚡ Quick Start

### 1 · Local Setup

```bash
git clone https://github.com/<your-username>/soa-student-analytics.git
cd soa-student-analytics
pip install pyspark delta-spark pandas
```

### 2 · Upload Data to Databricks

```
Databricks UI → Data → DBFS → FileStore
Upload: data/mock/student_score_dataset.csv
Result: dbfs:/FileStore/student_score_dataset.csv
```

---

## 🔗 GitHub → Databricks Integration (Git Repos)

### Step 1 — Generate GitHub Token
1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Scopes: `repo` ✅
3. Copy the token

### Step 2 — Link in Databricks
```
Databricks UI
→ User Settings (top right) → Git Integration
→ Provider: GitHub
→ Token: paste your token
→ Save
```

### Step 3 — Add Repo
```
Databricks → Repos → Add Repo
→ URL: https://github.com/<your-username>/soa-student-analytics
→ Provider: GitHub
→ Clone
```

Your repo is now at:
```
/Repos/<your-username>/soa-student-analytics/
```

### Step 4 — Update notebook paths in Job JSON
Open `databricks/jobs/etl_pipeline_job.json` and replace:
```
<your-username>  →  your actual Databricks username
```

---

## 🚀 Running the Pipeline

### Option A — Run notebooks manually (dev/test)

Open each notebook in Databricks and click **Run All** in order:
```
01 → 02 → 03 → 04
```

### Option B — Create a Job (production)

```bash
# Using Databricks CLI
pip install databricks-cli
databricks configure --token   # enter host + token

databricks jobs create --json-file databricks/jobs/etl_pipeline_job.json
```

Or via UI:
```
Databricks → Workflows → Jobs → Create Job → Import JSON
Paste contents of: databricks/jobs/etl_pipeline_job.json
```

### Option C — Run orchestrator notebook
Run `05_pipeline_runner.py` directly — it chains all stages.

---

## 🗄️ Delta Lake Paths

| Layer   | Path                              | Format        |
|---------|-----------------------------------|---------------|
| Staging | `dbfs:/delta/staging/student_scores` | Parquet    |
| Bronze  | `dbfs:/delta/bronze/student_scores`  | Delta Lake |
| Silver  | `dbfs:/delta/silver/student_scores`  | Delta Lake |
| Gold — GPA     | `dbfs:/delta/gold/student_gpa_summary` | Delta |
| Gold — Major   | `dbfs:/delta/gold/major_analytics`     | Delta |
| Gold — Subject | `dbfs:/delta/gold/subject_analytics`   | Delta |
| Gold — ML      | `dbfs:/delta/gold/ml_features`         | Delta |
| Pipeline logs  | `dbfs:/delta/pipeline_runs`            | Delta |

---

## 📊 Dataset Schema

`student_score_dataset.csv` — 300 rows, 12 columns

| Column            | Type    | Description               |
|-------------------|---------|---------------------------|
| `student_id`      | String  | Unique ID (SV0001…)       |
| `full_name`       | String  | Vietnamese full name       |
| `major`           | String  | Faculty / major            |
| `year_of_study`   | Integer | 1–4                        |
| `subject`         | String  | Course name                |
| `midterm_score`   | Double  | 0–10                       |
| `final_score`     | Double  | 0–10                       |
| `attendance_rate` | Double  | 0.0–1.0                    |
| `gpa`             | Double  | Computed (raw)             |
| `grade`           | String  | A / B / C / D / F          |
| `exam_date`       | String  | yyyy-MM-dd                 |
| `semester`        | String  | e.g. `2024-1`             |

**GPA formula:** `(midterm × 0.30 + final × 0.70) × attendance_rate`

---

## 🏗️ Pipeline Architecture

```
CSV (DBFS)
    │
    ▼  01_data_ingestion (schema validation, null checks, score range)
Staging (Parquet)
    │
    ▼  02_bronze_layer (MERGE by hash — idempotent, partitioned by semester/grade)
Delta Bronze  /delta/bronze/
    │
    ▼  03_silver_layer (dedup, cast, normalise strings, enrich: tier/improvement)
Delta Silver  /delta/silver/
    │
    ▼  04_gold_analytics (4 aggregation tables + ML feature store)
Delta Gold    /delta/gold/
    ├── student_gpa_summary
    ├── major_analytics
    ├── subject_analytics
    └── ml_features (label: at_risk)
```

---

## 🔧 Cluster Config

| Setting        | Value                    |
|----------------|--------------------------|
| Runtime        | 14.3 LTS (Spark 3.5)     |
| Scala          | 2.12                     |
| Workers        | 2 (autoscale 1–4)        |
| Library        | `delta-spark==2.4.0`     |
| Schedule       | Daily 06:00 (GMT+7)      |

---

## 📬 Contact

| Role | Name |
|------|------|
| Data Engineering | _your name here_ |
| Microservices (WIP) | _team_ |
