import pytest
from unittest.mock import MagicMock
import rclpy
from decoder.decoder_node import DecoderNode
from custom_msgs.msg import DecoderInfo
from etsi_its_spatem_ts_msgs.msg import SPATEM


# ---------- Fixtures ----------

@pytest.fixture(scope="module", autouse=True)
def rclpy_context():
    """Initialize and shut down rclpy once for all tests."""
    rclpy.init()
    yield
    rclpy.shutdown()


@pytest.fixture
def node():
    """Create a DecoderNode instance with mocks for testing."""
    node = DecoderNode()
    node.get_logger = MagicMock()
    node.publisher.publish = MagicMock()
    return node


# ---------- Helpers ----------

def make_mock_spatem(
    intersection_id=101,
    intersection_name="Main_Street",
    signal_group=3,
    event_state=5,
    with_value=True,
):
    """Construct a mock SPATEM message with flexible field presence."""
    msg = MagicMock(spec=SPATEM)

    intersection = MagicMock()
    intersection.id.id.value = intersection_id
    intersection.name.value = intersection_name

    state = MagicMock()
    state.signal_group.value = signal_group

    event = MagicMock()
    if with_value:
        event.event_state.value = event_state
    else:
        event.event_state = event_state  # direct int or None
    state.state_time_speed.array = [event]

    intersection.states.array = [state]
    msg.spat.intersections.array = [intersection]
    return msg


# ---------- Tests for spat_callback ----------

def test_spat_callback_publishes_correct_message(node):
    msg = make_mock_spatem()
    node.spat_callback(msg)
    node.publisher.publish.assert_called_once()
    published_msg = node.publisher.publish.call_args[0][0]
    assert isinstance(published_msg, DecoderInfo)
    assert published_msg.intersection_id == 101
    assert published_msg.signal_group == 3
    assert published_msg.event_state == 5
    assert published_msg.intersection_name == "Main_Street"


def test_spat_callback_handles_missing_values(node):
    msg = MagicMock(spec=SPATEM)
    msg.spat.intersections.array = []
    node.spat_callback(msg)
    node.publisher.publish.assert_not_called()


def test_spat_callback_no_event_state_value(node):
    """Covers branch where event_state has no .value attribute."""
    msg = make_mock_spatem(event_state=8, with_value=False)
    node.spat_callback(msg)
    node.publisher.publish.assert_called_once()
    published = node.publisher.publish.call_args[0][0]
    assert published.event_state == 8


def test_spat_callback_none_event_state(node):
    """Covers branch where event_state is None."""
    msg = make_mock_spatem(event_state=None, with_value=False)
    node.spat_callback(msg)
    published = node.publisher.publish.call_args[0][0]
    assert published.event_state == -1


def test_spat_callback_missing_fields(node):
    """Covers getattr fallbacks when fields are missing but valid defaults allow publishing."""
    msg = MagicMock(spec=SPATEM)
    intersection = MagicMock()

    # intersection.id.id.value present but string "0" (safe numeric fallback)
    intersection.id.id.value = "0"
    # simulate missing name field entirely
    intersection.name = None

    state = MagicMock()
    # simulate missing signal_group but with safe numeric string fallback
    state.signal_group = MagicMock()
    state.signal_group.value = "0"

    event = MagicMock()
    event.event_state.value = 4
    state.state_time_speed.array = [event]

    intersection.states.array = [state]
    msg.spat.intersections.array = [intersection]

    node.spat_callback(msg)
    node.publisher.publish.assert_called_once()
    published = node.publisher.publish.call_args[0][0]
    assert isinstance(published, DecoderInfo)
    assert published.intersection_id == 0
    assert published.signal_group == 0
    assert published.intersection_name == "unknown"


# ---------- Tests for main() ----------

def test_main_function_normal(monkeypatch):
    """Covers the normal main() execution flow."""
    import decoder.decoder_node as dn

    called = {}

    monkeypatch.setattr(dn.rclpy, "init", lambda args=None: called.setdefault("init", True))
    monkeypatch.setattr(dn.rclpy, "spin", lambda node: called.setdefault("spin", True))
    monkeypatch.setattr(dn.rclpy, "shutdown", lambda: called.setdefault("shutdown", True))
    monkeypatch.setattr(dn.DecoderNode, "destroy_node", lambda self: called.setdefault("destroy", True))

    dn.main()

    assert {"init", "spin", "shutdown", "destroy"}.issubset(called.keys())


def test_main_function_keyboard_interrupt(monkeypatch):
    """Covers the KeyboardInterrupt branch in main()."""
    import decoder.decoder_node as dn

    called = {}

    monkeypatch.setattr(dn.rclpy, "init", lambda args=None: called.setdefault("init", True))

    def fake_spin(node):
        called["spin"] = True
        raise KeyboardInterrupt

    monkeypatch.setattr(dn.rclpy, "spin", fake_spin)
    monkeypatch.setattr(dn.rclpy, "shutdown", lambda: called.setdefault("shutdown", True))
    monkeypatch.setattr(dn.DecoderNode, "destroy_node", lambda self: called.setdefault("destroy", True))

    dn.main()

    assert {"init", "spin", "shutdown", "destroy"}.issubset(called.keys())
