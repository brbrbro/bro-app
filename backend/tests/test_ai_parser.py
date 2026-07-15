def test_ai_parser_reads_unified_config(monkeypatch):
    monkeypatch.setenv('AI_API_KEY', 'test-key')
    monkeypatch.setenv('AI_BASE_URL', 'https://example.com/v3')
    monkeypatch.setenv('AI_MODEL', 'test-model')

    from services.ai_parser import AIParser
    parser = AIParser()
    assert parser.config['api_key'] == 'test-key'
    assert parser.config['base_url'] == 'https://example.com/v3'
    assert parser.config['model'] == 'test-model'


def test_answer_explainer_reads_unified_config(monkeypatch):
    monkeypatch.setenv('AI_API_KEY', 'explainer-key')
    monkeypatch.setenv('AI_BASE_URL', 'https://explainer.example.com/v3')
    monkeypatch.setenv('AI_MODEL', 'explainer-model')

    from services.answer_explainer import AnswerExplainer
    explainer = AnswerExplainer()
    assert explainer.config['api_key'] == 'explainer-key'
    assert explainer.config['base_url'] == 'https://explainer.example.com/v3'
    assert explainer.config['model'] == 'explainer-model'
