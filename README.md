# 신입 개발자 직무별 요구 기술 분석 프로젝트

본 프로젝트는 텍스트 형태의 채용 공고 데이터를 시각화하여, 막연한 추측이 아닌 데이터에 기반한 신입 개발자 진로 설계 기준을 제시하는 것을 목표로 합니다.

## 1. 문제 인식

데이터사이언스학을 전공하며 데이터를 다루는 법을 배우지만, 정작 학생들의 진로 선택은 데이터가 아닌 막연한 소문에 의존하고 있습니다. 수백 개의 채용 공고는 그저 거대한 텍스트의 나열일 뿐, 그 안에서 직무별 핵심 기술의 차이를 한눈에 파악하기 어렵기 때문입니다.

본 프로젝트는 ‘데이터 시각화’ 를 통해 정보의 비대칭을 해소하고, 예비 개발자들이 자신의 강점에 맞는 직무를 전략적으로 선택할 수 있도록 돕습니다.

## 2. 분석 데이터

- 데이터 소스: 국내 주요 IT 채용 플랫폼 ‘원티드(Wanted)’

- 수집 대상: `years=0` 검색 조건을 적용한 개발 직군 3개 직무(서버 개발자, 프론트엔드 개발자, 데이터 사이언티스트)

- 분석 표본 Row 수: 서버 개발자 44건, 프론트엔드 개발자 46건, 데이터 사이언티스트 29건 (총 119건)

119행은 직무별 검색 결과의 role-posting row입니다. 회사명·제목 조합은 112개이며, 7개 조합이 여러 직무 검색 결과에 나타납니다. 이 조합은 공고 식별용 proxy이며 실제 Wanted job ID와 같지 않습니다.

경력 범위가 더 넓은 제목도 포함되어 있어 경력 1년 미만 집단으로 검증된 데이터는 아닙니다. 원본 CSV는 2025년 분석 표본으로 보존하며, 수집일과 개별 공고 URL/job ID는 저장되어 있지 않습니다.

## 3. 파일 설명

### scraper.py

Python의 Selenium과 BeautifulSoup을 활용한 웹 스크레이핑 스크립트입니다.

동적 페이지 로딩을 처리하며 공고의 '기술 스택 태그'와 '본문 텍스트'를 수집합니다.

정규표현식(re)을 사용하여 "R&D"와 같은 노이즈 데이터를 필터링합니다.

향후 수집은 `python scraper.py --output scrape_output/wanted_jobs_new.csv`처럼 출력 경로를 지정합니다. 기존 파일과 `wanted_jobs.csv` 덮어쓰기를 차단합니다. 현재 Wanted DOM에 대한 selector 검증은 되어 있지 않으며, 페이지 변경이나 접근 제한으로 실패할 수 있습니다.

### analysis.py

기술 목록 검증, 정규화, 직무별 집계와 표본 감사를 담당합니다. 알려진 alias를 통합하고 미등록 기술은 원본 표기를 보존합니다. 한 row 안의 동일 canonical 기술은 한 번만 집계합니다.

### visualizer.py

수집된 데이터를 정제하고 시각화하는 파이프라인입니다.

- 데이터 정규화: 'React.js' -> 'React', 'Golang' -> 'Go' 등 동일 기술의 표기를 통일합니다.

- 시각화: Matplotlib과 Seaborn을 활용하여 막대그래프(Bar Chart), 히트맵(Heatmap), 누적 막대그래프(Stacked Bar Chart)를 생성합니다.

### wanted_jobs.csv

수집 및 1차 전처리가 완료된 원본 데이터 파일입니다.

### graph_*.png

분석 결과로 도출된 최종 시각화 이미지 파일들입니다.

## 4. 요구 사항 (Requirements)

Python 3.12에서 검증했습니다. Linux에서 한글 그래프를 생성하려면 Noto CJK 또는 NanumGothic 폰트가 필요합니다.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python visualizer.py --input wanted_jobs.csv --output-dir .
```

분석은 기본적으로 headless로 실행하며, 화면 표시가 필요하면 `--show`를 추가합니다. Windows에서는 `.venv\Scripts\activate`로 가상 환경을 활성화합니다.

`results/analysis_summary.json`은 분석 수치와 분모 정의, `results/sample_audit.json`은 표본 중복과 경력 제목 heuristic, `results/normalization_audit.csv`는 raw 기술별 정규화 결과를 기록합니다. 경력 제목 heuristic은 정답 레이블이 아니며 표본 삭제에 사용하지 않습니다.

## 5. 시각화 결과 및 분석

### 분석 1. 직무별 주요 기술

아래 비율의 분모는 해당 직무의 분석 표본 Row 수입니다.

- 서버 개발자: Java와 AWS 각각 36.4%.
- 프론트엔드 개발자: React 71.7%, TypeScript 47.8%.
- 데이터 사이언티스트: Python 65.5%, PyTorch 44.8%, TensorFlow 31.0%.

### 분석 2. 직무 간 기술 비교

히트맵은 각 직무 표본에서 해당 기술을 포함하는 Row의 비율을 표시합니다. 표본의 검색 조건과 직무 간 중복을 고려해야 하며, 전체 채용 시장의 필수 기술이나 시장 규모를 나타내지 않습니다.

### 분석 3. 기술 카테고리

누적 막대그래프는 각 직무의 **canonical 기술 occurrence 중 해당 카테고리의 구성 비율**입니다. 공고 포함률과는 다른 지표입니다.

| 지표 | 서버 | 프론트엔드 | 데이터 사이언티스트 |
| --- | ---: | ---: | ---: |
| Cloud/Infra occurrence 구성비 | 18.5% | 7.7% | 6.8% |
| Cloud/Infra 기술이 하나 이상 있는 Row 비율 | 54.5% | 21.7% | 13.8% |
| Framework/Library occurrence 구성비 | 26.5% | 42.9% | 34.1% |

Git은 Development Tool로 분류합니다. 전체 503개 raw 기술 언급은 row 내부 중복 통합 후 495개 canonical occurrence가 됩니다. 정규화 맵에 없는 64개 raw 언급도 보존합니다.

## 6. 해석 범위

이 분석은 2025년 Wanted 검색 표본의 기술 분포를 설명합니다. 전체 시장의 규모·직무별 수요 또는 엄격한 신입 집단의 특성으로 일반화할 수 없습니다. 2026년 분석 개정에서는 기술 보존 정책, 표본 감사, 분모 구분, 테스트와 CI를 추가했습니다.

첨부 PDF는 2025년 프로젝트의 원본 보고서이며 당시 분석을 기록합니다. 현재 정규화·카테고리 정의와 수치는 코드 및 `results/analysis_summary.json`을 기준으로 확인해야 합니다.
