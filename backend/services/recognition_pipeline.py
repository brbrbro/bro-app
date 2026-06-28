from services.import_schema import QuestionCandidate
from services.question_segmenter import QuestionSegmenter


class RecognitionPipeline:
    def __init__(self):
        self.segmenter = QuestionSegmenter()

    def recognize(self, pages, subject=''):
        candidates = []
        text_pages = [p for p in pages if p.text and p.text.strip()]
        image_only_pages = [p for p in pages if not (p.text and p.text.strip()) and p.images]

        if text_pages:
            candidates.extend(self.segmenter.segment(text_pages))

        for page in image_only_pages:
            candidates.append(QuestionCandidate(
                index=0,
                content='[图片题待识别]',
                options=[],
                answer='',
                explanation='',
                question_type='unknown',
                difficulty=3,
                source_page=page.page,
                raw_ocr_text='',
                images=page.images,
                confidence_detail={'text': 0.2, 'layout': 0.4, 'image': 0.8}
            ))

        candidates.sort(key=lambda candidate: candidate.source_page or 0)
        for index, candidate in enumerate(candidates, start=1):
            candidate.index = index
        return candidates
