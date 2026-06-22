from services.import_schema import QuestionCandidate
from services.question_segmenter import QuestionSegmenter


class RecognitionPipeline:
    def __init__(self):
        self.segmenter = QuestionSegmenter()

    def recognize(self, pages, subject=''):
        candidates = []

        for page in pages:
            if page.text and page.text.strip():
                for candidate in self.segmenter.segment([page]):
                    candidate.index = len(candidates) + 1
                    candidates.append(candidate)
            elif page.images:
                candidates.append(QuestionCandidate(
                    index=len(candidates) + 1,
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

        return candidates
