import re
from urllib.parse import unquote, urlsplit

from app.core.exceptions import InvalidProjectUrlError

_PATH_PART_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def validate_github_url(url: str) -> str:
    """Validate and normalize an HTTPS GitHub repository URL.

    A canonical URL without a trailing slash or ``.git`` suffix is returned so
    callers can reliably compare repository URLs.
    """

    value = url.strip()
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise InvalidProjectUrlError("Invalid GitHub repository URL") from exc

    if parsed.scheme.lower() != "https":
        raise InvalidProjectUrlError("GitHub repository URL must use HTTPS")
    if parsed.hostname is None or parsed.hostname.lower() not in {
        "github.com",
        "www.github.com",
    }:
        raise InvalidProjectUrlError("Only github.com repository URLs are supported")
    if parsed.username or parsed.password or port is not None:
        raise InvalidProjectUrlError("GitHub repository URL must not contain credentials or a port")
    if parsed.query or parsed.fragment:
        raise InvalidProjectUrlError("GitHub repository URL must not contain a query or fragment")

    path = unquote(parsed.path).strip("/")
    parts = path.split("/") if path else []
    if len(parts) != 2:
        raise InvalidProjectUrlError("URL must point to a GitHub repository")

    owner, repository = parts
    if repository.endswith(".git"):
        repository = repository[:-4]
    if not owner or not repository or not all(
        _PATH_PART_PATTERN.fullmatch(part) for part in (owner, repository)
    ):
        raise InvalidProjectUrlError("URL contains an invalid repository owner or name")

    return f"https://github.com/{owner}/{repository}"
