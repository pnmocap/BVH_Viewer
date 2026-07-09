import importlib
import sys
import types
import unittest


class FakeMCPApplication:
    instances = []

    def __init__(self):
        self.settings = None
        FakeMCPApplication.instances.append(self)

    def set_settings(self, settings):
        self.settings = settings

    def open(self):
        return True, "ok"

    def close(self):
        pass


class FakeMCPSettings:
    instances = []

    def __init__(self):
        self.calls = []
        FakeMCPSettings.instances.append(self)

    def set_bvh_data(self, value):
        self.calls.append(("set_bvh_data", value))

    def set_bvh_rotation(self, value):
        self.calls.append(("set_bvh_rotation", value))

    def set_bvh_transformation(self, value):
        self.calls.append(("set_bvh_transformation", value))

    def set_udp(self, port):
        self.calls.append(("set_udp", port))

    def set_tcp(self, ip, port):
        self.calls.append(("set_tcp", ip, port))


def import_connector_with_fake_sdk():
    fake_sdk = types.SimpleNamespace(
        MCPApplication=FakeMCPApplication,
        MCPSettings=FakeMCPSettings,
        MCPAvatar=object,
        MCPJoint=object,
        MCPBvhData=types.SimpleNamespace(Binary=2),
        MCPBvhRotation=types.SimpleNamespace(YXZ=2),
        MCPBvhDisplacement=types.SimpleNamespace(Enable=1),
        MCPEventType=types.SimpleNamespace(AvatarUpdated=256, RigidBodyUpdated=512, Error=0),
    )
    sys.modules["numpy"] = types.SimpleNamespace()
    sys.modules["mocap_api"] = fake_sdk
    sys.modules.pop("axis_studio_connector", None)
    return importlib.import_module("axis_studio_connector")


class AxisStudioConnectorTests(unittest.TestCase):
    def setUp(self):
        FakeMCPApplication.instances.clear()
        FakeMCPSettings.instances.clear()
        self.connector_module = import_connector_with_fake_sdk()

    def test_tcp_mode_uses_set_tcp_endpoint_and_bvh_defaults(self):
        connector = self.connector_module.AxisStudioConnector()
        connector.configure(transport="tcp", tcp_ip="192.168.1.155", tcp_port=7003)

        success, message = connector.start_listening()

        self.assertTrue(success)
        self.assertEqual(message, "Listening on TCP:192.168.1.155:7003")
        settings = FakeMCPSettings.instances[-1]
        self.assertIn(("set_tcp", "192.168.1.155", 7003), settings.calls)
        self.assertNotIn(("set_udp", 7003), settings.calls)
        self.assertIn(("set_bvh_data", 2), settings.calls)
        self.assertIn(("set_bvh_rotation", 2), settings.calls)
        self.assertIn(("set_bvh_transformation", 1), settings.calls)

    def test_udp_mode_keeps_existing_default_port(self):
        connector = self.connector_module.AxisStudioConnector()

        success, message = connector.start_listening()

        self.assertTrue(success)
        self.assertEqual(message, "Listening on UDP:7012")
        settings = FakeMCPSettings.instances[-1]
        self.assertIn(("set_udp", 7012), settings.calls)


if __name__ == "__main__":
    unittest.main()
