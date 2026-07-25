import re
from services.import_schema import QuestionCandidate


QUESTION_SPLIT_RE = re.compile(r'(?:^|\n)[ \t]*(?:(\d+)[\.、．]|第[ \t]*(\d+)[ \t]*[題题])[ \t]*')
LEADING_NUMBER_RE = re.compile(r'^[ \t]*(?:(\d+)[\.、．]|第[ \t]*(\d+)[ \t]*[題题])[ \t]*')
OPTION_RE = re.compile(r'^\s*([A-Fa-fＡ-Ｆａ-ｆ])\s*[\.、．]?\s*(.+)$', re.MULTILINE)
ANSWER_RE = re.compile(r'(?:答案|Answer)\s*[:：]\s*([^\n解析]+)')
EXPLANATION_RE = re.compile(r'(?:解析|Explanation)\s*[:：]\s*([\s\S]+)$')
ANSWER_BLOCK_RE = re.compile(r'^\s*(?:答案|Answer)\s*[:：]')
FULLWIDTH_MAP = str.maketrans({'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'ａ': 'A', 'ｂ': 'B', 'ｃ': 'C', 'ｄ': 'D', 'ｅ': 'E', 'ｆ': 'F'})

SECTION_START_RE = re.compile(r'(?:甲部|甲\s*部|Section\s*A|SECTION\s*A)', re.IGNORECASE)
SECTION_END_RE = re.compile(r'(?:乙部|乙\s*部|Section\s*B|SECTION\s*B|丙部|Section\s*C)', re.IGNORECASE)
ANSWER_KEY_HEADER_RE = re.compile(r'(?:评卷参考|評卷參考|Answer\s*Key|答案卷|答案表)', re.IGNORECASE)
ANSWER_RATE_RE = re.compile(r'(\d+)\s*[-\.、．]\s*([A-Da-fＡ-Ｄ])\s*[\(（]\s*(\d+)\s*%\s*[\)）]')


class QuestionSegmenter:
    def segment(self, pages):
        all_text = '\n'.join(p.text for p in pages)
        section_start = self._find_section_start(all_text)
        section_end = self._find_section_end(all_text, section_start)
        answer_key_start = self._find_answer_key_start(all_text)

        questions = {}
        order = []
        answer_blocks = {}

        for page in pages:
            page_text = page.text
            if section_start is not None:
                page_start_in_all = all_text.index(page_text) if page_text in all_text else 0
                page_end_in_all = page_start_in_all + len(page_text)
                if page_end_in_all <= section_start:
                    continue
                if section_end is not None and page_start_in_all >= section_end:
                    continue
                if answer_key_start is not None and page_start_in_all >= answer_key_start:
                    continue

            for number, raw in self._split_page(page.text):
                if self._is_answer_block(raw):
                    answer_blocks[number] = (raw, page.page)
                    continue
                candidate = self._parse_raw_question(raw, index=len(order) + 1, source_page=page.page)
                if not candidate or not candidate.content.strip():
                    continue
                if candidate.question_type != 'choice':
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

        if answer_key_start is not None:
            answer_key_text = all_text[answer_key_start:]
            for match in ANSWER_RATE_RE.finditer(answer_key_text):
                number = int(match.group(1))
                answer = match.group(2).translate(FULLWIDTH_MAP).upper()
                rate = int(match.group(3))
                candidate = questions.get(number)
                if candidate:
                    candidate.answer = answer
                    candidate.confidence_detail['correct_rate'] = rate / 100.0

        ordered = []
        for index, number in enumerate(order, start=1):
            candidate = questions[number]
            candidate.index = index
            ordered.append(candidate)
        return ordered

    def _find_section_start(self, all_text):
        match = SECTION_START_RE.search(all_text)
        if match:
            return match.start()
        return None

    def _find_section_end(self, all_text, section_start):
        if section_start is None:
            return None
        match = SECTION_END_RE.search(all_text, section_start)
        if match:
            return match.start()
        return None

    def _find_answer_key_start(self, all_text):
        match = ANSWER_KEY_HEADER_RE.search(all_text)
        if match:
            return match.start()
        return None

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
