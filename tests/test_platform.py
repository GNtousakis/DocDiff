import pytest
from PIL import Image

from docdiff.capture import CaptureError, Monitor, crop_selection, match_monitor
from docdiff.imaging import preprocess
from docdiff.platform_win import HotkeyError, HotkeyRegistry, MOD_ALT, MOD_CONTROL, MOD_SHIFT, parse_hotkey
from docdiff.regions import append_text, remove_region_text


def test_parse_hotkey_defaults():
    assert parse_hotkey("Ctrl+Alt+A") == (MOD_CONTROL | MOD_ALT, ord("A"))
    assert parse_hotkey("ctrl+shift+f5") == (MOD_CONTROL | MOD_SHIFT, 0x74)
    assert parse_hotkey("Ctrl+Alt+7") == (MOD_CONTROL | MOD_ALT, ord("7"))


@pytest.mark.parametrize("bad", ["", "A", "Ctrl", "Ctrl+", "Foo+A", "Ctrl+Alt+Esc", "Ctrl+F99"])
def test_parse_hotkey_invalid(bad):
    with pytest.raises(HotkeyError):
        parse_hotkey(bad)


def test_registry_reports_invalid_and_unsupported():
    reg = HotkeyRegistry()
    assert reg.register("a", "nonsense") == "invalid"
    import sys

    if sys.platform != "win32":
        assert reg.register("a", "Ctrl+Alt+A") == "unsupported"
    reg.unregister_all()


def test_preprocess_upscales_and_grays():
    out = preprocess(Image.new("RGB", (200, 100), "white"))
    assert out.mode == "L" and out.size == (600, 300)
    big = preprocess(Image.new("RGB", (1200, 900), "white"))
    assert big.size == (2400, 1800)


def test_crop_selection_scales_logical_to_physical():
    img = Image.new("RGB", (3000, 2000))  # 150% of a 2000x1333 logical widget
    c = crop_selection(img, (100, 100, 200, 100), (2000, 1333.3333))
    assert abs(c.width - 300) <= 1 and abs(c.height - 150) <= 1
    with pytest.raises(CaptureError):
        crop_selection(img, (10, 10, 0, 0), (2000, 1333))


def test_match_monitor_prefers_closest_geometry():
    mons = [Monitor(0, 0, 2880, 1620), Monitor(2880, 0, 1920, 1080)]
    assert match_monitor(mons, 2880, 0, 1920, 1080) == 1
    assert match_monitor(mons, 0, 0, 2880, 1620) == 0


def test_region_text_helpers():
    assert append_text("", "a") == "a"
    assert append_text("a\n", "b") == "a\nb"
    assert remove_region_text("a\nb\nc", "b") == ("a\nc", True)
    assert remove_region_text("a\nb", "b") == ("a", True)
    assert remove_region_text("a\nb", "zzz") == ("a\nb", False)
