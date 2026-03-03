"""Tests for the health check endpoint."""

from __future__ import annotations


def test_health_returns_200(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_response_schema(client):
    response = client.get("/api/v1/health")
    body = response.json()

    assert body["status"] == "ok"
    assert "version" in body
    assert "environment" in body
    assert "timestamp" in body


def test_health_environment_is_test(client):
    response = client.get("/api/v1/health")
    body = response.json()
    assert body["environment"] == "test"
