import pytest

from app.bitrix_client import BitrixApiError, BitrixClient


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class FakeSession:
    def __init__(self, responses: list[dict]):
        self._responses = responses
        self.calls: list[str] = []

    def post(self, url: str, json: dict, timeout: int):
        self.calls.append(url)
        return FakeResponse(self._responses.pop(0))


def test_add_lead_returns_new_id():
    session = FakeSession([{"result": 42}])
    client = BitrixClient("https://x.bitrix24.ru/rest/1/token", session=session)

    lead_id = client.add_lead({"TITLE": "Test"})

    assert lead_id == 42
    assert session.calls == ["https://x.bitrix24.ru/rest/1/token/crm.lead.add.json"]


def test_call_raises_on_error():
    session = FakeSession([{"error": "INVALID_ARGUMENT_VALUE", "error_description": "bad field"}])
    client = BitrixClient("https://x.bitrix24.ru/rest/1/token", session=session)

    with pytest.raises(BitrixApiError) as exc_info:
        client.add_lead({"TITLE": ""})

    assert exc_info.value.error == "INVALID_ARGUMENT_VALUE"


def test_call_retries_on_rate_limit(monkeypatch):
    monkeypatch.setattr("app.bitrix_client.time.sleep", lambda _: None)
    session = FakeSession(
        [
            {"error": "QUERY_LIMIT_EXCEEDED", "error_description": "too many requests"},
            {"result": 7},
        ]
    )
    client = BitrixClient("https://x.bitrix24.ru/rest/1/token", session=session)

    lead_id = client.add_lead({"TITLE": "Test"})

    assert lead_id == 7
    assert len(session.calls) == 2
