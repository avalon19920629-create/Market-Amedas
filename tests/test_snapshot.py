import json
import math
import runpy
import sys
import types
from pathlib import Path


sys.modules.setdefault("yfinance", types.ModuleType("yfinance"))

pandas_stub = types.ModuleType("pandas")
pandas_stub.Timestamp = type("Timestamp", (), {})
sys.modules.setdefault("pandas", pandas_stub)

numpy_stub = types.ModuleType("numpy")
numpy_stub.generic = type("generic", (), {})
sys.modules.setdefault("numpy", numpy_stub)

pyplot_stub = types.ModuleType("matplotlib.pyplot")
pyplot_stub.rcParams = {}
matplotlib_stub = types.ModuleType("matplotlib")
matplotlib_stub.pyplot = pyplot_stub
sys.modules.setdefault("matplotlib", matplotlib_stub)
sys.modules.setdefault("matplotlib.pyplot", pyplot_stub)

MODULE = runpy.run_path(str(Path(__file__).parents[1] / "Market AMeDAS (Pure Edition)"))


def sample_inputs():
    season_pressure = {
        "Spring": {"positive": 1.5, "negative": 0.5, "net": 1.0, "legacy_positive": 1.5},
        "Summer": {"positive": 0.2, "negative": 1.0, "net": -0.8, "legacy_positive": 0.2},
        "Autumn": {"positive": 0.6, "negative": 0.2, "net": 0.4, "legacy_positive": 0.6},
        "Winter": {"positive": 0.3, "negative": 0.3, "net": 0.0, "legacy_positive": 0.3},
    }
    net_ratio = {"Spring": 45.5, "Summer": -36.4, "Autumn": 18.2, "Winter": 0.0}
    legacy_ratio = {"Spring": 57.7, "Summer": 7.7, "Autumn": 23.1, "Winter": 11.5}
    detailed_assets = [
        {"Name": "ナスダック", "Ticker": "QQQ", "Score": 1.2, "Season": "Spring", "Contrib_Val": 1.2},
        {"Name": "BTC", "Ticker": "BTC-USD", "Score": -0.7, "Season": "Spring", "Contrib_Val": 0.0},
    ]
    return (
        season_pressure, net_ratio, legacy_ratio, {"Spring": 0.8, "Summer": 0.2},
        ("ドル表示", "ジャンク表示", "小型株表示"), detailed_assets,
        [detailed_assets[0]], [detailed_assets[1]], True,
    )


def test_snapshot_schema_and_warnings():
    snapshot = MODULE["build_market_amedas_snapshot"](
        *sample_inputs(), generated_at="2026-06-12T00:00:00+00:00"
    )

    assert snapshot["generated_at"] == "2026-06-12T00:00:00+00:00"
    assert snapshot["regime"]["dominant_air_mass"] == "growth"
    assert snapshot["regime"]["secondary_air_mass"] == "yield"
    assert snapshot["regime"]["net_air_mass"]["inflation"]["downdraft_pressure"] == -1.0
    assert snapshot["regime"]["net_air_mass"]["growth"]["share_pct"] == 45.5
    assert snapshot["flows"]["updrafts"][0]["asset"] == "nasdaq"
    assert snapshot["market_warnings"] == [
        "vix_storm_warning",
        "inflation_air_mass_negative",
        "btc_downdraft_under_risk_on_sensor",
    ]


def test_tie_break_and_all_negative_warning():
    args = list(sample_inputs())
    for pressure in args[0].values():
        pressure["positive"] = 0.0
        pressure["negative"] = 1.0
        pressure["net"] = -1.0

    snapshot = MODULE["build_market_amedas_snapshot"](
        *args, generated_at="2026-06-12T00:00:00+00:00"
    )

    assert snapshot["regime"]["dominant_air_mass"] == "growth"
    assert snapshot["regime"]["secondary_air_mass"] == "yield"
    assert "all_air_masses_negative" in snapshot["market_warnings"]


def test_writer_emits_utf8_standard_json_without_nonfinite_values(tmp_path, capsys):
    snapshot = {"label": "成長気団", "nan": float("nan"), "inf": math.inf}
    output_path = tmp_path / "snapshot.json"

    assert MODULE["write_market_amedas_snapshot"](snapshot, output_path)
    raw = output_path.read_text(encoding="utf-8")
    loaded = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

    assert "成長気団" in raw
    assert loaded == {"label": "成長気団", "nan": None, "inf": None}
    assert capsys.readouterr().out == ""


def test_writer_failure_is_non_fatal(tmp_path, capsys):
    assert MODULE["write_market_amedas_snapshot"]({}, tmp_path) is False
    assert capsys.readouterr().out == ""
