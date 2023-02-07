from time import time
from unittest.mock import Mock

from gi.repository import GLib
import pytest

from proton.vpn.servers import ServerList

from proton.vpn.app.gtk.widgets.vpn.search import SearchWidget
from proton.vpn.app.gtk.widgets.vpn.server_list import ServerListWidget
from tests.unit.utils import process_gtk_events, run_main_loop

PLUS_TIER = 2
FREE_TIER = 0


@pytest.fixture
def server_list():
    return ServerList(apidata={
        "LogicalServers": [
            {
                "ID": 2,
                "Name": "AR#10",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 1,
                "Name": "JP-FREE#10",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": FREE_TIER,

            },
            {
                "ID": 3,
                "Name": "AR#9",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 5,
                "Name": "CH-JP#1",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "Features": 1,  # Secure core feature
                "ExitCountry": "JP",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 4,
                "Name": "JP#9",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": PLUS_TIER,

            },
        ],
        "LogicalsUpdateTimestamp": time(),
        "LoadsUpdateTimestamp": time()
    })


@pytest.fixture
def server_list_widget(server_list):
    server_list_widget = ServerListWidget(controller=Mock())
    server_list_widget.display(user_tier=PLUS_TIER, server_list=server_list)
    process_gtk_events()
    return server_list_widget


def test_search_shows_matching_server_row_and_its_country_when_searching_for_a_server_name(server_list_widget):
    search_widget = SearchWidget(server_list_widget)

    main_loop = GLib.MainLoop()

    # Changing the search widget text triggers the search.
    GLib.idle_add(search_widget.set_text, "jp-free#10")

    search_widget.connect("search-complete", lambda _: main_loop.quit())

    run_main_loop(main_loop)

    for country_row in server_list_widget.country_rows:
        expected_country_match = (country_row.country_name == "Japan")
        assert country_row.get_visible() is expected_country_match, \
            f"{country_row.country_name} did not have the expected visibility."

        # As our test search only matches a server name, the country row
        # containing it should be displayed expanded (rather than collapsed):
        assert country_row.showing_servers is expected_country_match, \
            f"{country_row.country_name} should be displayed " \
            f"{'expanded' if expected_country_match else 'collapsed'}"

        for server_row in country_row.server_rows:
            expected_server_match = (server_row.server_label == "JP-FREE#10")
            assert server_row.get_visible() is expected_server_match


def test_search_shows_matching_country_with_servers_collapsed_when_search_only_matches_country_name(server_list_widget):
    search_widget = SearchWidget(server_list_widget)

    main_loop = GLib.MainLoop()

    # Changing the search widget text triggers the search.
    GLib.idle_add(search_widget.set_text, "argentina")

    search_widget.connect("search-complete", lambda _: main_loop.quit())

    run_main_loop(main_loop)

    for country_row in server_list_widget.country_rows:
        expected_country_visible = (country_row.country_name == "Argentina")
        assert country_row.get_visible() is expected_country_visible, \
            f"{country_row.country_name} did not have the expected visibility."

        # Servers should be collapsed, as the search text does not match any.
        assert not country_row.showing_servers

        # Servers belonging to the country matched by the search text should
        # be flagged "visible", meaning that **if the country row is expanded**
        # then the user will see them.
        for server_row in country_row.server_rows:
            assert server_row.get_visible() is expected_country_visible


def test_search_does_not_show_any_countries_nor_servers_when_search_does_not_match_anything(server_list_widget):
    search_widget = SearchWidget(server_list_widget)

    main_loop = GLib.MainLoop()

    # Changing the search widget text triggers the search.
    GLib.idle_add(search_widget.set_text, "foobar")

    search_widget.connect("search-complete", lambda _: main_loop.quit())

    run_main_loop(main_loop)

    for country_row in server_list_widget.country_rows:
        assert not country_row.get_visible()