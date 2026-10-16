# Datathon: Smart City — Where Should We Fix First?

An intelligent civic infrastructure prioritization and intervention-support system. This project analyzes civic reports, incidents, and public complaints to identify and prioritize high-risk urban locations that need immediate municipal remediation.

## 📁 Repository Structure

- **`03_smart_city_where_fix_first/`**: Core analytics pipeline and visualization tools.
  - `compute_scores.py`: Computes urgency, severity, and prioritization scores for locations across incidents and public complaints.
  - `generate_dashboard.py`: Generates an interactive visual dashboard for civic decision-makers.
  - `test_pipeline.py`: Unit and regression test suite.
  - `locations.csv`, `incidents.csv`, `public_complaints.csv`: Datasets with simulated civic and spatial data.
  - `scores_output.json`: Output scores and priority rankings.
  - `dashboard.html`: Self-contained interactive decision support dashboard.
- **`smart_city_antigravity_prompts/`**: Architecture design, problem context, and technical stack specifications.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Pandas, NumPy, and standard data science libraries

### Running the Scoring Pipeline
```bash
python 03_smart_city_where_fix_first/compute_scores.py
```

### Generating the Dashboard
```bash
python 03_smart_city_where_fix_first/generate_dashboard.py
```

### Running Tests
```bash
pytest 03_smart_city_where_fix_first/test_pipeline.py
```
