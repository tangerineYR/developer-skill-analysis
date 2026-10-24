<div align="center">

# Developer Skill Analysis 📊

### Developer Job-posting Skill Analysis with a Frozen 2025 Wanted Snapshot

**Wanted 개발 직군 검색 결과를 수집하고  
기술명을 정규화한 뒤 직무별 요구 기술의 차이를  
재현 가능한 데이터 분석·시각화 파이프라인으로 비교합니다.**

<br/>

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Selenium](https://img.shields.io/badge/Selenium-Web_Scraping-43B02A?style=for-the-badge&logo=selenium&logoColor=white)](https://www.selenium.dev/)

[![Dataset](https://img.shields.io/badge/Historical_Snapshot-119_Rows-444444?style=flat-square)]()
[![Tests](https://img.shields.io/badge/Tests-23-4C8BF5?style=flat-square)]()
[![CI](https://img.shields.io/badge/GitHub_Actions-Passing-2088FF?style=flat-square&logo=githubactions&logoColor=white)]()

<br/>

[📄Historical Project Report (2025)](docs/historical-report-2025.pdf)
&nbsp;·&nbsp;
[📊 Analysis Summary](results/analysis_summary.json)
&nbsp;·&nbsp;
[🔍 Sample Audit](results/sample_audit.json)
&nbsp;·&nbsp;
[🧹 Normalization Audit](results/normalization_audit.csv)

</div>

---

## 📌 Overview

**Developer Skill Analysis**는 개발 직무를 준비하는 학생이 막연한 인식이 아니라 실제 채용공고 표본을 통해 직무별 기술 요구 차이를 파악할 수 있도록 수행한 데이터시각화 전공 프로젝트입니다.

2025년 Wanted에서 서버 개발자, 프론트엔드 개발자, 데이터 사이언티스트 검색 결과를 수집하고, 공고에 등장하는 기술명을 정규화해 직무별 기술 포함 비율과 기술 카테고리 구성을 비교했습니다.

```text
Wanted Job Search
        ↓
Selenium + BeautifulSoup
        ↓
Historical CSV Snapshot
        ↓
Skill Parsing & Normalization
        ↓
Sample / Normalization Audit
        ↓
Role-level Aggregation
        ↓
Matplotlib / Seaborn Visualization
```

### Project Info

| 항목 | 내용 |
| --- | --- |
| **프로젝트 유형** | 데이터시각화 전공 프로젝트 · 개인 |
| **수행 시기** | 3학년 2학기 · 2025 |
| **데이터 소스** | Wanted 개발 직군 검색 결과 |
| **검색 조건** | `years=0` |
| **분석 직무** | 서버 · 프론트엔드 · 데이터 사이언티스트 |
| **Historical Dataset** | 119 role-posting rows |
| **고유 공고 Proxy** | 112 company-title pairs |
| **Data Collection** | Selenium · BeautifulSoup |
| **Analysis** | Pandas |
| **Visualization** | Matplotlib · Seaborn |
| **Validation** | 23 automated tests · GitHub Actions |

> **Dataset Scope**
>
> `wanted_jobs.csv`는 2025년 프로젝트 당시 생성한 frozen snapshot입니다.
>
> `years=0` 검색 조건을 사용했지만 일부 결과에는 `0~5년`, `~6년` 등 더 넓은 경력 범위를 명시한 제목도 포함되어 있으므로, 이 데이터를 **엄격한 경력 1년 미만 채용 집단으로 해석하지 않습니다.**
>
> 또한 표본 수를 전체 개발자 채용시장의 규모로 해석하지 않습니다.

---

# 🏗️ Analysis Pipeline

```mermaid
flowchart LR
    SEARCH["Wanted Search Results<br/>3 Developer Roles"]
        --> SCRAPE["Selenium<br/>BeautifulSoup"]

    SCRAPE --> CSV["Frozen 2025 Snapshot<br/>119 Role-posting Rows"]

    CSV --> PARSE["Skill Parsing<br/>Validation"]

    PARSE --> NORMALIZE["Canonicalization<br/>Alias Normalization"]

    NORMALIZE --> AUDIT["Sample &<br/>Normalization Audit"]

    AUDIT --> ANALYSIS["Role-level<br/>Aggregation"]

    ANALYSIS --> TOP["Top Skills"]
    ANALYSIS --> HEAT["Cross-role Heatmap"]
    ANALYSIS --> CATEGORY["Category Analysis"]

    TOP --> VIS["Matplotlib / Seaborn"]
    HEAT --> VIS
    CATEGORY --> VIS
```

---

# 📦 Dataset Audit

Historical CSV에는 총 **119개의 role-posting row**가 있습니다.

| Role | Rows |
| --- | ---: |
| **서버 개발자** | **44** |
| **프론트엔드 개발자** | **46** |
| **데이터 사이언티스트** | **29** |
| **Total** | **119** |

한 공고가 여러 Wanted 직무 검색 결과에 나타날 수 있기 때문에 row 수와 고유 공고 수는 동일하지 않습니다.

```text
119 role-posting rows
        ↓
112 unique company-title proxies
        ↓
7 proxies appear in multiple role queries
```

Historical CSV에는 Wanted의 실제 job ID와 posting URL이 저장되지 않았기 때문에, `company + title` 조합은 **공고 identity의 proxy**로만 사용합니다.

또 제목 기준 heuristic에서 9개 row가 1년 이상의 경력 범위를 명시했습니다. 이 heuristic은 표본 감사용이며 row 삭제나 strict entry-level 판정에는 사용하지 않았습니다.

---

# 🧹 Skill Normalization

## Problem

2025년 구현에서는 normalization map에 등록되지 않은 기술이 분석 단계에서 조용히 제거됐습니다.

Historical snapshot에는:

```text
503 raw skill mentions
```

이 존재했지만 기존 pipeline에서는 상당수 기술이 map에 없다는 이유만으로 사라질 수 있었습니다.

예:

```text
Linux
Golang
Flutter
C#
Android
GraphQL
React Native
OpenCV
NLP
...
```

## Engineering Decision

2026 Portfolio Refactoring에서는 다음 정책으로 변경했습니다.

```text
Known Alias
   ↓
Canonical Skill

Unknown Valid Skill
   ↓
Preserve Original Value
```

예:

```text
React.js       → React
GitHub         → Git
Tensorflow     → TensorFlow
C / C++        → C++
Golang         → Go

Unmapped Skill → 그대로 보존
```

한 공고 안에서 alias normalization 후 동일 기술이 중복되면 한 번만 집계합니다.

### Result

```text
Raw skill mentions               503
Canonical occurrences            495
Retained unmapped raw mentions    64
Silently dropped valid mentions    0
```

503 → 495의 차이는 기술 제거가 아니라 동일 row 안의 alias / duplicate canonicalization에 따른 중복 통합입니다.

세부 mapping은 [`results/normalization_audit.csv`](results/normalization_audit.csv)에서 확인할 수 있습니다.

---

# 📊 Snapshot Findings

## 1. Server Developer

Historical server sample에서 가장 많이 등장한 기술은:

| Skill | Posting-row Prevalence |
| --- | ---: |
| **AWS** | **36.4%** |
| **Java** | **36.4%** |
| Python | 29.5% |
| MySQL | 27.3% |
| Spring | 22.7% |
| Docker | 20.5% |

<p align="center">
  <img src="results/figures/graph_top_skills_서버_개발자.png" width="820" alt="Server developer top skills" />
</p>

Corrected taxonomy 기준으로 **서버 row의 54.5%에는 Cloud/Infra 기술이 하나 이상 포함**되어 있었습니다.

이는 전체 채용시장 추세를 의미하지는 않지만, 해당 표본에서는 application development뿐 아니라 AWS·Docker·Kubernetes 등의 인프라 관련 기술이 함께 등장하는 패턴을 보여줍니다.

---

## 2. Frontend Developer

| Skill | Posting-row Prevalence |
| --- | ---: |
| **React** | **71.7%** |
| **TypeScript** | **47.8%** |
| Next.js | 37.0% |
| JavaScript | 26.1% |
| Git | 23.9% |

<p align="center">
  <img src="results/figures/graph_top_skills_프론트엔드_개발자.png" width="820" alt="Frontend developer top skills" />
</p>

React와 TypeScript가 표본 내에서 높은 빈도로 나타났으며, 기술 occurrence 기준으로 **Framework/Library category가 42.9%**를 차지했습니다.

---

## 3. Data Scientist

| Skill | Posting-row Prevalence |
| --- | ---: |
| **Python** | **65.5%** |
| **PyTorch** | **44.8%** |
| **TensorFlow** | **31.0%** |
| SQL | 20.7% |
| Git | 13.8% |

<p align="center">
  <img src="results/figures/graph_top_skills_데이터_사이언티스트.png" width="820" alt="Data scientist top skills" />
</p>

Python이 가장 넓게 나타났고 PyTorch와 TensorFlow가 뒤를 이어, 이 historical sample에서는 ML framework가 주요 요구 기술군으로 나타났습니다.

---

# 🔥 Cross-role Comparison

각 셀은:

```text
해당 기술을 포함한 role-posting rows
──────────────────────────────────
해당 직무 전체 분석 rows
```

의 비율입니다.

<p align="center">
  <img src="results/figures/graph_skill_heatmap.png" width="1000" alt="Developer skill heatmap" />
</p>

히트맵에서는 세 직무가 서로 다른 기술 생태계에 집중되는 패턴을 확인할 수 있습니다.

```text
Server
→ Java · AWS · Spring · MySQL

Frontend
→ React · TypeScript · Next.js

Data Science
→ Python · PyTorch · TensorFlow
```

이는 표본 내 기술 집중 패턴에 대한 관찰이며, 직무 간 기술 장벽을 통계적으로 입증한 결과로 해석하지 않습니다.

---

# 🧩 Two Different Category Metrics

카테고리 분석에서는 서로 다른 두 denominator를 명시적으로 구분합니다.

### 1. Skill Occurrence Composition

```text
category canonical skill occurrences
────────────────────────────────────
all canonical skill occurrences
```

직무별 합계가 100%가 되는 지표입니다.

### 2. Posting Prevalence

```text
rows containing ≥1 skill in category
────────────────────────────────────
all role rows
```

하나의 공고가 여러 category에 포함될 수 있으므로 합계가 100%일 필요가 없습니다.

대표적으로 서버 직무의 Cloud/Infra는:

```text
Occurrence Composition : 18.5%
Posting Prevalence      : 54.5%
```

입니다.

두 값을 혼용하지 않습니다.

<p align="center">
  <img src="results/figures/graph_skill_category_stacked.png" width="900" alt="Skill category composition" />
</p>

---

# 🚀 Engineering Highlights

## 1. Analysis Logic과 Visualization 분리

기존 `visualizer.py`에 섞여 있던 parsing, normalization, aggregation logic을 `analysis.py`로 분리했습니다.

```text
analysis.py
├─ skill parsing
├─ normalization
├─ category mapping
├─ sample audit
├─ skill frequency
├─ category metrics
└─ summary generation

visualizer.py
└─ plotting / artifact output
```

분석 함수를 plotting과 분리해 deterministic unit test가 가능하도록 변경했습니다.

---

## 2. Malformed Data를 조용히 누락하지 않음

기존 pipeline은 skill column parsing에 실패하면 빈 list로 대체할 수 있었습니다.

현재는:

```text
Malformed list
Non-list value
Non-string skill
Blank skill
Missing required column
```

을 명시적인 validation error로 처리합니다.

분석 결과에서 잘못된 row가 조용히 사라지지 않도록 하기 위한 결정입니다.

---

## 3. Historical Snapshot 보호

`wanted_jobs.csv`는 2025 프로젝트의 provenance이므로 fresh scraping으로 덮어쓸 수 없도록 보호했습니다.

향후 scraper는:

```bash
python scraper.py \
  --output scrape_output/wanted_jobs_new.csv
```

처럼 명시적인 별도 output을 요구합니다.

이미 존재하는 파일도 자동으로 overwrite하지 않습니다.

---

## 4. Future Scraping Provenance

향후 새로운 데이터를 수집할 경우 다음 metadata를 저장하도록 개선했습니다.

```text
source
query_role
posting_url
job_id
collected_at_utc
company
title
skills
```

Historical 2025 CSV에 존재하지 않는 URL이나 job ID를 사후에 추측하여 채워 넣지는 않았습니다.

현재 Wanted DOM에 대한 live scraper 재검증은 수행하지 않았으며, hashed CSS selector 일부는 페이지 변경에 따라 다시 검증이 필요할 수 있습니다.

---

# 🧪 Tests & CI

현재 analysis layer에는 **23개의 automated tests**가 있습니다.

주요 검증 범위:

```text
Alias normalization
Unknown skill preservation
Within-row deduplication
Malformed skill rejection

119-row historical snapshot
44 / 46 / 29 role counts
112 company-title proxies
7 cross-role duplicates

Historical top-skill percentages
Category occurrence composition
Category posting prevalence
Normalization audit
Frozen snapshot integrity
```

실행:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions에서는 Python 3.12 환경에서:

```text
Install dependencies
        ↓
Run 23 tests
        ↓
Run offline historical analysis
        ↓
Verify generated artifacts
        ↓
Verify frozen CSV integrity
```

를 수행합니다.

현재 `main` workflow는 통과합니다.

---

# ▶️ Reproduction

## Installation

```bash
git clone https://github.com/tangerineYR/developer-skill-analysis.git
cd developer-skill-analysis

python -m venv .venv
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

의존성 설치:

```bash
pip install -r requirements.txt
```

## Historical Analysis

```bash
python visualizer.py \
  --input wanted_jobs.csv \
  --output-dir .
```

headless 실행이 기본이며, plotting window가 필요하면:

```bash
python visualizer.py \
  --input wanted_jobs.csv \
  --output-dir . \
  --show
```

를 사용합니다.

---

# 📁 Project Structure

```text
developer-skill-analysis/
│
├── analysis.py                  # 기술 정규화·표본 감사·집계 로직
├── scraper.py                   # Wanted 채용공고 수집 및 provenance 기록
├── visualizer.py                # 분석 결과 시각화 및 artifact 생성
│
├── wanted_jobs.csv              # 2025 Historical Project의 frozen dataset
├── requirements.txt
├── README.md
│
├── results/
│   ├── analysis_summary.json    # 핵심 분석 지표 및 denominator 정의
│   ├── sample_audit.json        # 표본 중복·경력 범위 heuristic 감사
│   ├── normalization_audit.csv  # raw → canonical 기술 정규화 기록
│   └── figures/
│       ├── graph_job_role_counts.png
│       ├── graph_skill_heatmap.png
│       ├── graph_skill_category_stacked.png
│       └── graph_top_skills_*.png
│
├── docs/
│   └── historical-report-2025.pdf
│
├── tests/
│   └── test_analysis.py
│
└── .github/
    └── workflows/
        └── analysis.yml
```

---

# 🔄 Historical Project vs Portfolio Refactoring

| 구분 | 2025 Historical Project | 2026 Portfolio Refactoring |
| --- | --- | --- |
| Data | Wanted 119-row snapshot | Historical snapshot 그대로 보존 |
| Collection | Selenium + BeautifulSoup | provenance / overwrite protection 보강 |
| Normalization | Known mapping 중심 | Unknown valid skill 보존 |
| Analysis | 직무별 기술 비교 | denominator semantics 명시 |
| Sample Definition | 119 rows | 112 proxy postings / 7 overlaps audit |
| Category | 기존 taxonomy | Cloud/Infra · Tooling 재정의 |
| Validation | 수동 확인 | 23 automated tests |
| Reproduction | Script 중심 | Offline deterministic CI |

2026 작업은 기존 결과를 더 좋아 보이게 만들기 위한 재분석이 아니라, **2025 snapshot을 그대로 유지하면서 분석 과정의 의미와 재현성을 명확하게 만든 작업**입니다.

---

# ⚠️ Scope & Limitations

**Historical Snapshot**

이 데이터는 2025년에 수집된 Wanted 검색 결과의 snapshot입니다. 현재 채용시장의 상태를 의미하지 않습니다.

**Not a Market Census**

119 rows는 전체 채용시장의 공고 수가 아니므로 직무별 시장 규모나 전체 수요를 추정하는 데 사용할 수 없습니다.

**Entry-level Scope**

검색에는 `years=0` 조건을 사용했지만 일부 공고 제목에는 더 넓은 경력 범위가 나타납니다. 따라서 strict `< 1 year` dataset으로 검증되지 않았습니다.

**Posting Identity**

Historical CSV에는 posting URL과 Wanted job ID가 없으므로 `company + title`을 proxy로 사용합니다.

**Cross-role Overlap**

동일 proxy posting이 서로 다른 role query에 포함될 수 있으며 현재 snapshot에서는 7개가 확인됩니다.

**Skill-detection Selection**

Historical scraper는 기술 스택을 하나 이상 탐지한 공고만 CSV에 저장했습니다. 따라서 수집 결과는 Wanted 검색 결과 전체를 그대로 보존한 표본이 아닙니다.

**Current Scraper Compatibility**

2026 refactoring에서는 scraper provenance와 failure handling을 개선했지만 현재 Wanted DOM을 대상으로 live scraping을 다시 수행하지 않았습니다.

---

# 💡 Future Direction

2025 프로젝트에서는 분석 결과를 확장해 사용자의 현재 기술과 목표 직무 요구 기술을 비교하는 **개인화된 Skill Gap Analysis / Learning Roadmap 서비스**를 후속 아이디어로 제안했습니다.

이 기능은 현재 repository에 구현되어 있지 않으며, 본 repository는 **채용공고 데이터 수집·정제·분석·시각화 pipeline**에 범위를 한정합니다.

---

<div align="center">

**Collect → Normalize → Audit → Analyze → Visualize**

_Data analysis is only useful when the denominator, sample scope, and information loss are explicit._

</div>
