"""Fleet CI smoke tests."""

def test_import_server_module() -> None:
    import suno_mcp.server as server

    assert hasattr(server, "mcp_app")