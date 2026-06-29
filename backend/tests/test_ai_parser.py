def test_ai_parser_uses_ark_openai_compatible_client(monkeypatch):
    captured = {}

    class FakeOpenAI:
        def __init__(self, api_key=None, base_url=None):
            captured['api_key'] = api_key
            captured['base_url'] = base_url

    monkeypatch.setenv('AI_PROVIDER', 'ark')
    monkeypatch.setenv('ARK_API_KEY', 'ark-test-key')
    monkeypatch.setenv('ARK_BASE_URL', 'https://ark.example.com/api/v3')
    monkeypatch.setenv('ARK_MODEL', 'GLM-5.2')
    monkeypatch.setattr('services.ai_parser.OpenAI', FakeOpenAI)

    from services.ai_parser import AIParser
    parser = AIParser()
    parser._get_client()

    assert captured['api_key'] == 'ark-test-key'
    assert captured['base_url'] == 'https://ark.example.com/api/v3'
    assert parser.model == 'GLM-5.2'


def test_ai_parser_openai_provider_keeps_default_base_url(monkeypatch):
    captured = {}

    class FakeOpenAI:
        def __init__(self, api_key=None, base_url=None):
            captured['api_key'] = api_key
            captured['base_url'] = base_url

    monkeypatch.setenv('AI_PROVIDER', 'openai')
    monkeypatch.setenv('OPENAI_API_KEY', 'openai-test-key')
    monkeypatch.delenv('ARK_API_KEY', raising=False)
    monkeypatch.setattr('services.ai_parser.OpenAI', FakeOpenAI)

    from services.ai_parser import AIParser
    parser = AIParser()
    parser._get_client()

    assert captured['api_key'] == 'openai-test-key'
    assert captured['base_url'] is None
