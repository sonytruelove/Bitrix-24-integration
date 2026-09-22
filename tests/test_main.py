from fastapi.testclient import TestClient

from app.bitrix_client import BitrixApiError
from app.main import app, get_client


class FakeClient:
    def __init__(self, lead_id: int = 99, raise_error: bool = False):
        self._lead_id = lead_id
        self._raise_error = raise_error
        self.received_fields: dict | None = None

    def add_lead(self, fields: dict) -> int:
        self.received_fields = fields
        if self._raise_error:
            raise BitrixApiError("INVALID_ARGUMENT_VALUE", "bad field")
        return self._lead_id

    def list_leads(self, filter_=None, select=None):
        if int(filter_["ID"]) != self._lead_id:
            return []
        return [{"ID": str(self._lead_id), "TITLE": "Заявка", "STATUS_ID": "NEW", "NAME": "Иван"}]


def _client_with_fake(fake: FakeClient) -> TestClient:
    app.dependency_overrides[get_client] = lambda: fake
    return TestClient(app)


def test_create_lead_success():
    fake = FakeClient(lead_id=99)
    client = _client_with_fake(fake)

    response = client.post("/leads", json={"name": "Иван", "phone": "+79990001122"})

    assert response.status_code == 201
    assert response.json() == {"bitrix_id": 99}
    assert fake.received_fields["NAME"] == "Иван"
    app.dependency_overrides.clear()


def test_create_lead_bitrix_error_maps_to_502():
    fake = FakeClient(raise_error=True)
    client = _client_with_fake(fake)

    response = client.post("/leads", json={"name": "Иван", "phone": "+79990001122"})

    assert response.status_code == 502
    app.dependency_overrides.clear()


def test_get_lead_found():
    fake = FakeClient(lead_id=99)
    client = _client_with_fake(fake)

    response = client.get("/leads/99")

    assert response.status_code == 200
    assert response.json()["status"] == "NEW"
    app.dependency_overrides.clear()


def test_get_lead_not_found():
    fake = FakeClient(lead_id=99)
    client = _client_with_fake(fake)

    response = client.get("/leads/1")

    assert response.status_code == 404
    app.dependency_overrides.clear()
