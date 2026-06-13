# Market AMeDAS

Market AMeDAS は、国際市場のデータを気象図として観測し、機械可読な
`market_amedas_snapshot.json` を生成します。

## Colab / CLI での実行

Python依存関係をインストールしたあと、リポジトリのルートでCLIランナーを実行します。

```bash
pip install -r requirements.txt
python run_market_amedas.py --output-dir ./artifacts/YYYY-MM-DD
```

`--output-dir` で指定したディレクトリは、存在しない場合に自動作成されます。実行が成功すると、
次のファイルが保存されます。

```text
./artifacts/YYYY-MM-DD/market_amedas_snapshot.json
```

CLIランナーは既存の `Market AMeDAS (Pure Edition)` を安全な一時ディレクトリで実行し、
生成されたJSONの存在、UTF-8 JSONとしての妥当性、および
`schema_version = market_amedas_snapshot.v1` を確認してから指定先へコピーします。

## El Shaddai / Parallax Engine との接続

El Shaddai / Parallax Engine のColab管制卓と接続する場合は、CLIランナーが生成した
`market_amedas_snapshot.json` をParallax Engineへの入力として渡してください。
