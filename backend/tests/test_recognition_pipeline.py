from services.import_schema import DocumentPage
from services.recognition_pipeline import RecognitionPipeline
from services.ai_json import parse_ai_questions_json


def test_parse_ai_questions_json_strips_markdown_fence():
    text = '```json\n[{"content":"1+1=?","answer":"2","type":"blank","difficulty":1}]\n```'
    questions = parse_ai_questions_json(text)
    assert len(questions) == 1
    assert questions[0]['answer'] == '2'


def test_pipeline_segments_text_without_ai():
    pages = [DocumentPage(page=1, text='1. 1+1=?\n答案：2')]
    candidates = RecognitionPipeline().recognize(pages, subject='数学')
    assert len(candidates) == 1
    assert candidates[0].answer == '2'


def test_pipeline_marks_image_only_as_low_confidence_candidate(tmp_path):
    from services.import_schema import ImageAsset
    pages = [DocumentPage(page=1, text='', images=[ImageAsset(path='x.png', url='/x.png', image_type='source_image')])]
    candidates = RecognitionPipeline().recognize(pages, subject='数学')
    assert len(candidates) == 1
    assert candidates[0].confidence_detail['text'] < 0.5
    assert candidates[0].images[0].url == '/x.png'


def test_pipeline_preserves_page_order_for_mixed_pages():
    from services.import_schema import ImageAsset

    pages = [
        DocumentPage(page=1, text='1. 第一题\n答案：A'),
        DocumentPage(page=2, text='', images=[ImageAsset(path='img.png', url='/img.png', image_type='source_image')]),
        DocumentPage(page=3, text='2. 第三页题\n答案：B')
    ]
    candidates = RecognitionPipeline().recognize(pages)
    assert [c.source_page for c in candidates] == [1, 2, 3]


def test_normalizer_prepares_parsed_question_payload():
    from services.import_schema import QuestionCandidate, FormulaAsset
    from services.question_normalizer import QuestionNormalizer

    candidate = QuestionCandidate(
        index=1,
        content='求 x^2=4',
        answer='±2',
        question_type='blank',
        formulas=[FormulaAsset(latex='x^2=4', image_url='/static/f.png')],
        confidence_detail={'text': 0.9, 'formula': 0.8}
    )
    payload = QuestionNormalizer().to_parsed_payload(candidate, defaults={
        'exam_type': 'gaokao',
        'subject': '数学',
        'grade': '高一',
        'knowledge_point': '方程'
    })

    assert payload['content'] == '求 x^2=4'
    assert payload['subject'] == '数学'
    assert payload['formula_latex'] == ['x^2=4']
    assert payload['confidence'] == 0.85
