from services.import_schema import DocumentPage
from services.question_segmenter import QuestionSegmenter


def test_segment_numbered_choice_questions():
    text = '''
1. 集合 A={1,2,3}, B={2,3,4}，则 A∩B=？
A. {1}
B. {2,3}
C. {4}
D. {1,2,3,4}
答案：B
解析：交集取公共元素。

2. 函数 f(x)=2x+1，则 f(3)=？
A. 5
B. 6
C. 7
D. 8
答案：C
解析：2×3+1=7。
'''
    pages = [DocumentPage(page=1, text=text)]
    candidates = QuestionSegmenter().segment(pages)
    assert len(candidates) == 2
    assert candidates[0].content.startswith('集合 A=')
    assert candidates[0].answer == 'B'
    assert len(candidates[0].options) == 4
    assert candidates[1].answer == 'C'


def test_segment_blank_question():
    text = '1. 等差数列 a1=1, d=2，则 a10=___\n答案：19\n解析：公式代入。'
    pages = [DocumentPage(page=1, text=text)]
    candidates = QuestionSegmenter().segment(pages)
    assert len(candidates) == 1
    assert candidates[0].question_type == 'blank'
    assert candidates[0].answer == '19'


def test_segment_keeps_source_page():
    text = '1. 速度单位是？\nA. m/s\nB. kg\n答案：A'
    pages = [DocumentPage(page=3, text=text)]
    candidates = QuestionSegmenter().segment(pages)
    assert candidates[0].source_page == 3
