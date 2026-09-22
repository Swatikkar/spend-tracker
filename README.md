# Spend Tracker

A small full-stack expense tracker. Users can register, log in, add expenses, filter their expense history, and view a monthly spending summary.

## Tech stack

- Python and FastAPI
- SQLAlchemy ORM
- SQLite
- Pydantic validation
- JWT authentication
- Plain HTML, CSS, and JavaScript
- Pytest

## Features

- `POST /expenses` creates an expense with an amount, category, optional note, and date.
- `GET /expenses` lists the logged-in user's expenses and supports `category`, `start_date`, and `end_date` filters.
- `GET /summary` returns the selected month's total, totals by category, and the percentage change from the previous month.
- `POST /auth/register` and `POST /auth/login` provide basic JWT authentication so each user only sees their own expenses.
- The summary flags categories whose spending increased by more than 20% compared with the previous month.
- A minimal browser UI supports registration, login, adding expenses, filtering expenses, and viewing the summary.

## Run locally

Python 3.10 or later is recommended.

```bash
python -m venv venv
```

Activate the environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Activate it on macOS or Linux:

```bash
source venv/bin/activate
```

Install dependencies and start the application:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` for the UI. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

The SQLite database is created automatically as `expenses.db` when the application starts.

## API usage

Register and log in first. Send the returned token to protected endpoints using this header:

```text
Authorization: Bearer <access_token>
```

Example expense body:

```json
{
  "amount": 250.50,
  "category": "Food",
  "note": "Team lunch",
  "date": "2026-09-22"
}
```

Example filters:

```text
GET /expenses?category=Food&start_date=2026-09-01&end_date=2026-09-30
GET /summary?month=2026-09
```

If `month` is omitted, the summary uses the current calendar month. The month-over-month percentage is `null` when the previous month has no spending because a percentage increase from zero cannot be calculated.

## Tests

Run the test suite from the project root:

```bash
pytest -q
```

The tests use a separate in-memory SQLite database and cover authentication, validation failures, filtering, user data isolation, summaries, month boundaries, and the spending insight.

## Design decisions

- Expense amounts use `Decimal`/SQL `Numeric` instead of floating-point values to avoid money rounding errors.
- Expense queries always include the authenticated user's ID so data is isolated between users.
- Month ranges use an inclusive start and exclusive next-month boundary, which also handles different month lengths.
- SQLite keeps setup simple while still satisfying the requirement for a real database.

## Improvements

I would use PostgreSQL instead of sqlite, pagination for large expense lists, edit/delete expense endpoints, more frontend feedback for API errors, change in allignment etc.

## AI usage

I used ChatGPT Codex to write test part,make the readme and suggestions for improvement, and Claude for help with the minimal frontend using simple html,css and javascript. I reviewed their generated code and readme and after doing certain changes finally kept those parts that allign with my planning and implementations. 
