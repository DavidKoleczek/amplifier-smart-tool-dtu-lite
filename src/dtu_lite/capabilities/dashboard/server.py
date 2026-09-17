"""Dashboard: the compiled web app shipped with the package and the JSON API it reads, both over the library."""

from pathlib import Path
import socket
import threading
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
import uvicorn

from dtu_lite.capabilities.universe import destroy as destroy_module
from dtu_lite.capabilities.universe import status as status_module
from dtu_lite.schemas import Dashboard, DtuLiteError

STATIC_DIR = Path(__file__).parent / "static"
BUILD_COMMAND = "uv run build-dashboard.py"
# The frontend branches on these; anything the library raises that is not listed is a server error.
ERROR_STATUS = {"universe-not-found": 404, "docker-unavailable": 503}


def create_app(static_dir: Path = STATIC_DIR) -> FastAPI:
    app = FastAPI(title="DTU Lite Dashboard")

    @app.exception_handler(DtuLiteError)
    async def dtu_lite_error(request: Request, error: DtuLiteError) -> JSONResponse:
        body = {"code": error.code, "message": error.message, "remedy": error.remedy}
        return JSONResponse(status_code=ERROR_STATUS.get(error.code, 500), content=body)

    @app.get("/api/universes")
    def list_universes() -> list[dict[str, Any]]:
        return [universe.model_dump(mode="json") for universe in status_module.list_universes()]

    @app.get("/api/universes/{id}")
    def get_universe(id: str) -> dict[str, Any]:
        return status_module.status(id).model_dump(mode="json")

    @app.delete("/api/universes/{id}")
    def delete_universe(id: str) -> dict[str, Any]:
        return destroy_module.destroy(id).model_dump(mode="json")

    @app.get("/{page_path:path}", include_in_schema=False)
    def spa(page_path: str) -> Response:
        index = static_dir / "index.html"
        if not index.is_file():
            return PlainTextResponse(
                f"The dashboard is not compiled. Run `{BUILD_COMMAND}` from the repository root.", status_code=503
            )
        candidate = (static_dir / page_path).resolve()
        if page_path and candidate.is_relative_to(static_dir.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)

    return app


def serve_dashboard(port: int | None = None, host: str = "127.0.0.1") -> Dashboard:
    """Serve the dashboard from a daemon thread, so it lives until the process exits, and say where it is."""
    # Bound and listening before this returns, so the URL it reports answers at once (connections queue until the
    # server thread accepts) and a held port is a named failure rather than uvicorn's own exit.
    sock = socket.socket(socket.AF_INET6 if ":" in host else socket.AF_INET)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port or 0))
    except OSError as error:
        sock.close()
        raise DtuLiteError(
            "port-in-use",
            f"The dashboard could not bind {host}:{port}: {error.strerror or error}.",
            "Omit --port to have a free one chosen, or pass a port nothing else holds.",
        ) from error
    sock.listen()
    bound_port = int(sock.getsockname()[1])
    config = uvicorn.Config(create_app(), host=host, port=bound_port, log_level="warning")
    thread = threading.Thread(target=uvicorn.Server(config).run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    display_host = "127.0.0.1" if host in ("127.0.0.1", "0.0.0.0", "localhost") else host
    reachable = "only this machine" if host in ("127.0.0.1", "localhost") else f"the local network (bound to {host})"
    return Dashboard(url=f"http://{display_host}:{bound_port}", host=host, port=bound_port, reachable=reachable)
