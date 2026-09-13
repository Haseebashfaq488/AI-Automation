import asyncio
import pytest
from app.registry import registry
from app.modules.gmail.pipelines.list_recent_emails_pipeline import ListRecentEmailsPipeline
from app.modules.gmail.skills import list_recent_emails
from app.modules.gmail.skills.list_recent_emails import ListRecentEmailsSkill


@pytest.fixture(autouse=True)
def setup_skill(monkeypatch):
    # ensure the skill is registered
    registry.register(ListRecentEmailsSkill())
    # force the "no credentials" path regardless of any real token.json
    monkeypatch.setattr(list_recent_emails, "_load_token_path", lambda: None)
    yield


@pytest.mark.asyncio
async def test_list_recent_emails_pipeline_no_creds():
    pipeline = ListRecentEmailsPipeline()
    result = await pipeline.run({"query": "test query"})
    # Without token.json the skill returns listed:false + error string
    assert isinstance(result, dict)
    assert result.get("success") == True
    assert result.get("result", {}).get("listed") == False
    assert "credentials not found" in result.get("result", {}).get("error", "")