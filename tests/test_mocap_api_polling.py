import importlib
import sys
import types
import unittest
from unittest import mock


def install_docutils_stub():
    docutils = types.ModuleType("docutils")
    parsers = types.ModuleType("docutils.parsers")
    rst = types.ModuleType("docutils.parsers.rst")
    directives = types.ModuleType("docutils.parsers.rst.directives")
    directives.encoding = None
    sys.modules["docutils"] = docutils
    sys.modules["docutils.parsers"] = parsers
    sys.modules["docutils.parsers.rst"] = rst
    sys.modules["docutils.parsers.rst.directives"] = directives


def import_mocap_api_with_fake_library():
    install_docutils_stub()
    sys.modules.pop("mocap_api", None)
    with (
        mock.patch("ctypes.cdll.LoadLibrary", return_value=types.SimpleNamespace()),
        mock.patch("platform.system", return_value="Windows"),
    ):
        return importlib.import_module("mocap_api")


class MocapApiPollingTests(unittest.TestCase):
    def test_poll_next_event_keeps_events_returned_with_more_event(self):
        mocap_api = import_mocap_api_with_fake_library()
        calls = []

        def poll_application_next_event(events, event_count, _handle):
            calls.append(bool(events))
            if not bool(events):
                event_count.contents.value = 1
                return mocap_api.MCPError.NoError

            events[0].size = mocap_api.sizeof(mocap_api.MCPEvent)
            events[0].event_type = mocap_api.MCPEventType.AvatarUpdated
            events[0].timestamp = 123.0
            event_count.contents.value = 1
            return mocap_api.MCPError.MoreEvent

        app = object.__new__(mocap_api.MCPApplication)
        app._handle = mocap_api.MCPApplicationHandle(1)
        app.api = types.SimpleNamespace(
            contents=types.SimpleNamespace(
                PollApplicationNextEvent=poll_application_next_event,
                DestroyApplication=lambda _handle: mocap_api.MCPError.NoError,
            )
        )

        events = app.poll_next_event()

        self.assertEqual([False, True], calls)
        self.assertEqual(1, len(events))
        self.assertEqual(mocap_api.MCPEventType.AvatarUpdated, events[0].event_type)
        self.assertEqual(123.0, events[0].timestamp)


if __name__ == "__main__":
    unittest.main()
