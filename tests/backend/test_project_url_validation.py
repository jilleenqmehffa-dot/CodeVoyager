import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import InvalidProjectUrlError
from app.main import app
from app.services.projects import validate_github_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/example/codevoyager", "https://github.com/example/codevoyager"),
        (" https://www.github.com/example/codevoyager.git/ ", "https://github.com/example/codevoyager"),
    ],
)
def test_validate_github_url(url: str, expected: str) -> None:
    assert validate_github_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://github.com/example/repo",
        "https://gitlab.com/example/repo",
        "https://github.com/example",
        "https://github.com/example/repo/issues",
        "https://github.com/example/repo?tab=readme",
        "https://user@github.com/example/repo",
    ],
)
def test_reject_invalid_github_url(url: str) -> None:
    with pytest.raises(InvalidProjectUrlError):
        validate_github_url(url)


@pytest.mark.anyio
async def test_validate_project_url_route() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/projects/validate-url",
            json={"url": "https://github.com/example/codevoyager.git"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "url": "https://github.com/example/codevoyager",
    }


@pytest.mark.anyio
async def test_validate_project_url_route_returns_application_error() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/projects/validate-url", json={"url": "https://example.com/a/b"}
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_project_url"
