import re
from services.import_schema import QuestionCandidate


QUESTION_SPLIT_RE = re.compile(r'(?:^|\n)\s*(?:(\d+)[\.、．]|第\s*(\d+)\s*[題题])\s*')
LEADING_NUMBER_RE = re.compile(r'^\s*(?:(\d+)[\.、．]|第\s*(\d+)\s*[題题])\s*')
OPTION_RE = re.compile(r'^\s*([A-Fa-fＡ-Ｆａ-ｆ])\s*[\.、．]?\s*(.+)$', re.MULTILINE)
ANSWER_RE = re.compile(r'(?:答案|Answer)\s*[:：]\s*([^\n解析]+)')
EXPLANATION_RE = re.compile(r'(?:解析|Explanation)\s*[:：]\s*([\s\S]+)$')
ANSWER_BLOCK_RE = re.compile(r'^\s*(?:答案|Answer)\s*[:：]')
FULLWIDTH_MAP = str.maketrans({'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'ａ': 'A', 'ｂ': 'B', 'ｃ': 'C', 'ｄ': 'D', 'ｅ': 'E', 'ｆ': 'F'})


class QuestionSegmenter:
    def segment(self, pages):
        questions = {}
        order = []
        answer_blocks = {}

        for page in pages:
            for number, raw in self._split_page(page.text):
                if self._is_answer_block(raw):
                    answer_blocks[number] = (raw, page.page)
                    continue
                candidate = self._parse_raw_question(raw, index=len(order) + 1, source_page=page.page)
                if not candidate or not candidate.content.strip():
                    continue
                if number in questions:
                    continue
                questions[number] = candidate
                order.append(number)

        for number, (raw, _) in answer_blocks.items():
            candidate = questions.get(number)
            if not candidate:
                continue
            answer_match = ANSWER_RE.search(raw)
            if answer_match and not candidate.answer:
                candidate.answer = answer_match.group(1).strip()
            explanation_match = EXPLANATION_RE.search(raw)
            if explanation_match and not candidate.explanation:
                candidate.explanation = explanation_match.group(1).strip()

        ordered = []
        for index, number in enumerate(order, start=1):
            candidate = questions[number]
            candidate.index = index
            ordered.append(candidate)
        return ordered

    def _split_page(self, text):
        matches = list(QUESTION_SPLIT_RE.finditer(text))
        if not matches:
            stripped = text.strip()
            if not stripped:
                return []
            number_match = LEADING_NUMBER_RE.match(stripped)
            number = self._match_number(number_match) if number_match else None
            return [(number, stripped)]

        parts = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            chunk = text[start:end].strip()
            if not chunk:
                continue
            parts.append((self._match_number(match), chunk))
        return parts

    def _match_number(self, match):
        if not match:
            return None
        return int(match.group(1) or match.group(2))

    def _is_answer_block(self, raw):
        body = LEADING_NUMBER_RE.sub('', raw).strip()
        return bool(ANSWER_BLOCK_RE.match(body))

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
            key = key.translate(FULLWIDTH_MAP).upper()
            options.append({'key': key, 'text': text.strip()})

        content = LEADING_NUMBER_RE.sub('', raw)
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
