# Nature Remo 自動制御プログラム

このプロジェクトは、Nature Remoデバイスを使用して家電製品を自動制御するPythonプログラムです。
AIアシスタント（Claude）によって作成されています。

## 機能

- Nature RemoのクラウドAPIおよびローカルAPIを利用したデバイス制御
- エアコンや照明などの家電製品の制御
- スケジュールベースの自動制御
- センサーデータに基づく自動制御（温度、湿度）
- 詳細なログ記録

## 必要条件

- Python 3.7以上
- Pipenv（パッケージ管理用）
- Nature Remoデバイス
- Nature Remo APIトークン

## インストール方法

1. リポジトリのクローン
```bash
git clone [リポジトリURL]
cd natureRemo
```

2. Python環境のセットアップ
```bash
pipenv install -r requirements.txt
pipenv shell
```

## 設定

1. 設定ファイルの作成
```bash
cp config.json.template config.json
```

2. `config.json`の編集
- APIトークンの設定
- デバイスIDの設定
- スケジュールの設定
- 自動化ルールの設定

設定例：
```json
{
  "api": {
    "token": "your_api_token_here",
    "base_url": "https://api.nature.global/1/",
    "local_url": "http://[Nature Remo IP]/messages"
  },
  "devices": {
    "aircon": {
      "id": "your_aircon_device_id",
      "settings": {
        "mode": "cool",
        "temp": "26",
        "fan": "auto"
      }
    }
  }
}
```

## 使用方法

1. プログラムの実行
```bash
python natureRemo.py
```

2. 動作確認
- ログファイル（natureRemo.log）で動作状況を確認
- 設定したスケジュールやセンサールールが正常に動作することを確認

## テスト

テストの実行：
```bash
pytest tests/
```

カバレッジレポートの生成：
```bash
pytest --cov=natureRemo tests/
```

## プロジェクト構成

```
natureRemo/
├── natureRemo.py      # メインプログラム
├── config.json        # 設定ファイル
├── requirements.txt   # 依存パッケージ
├── tests/            # テストファイル
│   └── test_natureRemo.py
└── logs/             # ログファイル
```

## 主な機能の説明

### スケジュール機能

時間指定で家電を制御できます。設定例：
```json
"schedule": [
  {
    "time": "07:00",
    "action": "turn_on_light",
    "device": "light",
    "params": {}
  }
]
```

### センサー自動制御

温度や湿度に基づいて自動制御を行います。設定例：
```json
"automation": {
  "temperature": {
    "high_threshold": 28,
    "action_high": {
      "device": "aircon",
      "action": "set_aircon",
      "params": {
        "mode": "cool",
        "temp": "26"
      }
    }
  }
}
```

## エラーハンドリング

- ネットワークエラー時は自動的にリトライ
- APIエラー時はログに詳細を記録
- 設定ファイルの不備は起動時にチェック

## 注意事項

- このプロジェクトはAI（Claude）によって生成されています
- 実運用前に十分なテストを行ってください
- APIトークンは安全に管理してください

## 参照

- [Nature Remo API ドキュメント](https://developer.nature.global/)
- [Nature Remo Cloud API](https://swagger.nature.global/)
- [Nature Remo Local API](https://local-swagger.nature.global/)

## ライセンス

MIT License
