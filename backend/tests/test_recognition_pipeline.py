from services.import_schema import DocumentPage
from services.recognition_pipeline import RecognitionPipeline
from services.ai_json import parse_ai_questions_json


def test_parse_ai_questions_json_strips_markdown_fence():
    text = '```json\n[{"content":"1+1=?","answer":"2","type":"blank","difficulty":1}]\n```'
    questions = parse_ai_questions_json(text)
    assert len(questions) == 1
    assert questions[0]['answer'] == '2'


def test_pipeline_segments_text_without_ai():
    pages = [DocumentPage(page=1, text='1. 1+1=?\nA. 1\nB. 2\n答案：2')]
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
        DocumentPage(page=1, text='1. 第一题\nA. 甲\nB. 乙\n答案：A'),
        DocumentPage(page=2, text='', images=[ImageAsset(path='img.png', url='/img.png', image_type='source_image')]),
        DocumentPage(page=3, text='2. 第三页题\nA. 丙\nB. 丁\n答案：B')
    ]
    candidates = RecognitionPipeline().recognize(pages)
    assert [c.source_page for c in candidates] == [1, 2, 3]


def test_pipeline_merges_late_answer_key_page_by_question_number():
    question_page = (
        '1. 以下哪項關於細胞膜「流動鑲嵌模型」的描述是正確的？\n'
        'A. 磷脂分子是固定的，而蛋白質分子可以橫向移動\n'
        'B. 細胞膜的流動性主要由膽固醇與磷脂的相互作用維持\n'
        'C. 蛋白質分子均勻地分佈在膜的表面\n'
        'D. 只有水分子能透過簡單擴散穿過磷脂雙分子層\n'
    )
    answer_page = (
        '1. 答案： B\n'
        '解析：磷脂雙分子層具有流動性（非固定）；蛋白質是不規則分佈的。\n'
    )
    candidates = RecognitionPipeline().recognize([
        DocumentPage(page=1, text=question_page),
        DocumentPage(page=10, text=answer_page)
    ])
    assert len(candidates) == 1
    assert candidates[0].answer == 'B'
    assert candidates[0].explanation.startswith('磷脂雙分子層具有流動性')


def test_pipeline_turns_image_parser_results_into_question_candidates():
    from services.import_schema import ImageAsset

    class FakeImageParser:
        def parse_image(self, path, subject=''):
            assert path == '/tmp/q.png'
            assert subject == '生物'
            return [{
                'content': '圖片中的題目？',
                'options': [{'key': 'A', 'text': '甲'}, {'key': 'B', 'text': '乙'}],
                'answer': 'B',
                'explanation': '圖片識別解析',
                'type': 'choice',
                'difficulty': 2
            }]

    pages = [DocumentPage(page=3, text='', images=[ImageAsset(path='/tmp/q.png', url='/static/q.png', image_type='source_image')])]
    candidates = RecognitionPipeline(image_parser=FakeImageParser()).recognize(pages, subject='生物')
    assert len(candidates) == 1
    assert candidates[0].content == '圖片中的題目？'
    assert candidates[0].answer == 'B'
    assert candidates[0].images[0].url == '/static/q.png'


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
