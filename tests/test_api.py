from decimal import Decimal

import pytest


def add_expense(client, headers, amount, category, expense_date, note=None):
    return client.post(
        "/expenses",
        headers=headers,
        json={
            "amount": amount,
            "category": category,
            "note": note,
            "date": expense_date,
        },
    )


def register_and_login(client, email):
    password = "secure123"
    assert client.post(
        "/auth/register",
        json={"email": email, "password": password},
    ).status_code == 201
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_register_login_and_reject_invalid_login(client):
    response = client.post(
        "/auth/register",
        json={"email": "person@example.com", "password": "secure123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "person@example.com"

    duplicate = client.post(
        "/auth/register",
        json={"email": "person@example.com", "password": "secure123"},
    )
    assert duplicate.status_code == 400

    invalid_login = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "wrong-password"},
    )
    assert invalid_login.status_code == 401


def test_expense_endpoints_require_authentication(client):
    expense = client.post(
        "/expenses",
        json={
            "amount": "100.00",
            "category": "Food",
            "note": None,
            "date": "2026-09-01",
        },
    )
    assert expense.status_code == 401
    assert client.get("/expenses").status_code == 401
    assert client.get("/summary").status_code == 401


def test_create_and_list_expense(client, auth_headers):
    response = add_expense(
        client,
        auth_headers,
        "125.50",
        "Food",
        "2026-09-10",
        "Lunch",
    )
    assert response.status_code == 201
    created = response.json()
    assert Decimal(str(created["amount"])) == Decimal("125.50")
    assert created["category"] == "Food"
    assert created["note"] == "Lunch"

    response = client.get("/expenses", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == created["id"]


@pytest.mark.parametrize(
    "payload",
    [
        {"amount": "0", "category": "Food", "date": "2026-09-10"},
        {"amount": "-5", "category": "Food", "date": "2026-09-10"},
        {"amount": "10", "category": "   ", "date": "2026-09-10"},
        {"amount": "10.999", "category": "Food", "date": "2026-09-10"},
        {"amount": "10", "category": "Food", "date": "not-a-date"},
    ],
)
def test_create_expense_rejects_invalid_input(client, auth_headers, payload):
    response = client.post("/expenses", headers=auth_headers, json=payload)
    assert response.status_code == 422


def test_expense_filters_and_invalid_date_range(client, auth_headers):
    add_expense(client, auth_headers, "10.00", "Food", "2026-08-31")
    add_expense(client, auth_headers, "20.00", "Travel", "2026-09-10")
    add_expense(client, auth_headers, "30.00", "Food", "2026-09-20")

    response = client.get(
        "/expenses?category=Food&start_date=2026-09-01&end_date=2026-09-30",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert Decimal(str(response.json()[0]["amount"])) == Decimal("30.00")

    invalid_range = client.get(
        "/expenses?start_date=2026-09-30&end_date=2026-09-01",
        headers=auth_headers,
    )
    assert invalid_range.status_code == 400
    assert invalid_range.json()["detail"] == "start_date cannot be later than end_date"


def test_users_only_see_their_own_expenses(client):
    first_user = register_and_login(client, "first@example.com")
    second_user = register_and_login(client, "second@example.com")

    add_expense(client, first_user, "10.00", "Food", "2026-09-01")
    add_expense(client, second_user, "99.00", "Travel", "2026-09-02")

    first_expenses = client.get("/expenses", headers=first_user).json()
    second_expenses = client.get("/expenses", headers=second_user).json()

    assert [expense["category"] for expense in first_expenses] == ["Food"]
    assert [expense["category"] for expense in second_expenses] == ["Travel"]


def test_summary_calculates_totals_categories_and_month_change(client, auth_headers):
    add_expense(client, auth_headers, "100.00", "Food", "2026-08-05")
    add_expense(client, auth_headers, "100.00", "Travel", "2026-08-12")
    add_expense(client, auth_headers, "150.00", "Food", "2026-09-03")
    add_expense(client, auth_headers, "150.00", "Travel", "2026-09-18")

    response = client.get("/summary?month=2026-09", headers=auth_headers)
    assert response.status_code == 200
    summary = response.json()

    assert Decimal(str(summary["total_spend"])) == Decimal("300.00")
    assert Decimal(str(summary["previous_month_total"])) == Decimal("200.00")
    assert Decimal(str(summary["spend_by_category"]["Food"])) == Decimal("150.00")
    assert Decimal(str(summary["spend_by_category"]["Travel"])) == Decimal("150.00")
    assert summary["month_over_month_change_percentage"] == 50.0
    assert len(summary["insights"]) == 2


def test_summary_handles_year_boundary_and_no_previous_spend(client, auth_headers):
    add_expense(client, auth_headers, "75.00", "Bills", "2026-01-15")

    response = client.get("/summary?month=2026-01", headers=auth_headers)
    assert response.status_code == 200
    summary = response.json()

    assert Decimal(str(summary["total_spend"])) == Decimal("75.00")
    assert Decimal(str(summary["previous_month_total"])) == Decimal("0.00")
    assert summary["month_over_month_change_percentage"] is None
    assert summary["insights"] == []


def test_summary_rejects_invalid_month(client, auth_headers):
    response = client.get("/summary?month=2026-13", headers=auth_headers)
    assert response.status_code == 400
    assert "YYYY-MM" in response.json()["detail"]

