from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint_returns_answer(monkeypatch):
    monkeypatch.setenv("APP_DATABASE_PATH", "data/test_api_chat.db")
    client = TestClient(create_app())

    response = client.post(
        "/api/chat",
        json={"session_id": "demo", "message": "我预算 4000，想买适合上课记笔记的平板，有没有优惠"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["final_answer"]
    assert body["trace_steps"]
    assert body["recommended_products"]


def test_web_index_returns_html():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "多 Agent 电商助手" in response.text


def test_web_index_contains_workbench_regions():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert 'data-region="chat-workspace"' in response.text
    assert 'data-region="product-recommendations"' in response.text
    assert 'data-region="coupon-plan"' in response.text
    assert 'data-region="order-status"' in response.text
    assert 'data-region="agent-trace"' in response.text
