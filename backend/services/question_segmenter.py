import re
from services.import_schema import QuestionCandidate


QUESTION_SPLIT_RE = re.compile(r'(?:^|\n)\s*(\d+)[\.、．]\s*')
OPTION_RE = re.compile(r'^\s*([A-D])\s*[\.、．]\s*(.+)$', re.MULTILINE)
ANSWER_RE = re.compile(r'(?:答案|Answer)\s*[:：]\s*([^\n]+)')
EXPLANATION_RE = re.compile(r'(?:解析|Explanation)\s*[:：]\s*([\s\S]+)$')


class QuestionSegmenter:
    def segment(self, pages):
        candidates = []
        index = 1
        for page in pages:
            parts = self._split_page(page.text)
            for raw in parts:
                candidate = self._parse_raw_question(raw, index=index, source_page=page.page)
                if candidate and candidate.content.strip():
                    candidates.append(candidate)
                    index += 1
        return candidates

    def _split_page(self, text):
        matches = list(QUESTION_SPLIT_RE.finditer(text))
        if not matches:
            stripped = text.strip()
            return [stripped] if stripped else []

        parts = []
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            parts.append(text[start:end].strip())
        return [p for p in parts if p]

    def _parse_raw_question(self, raw, index, source_page):
        answer = ''
        explanation = ''

        answer_match = ANSWER_RE.search(raw)
        if answer_match:
            answer = answer_match.group(1).strip()

        explanation_match = EXPLANATION_RE.search(raw)
        if explanation_match:
            explanation = explanation_match.group(1).strip()

        options = []
        for key, text in OPTION_RE.findall(raw):
            options.append({'key': key, 'text': text.strip()})

        content = raw
        content = ANSWER_RE.sub('', content)
        content = EXPLANATION_RE.sub('', content)
        content = OPTION_RE.sub('', content).strip()

        question_type = 'choice' if options else ('blank' if '___' in content or '____' in content else 'unknown')

        return QuestionCandidate(
            index=index,
            content=content,
            options=options,
            answer=answer,
            explanation=explanation,
            question_type=question_type,
            difficulty=3,
            source_page=source_page,
            raw_ocr_text=raw,
            confidence_detail={'layout': 0.85, 'text': 0.9}
        )
