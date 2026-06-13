#!/usr/bin/env python3
"""CLI runner for the extensionless Market AMeDAS Pure Edition script."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Sequence


SOURCE_FILE = Path(__file__).resolve().with_name("Market AMeDAS (Pure Edition)")
SNAPSHOT_FILENAME = "market_amedas_snapshot.json"
EXPECTED_SCHEMA_VERSION = "market_amedas_snapshot.v1"


class MarketAmedasRunError(RuntimeError):
    """Raised when Market AMeDAS does not produce a usable snapshot."""


def run_market_amedas(
    output_dir: str | Path,
    *,
    command_runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> Path:
    """Run the existing script and copy its generated snapshot to *output_dir*."""
    destination_dir = Path(output_dir).expanduser().resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)

    if not SOURCE_FILE.is_file():
        raise MarketAmedasRunError(f"Market AMeDAS本体が見つかりません: {SOURCE_FILE}")

    with tempfile.TemporaryDirectory(prefix="market-amedas-") as work_dir_name:
        work_dir = Path(work_dir_name)
        try:
            result = command_runner([sys.executable, str(SOURCE_FILE)], cwd=work_dir)
        except OSError as exc:
            raise MarketAmedasRunError(f"Market AMeDAS本体を起動できません: {exc}") from exc
        if result.returncode != 0:
            raise MarketAmedasRunError(
                f"Market AMeDAS本体の実行に失敗しました (終了コード: {result.returncode})"
            )

        generated_snapshot = work_dir / SNAPSHOT_FILENAME
        if not generated_snapshot.is_file():
            raise MarketAmedasRunError(
                f"Market AMeDAS本体が {SNAPSHOT_FILENAME} を生成しませんでした"
            )

        try:
            snapshot = json.loads(
                generated_snapshot.read_text(encoding="utf-8"),
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"非有限値 {value} は許可されていません")
                ),
            )
        except (OSError, UnicodeError, ValueError) as exc:
            raise MarketAmedasRunError(f"生成されたJSONを読み込めません: {exc}") from exc

        schema_version = snapshot.get("schema_version") if isinstance(snapshot, dict) else None
        if schema_version != EXPECTED_SCHEMA_VERSION:
            raise MarketAmedasRunError(
                "生成されたJSONのschema_versionが不正です: "
                f"期待値={EXPECTED_SCHEMA_VERSION}, 実際={schema_version!r}"
            )

        destination = destination_dir / SNAPSHOT_FILENAME
        shutil.copy2(generated_snapshot, destination)

    print(f"Market AMeDAS snapshot: {destination}")
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Market AMeDASを実行し、JSONスナップショットを指定先へ保存します。"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="market_amedas_snapshot.json の保存先ディレクトリ",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    command_runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_market_amedas(args.output_dir, command_runner=command_runner)
    except MarketAmedasRunError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
