"""
Copyright (c) 2023 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
import pytest
from proton.vpn.core.settings import CustomDNSEntry
from tests.unit.testing_utils import process_gtk_events
from unittest.mock import MagicMock, Mock, patch
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns import \
    CustomDNSList, CustomDNSManager, CustomDNSWidget
from proton.vpn.core.settings import NetShield


FREE_TIER = 0
PLUS_TIER = 1


class TestCustomDNSList:

    @pytest.mark.parametrize("ips_to_add", [
        [],
        [CustomDNSEntry.new_from_string("1.1.1.1")],
        [CustomDNSEntry.new_from_string("1.1.1.1"), CustomDNSEntry.new_from_string("2.2.2.2")],
        [CustomDNSEntry.new_from_string("1.1.1.1"), CustomDNSEntry.new_from_string("2.2.2.2"), CustomDNSEntry.new_from_string("3.3.3.3")]
    ])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSList.pack_start")
    def test_initialize_ensure_ips_are_added_to_ui_when_a_list_with_ips_is_passed(self, pack_start_mock, ips_to_add):
        CustomDNSList(ip_list=ips_to_add)
        assert pack_start_mock.call_count == len(ips_to_add)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSList.pack_start")
    def test_successfully_add_ip_after_list_has_been_generated(self, pack_start_mock):
        new_ip = "192.159.1.1"
        existing_ips = [CustomDNSEntry.new_from_string("1.1.1.1"), CustomDNSEntry.new_from_string("2.2.2.2"), CustomDNSEntry.new_from_string("3.3.3.3")]
        custom_dns_list = CustomDNSList(ip_list=existing_ips)
        custom_dns_list.add_dns(CustomDNSEntry.new_from_string(new_ip))

        # Since `existing_ips` is never stored internally, we need to add +1 which is the `new_ip` that we added.
        assert pack_start_mock.call_count == len(existing_ips) + 1

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSList.pack_start")
    def test_successfully_delete_ip_from_list(self, pack_start_mock):
        existing_ip = CustomDNSEntry.new_from_string("1.1.1.1")
        on_dns_ip_removed = Mock()
        custom_dns_list = CustomDNSList(ip_list=[existing_ip])

        custom_dns_list.connect("dns-ip-removed", on_dns_ip_removed)

        first_custom_dns_row = pack_start_mock.call_args[0][0]
        first_custom_dns_row.button.clicked()

        on_dns_ip_removed.assert_called_once_with(custom_dns_list, existing_ip)


class TestCustomDNSManager:

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.pack_start")
    def test_error_message_is_displayed_when_trying_to_add_invalid_dns_ip(self, pack_start_mock, get_setting_mock):
        new_dns_to_be_added = "some invalid ip"
        get_setting_mock.return_value = []
        gtk_mock = Mock()
        revealer_mock = Mock()
        add_button_mock = Mock()

        revealer_mock.get_reveal_child.return_value = False
        revealer_mock.get_children.return_value = [Mock()]

        gtk_mock.Revealer.return_value = revealer_mock
        gtk_mock.Button.return_value = add_button_mock

        custom_dns_manager = CustomDNSManager(controller=Mock(), custom_dns_list=Mock(), gtk=gtk_mock)

        on_button_clicked_callback = add_button_mock.connect.call_args[0][1]
        revealer_mock.reset_mock()

        custom_dns_manager.set_entry_text(new_dns_to_be_added)
        on_button_clicked_callback(add_button_mock, revealer_mock)

        revealer_mock.set_reveal_child.assert_called_once_with(True)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.save_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.pack_start")
    def test_add_new_dns_ensure_it_stores_new_dns_to_file(self, pack_start_mock, get_setting_mock, save_setting_mock):
        controller_mock = Mock(name="controller_mock")
        new_dns_to_be_added = CustomDNSEntry.new_from_string("192.1.1.1")
        get_setting_mock.return_value = []
        custom_dns_manager = CustomDNSManager(controller=controller_mock, custom_dns_list=Mock())
        custom_dns_manager.set_entry_text(str(new_dns_to_be_added.ip))
        custom_dns_manager.add_button_click()

        save_setting_mock.assert_called_once_with(controller_mock, CustomDNSManager.SETTING_NAME, [new_dns_to_be_added])

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.save_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.pack_start")
    def test_on_delete_dns_ensure_it_removes_dns_from_file(self, pack_start_mock, get_setting_mock, save_setting_mock):
        controller_mock = Mock(name="controller_mock")
        custom_dns_list_mock = Mock(name="custom_dns_list_mock")
        existing_dns_ip = CustomDNSEntry.new_from_string("192.1.1.1")
        get_setting_mock.return_value = [existing_dns_ip]
        custom_dns_manager = CustomDNSManager(controller=controller_mock, custom_dns_list=custom_dns_list_mock)

        on_delete_dns_entry_callback = custom_dns_list_mock.connect.call_args[0][1]

        on_delete_dns_entry_callback(custom_dns_list_mock, existing_dns_ip)

        save_setting_mock.assert_called_once_with(controller_mock, CustomDNSManager.SETTING_NAME, [])


class TestCustomDNSWidget:

    @pytest.mark.parametrize("response_type", [-8, -9])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.ConfirmationDialog")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSWidget.off")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    def test_disable_custom_dns_and_prompt_user_via_dialog_when_enabling_netshield_while_custom_dns_is_enabled_and_ensure_that_either_custom_dns_or_netshield_is_disabled(self, get_setting_mock, custom_dns_off_mock, confirmation_dialog_mock, response_type):
        get_setting_mock.return_value = False
        controller_mock = Mock(name="controller_mock")
        controller_mock.user_tier = PLUS_TIER
        settings_window_mock = Mock(name="settings_window_mock")
        feature_settings_mock = Mock(name="feature_settings_mock")
        gtk_mock = Mock(name="gtk_mock")
        confirmation_dialog_instance_mock = Mock(name="confirmation_dialog_instance_mock")
        confirmation_dialog_mock.return_value = confirmation_dialog_instance_mock

        dns_widget = CustomDNSWidget(controller=controller_mock, settings_window=settings_window_mock, gtk=gtk_mock)

        dns_widget.on_netshield_setting_changed(feature_settings_mock, new_setting=NetShield.BLOCK_MALICIOUS_URL)

        on_dialog_button_click_callback = confirmation_dialog_instance_mock.connect.call_args[0][1]

        on_dialog_button_click_callback(confirmation_dialog_instance_mock, response_type)

        # -8: Gtk.ResponseType.YES
        # -9: Gtk.ResponseType.NO
        Gtk_ResponseType_YES = -8

        if response_type == Gtk_ResponseType_YES:
            custom_dns_off_mock.assert_called_once()
            feature_settings_mock.netshield.off.assert_not_called()
        else:
            feature_settings_mock.netshield.off.assert_called_once()
            custom_dns_off_mock.assert_not_called()

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.ConfirmationDialog")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    def test_custom_dns_prompt_is_not_shown_to_the_user_when_custom_dns_is_disabled_while_enabling_netshield(self, get_setting_mock, confirmation_dialog_mock):
        get_setting_mock.return_value = False
        controller_mock = Mock(name="controller_mock")
        controller_mock.user_tier = PLUS_TIER
        settings_window_mock = Mock(name="settings_window_mock")
        feature_settings_mock = Mock(name="feature_settings_mock")
        confirmation_dialog_instance_mock = Mock(name="confirmation_dialog_instance_mock")
        confirmation_dialog_mock.return_value = confirmation_dialog_instance_mock

        dns_widget = CustomDNSWidget(controller=controller_mock, settings_window=settings_window_mock)

        dns_widget.on_netshield_setting_changed(feature_settings_mock, new_setting=NetShield.NO_BLOCK)

        confirmation_dialog_mock.assert_not_called()
