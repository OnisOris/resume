from __future__ import annotations

import uvicorn

from .app_factory import create_app
from .config import get_settings

app = create_app()


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.__main__:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        factory=False,
    )


def dev() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.__main__:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        factory=False,
    )


if __name__ == "__main__":
    main()
