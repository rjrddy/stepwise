from __future__ import annotations

import json
import os
import subprocess
import threading
import urllib.error
import urllib.request

import pytest

from stepwise.sdk import Client
from stepwise.server import Server
from stepwise.store import configured


@pytest.fixture
def server():
    store = configured()
    store.migrate()
    server = Server(("127.0.0.1", 0), store, "synthetic-test-token-at-least-24")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


def test_python_and_node_sdk_real_http_postgres(server):
    base = f"http://127.0.0.1:{server.server_port}"
    client = Client(base, server.token, ("SYNTHETIC-NEVER-PERSIST-KEY",))
    rid, tape = client.record("Python SDK")
    tape.call("model", "plan", {"q": "SYNTHETIC-NEVER-PERSIST-KEY"}, lambda _: {"x": 2})
    replay = client.replay(rid)
    assert replay.call("model", "plan", {"q": "SYNTHETIC-NEVER-PERSIST-KEY"}, lambda _: pytest.fail()) == {"x": 2}
    replay.finish()
    assert tape.events == replay.events
    env = {**os.environ, "STEPWISE_BASE": base, "STEPWISE_TOKEN": server.token}
    result = subprocess.run(["node", "tests/node_test.mjs"], env=env, capture_output=True, text=True,
                            check=True)
    assert json.loads(result.stdout)["node_sdk"] == "pass"
    with pytest.raises(urllib.error.HTTPError) as error:
        Client(base).request("/api/runs")
    assert error.value.code == 401


def test_http_validation_origin_and_database_failure(server):
    base = f"http://127.0.0.1:{server.server_port}"
    headers = {"Authorization": "Bearer " + server.token, "Content-Type": "application/json"}
    for body, status in [(b'{"x":NaN}', 400), (b'[]', 400), (b'x'*65537, 413)]:
        request = urllib.request.Request(base + "/api/runs", data=body, headers=headers)
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        assert error.value.code == status
    request = urllib.request.Request(base + "/api/runs", data=b'{}',
                                     headers={**headers, "Origin": "https://other.invalid"})
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(request)
    assert error.value.code == 403
    original = server.store.url
    server.store.url = "postgresql://127.0.0.1:1/missing"
    try:
        with pytest.raises(urllib.error.HTTPError) as error:
            Client(base, server.token).request("/api/runs")
        assert error.value.code == 503
        assert b"postgresql" not in error.value.read()
    finally:
        server.store.url = original
