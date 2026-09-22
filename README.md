# Bitrix24 Lead Sync

Мини-сервис синхронизации заявок с сайта в CRM Bitrix24 через REST API.

## Что делает

- `POST /leads` — принимает заявку с сайта (имя, телефон, email, комментарий),
  валидирует и создаёт лид в Bitrix24 через `crm.lead.add`.
- `GET /leads/{id}` — возвращает текущий статус лида (`crm.lead.list`).
- `POST /webhook/bitrix` — принимает исходящий вебхук Bitrix24 (например
  `ONCRMLEADUPDATE`), чтобы реагировать на изменения в CRM со стороны Bitrix24.

Получился минимальный, но настоящий двусторонний обмен: наружу (создание/чтение
лидов через входящий вебхук) и внутрь (приём событий CRM через исходящий вебхук).

## Архитектура

```
app/
  bitrix_client.py   REST-клиент: call/batch, обработка ошибок и лимита запросов
  schemas.py          Pydantic-модели запросов/ответов
  main.py             FastAPI: HTTP-слой, не знает деталей Bitrix24 API
  config.py            Настройки из .env
```

`BitrixClient` не зависит от FastAPI и покрыт тестами без обращения к сети
(HTTP-запросы подменены фейковой сессией) — так же замокан и в тестах `main.py`
через `Depends`.

## Быстрый запуск

```bash
python -m venv .venv
.venv/Scripts/activate      # Windows
pip install -r requirements.txt

cp .env.example .env
# впишите BITRIX_WEBHOOK_URL от вашего портала (см. ниже, как получить)

uvicorn app.main:app --reload
# Swagger: http://127.0.0.1:8000/docs
```

Тесты (не требуют реального Bitrix24):

```bash
pytest -q
```

## Как получить вебхук Bitrix24 для реального теста (5 минут)

1. Зарегистрировать бесплатный портал на bitrix24.ru.
2. В левом меню: **Разработчикам → Другое → Входящий вебхук**.
3. Выбрать права `crm` (Лиды, Сделки), скопировать URL вида
   `https://ваш-портал.bitrix24.ru/rest/1/xxxxxxxxxxxxxxxx/`.
4. Вставить в `.env` как `BITRIX_WEBHOOK_URL`.
5. Проверить:
   ```bash
   curl -X POST http://127.0.0.1:8000/leads \
     -H "Content-Type: application/json" \
     -d '{"name":"Иван Тестов","phone":"+79990001122","email":"test@example.com"}'
   ```
   Новый лид появится в разделе CRM → Лиды.

Для приёма исходящего вебхука: **Разработчикам → Другое → Исходящий вебхук**,
указать событие (например `ONCRMLEADUPDATE`) и URL вашего сервиса
`https://<ваш-домен>/webhook/bitrix` (для локальной разработки — туннель,
например ngrok).
