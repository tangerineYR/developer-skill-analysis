"""Offline analysis of the frozen 2025 Wanted query snapshot.

A posting in role metrics means a CSV role-posting row, not a verified job ID.
"""
import ast
from collections import Counter
import hashlib
import re
from pathlib import Path

import pandas as pd

ANALYSIS_VERSION = "2.0"
SKILL_NORMALIZATION_MAP = {'c++': 'C++',
 'c / c++': 'C++',
 'c/c++': 'C++',
 'python': 'Python',
 'django': 'Django',
 'flask': 'Flask',
 'fastapi': 'FastAPI',
 'java': 'Java',
 'spring': 'Spring',
 'spring boot': 'Spring Boot',
 'springboot': 'Spring Boot',
 'jpa': 'JPA',
 'kotlin': 'Kotlin',
 'javascript': 'JavaScript',
 'typescript': 'TypeScript',
 'react': 'React',
 'react.js': 'React',
 'vue.js': 'Vue.js',
 'vue': 'Vue.js',
 'next.js': 'Next.js',
 'node.js': 'Node.js',
 'redux': 'Redux',
 'recoil': 'Recoil',
 'svelte': 'Svelte',
 'sql': 'SQL',
 'mysql': 'MySQL',
 'postgresql': 'PostgreSQL',
 'oracle': 'Oracle',
 'redis': 'Redis',
 'mongodb': 'MongoDB',
 'mariadb': 'MariaDB',
 'aws': 'AWS',
 'gcp': 'GCP',
 'azure': 'Azure',
 'docker': 'Docker',
 'kubernetes': 'Kubernetes',
 'git': 'Git',
 'github': 'Git',
 'r': 'R',
 'pandas': 'Pandas',
 'tensorflow': 'TensorFlow',
 'pytorch': 'PyTorch',
 'scikit-learn': 'Scikit-learn',
 'keras': 'Keras',
 'tableau': 'Tableau',
 'power bi': 'Power BI',
 'golang': 'Go',
 'go': 'Go'}
SKILL_CATEGORY_MAP = {
    "Language": ["Java", "Python", "JavaScript", "TypeScript", "Kotlin", "C++", "SQL", "R", "C#", "Go", "Swift", "PHP"],
    "Framework/Library": ["React", "Spring", "Spring Boot", "Next.js", "Django", "Flask", "FastAPI", "Vue.js", "PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "Redux", "Recoil", "Svelte", "Node.js", "Keras", "JPA", "Flutter", "Nuxt.js", "React Native", "OpenCV", "Ruby on Rails", "Nest.js", "MFC", ".NET", "Laravel", "WPF"],
    "Database": ["MySQL", "PostgreSQL", "Redis", "MongoDB", "MariaDB", "Oracle", "MSSQL"],
    "Cloud/Infra": ["AWS", "Docker", "Kubernetes", "GCP", "Azure", "Linux", "UNIX"],
    "Development Tool": ["Git", "Visual Studio"],
    "Data/BI Tool": ["Tableau", "Power BI", "Excel"],
    "Other": [],
}
CATEGORIES = tuple(SKILL_CATEGORY_MAP)
SAMPLE_SCOPE = {
    "source": "Wanted historical 2025 project CSV",
    "search_filter": "years=0",
    "strict_entry_level_verified": False,
    "collection_date": None,
    "posting_identity": "Exact company-title tuple proxy; not a Wanted job ID",
    "historical_posting_urls_and_ids_available": False,
}


def parse_skill_list(value, row_index=None):
    """Reject malformed, non-list, non-string or blank tags with row context."""
    try:
        parsed = ast.literal_eval(value) if isinstance(value, str) else value
        if not isinstance(parsed, list):
            raise ValueError("expected a list")
        if any(not isinstance(s, str) or not s.strip() for s in parsed):
            raise ValueError("expected nonblank string skills")
        return parsed
    except (ValueError, SyntaxError, TypeError) as exc:
        raise ValueError(f"Invalid skills at row {row_index}: {value!r} ({exc})") from exc


def canonicalize_skill(skill):
    if not isinstance(skill, str) or not skill.strip():
        raise ValueError(f"Invalid skill: {skill!r}")
    return SKILL_NORMALIZATION_MAP.get(skill.strip().lower(), skill.strip())


def normalize_skills(skills):
    """Keep first-seen order; count a canonical skill once per role-posting row."""
    return list(dict.fromkeys(canonicalize_skill(s) for s in parse_skill_list(skills)))


def categorize_skill(skill):
    return next((cat for cat, skills in SKILL_CATEGORY_MAP.items() if skill in skills), "Other")


def validate_dataset_columns(df):
    missing = {"job_role", "company", "title", "skills"} - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    for column in ("job_role", "company", "title"):
        for index, value in df[column].items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Invalid {column} at row {index}: {value!r}")


def load_and_clean_data(path):
    df = pd.read_csv(path)
    validate_dataset_columns(df)
    df["skills_raw"] = [parse_skill_list(v, i) for i, v in df["skills"].items()]
    df["skills"] = df["skills_raw"].map(normalize_skills)
    return df


def compute_role_counts(df):
    return {role: len(group) for role, group in df.groupby("job_role", sort=True)}


def compute_skill_frequency(df, top_n=None):
    result = {}
    for role, group in df.groupby("job_role", sort=True):
        counts = Counter(s for skills in group["skills"] for s in skills)
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        result[role] = [{"skill": s, "count": n, "percentage": n / len(group) * 100}
                        for s, n in ranked[:top_n]]
    return result


def _category_metric(df, prevalence):
    result = {}
    for role, group in df.groupby("job_role", sort=True):
        counts = Counter()
        for skills in group["skills"]:
            categories = [categorize_skill(s) for s in skills]
            counts.update(set(categories) if prevalence else categories)
        denominator = len(group) if prevalence else sum(counts.values())
        result[role] = {cat: counts[cat] / denominator * 100 if denominator else 0.0
                        for cat in CATEGORIES}
    return result


def compute_category_occurrence_composition(df):
    """Percent of canonical skill occurrences per role; empty roles yield zeros."""
    return _category_metric(df, False)


def compute_category_posting_prevalence(df):
    """Percent of role-posting rows containing >=1 skill in a category."""
    return _category_metric(df, True)


def broader_experience_title(title):
    """Audit-only Korean title heuristic: explicit year count >=1.

    Includes upper bounds, ranges and year-suffixed counts (including 신입~1년차).
    Not a strict entry-level label; does not infer requirements from absent text.
    """
    return any(int(n) >= 1 for n in re.findall(r"(\d+)\s*년", title))


def compute_sample_audit(df):
    proxies = df.groupby(["company", "title"], sort=True)
    duplicates = [{"company": company, "title": title,
                   "query_roles": sorted(group["job_role"].unique()), "row_count": len(group)}
                  for (company, title), group in proxies if group["job_role"].nunique() > 1]
    flagged = [{"row_index": int(i), "job_role": row.job_role, "title": row.title}
               for i, row in df.iterrows() if broader_experience_title(row.title)]
    return {"row_count": len(df), "role_counts": compute_role_counts(df),
            "unique_company_title_proxy_count": len(proxies),
            "cross_role_duplicate_proxy_count": len(duplicates),
            "cross_role_duplicate_proxies": duplicates,
            "broader_experience_title_row_count": len(flagged),
            "broader_experience_title_rows": flagged,
            "experience_heuristic": "Explicit integer >=1 followed by 년; audit only, not ground truth. Includes 신입~1년차.",
            "rows_removed": 0, "sample_scope": SAMPLE_SCOPE}


def normalization_audit(df):
    counts = Counter(s for skills in df["skills_raw"] for s in skills)
    rows = []
    for raw, count in sorted(counts.items()):
        canonical = canonicalize_skill(raw)
        mapping_type = ("retained_unmapped" if raw.strip().lower() not in SKILL_NORMALIZATION_MAP
                        else "canonical" if raw.strip() == canonical else "alias")
        rows.append({"raw_skill": raw, "canonical_skill": canonical,
                     "category": categorize_skill(canonical), "raw_occurrence_count": count,
                     "mapping_type": mapping_type})
    return pd.DataFrame(rows, columns=["raw_skill", "canonical_skill", "category", "raw_occurrence_count", "mapping_type"])


def build_summary(df, source_file):
    audit = compute_sample_audit(df)
    normalization = normalization_audit(df)
    raw = sum(map(len, df["skills_raw"]))
    canonical = sum(map(len, df["skills"]))
    return {"analysis_version": ANALYSIS_VERSION, "historical_project_year": 2025,
            "analysis_revision_year": 2026, "source_file": Path(source_file).name,
            "source_sha256": hashlib.sha256(Path(source_file).read_bytes()).hexdigest(),
            **{k: audit[k] for k in ("row_count", "role_counts", "unique_company_title_proxy_count", "cross_role_duplicate_proxy_count")},
            "raw_skill_mentions": raw, "canonical_skill_mentions": canonical,
            "retained_unmapped_skill_mentions": int(normalization.loc[normalization.mapping_type == "retained_unmapped", "raw_occurrence_count"].sum()),
            "within_row_alias_or_duplicate_mentions_collapsed": raw - canonical,
            "silent_dropped_valid_skill_mentions": 0,
            "top_skills_by_role": compute_skill_frequency(df, 20),
            "category_occurrence_composition": compute_category_occurrence_composition(df),
            "category_posting_prevalence": compute_category_posting_prevalence(df),
            "metric_semantics": {"category_occurrence_composition": "100 * category canonical occurrences / all canonical occurrences in role",
                                 "category_posting_prevalence": "100 * role rows with >=1 category skill / all rows in role",
                                 "top_skills_by_role": "100 * role rows containing canonical skill / all rows in role",
                                 "retained_unmapped_skill_mentions": "Raw mentions retained by fallback before within-row deduplication"},
            "sample_scope": SAMPLE_SCOPE}
