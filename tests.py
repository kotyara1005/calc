import asyncio

import pytest
from fastapi.testclient import TestClient

from app.app import create_app


@pytest.fixture(scope="session")
def test_app():
    app = create_app()
    client = TestClient(app)
    asyncio.get_event_loop().run_until_complete(app.router.startup())
    yield client
    asyncio.get_event_loop().run_until_complete(app.router.shutdown())


@pytest.fixture()
def init_db(test_app):
    from app.commands import drop_db, init_db

    asyncio.get_event_loop().run_until_complete(drop_db())
    asyncio.get_event_loop().run_until_complete(init_db())


def test_ping(test_app):
    response = test_app.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"text": "pong"}


def test_get_states(test_app, init_db):
    response = test_app.get("/states")
    assert response.status_code == 200

    data = response.json()
    assert data["success"]
    assert data["errors"] == []
    assert data["result"]["state_codes"] == ["UT", "NV", "TX", "AL", "CA"]


def test_compute_total_price(test_app, init_db):
    response = test_app.post(
        "/total_price",
        json={"amount": 3000, "price_for_one": 3.5, "state_code": "TX"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data == {
        "success": True,
        "errors": [],
        "result": {
            "price_info": {
                "price": "10500.00",
                "discount_value": "1050.00",
                "price_with_discount": "9450.00",
                "taxes": "590.63",
                "total_price": "10040.63",
            },
            "discount": {"min_price": 10000, "discount": 0.1},
            "state_tax": {"state_code": "TX", "tax_rate": 0.0625},
        },
    }


def test_compute_total_no_discount(test_app, init_db):
    response = test_app.post(
        "/total_price",
        json={"amount": 1, "price_for_one": 1, "state_code": "UT"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data == {
        "success": True,
        "errors": [],
        "result": {
            "price_info": {
                "price": "1.00",
                "discount_value": "0.00",
                "price_with_discount": "1.00",
                "taxes": "0.07",
                "total_price": "1.07",
            },
            "discount": None,
            "state_tax": {"state_code": "UT", "tax_rate": 0.0685},
        },
    }


@pytest.mark.parametrize(
    "test_input,errors",
    [
        (
            {"amount": 1, "price_for_one": 1.23, "state_code": "INVALID"},
            ["invalid state code"],
        ),
        (
            {"amount": 0, "price_for_one": 1.23, "state_code": "TX"},
            [
                {
                    "ctx": {"limit_value": 0},
                    "loc": ["body", "amount"],
                    "msg": "ensure this value is greater than 0",
                    "type": "value_error.number.not_gt",
                }
            ],
        ),
        (
            {"amount": 1.2, "price_for_one": 1.23, "state_code": "TX"},
            [
                {
                    "loc": ["body", "amount"],
                    "msg": "value is not a valid integer",
                    "type": "type_error.integer",
                }
            ],
        ),
        (
            {"amount": -1, "price_for_one": 1.23, "state_code": "TX"},
            [
                {
                    "ctx": {"limit_value": 0},
                    "loc": ["body", "amount"],
                    "msg": "ensure this value is greater than 0",
                    "type": "value_error.number.not_gt",
                }
            ],
        ),
        (
            {"amount": 1, "price_for_one": -1, "state_code": "TX"},
            [
                {
                    "ctx": {"limit_value": "0"},
                    "loc": ["body", "price_for_one"],
                    "msg": "ensure this value is greater than 0",
                    "type": "value_error.number.not_gt",
                }
            ],
        ),
        (
            {"amount": 1, "price_for_one": 0, "state_code": "TX"},
            [
                {
                    "ctx": {"limit_value": "0"},
                    "loc": ["body", "price_for_one"],
                    "msg": "ensure this value is greater than 0",
                    "type": "value_error.number.not_gt",
                }
            ],
        ),
    ],
)
def test_compute_total_invalid_input(test_app, init_db, test_input, errors):
    response = test_app.post("/total_price", json=test_input,)
    assert response.status_code == 422

    data = response.json()
    assert data == {
        "success": False,
        "errors": errors,
        "result": None,
    }
