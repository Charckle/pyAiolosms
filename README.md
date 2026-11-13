# pyAiolosms

SMS gateway. This app holds the Lertify account. People and other apps send through users you create here.

The first visit opens a setup page where you create the admin account. That account lives in SQLite, not in `.env`.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open http://localhost:5000 and create the admin user.

Set `LERTIFY_API_KEY` and `LERTIFY_SENDER` in `.env` before sending. The sender must be one you already approved in Lertify. Restart the app after changing `.env`.

Docker:

```bash
cp .env.example .env
docker compose up -d --build
```

The site is on http://localhost:5044. The database is `data/sms.db`.

## Users

Admin can create users and give each one an API token. The token is shown once. It is stored only as a hash.

Read / Write users can send from the site. Read Only users can sign in and see their own log. Admins see every message.

## API

```bash
curl -X POST http://localhost:5000/api/v1/sms \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to": "+38640123456", "message": "Hello"}'
```

`to` can also be a local number such as `040123456`. Those get the country code from `DEFAULT_COUNTRY_CODE` (386). A success response is HTTP 202 with the Lertify message id.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Flask session secret |
| `DATA_DIR` | `data` | Directory for `sms.db` |
| `APP_NAME` | `pyAiolosms` | Name shown in the header |
| `ENVCONFIG` | `DEV` | `PROD` turns on secure session cookies |
| `READ_ONLY_MODE` | `False` | Blocks changes, including setup and sending |
| `LERTIFY_API_KEY` | — | Lertify API key |
| `LERTIFY_SENDER` | — | Approved sender name or number |
| `DEFAULT_COUNTRY_CODE` | `386` | Used for numbers that are not already international |
