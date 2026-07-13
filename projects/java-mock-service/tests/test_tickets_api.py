from fastapi.testclient import TestClient


def test_create_ticket_api_returns_created_ticket(client: TestClient) -> None:
    response = client.post(
        "/tickets",
        json={
            "requester_id": "demo_user_001",
            "title": "订单 A1001 未发货",
            "description": "用户反馈订单迟迟未发货。",
            "category": "complaint",
            "priority": "high",
            "related_order_id": "A1001",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ticket_id"] == "T1001"
    assert data["requester_id"] == "demo_user_001"
    assert data["category"] == "complaint"


def test_create_ticket_api_reuses_ticket_for_same_idempotency_key(
    client: TestClient,
) -> None:
    request_body = {
        "requester_id": "demo_user_001",
        "title": "订单 A1001 未发货",
        "description": "用户反馈订单迟迟未发货。",
        "category": "complaint",
        "priority": "high",
        "related_order_id": "A1001",
    }

    first_response = client.post(
        "/tickets",
        headers={"Idempotency-Key": "ticket-create-key-001"},
        json=request_body,
    )
    second_response = client.post(
        "/tickets",
        headers={"Idempotency-Key": "ticket-create-key-001"},
        json=request_body,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json() == second_response.json()


def test_create_ticket_api_rejects_idempotency_key_reused_with_new_arguments(
    client: TestClient,
) -> None:
    request_body = {
        "requester_id": "demo_user_001",
        "title": "订单 A1001 未发货",
        "description": "用户反馈订单迟迟未发货。",
        "category": "complaint",
        "priority": "high",
        "related_order_id": "A1001",
    }
    client.post(
        "/tickets",
        headers={"Idempotency-Key": "ticket-create-key-002"},
        json=request_body,
    )

    response = client.post(
        "/tickets",
        headers={"Idempotency-Key": "ticket-create-key-002"},
        json={**request_body, "related_order_id": "A1002"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "TICKET_IDEMPOTENCY_KEY_CONFLICT"
