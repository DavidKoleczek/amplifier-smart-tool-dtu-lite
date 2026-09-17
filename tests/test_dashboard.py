"""The dashboard apart from Docker: the API over the library, error bodies, the SPA routes, and serving."""

from pathlib import Path
import socket
from urllib.request import urlopen

from fastapi.testclient import TestClient
import pytest

from dtu_lite import lib
from dtu_lite.capabilities.dashboard import server
from dtu_lite.capabilities.universe import status as status_module
from dtu_lite.schemas import DtuLiteError


def _client(tmp_path: Path) -> TestClient:
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("<html>dashboard</html>", encoding="utf-8")
    (static / "assets").mkdir()
    (static / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    return TestClient(server.create_app(static))


def test_an_empty_machine_lists_nothing_without_docker(tmp_path: Path, state_root: Path) -> None:
    response = _client(tmp_path).get("/api/universes")

    assert response.status_code == 200
    assert response.json() == []


def test_an_unknown_id_is_404_with_the_librarys_code_message_and_remedy(tmp_path: Path, state_root: Path) -> None:
    client = _client(tmp_path)

    for response in (client.get("/api/universes/dtu-nope-0000"), client.delete("/api/universes/dtu-nope-0000")):
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "universe-not-found"
        assert "dtu-nope-0000" in body["message"]
        assert body["remedy"]


def test_docker_down_is_503_and_anything_else_the_library_names_is_500(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path)

    def down() -> list[object]:
        raise DtuLiteError("docker-unavailable", "Docker is not usable.", "Run `dtu-lite check`.")

    monkeypatch.setattr(status_module, "list_universes", down)
    assert client.get("/api/universes").status_code == 503
    assert client.get("/api/universes").json()["remedy"] == "Run `dtu-lite check`."

    def other() -> list[object]:
        raise DtuLiteError("something-else", "It broke.", "Fix it.")

    monkeypatch.setattr(status_module, "list_universes", other)
    assert client.get("/api/universes").status_code == 500


def test_pages_serve_the_app_and_assets_serve_themselves(tmp_path: Path) -> None:
    client = _client(tmp_path)

    assert client.get("/").text == "<html>dashboard</html>"
    assert client.get("/some/deep/route").text == "<html>dashboard</html>"
    assert client.get("/assets/app.js").text == "console.log(1)"
    assert client.get("/assets/../../secret").text == "<html>dashboard</html>"


def test_an_uncompiled_dashboard_says_how_to_build_it(tmp_path: Path) -> None:
    response = TestClient(server.create_app(tmp_path / "missing")).get("/")

    assert response.status_code == 503
    assert server.BUILD_COMMAND in response.text


def test_serve_picks_a_free_port_and_answers_on_it(state_root: Path) -> None:
    dashboard = lib.serve_dashboard()

    assert dashboard.url == f"http://127.0.0.1:{dashboard.port}"
    assert dashboard.reachable == "only this machine"
    with urlopen(f"{dashboard.url}/api/universes", timeout=5) as response:
        assert response.read() == b"[]"


def test_serve_names_a_held_port() -> None:
    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        held.listen()
        port = held.getsockname()[1]

        with pytest.raises(DtuLiteError) as raised:
            lib.serve_dashboard(port)

    assert raised.value.code == "port-in-use"
    assert str(port) in raised.value.message


def test_the_compiled_dashboard_ships_in_the_package() -> None:
    assert (server.STATIC_DIR / "index.html").is_file(), f"Run `{server.BUILD_COMMAND}` and commit the result."


@pytest.mark.needs_docker
@pytest.mark.live
def test_the_api_lists_measures_and_destroys_a_real_universe(tmp_path: Path, state_root: Path) -> None:
    (tmp_path / "compose.yaml").write_text(
        "name: dash\nx-dtu:\n  twin_machine: box\nservices:\n  box:\n    image: alpine:3.20\n    command: sleep infinity\n"
        "    healthcheck:\n      test: [CMD, 'true']\n      interval: 1s\n",
        encoding="utf-8",
    )
    universe = lib.launch(tmp_path / "compose.yaml", timeout_seconds=120)
    client = TestClient(server.create_app())
    try:
        listed = client.get("/api/universes").json()
        assert [entry["id"] for entry in listed] == [universe.id]
        assert listed[0]["state"] == "running"
        assert client.get(f"/api/universes/{universe.id}").json() == lib.status(universe.id).model_dump(mode="json")
    finally:
        destroyed = client.delete(f"/api/universes/{universe.id}")

    assert destroyed.status_code == 200
    assert f"{universe.id}-box-1" in destroyed.json()["removed"]
    assert client.get("/api/universes").json() == []
