"""
This module includes the Proton VPN GTK application for Linux.
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # pylint: disable=C0413 # noqa: E402

from proton.vpn.core_api import vpn_logging as logging  # pylint: disable=C0413 # noqa: E402


logging.config(filename="vpn-app")

__all__ = [Gtk]
