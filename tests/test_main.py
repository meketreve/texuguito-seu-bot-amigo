from chat_parade.config import Config
from chat_parade.main import build_components


async def test_build_components_wires_everything_without_network(tmp_path):
    config = Config(
        client_id="id",
        token="tok",
        broadcaster_id="1",
        channel="canal",
        data_dir=tmp_path,
        overlay_port=8901,
    )

    store, events, app, broadcaster, bot = build_components(config)

    assert store is not None
    assert events.empty()
    assert app is not None
    assert broadcaster is not None
    assert bot is not None
