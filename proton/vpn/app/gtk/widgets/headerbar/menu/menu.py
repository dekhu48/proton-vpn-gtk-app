"""
This module defines the menu that shown in the header bar.


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
from typing import TYPE_CHECKING
from concurrent.futures import Future

from gi.repository import Gio, GLib, GObject
from proton.vpn.app.gtk import Gtk

from proton.vpn.connection.states import State, Disconnected
from proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog import BugReportDialog
from proton.vpn.app.gtk.widgets.headerbar.menu.about_dialog import AboutDialog
from proton.vpn.app.gtk.widgets.main.confirmation_dialog import ConfirmationDialog
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget, DefaultLoadingWidget
from proton.vpn.app.gtk.widgets.headerbar.menu.settings import SettingsWindow
from proton.vpn.app.gtk.widgets.headerbar.menu.release_notes_dialog import ReleaseNotesDialog
from proton.vpn.connection.enum import KillSwitchSetting as KillSwitchSettingEnum

from proton.session.exceptions import ProtonAPINotReachable
from proton.vpn import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow


class Menu(Gio.Menu):  # pylint: disable=too-many-instance-attributes
    """App menu shown in the header bar."""

    LOGOUT_LOADING_MESSAGE = "Signing out..."
    UNABLE_TO_LOGOUT_MESSAGE = "Unable to sign out, please ensure you have internet access."
    DISCONNECT_ON_LOGOUT_MESSAGE = "Signing out will cancel the current VPN connection.\n\n" \
                                   "Do you want to continue?"
    DISCONNECT_ON_LOGOUT_WITH_KILL_SWITCH_ENABLED_MESSAGE = "Signing out "\
        "will cancel the current VPN connection and disable the kill switch."\
        "\n\nDo you want to continue?"
    LOGOUT_AND_KILL_SWITCH_ENABLED_MESSAGE = "Signing out will "\
        "disable the kill switch, potentially exposing your internet traffic. "\
        "\n\nDo you want to continue?"
    DISCONNECT_ON_QUIT_MESSAGE = "Quitting the application will cancel the current" \
                                 " VPN connection.\n\nDo you want to continue?"
    DISCONNECT_ON_QUIT_WITH_PERMANENT_KILL_SWITCH_ENABLED_MESSAGE = "Quitting the application "\
        "will keep the kill switch active, but your current VPN connection will be terminated."\
        "\n\nDo you want to continue?"
    DISCONNECT_TITLE = "Active connection found"
    KILLSWITCH_ENABLED_TITLE = "Kill Switch enabled"

    def __init__(
        self, controller: Controller,
        main_window: "MainWindow", overlay_widget: OverlayWidget
    ):
        super().__init__()
        self._main_window = main_window
        self._controller = controller
        self._overlay_widget = overlay_widget

        self.bug_report_action = Gio.SimpleAction.new("report", None)
        self.settings_action = Gio.SimpleAction.new("settings", None)
        self.release_notes_action = Gio.SimpleAction.new("release_notes", None)
        self.about_action = Gio.SimpleAction.new("about", None)
        self.logout_action = Gio.SimpleAction.new("logout", None)
        self.quit_action = Gio.SimpleAction.new("quit", None)

        self.append_item(Gio.MenuItem.new("About", "win.about"))
        self.append_item(Gio.MenuItem.new("Settings", "win.settings"))
        self.append_item(Gio.MenuItem.new("Release notes", "win.release_notes"))
        self.append_item(Gio.MenuItem.new("Report an issue", "win.report"))
        self.append_item(Gio.MenuItem.new("Sign out", "win.logout"))
        self.append_item(Gio.MenuItem.new("Quit", "win.quit"))

        self._settings_window = None

        self._setup_actions()

    def status_update(self, connection_status: State):
        """
        This method is set as a callback to monitor the VPN connection after
        the user clicks on the quit menu option.
        """
        if isinstance(connection_status, Disconnected):
            self._main_window.quit()

    @property
    def logout_enabled(self) -> bool:
        """Returns if logout button is enabled or disabled."""
        return self.logout_action.get_enabled()

    @logout_enabled.setter
    def logout_enabled(self, newvalue: bool):
        """Set the logout button to either be enabled or disabled."""
        self.logout_action.set_enabled(newvalue)

    @property
    def settings_enabled(self) -> bool:
        """Returns if logout button is enabled or disabled."""
        return self.settings_action.get_enabled()

    @settings_enabled.setter
    def settings_enabled(self, newvalue: bool):
        """Set the settings button to either be enabled or disabled."""
        self.settings_action.set_enabled(newvalue)

    @GObject.Signal
    def user_logged_out(self):
        """Signal emitted after a successful logout."""

    def close_settings_window(self):
        """Closes the settings window if it's open."""
        if self._settings_window:
            self._settings_window.close()

    def _setup_actions(self):
        # Add actions to Gtk.ApplicationWindow
        self._main_window.add_action(self.bug_report_action)
        self._main_window.add_action(self.settings_action)
        self._main_window.add_action(self.release_notes_action)
        self._main_window.add_action(self.about_action)
        self._main_window.add_action(self.logout_action)
        self._main_window.add_action(self.quit_action)

        # Connect actions to callbacks
        self.bug_report_action.connect(
            "activate", self._on_report_an_issue_clicked
        )
        self.settings_action.connect(
            "activate", self._on_settings_clicked
        )
        self.release_notes_action.connect(
            "activate", self._on_release_notes_clicked
        )
        self.about_action.connect(
            "activate", self._on_about_clicked
        )
        self.logout_action.connect(
            "activate", self._on_logout_clicked
        )
        self.quit_action.connect(
            "activate", self._on_quit_clicked
        )

    def _on_report_an_issue_clicked(self, *_):
        bug_dialog = BugReportDialog(self._controller, self._main_window)
        bug_dialog.set_transient_for(self._main_window)
        # run() blocks the main loop, and only exist once the `::response` signal
        # is emitted.
        bug_dialog.run()
        bug_dialog.destroy()

    def _on_settings_clicked(self,  *_):
        self._settings_window = SettingsWindow(
            self._controller,
            self._main_window.application.tray_indicator
        )
        self._settings_window.set_transient_for(self._main_window)

        def on_unrealize(_):
            self._settings_window = None

        self._settings_window.connect("unrealize", on_unrealize)
        self._settings_window.present()

    def _on_release_notes_clicked(self,  *_):
        release_notes = ReleaseNotesDialog()
        release_notes.set_transient_for(self._main_window)
        release_notes.present()

    def _on_about_clicked(self, *_):
        about_dialog = AboutDialog()
        # run() blocks the main loop, and only exist once the `::response` signal
        # is emitted.
        about_dialog.run()
        about_dialog.destroy()

    def _on_logout_clicked(self, *_):
        logger.info("Logout button clicked", category="ui", subcategory="logout", event="click")

        self.logout_enabled = False
        kill_switch_state = self._controller.get_settings().killswitch
        confirm_logout = True

        if not self._controller.is_connection_disconnected:  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.maintainability.is-function-without-parentheses.is-function-without-parentheses
            dialog = ConfirmationDialog(
                self.DISCONNECT_ON_LOGOUT_MESSAGE
                if kill_switch_state < KillSwitchSettingEnum.ON
                else self.DISCONNECT_ON_LOGOUT_WITH_KILL_SWITCH_ENABLED_MESSAGE,
                self.DISCONNECT_TITLE
            )
            confirm_logout = self._display_dialog(dialog)
        elif kill_switch_state == KillSwitchSettingEnum.PERMANENT:
            confirm_logout = self._display_dialog(
                ConfirmationDialog(
                    self.LOGOUT_AND_KILL_SWITCH_ENABLED_MESSAGE,
                    self.KILLSWITCH_ENABLED_TITLE
                )
            )

        if confirm_logout:
            logger.info("Yes", category="ui", subcategory="dialog", event="logout")

            self._overlay_widget.show(DefaultLoadingWidget(self.LOGOUT_LOADING_MESSAGE))

            if kill_switch_state > KillSwitchSettingEnum.OFF:
                future = self._controller.disable_killswitch()
                future.add_done_callback(
                    lambda f: GLib.idle_add(self._on_killswitch_disabled_logout, f)
                )
                return

            self._request_logout()

    def _on_quit_clicked(self, *_):
        kill_switch_state = self._controller.get_settings().killswitch

        if self._controller.is_connection_disconnected:  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.maintainability.is-function-without-parentheses.is-function-without-parentheses
            self._main_window.quit()
        else:
            dialog = ConfirmationDialog(
                self.DISCONNECT_ON_QUIT_WITH_PERMANENT_KILL_SWITCH_ENABLED_MESSAGE
                if kill_switch_state == KillSwitchSettingEnum.PERMANENT
                else self.DISCONNECT_ON_QUIT_MESSAGE,
                self.DISCONNECT_TITLE
            )
            confirm_quit = self._display_dialog(dialog)

            if confirm_quit:
                logger.info("Yes", category="ui", subcategory="dialog", event="quit")
                self._controller.register_connection_status_subscriber(self)
                future = self._controller.disconnect()
                future.add_done_callback(lambda f: GLib.idle_add(f.result))

    def _on_killswitch_disabled_logout(self, future: Future):
        future.result()
        self._request_logout()

    def _request_logout(self):
        future = self._controller.logout()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_logout_result, future)
        )

    def _on_logout_result(self, future: Future):
        """Callback when attempting to log out.
        Mainly used to emit if a successful logout has happened, or if a
            connection is found at logout, to display the dialog to the user.
        """
        try:
            future.result()
            logger.info(
                "Successful logout",
                category="app", subcategory="logout", event="success"
            )
            self.emit("user-logged-out")
        except ProtonAPINotReachable as e:  # pylint: disable=invalid-name
            logger.info(
                getattr(e, 'message', repr(e)),
                category="app", subcategory="logout", event="fail"
            )
            self._main_window.main_widget.notifications.show_error_message(
                self.UNABLE_TO_LOGOUT_MESSAGE
            )
            self.logout_enabled = True
        finally:
            self._overlay_widget.hide()

    def _display_dialog(self, dialog: ConfirmationDialog) -> bool:
        dialog.set_transient_for(self._main_window)
        # run() blocks the main loop, and only exist once the `::response` signal
        # is emitted.
        response = Gtk.ResponseType(dialog.run())
        dialog.destroy()

        self.logout_enabled = response in (Gtk.ResponseType.NO, Gtk.ResponseType.DELETE_EVENT)

        return response == Gtk.ResponseType.YES

    def bug_report_button_click(self):
        """Clicks the bug report menu entry."""
        self._on_report_an_issue_clicked(self.bug_report_action)

    def about_button_click(self):
        """Clicks the about menu entry."""
        self._on_about_clicked(self.about_action)

    def logout_button_click(self):
        """Clicks the logout menu entry."""
        self._on_logout_clicked(self.logout_action)

    def quit_button_click(self):
        """Clicks the quit menu entry."""
        self._on_quit_clicked(self.quit_action)
