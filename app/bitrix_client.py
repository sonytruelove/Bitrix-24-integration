import time

import requests


class BitrixApiError(Exception):
    def __init__(self, error: str, description: str):
        self.error = error
        self.description = description
        super().__init__(f"{error}: {description}")


class BitrixClient:
    """Тонкая обёртка над REST API Bitrix24 поверх входящего вебхука.

    Формат вызова: {webhook_url}/{method}.json
    https://apidocs.bitrix24.ru/api-reference/how-does-rest-work.html
    """

    def __init__(self, webhook_url: str, session: requests.Session | None = None, max_retries: int = 3):
        self._base_url = webhook_url.rstrip("/") + "/"
        self._session = session or requests.Session()
        self._max_retries = max_retries

    def call(self, method: str, params: dict | None = None) -> dict:
        url = f"{self._base_url}{method}.json"
        attempt = 0
        while True:
            response = self._session.post(url, json=params or {}, timeout=10)
            payload = response.json()

            if "error" in payload:
                # Bitrix24 отдаёт лимит как HTTP 200 + error=QUERY_LIMIT_EXCEEDED,
                # поэтому ретраим по коду ошибки, а не по статусу ответа.
                if payload["error"] == "QUERY_LIMIT_EXCEEDED" and attempt < self._max_retries:
                    attempt += 1
                    time.sleep(2 ** attempt)
                    continue
                raise BitrixApiError(payload["error"], payload.get("error_description", ""))

            return payload["result"]

    def batch(self, calls: dict[str, tuple[str, dict]], halt_on_error: bool = False) -> dict:
        """Групповой запрос: до 50 вызовов за один HTTP-запрос.

        calls: {"my_key": ("crm.lead.add", {"fields": {...}})}
        """
        cmd = {key: f"{method}?{self._to_query(params)}" for key, (method, params) in calls.items()}
        return self.call("batch", {"halt": int(halt_on_error), "cmd": cmd})

    @staticmethod
    def _to_query(params: dict) -> str:
        from urllib.parse import urlencode

        return urlencode(params, doseq=True)

    def add_lead(self, fields: dict) -> int:
        return self.call("crm.lead.add", {"fields": fields})

    def list_leads(self, filter_: dict | None = None, select: list[str] | None = None) -> list[dict]:
        return self.call(
            "crm.lead.list",
            {"filter": filter_ or {}, "select": select or ["ID", "TITLE", "STATUS_ID", "NAME", "PHONE", "EMAIL"]},
        )

    def update_lead(self, lead_id: int, fields: dict) -> bool:
        return self.call("crm.lead.update", {"id": lead_id, "fields": fields})
