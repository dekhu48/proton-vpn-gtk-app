from unittest.mock import Mock
import pytest

from proton.vpn.servers.server_types import LogicalServer

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.server import ServerRow

from tests.unit.utils import process_gtk_events

FREE_TIER = 0
PLUS_TIER = 2


@pytest.fixture
def plus_logical_server():
    return LogicalServer(data={
        "Name": "IS#1",
        "Status": 1,
        "Servers": [
            {
                "ID": "OYB-3pMQQA2Z2Qnp5s5nIvTV…x9DCAUM9uXfM2ZUFjzPXw==",
                "Status": 1
            }
        ],
        "Tier": PLUS_TIER,
    })


@pytest.fixture
def mock_controller():
    return Mock(Controller)


def test_server_row_displays_server_name(
        plus_logical_server, mock_controller
):
    server_row = ServerRow(
        server=plus_logical_server, user_tier=PLUS_TIER, controller=mock_controller
    )

    assert server_row.server_label == "IS#1"


@pytest.fixture
def unavailable_logical_server():
    return LogicalServer(data={
        "Name": "IS#1",
        "Status": 0,
        "Servers": [],
        "Tier": PLUS_TIER,
    })


def test_server_row_signals_server_under_maintenance(
        unavailable_logical_server, mock_controller
):
    server_row = ServerRow(
        server=unavailable_logical_server, user_tier=PLUS_TIER, controller=mock_controller
    )

    assert server_row.under_maintenance


def test_connect_button_click_triggers_vpn_connection(plus_logical_server, mock_controller):
    server_row = ServerRow(
        server=plus_logical_server, user_tier=PLUS_TIER, controller=mock_controller
    )

    server_row.click_connect_button()

    process_gtk_events()

    mock_controller.connect_to_server.assert_called_once_with(
        plus_logical_server.name
    )

