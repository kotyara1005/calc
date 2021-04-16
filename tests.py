import asyncio
import uuid

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
def truncate_db(test_app):
    from app.models import database

    asyncio.get_event_loop().run_until_complete(
        database.execute(
            """
                TRUNCATE TABLE transaction RESTART IDENTITY;
            """
        )
    )
    asyncio.get_event_loop().run_until_complete(
        database.execute(
            """
                TRUNCATE TABLE wallet RESTART IDENTITY;
            """
        )
    )


def test_ping(test_app):
    response = test_app.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"text": "pong"}


def test_create_wallet(test_app, truncate_db):
    response = test_app.post(
        "/wallet", json={"client_id": 1, "currency": "USD"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["success"]
    assert data["errors"] == []
    assert data["result"]["wallet"]["client_id"] == 1
    assert data["result"]["wallet"]["amount"] == 0
    assert data["result"]["wallet"]["currency"] == "USD"


def test_create_wallet_conflict(test_app, truncate_db):
    response = test_app.post(
        "/wallet", json={"client_id": 1, "currency": "USD"}
    )
    assert response.status_code == 200
    response = test_app.post(
        "/wallet", json={"client_id": 1, "currency": "USD"}
    )
    assert response.status_code == 409


def test_add_money(test_app, truncate_db):
    response = test_app.post(
        "/wallet", json={"client_id": 101, "currency": "USD"}
    )
    assert response.status_code == 200

    wallet_id = response.json()["result"]["wallet"]["id"]
    request_id = str(uuid.uuid4())
    response = test_app.post(
        "/money/add",
        json={
            "wallet_id": wallet_id,
            "request_id": request_id,
            "amount": 10.1,
            "currency": "USD",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "errors": [],
        "result": {
            "wallet": {
                "id": wallet_id,
                "client_id": 101,
                "amount": 10.1,
                "currency": "USD",
            },
            "tr": {
                "id": 1,
                "from_wallet_id": None,
                "to_wallet_id": 1,
                "request_id": request_id,
                "amount": 10.1,
                "currency": "USD",
            },
        },
    }


def test_add_money_negative_amount(test_app, truncate_db):
    response = test_app.post(
        "/money/add",
        json={
            "wallet_id": 1,
            "request_id": str(uuid.uuid4()),
            "amount": -10,
            "currency": "USD",
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "errors": [
            {
                "loc": ["body", "amount"],
                "msg": "value should be greater then zero",
                "type": "value_error",
            }
        ],
        "result": None,
    }


def test_add_money_wallet_not_found(test_app, truncate_db):
    request_id = str(uuid.uuid4())
    response = test_app.post(
        "/money/add",
        json={
            "wallet_id": 1,
            "request_id": request_id,
            "amount": 10.1,
            "currency": "USD",
        },
    )
    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "errors": ["Wallet(id=1) not found"],
        "result": None,
    }


def test_send_money(test_app, truncate_db):
    response = test_app.post(
        "/wallet", json={"client_id": 1, "currency": "USD"}
    )
    assert response.status_code == 200
    wallet_id_from = response.json()["result"]["wallet"]["id"]

    response = test_app.post(
        "/wallet", json={"client_id": 2, "currency": "USD"}
    )
    assert response.status_code == 200
    wallet_id_to = response.json()["result"]["wallet"]["id"]

    response = test_app.post(
        "/money/add",
        json={
            "wallet_id": wallet_id_from,
            "request_id": str(uuid.uuid4()),
            "amount": 1000,
            "currency": "USD",
        },
    )
    assert response.status_code == 200

    request_id = str(uuid.uuid4())

    response = test_app.post(
        "/money/send",
        json={
            "from_wallet_id": wallet_id_from,
            "to_wallet_id": wallet_id_to,
            "request_id": request_id,
            "amount": 500,
            "currency": "USD",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "errors": [],
        "result": {
            "wallet_from": {
                "id": 1,
                "client_id": 1,
                "amount": 500.0,
                "currency": "USD",
            },
            "wallet_to": {
                "id": 2,
                "client_id": 2,
                "amount": 500.0,
                "currency": "USD",
            },
            "tr": {
                "id": 2,
                "from_wallet_id": 1,
                "to_wallet_id": 2,
                "request_id": request_id,
                "amount": 500,
                "currency": "USD",
            },
        },
    }


def test_send_money_self_sending(test_app, truncate_db):
    request_id = str(uuid.uuid4())
    response = test_app.post(
        "/money/send",
        json={
            "from_wallet_id": 1,
            "to_wallet_id": 1,
            "request_id": request_id,
            "amount": 500,
            "currency": "USD",
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "errors": [
            {
                "loc": ["body", "__root__"],
                "msg": "self sending",
                "type": "value_error",
            }
        ],
        "result": None,
    }


def test_send_money_not_enough_money(test_app, truncate_db):
    response = test_app.post(
        "/wallet", json={"client_id": 1, "currency": "USD"}
    )
    assert response.status_code == 200
    wallet_id_from = response.json()["result"]["wallet"]["id"]

    response = test_app.post(
        "/wallet", json={"client_id": 2, "currency": "USD"}
    )
    assert response.status_code == 200
    wallet_id_to = response.json()["result"]["wallet"]["id"]

    request_id = str(uuid.uuid4())

    response = test_app.post(
        "/money/send",
        json={
            "from_wallet_id": wallet_id_from,
            "to_wallet_id": wallet_id_to,
            "request_id": request_id,
            "amount": 500,
            "currency": "USD",
        },
    )
    assert response.status_code == 402
    assert response.json() == {
        "success": False,
        "errors": ["not enough money"],
        "result": None,
    }


def test_send_money_not_enough_money_wallet_id_from_not_found(
    test_app, truncate_db
):
    request_id = str(uuid.uuid4())

    response = test_app.post(
        "/money/send",
        json={
            "from_wallet_id": 102,
            "to_wallet_id": 101,
            "request_id": request_id,
            "amount": 500,
            "currency": "USD",
        },
    )
    assert response.status_code == 404


def test_send_money_not_enough_money_wallet_id_to_not_found(
    test_app, truncate_db
):
    response = test_app.post(
        "/wallet", json={"client_id": 1, "currency": "USD"}
    )
    assert response.status_code == 200
    wallet_id_from = response.json()["result"]["wallet"]["id"]

    request_id = str(uuid.uuid4())

    response = test_app.post(
        "/money/send",
        json={
            "from_wallet_id": wallet_id_from,
            "to_wallet_id": 100,
            "request_id": request_id,
            "amount": 500,
            "currency": "USD",
        },
    )
    assert response.status_code == 404
