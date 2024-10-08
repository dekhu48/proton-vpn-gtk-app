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
from unittest.mock import Mock, PropertyMock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings import FeatureSettings, KillSwitchSetting, KillSwitchSettingEnum
from proton.vpn.core.settings import NetShield


FREE_TIER = 0
PLUS_TIER = 1

KILLSWITCH_STANDARD = 1
KILLSWITCH_ADVANCED = 2


@pytest.fixture
def mocked_controller_and_netshield():
    controller_mock = Mock(name="controller")

    setting_property_mock = PropertyMock()
    type(controller_mock.get_settings.return_value.features).netshield = setting_property_mock

    user_tier_mock = PropertyMock(return_value=PLUS_TIER)
    type(controller_mock).user_tier = user_tier_mock

    return controller_mock, setting_property_mock


@pytest.fixture
def mocked_controller_and_port_forwarding():
    controller_mock = Mock(name="controller")
    controller_mock.get_settings.return_value = Mock()

    property_mock = PropertyMock()
    type(controller_mock.get_settings.return_value.features).port_forwarding = property_mock

    user_tier_mock = PropertyMock(return_value=PLUS_TIER)
    type(controller_mock).user_tier = user_tier_mock

    return controller_mock, property_mock


def test_netshield_when_setting_is_called_upon_building_ui_elements(mocked_controller_and_netshield):
    controller_mock, netshield_mock = mocked_controller_and_netshield
    feature_settings = FeatureSettings(controller_mock, Mock())
    feature_settings.build_netshield()

    netshield_mock.assert_called_once()

def test_netshield_when_combobox_is_set_to_initial_value(mocked_controller_and_netshield):
    controller_mock, netshield_mock = mocked_controller_and_netshield

    netshield_option = NetShield.BLOCK_MALICIOUS_URL.value
    netshield_mock.return_value = netshield_option

    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.Gtk.ComboBoxText.set_active_id") as set_active_mock:
        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_netshield()

        set_active_mock.assert_called_once_with(str(netshield_option))

def test_netshield_when_switching_netshield_and_ensure_changes_are_saved(mocked_controller_and_netshield):
    controller_mock, netshield_mock = mocked_controller_and_netshield
    netshield_mock.return_value = NetShield.NO_BLOCK.value
    feature_settings = FeatureSettings(controller_mock, Mock())
    feature_settings.build_netshield()

    netshield_mock.reset_mock()

    feature_settings.netshield_row.interactive_object.set_active_id(str(NetShield.BLOCK_MALICIOUS_URL.value))

    netshield_mock.assert_called_once_with(NetShield.BLOCK_MALICIOUS_URL.value)
    controller_mock.save_settings.assert_called_once()


@pytest.mark.parametrize("user_tier", [FREE_TIER, PLUS_TIER])
def test_netshield_upgrade_tag_override_interactive_object_if_plan_upgrade_is_required(user_tier, mocked_controller_and_netshield):
    controller_mock, netshield_mock = mocked_controller_and_netshield
    user_tier_mock = PropertyMock(return_value=user_tier)
    type(controller_mock).user_tier = user_tier_mock

    feature_settings = FeatureSettings(controller_mock, Mock())
    feature_settings.build_netshield()

    if user_tier == FREE_TIER:
        assert feature_settings.netshield_row.overridden_by_upgrade_tag
    else:
        assert not feature_settings.netshield_row.overridden_by_upgrade_tag


def test_port_forwarding_when_setting_is_called_upon_building_ui_elements(mocked_controller_and_port_forwarding):
    controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

    feature_settings = FeatureSettings(controller_mock, Mock())
    feature_settings.build_port_forwarding()

    port_forwarding_mock.assert_called_once()

@pytest.mark.parametrize("port_forwarding_enabled", [False, True])
def test_port_forwarding_when_switch_is_set_to_initial_value(port_forwarding_enabled, mocked_controller_and_port_forwarding):
    controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

    port_forwarding_mock.return_value = port_forwarding_enabled

    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.Gtk.Switch.set_state") as set_state_mock:
        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_port_forwarding()

        set_state_mock.assert_called_once_with(port_forwarding_enabled)
    
@pytest.mark.parametrize("is_port_forwarding_enabled", [True, False])
def test_port_forwarding_when_switch_is_set_to_initial_value_and_description_is_displayed_accordingly(is_port_forwarding_enabled, mocked_controller_and_port_forwarding):
    controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

    port_forwarding_mock.return_value = is_port_forwarding_enabled

    feature_settings = FeatureSettings(controller_mock, Mock())
    feature_settings.build_port_forwarding()

    if is_port_forwarding_enabled:
        assert feature_settings.port_forwarding_row.description.get_label() != feature_settings.PORT_FORWARDING_DESCRIPTION
    else:
        assert feature_settings.port_forwarding_row.description.get_label() == feature_settings.PORT_FORWARDING_DESCRIPTION

@pytest.mark.parametrize("is_port_forwarding_enabled", [False, True])
def test_port_forwarding_when_switching_switch_state_and_ensure_changes_are_saved(is_port_forwarding_enabled, mocked_controller_and_port_forwarding):
    controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

    port_forwarding_mock.return_value = is_port_forwarding_enabled

    feature_settings = FeatureSettings(controller_mock, Mock())
    feature_settings.build_port_forwarding()

    port_forwarding_mock.reset_mock()

    feature_settings.port_forwarding_row.interactive_object.set_state(not is_port_forwarding_enabled)

    port_forwarding_mock.assert_called_once_with(not is_port_forwarding_enabled)
    controller_mock.save_settings.assert_called_once()

@pytest.mark.parametrize("is_port_forwarding_enabled", [False, True])
def test_port_forwarding_when_switching_switch_state_and_description_is_updated(is_port_forwarding_enabled, mocked_controller_and_port_forwarding):
    controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

    port_forwarding_mock.return_value = is_port_forwarding_enabled

    feature_settings = FeatureSettings(controller_mock, Mock())
    feature_settings.build_port_forwarding()

    port_forwarding_mock.reset_mock()

    feature_settings.port_forwarding_row.interactive_object.set_state(not is_port_forwarding_enabled)

    if not is_port_forwarding_enabled:
        assert feature_settings.port_forwarding_row.description.get_label() != feature_settings.PORT_FORWARDING_DESCRIPTION
    else:
        assert feature_settings.port_forwarding_row.description.get_label() == feature_settings.PORT_FORWARDING_DESCRIPTION


@pytest.mark.parametrize("user_tier", [FREE_TIER, PLUS_TIER])
def test_port_forwarding_upgrade_tag_override_interactive_object_if_plan_upgrade_is_required(user_tier, mocked_controller_and_port_forwarding):
    controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding
    user_tier_mock = PropertyMock(return_value=user_tier)
    type(controller_mock).user_tier = user_tier_mock

    feature_settings = FeatureSettings(controller_mock, Mock())
    feature_settings.build_port_forwarding()

    if user_tier == FREE_TIER:
        assert feature_settings.port_forwarding_row.overridden_by_upgrade_tag
    else:
        assert not feature_settings.port_forwarding_row.overridden_by_upgrade_tag


class TestKillSwitchSetting:

    @pytest.fixture
    def mocked_controller_and_killswitch(self):
        controller_mock = Mock(name="controller")
        controller_mock.get_settings.return_value = Mock()

        property_mock = PropertyMock(return_value=KillSwitchSettingEnum.OFF)
        type(controller_mock.get_settings.return_value).killswitch = property_mock

        user_tier_mock = PropertyMock(return_value=PLUS_TIER)
        type(controller_mock).user_tier = user_tier_mock

        return controller_mock, property_mock

    def test_killswitch_when_setting_is_called_upon_building_ui_elements(self, mocked_controller_and_killswitch):
        controller_mock, killswitch_mock = mocked_controller_and_killswitch

        setting = KillSwitchSetting(controller_mock)

        killswitch_mock.assert_called_once()

    @pytest.mark.parametrize("killswitch_enabled", [False, True])
    def test_killswitch_when_switch_is_set_to_initial_value(self, killswitch_enabled, mocked_controller_and_killswitch):
        controller_mock, killswitch_mock = mocked_controller_and_killswitch

        killswitch_mock.return_value = killswitch_enabled

        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.Gtk.Switch.set_state") as set_state_mock:
            setting = KillSwitchSetting(controller_mock)

            set_state_mock.assert_called_once_with(killswitch_enabled)

    @pytest.mark.parametrize("initial_killswitch_state", [False, True])
    def test_killswitch_when_switch_is_set_to_initial_value_and_revealer_reacts_accordingly(self, initial_killswitch_state, mocked_controller_and_killswitch):
        controller_mock, killswitch_mock = mocked_controller_and_killswitch

        killswitch_mock.return_value = initial_killswitch_state

        setting = KillSwitchSetting(controller_mock)

        assert setting.revealer.get_reveal_child() == initial_killswitch_state

    @pytest.mark.parametrize("killswitch_state", [False, True])
    def test_killswitch_when_switching_switch_state_and_ensure_changes_are_saved(self, killswitch_state, mocked_controller_and_killswitch):
        controller_mock, killswitch_mock = mocked_controller_and_killswitch

        killswitch_mock.return_value = not killswitch_state

        setting = KillSwitchSetting(controller_mock)

        killswitch_mock.reset_mock()

        setting.interactive_object.set_state(killswitch_state)

        killswitch_mock.assert_called_once_with(killswitch_state)
        controller_mock.save_settings.assert_called_once()

    @pytest.mark.parametrize("change_to_new_kill_switch_state, initial_kill_switch_state", [
        (KILLSWITCH_ADVANCED, KILLSWITCH_STANDARD),
        (KILLSWITCH_STANDARD, KILLSWITCH_ADVANCED)
    ])
    def test_killswitch_when_switching_between_standard_and_advanced_settings_and_ensure_changes_are_saved(self, change_to_new_kill_switch_state, initial_kill_switch_state, mocked_controller_and_killswitch):
        controller_mock, killswitch_mock = mocked_controller_and_killswitch

        killswitch_mock.return_value = initial_kill_switch_state

        setting = KillSwitchSetting(controller_mock)

        killswitch_mock.reset_mock()

        if change_to_new_kill_switch_state == KILLSWITCH_ADVANCED:
            setting.advanced_radio_button.set_active(True)
        else:
            setting.standard_radio_button.set_active(True)

        killswitch_mock.assert_called_once_with(change_to_new_kill_switch_state)
        controller_mock.save_settings.assert_called_once()

    @pytest.mark.parametrize("is_killswitch_enabled", [False, True])
    def test_killswitch_when_switching_switch_state_and_revealer_reacts_accordingly(self, is_killswitch_enabled, mocked_controller_and_killswitch):
        controller_mock, killswitch_mock = mocked_controller_and_killswitch

        killswitch_mock.return_value = not is_killswitch_enabled

        setting = KillSwitchSetting(controller_mock)

        killswitch_mock.reset_mock()

        setting.interactive_object.set_state(is_killswitch_enabled)
        assert setting.revealer.get_reveal_child() == is_killswitch_enabled

    def test_killswitch_when_switching_from_adavanced_to_disabled_and_then_swithing_to_standard(self, mocked_controller_and_killswitch):
        controller_mock, killswitch_mock = mocked_controller_and_killswitch

        killswitch_mock.return_value = KILLSWITCH_ADVANCED

        setting = KillSwitchSetting(controller_mock)

        killswitch_mock.reset_mock()

        setting.interactive_object.set_state(False)
        killswitch_mock.assert_called_once_with(False)

        killswitch_mock.reset_mock()

        setting.interactive_object.set_state(True)
        killswitch_mock.assert_called_once_with(True)

    @pytest.mark.parametrize("is_vpn_connection_disconnected", [True, False])
    def test_killswitch_setting_is_interactive_only_if_vpn_connection_is_disconnected(
            self, is_vpn_connection_disconnected, mocked_controller_and_killswitch
    ):
        controller_mock, killswitch_mock = mocked_controller_and_killswitch

        controller_mock.is_connection_disconnected = is_vpn_connection_disconnected

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_killswitch()

        # The kill switch setting should be interactive only if the VPN connection is disconnected.
        assert feature_settings.killswitch_row.enabled is is_vpn_connection_disconnected