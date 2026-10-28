"""Optional Wanted job-posting collection script.

Selectors have not been validated against the current Wanted DOM.
New collections require a separate output path and cannot overwrite
the stored wanted_jobs.csv snapshot.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# 1. 수집 타겟 정의
TARGET_URLS = {
    "서버 개발자": "https://www.wanted.co.kr/wdlist/518/872?country=kr&job_sort=job.popularity_order&years=0&locations=all",
    "프론트엔드 개발자": "https://www.wanted.co.kr/wdlist/518/669?country=kr&job_sort=job.popularity_order&years=0&locations=all",
    "데이터 사이언티스트": "https://www.wanted.co.kr/wdlist/518/1024?country=kr&job_sort=job.popularity_order&years=0&locations=all"
}

# 2. 스크레이핑 설정
LIST_ITEM_CLASS = "Card_Card__aaatv"
DETAIL_LINK_SELECTOR = "div[data-cy='job-card'] > a"
#Method A
DETAIL_SKILL_CLASS = "SkillTagItem_SkillTagItem__MAo9X"
#Method B
# '상세 내용' 본문 전체를 감싸는 div의 class (Method B)
TITLE_CLASS = "wds-58fmok"
COMPANY_CLASS = "JobHeader_JobHeader__Tools__Company__Link__NoBQI"
DESCRIPTION_CLASS = "JobDescription_JobDescription__paragraph__wrapper__WPrKC"

# 본문 텍스트에서 검색할 기술 키워드 사전
# 순서 중요: 'Spring Boot'가 'Spring'보다, 'JavaScript'가 'Java'보다 먼저 와야 함
SKILL_DICTIONARY = [
    'Spring Boot', 'Next.js', 'FastAPI', 'JavaScript', 'TypeScript', 'Node.js',
    'Java', 'Spring', 'JPA', 'Kotlin', 'Python', 'Django', 'Flask',
    'React', 'Vue.js', 'Redux', 'Recoil', 'Svelte',
    'SQL', 'MySQL', 'PostgreSQL', 'Oracle', 'Redis', 'MongoDB', 'MariaDB',
    'AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes', 'Git',
    'Pandas', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'Keras', 'R', 'Tableau', 'Power BI'
]

# Selenium 드라이버 설정
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# 3. 데이터 수집 실행
def validate_output(output):
    output = Path(output)
    frozen = Path(__file__).resolve().parent / "wanted_jobs.csv"
    if output.resolve() == frozen or output.name == "wanted_jobs.csv":
        raise ValueError("The historical wanted_jobs.csv is protected; choose a fresh output path")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    return output


def posting_identity(href):
    parts = urlsplit(urljoin("https://www.wanted.co.kr", href))
    if parts.scheme != "https" or parts.netloc != "www.wanted.co.kr":
        raise ValueError(f"Unexpected posting host: {href!r}")
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    match = re.fullmatch(r"/wd/(\d+)/?", parts.path)
    return url, match.group(1) if match else None


def extract_detail_links(soup):
    # Prefer the data-cy selector already present in the 2025 implementation.
    links = soup.select(DETAIL_LINK_SELECTOR)
    if not links:
        links = [link for card in soup.find_all("li", class_=LIST_ITEM_CLASS)
                 for link in card.select(DETAIL_LINK_SELECTOR)]
    return list(dict.fromkeys(posting_identity(link["href"])[0]
                             for link in links if link.get("href")))


def scrape_wanted(output):
    output = validate_output(output)
    driver = setup_driver()
    all_results = []

    print("데이터 수집을 시작합니다!")

    try:
        for job_role, url in TARGET_URLS.items():
            print(f"\n[{job_role}] 직무 수집 중...")
            driver.get(url)

            # 목록 페이지에서 상세 페이지 링크(href) 수집
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f"{DETAIL_LINK_SELECTOR}, li.{LIST_ITEM_CLASS}"))
                )
                time.sleep(3)
            except Exception as e:
                raise RuntimeError(f"{job_role}: list loading failed; selectors or site access may have changed") from e

            # 스크롤
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(20):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            list_soup = BeautifulSoup(driver.page_source, 'html.parser')
            detail_links = extract_detail_links(list_soup)
            if not detail_links:
                raise RuntimeError(f"{job_role}: no posting links; semantic selector unavailable / not verified")

            print(f"> {job_role}: 총 {len(detail_links)}개의 공고 링크 발견.")

            collected_count = 0
            TARGET_COUNT = 100

            # 각 상세 페이지에 접속하여 정보 수집
            for i, link in enumerate(detail_links):

                print(f"> {i+1}/{len(detail_links)} 번째 링크 시도 중... {link}")
                driver.get(link)

                try:
                    # '상세 내용' 본문이 로드될 때까지 대기
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, DESCRIPTION_CLASS))
                    )
                    time.sleep(1)
                except Exception as exc:
                    raise RuntimeError(f"Detail loading failed: {link}; selector/site access not verified") from exc

                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

                # 하이브리드 수집
                found_skills = set()    # 중복 제거

                # Method A: 태그에서 수집
                skill_tags = detail_soup.find_all('li', class_=DETAIL_SKILL_CLASS)
                if skill_tags:
                    for tag in skill_tags:
                        found_skills.add(tag.text.strip())

                # Method B: 본문 텍스트에서 검색
                description_block = detail_soup.find('div', class_=DESCRIPTION_CLASS)
                if description_block:
                    description_text = description_block.get_text() # 원본 텍스트

                    for skill in SKILL_DICTIONARY:
                        if skill == 'R':
                            # 'R'을 찾되, '&'가 바로 뒤에 오지 않는 경우만
                            pattern = r'\bR(?![&])\b'
                        else:
                            # 다른 모든 스킬은 전후 단어 경계
                            pattern = r'\b' + re.escape(skill) + r'\b'

                        # 대소문자 무시하고 검색
                        if re.search(pattern, description_text, re.IGNORECASE):
                            found_skills.add(skill) # 딕셔너리의 원본으로 추가

                # 수집된 스킬이 없으면 건너뜀
                if not found_skills:
                    print("[알림] 이 공고에서는 정의된 기술 스택을 찾지 못했습니다.")

                skills = sorted(found_skills) # 최종 스킬 목록 (리스트로 변환)

                # 제목, 회사명 수집
                title = detail_soup.find('h1', class_=TITLE_CLASS)
                company = detail_soup.find('a', class_=COMPANY_CLASS)
                if title is None or company is None:
                    raise RuntimeError(f"Missing title/company at {link}; selectors not verified")
                title_text = title.text.strip()
                company_text = company.text.strip()

                # 기술 스택이 1개 이상 발견된 경우에만 수집 및 카운트
                if skills:
                    all_results.append({
                        "source": "Wanted",
                        "query_role": job_role,
                        "job_role": job_role,
                        "posting_url": link,
                        "job_id": posting_identity(link)[1],
                        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                        "company": company_text,
                        "title": title_text,
                        "skills": skills
                    })

                    collected_count += 1
                    print(f"[{job_role}] {collected_count}개 수집 성공.")
                else:
                    # 기술 스택이 없으면, 수집하지 않고 알림만 출력
                    print("[알림] 이 공고에서는 정의된 기술 스택을 찾지 못했습니다. (수집 X)")

                # 기술 스택이 있든 없든, 시도 후에는 항상 1초 대기
                time.sleep(1)

                # 목표 개수(100개)를 채웠으면 이 직무는 중단
                if collected_count >= TARGET_COUNT:
                    print(f"  > {job_role} 직무 {TARGET_COUNT}개 수집 완료. 다음 직무로 넘어갑니다.")
                    break

    finally:
        driver.quit()

    # 4. CSV 파일로 저장
    if all_results:
        df = pd.DataFrame(all_results)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8-sig', newline='') as handle:
            df.to_csv(handle, index=False)
        print(f"\n스크레이핑 완료! 총 {len(df)}개의 공고를 '{output}'에 저장했습니다.")
    else:
        raise RuntimeError("No data collected; check site policy, network and selectors")

# --- 스크립트 실행 ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    scrape_wanted(parser.parse_args().output)
