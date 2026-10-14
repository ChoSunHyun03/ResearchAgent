"""공고의 HTML과 공개 직무 데이터를 함께 읽습니다. 외부 코드는 실행하지 않습니다."""
import ast
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from backend.app.models import JobPosting, PostingRole
from backend.app.scraper import fetch_document, extract_html, PageFetchError


class LiteralReader:
    """문자열·배열·객체·불리언만 허용하는 제한된 JS 데이터 파서입니다."""
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.nodes = 0

    def skip(self):
        while self.pos < len(self.text):
            match = re.match(r"\s+|//[^\n]*|/\*[\s\S]*?\*/", self.text[self.pos:])
            if not match:
                break
            self.pos += len(match[0])

    def take(self, token):
        self.skip()
        if not self.text.startswith(token, self.pos):
            raise ValueError("직무 데이터의 형식을 확인할 수 없습니다.")
        self.pos += len(token)

    def value(self, depth=0, stop_fields=None):
        self.skip()
        self.nodes += 1
        if depth > 20 or self.nodes > 10000 or self.pos >= len(self.text):
            raise ValueError("직무 데이터의 범위가 제한을 초과했습니다.")
        char = self.text[self.pos]
        if char in "\"'":
            start = self.pos
            self.pos += 1
            while self.pos < len(self.text):
                current = self.text[self.pos]
                self.pos += 1
                if current == "\\":
                    self.pos += 1
                elif current == char:
                    return ast.literal_eval(self.text[start:self.pos])
            raise ValueError("직무 데이터 문자열이 완성되지 않았습니다.")
        if char in "[{":
            self.pos += 1
            result = {} if char == "{" else []
            end = "}" if char == "{" else "]"
            while True:
                self.skip()
                if self.text.startswith(end, self.pos):
                    self.pos += 1
                    return result
                if char == "{":
                    if self.text[self.pos] in "\"'":
                        key = self.value(depth + 1)
                    else:
                        match = re.match(r"[A-Za-z_$][\w$]*", self.text[self.pos:])
                        if not match:
                            raise ValueError("직무 데이터 항목 이름이 올바르지 않습니다.")
                        key = match[0]
                        self.pos += len(key)
                    if key in result:
                        raise ValueError("직무 데이터 항목이 중복되었습니다.")
                    self.take(":")
                    result[key] = self.value(depth + 1)
                    # 필요한 최상위 데이터 뒤의 메서드 코드는 해석하지 않습니다.
                    if stop_fields and stop_fields.issubset(result):
                        return result
                else:
                    result.append(self.value(depth + 1))
                self.skip()
                if self.text.startswith(end, self.pos):
                    self.pos += 1
                    return result
                self.take(",")
        match = re.match(r"(?:true|false|null)\b", self.text[self.pos:])
        if match:
            self.pos += len(match[0])
            return {"true": True, "false": False, "null": None}[match[0]]
        raise ValueError("실행 코드가 아닌 직무 데이터만 읽을 수 있습니다.")


def parse_jd_data(text):
    match = re.search(r"\bconst\s+JDDataStore\s*=\s*", text)
    if not match:
        raise ValueError("공개 직무 데이터가 없습니다.")
    reader = LiteralReader(text)
    reader.pos = match.end()
    try:
        data = reader.value(stop_fields={"tabs", "detailLabels", "items"})
    except (SyntaxError, IndexError, RecursionError) as error:
        raise ValueError("직무 데이터 형식이 변경되었습니다.") from error
    if not isinstance(data, dict) or not isinstance(data.get("tabs"), list) or not isinstance(data.get("items"), dict):
        raise ValueError("직무 목록 형식이 올바르지 않습니다.")
    if data.get("detailLabels") != ["[직무기술]", "[자격 요건]", "[필요 역량]", "[우대사항]"]:
        raise ValueError("직무 조건 항목이 변경되었습니다.")
    return data


def detail_lines(value):
    if not isinstance(value, list):
        raise ValueError("직무 조건 목록이 올바르지 않습니다.")
    lines = []
    for item in value:
        if isinstance(item, str) and item.strip():
            lines.append(item.strip())
        elif isinstance(item, dict) and isinstance(item.get("list"), list):
            prefix = " / ".join(str(item[k]) for k in ("title1", "title") if item.get(k))
            lines.extend(f"{prefix}: {line}" if prefix else line for line in detail_lines(item["list"]))
        else:
            raise ValueError("직무 조건 내용을 확인할 수 없습니다.")
    return lines


def build_roles(data, common_text, company, source_url):
    roles = []
    seen = set()
    for tab in data["tabs"]:
        group = tab["title"]
        items = data["items"].get(tab["id"], [])
        if not isinstance(group, str) or not isinstance(items, list):
            raise ValueError("직군 정보가 올바르지 않습니다.")
        for item in items:
            if not isinstance(item["id"], str) or item["id"] in seen or not isinstance(item["title"], str):
                raise ValueError("직무 식별자가 올바르지 않습니다.")
            seen.add(item["id"])
            details = item["details"]
            if not isinstance(details, list) or len(details) != 4:
                raise ValueError("직무 조건 항목이 부족합니다.")
            values = [detail_lines(part) for part in details]
            body = f"회사: {company}\n공통 지원자격:\n{common_text}\n모집 직군: {group}\n모집 직무: {item['title']}\n"
            body += "\n".join(label + "\n" + "\n".join(lines) for label, lines in zip(data["detailLabels"], values))
            if len(body) > 20000:
                raise ValueError("선택 직무의 본문이 분석 한도를 초과했습니다.")
            application_url = urljoin(source_url, tab.get("link", ""))
            if urlsplit(application_url).scheme not in {"http", "https"}:
                application_url = source_url
            roles.append(PostingRole(id=item["id"], group=group, position=item["title"],
                responsibilities=values[0], requirements=values[1], competencies=values[2],
                preferred=values[3], analysis_text=body, application_url=application_url))
    return roles


def fetch_job_details(url):
    html, final_url = fetch_document(url)
    _, text, truncated = extract_html(html, 20000)
    posting = JobPosting(job_text=text, source_url=final_url)
    if truncated:
        posting.warnings.append("공고가 길어 수집 원문 일부가 잘렸습니다.")
    if len(text.strip()) < 200:
        posting.warnings.append("수집 내용이 짧습니다. 상세 공고가 포함되어 있는지 확인해주세요.")
    # 사이트별 구조를 식별합니다. 직군명·직무 수·조건은 하드코딩하지 않습니다.
    if urlsplit(final_url).hostname not in {"skbroadband-juniortalent.co.kr", "www.skbroadband-juniortalent.co.kr"}:
        return posting
    posting.company = "SK브로드밴드"
    soup = BeautifulSoup(html, "html.parser")
    script_url = next((urljoin(final_url, tag["src"]) for tag in soup.select("script[src]")
        if urlsplit(urljoin(final_url, tag["src"])).netloc == urlsplit(final_url).netloc
        and urlsplit(urljoin(final_url, tag["src"])).path == "/assets/js/data/jd-data.js"), None)
    if not script_url:
        posting.warnings.append("직무 목록을 찾지 못했습니다. 사이트 구조가 변경되었을 수 있습니다.")
        return posting
    try:
        raw, _ = fetch_document(script_url, content_types=frozenset({"text/javascript", "application/javascript", "application/x-javascript", "text/plain"}))
        data = parse_jd_data(raw.decode("utf-8-sig"))
        common = text.split("지원자격", 1)[1].split("전형일정", 1)[0].strip() if "지원자격" in text and "전형일정" in text else ""
        posting.roles = build_roles(data, common, posting.company, final_url)
        if not posting.roles:
            posting.warnings.append("현재 공고에 확인 가능한 모집 직무가 없습니다.")
    except (PageFetchError, ValueError, KeyError, TypeError, UnicodeError):
        posting.warnings.append("직무 상세 데이터를 가져오지 못했습니다. 재시도하거나 상세 공고를 직접 입력해주세요.")
    return posting
