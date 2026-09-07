<p align="right">
  <a href="README_en.md">English version is here</a>
</p>

# Ap4726Decoder

Ap4726Decoder は、Non-GPL 構成でリアルタイム動画パイプラインを構築するための、C++ 製 decoder 実行環境です。  
RTSP/RTSPS で受信した H.264 ストリームを OpenH264 でデコードし、BGR フレームとして TCP/IP 経由で後段アプリケーションへ配信します。

Docker ベースで利用できるため、映像デコード処理をコンテナ内部に閉じ込めつつ、外部アプリケーションとは Raw フレーム受け渡しで疎結合に構成できます。  
TCP/IP で BGR フレームを配信する構成のため、受信側アプリケーションは Ap4726Decoder とは別の PC 上で動作させることができます。  
このため、後段処理は Linux 環境に限定されず、Windows、macOS、Linux など任意の環境で構成可能です。

AI 推論、保存、再配信などの後段処理と組み合わせやすく、ライセンス条件も整理しやすい構成です。

本プロジェクトの設計方針や背景については、[Real-time Video Pipeline Architect](https://github.com/lastec-akimaru/lastec-akimaru/blob/main/readme_jp.md#real-time-video-pipeline-architect)を併せて参照してください。

## INDEX

1. [特徴](#1-特徴)
2. [想定される利用例](#2-想定される利用例)
3. [このリポジトリについて](#3-このリポジトリについて)
4. [動作環境](#4-動作環境)
5. [ディレクトリ構成](#5-ディレクトリ構成)
6. [セットアップ手順](#6-セットアップ手順)
7. [通常の起動・停止](#7-通常の起動停止)
8. [更新方法](#8-更新方法)
9. [設定ファイル](#9-設定ファイル)
10. [AI 連携サンプルプログラムの使い方](#10-ai-連携サンプルプログラムの使い方)
11. [注意点](#11-注意点)
12. [トラブルシューティング](#12-トラブルシューティング)
13. [お問い合わせ](#13-お問い合わせ)
14. [免責](#14-免責)

## 1. 特徴

- RTSP/RTSPS で配信される H.264 ストリームを受信可能
- OpenH264 により H.264 をデコード
- デコード後の I420 データを BGR に変換して利用可能
- 変換後の BGR データを TCP/IP 経由でクライアントへ配信可能
- TCP/IP 経由で別 PC にフレーム配信できるため、受信側アプリケーションを別環境で構成可能
- 後段処理は Linux に限定されず、Windows / macOS / Linux で構成可能
- C++ により実装され、リアルタイム動画処理を意識した構成
- GPL に依存しない LGPL ベース構成
- Docker ベースで導入・配布・再現が容易
- 設定ファイルにより入力先や配信条件を切り替え可能

## 2. 想定される利用例

Ap4726Decoder は、カメラや動画入力から取得した映像を Raw データとして後段アプリケーションへ受け渡したい場合に利用できます。  
特に、既存の映像入力資産を活かしながら、AI 連携や簡易評価を行いたいケースに適しています。

### 2.1 既存カメラの再利用

既存のカメラを AI 処理に活用できます。AI 専用のカメラを新たに用意する必要はありません。

Ap4726Decoder は、カメラ映像から Raw フレームを取り出して後段アプリケーションへ受け渡すことができます。  
これにより、既存カメラや余剰カメラを、後段の AI アプリケーションへ接続して活用できます。

### 2.2 AI 学習・推論用途への接続

お手持ちのカメラ入力や mp4 などの動画データを入力元として利用し、後段の AI 学習・推論処理へ接続するための前段として利用できます。  
映像の受信、デコード、Raw フレーム取得の部分を分離できるため、利用者は後段の前処理や推論ロジックの実装に集中できます。

### 2.3 簡易的な動作確認

カメラからのデータをデコードした Raw データとして容易に取り出せるため、PoC や簡易実装において少ない工数で動作イメージを確認できます。  
たとえば、後段で簡単な描画、保存、AI 推論、転送処理を追加することで、全体構成の初期評価を進めやすくなります。

### 2.4 既存構成からの置き換え

これまで独自にデコード処理を実装し、Raw データを取得していた構成に対しても、Ap4726Decoder へ置き換えやすいように設計しています。  
映像入力から Raw フレーム取得までを分離することで、既存の後段アプリケーション資産を活かしたまま構成変更しやすくなります。

## 3. このリポジトリについて

このリポジトリは、Non-GPL 構成のリアルタイム動画パイプラインにおける C++ 製 decoder 側の配布物です。  
Ap4726Decoder は、RTSP/RTSPS で受信した H.264 ストリームを OpenH264 でデコードし、I420 から BGR に変換した画像データを TCP/IP 経由で後段アプリケーションへ配信します。

本リポジトリでは、Ap4726Decoder の実行方法、設定方法、配布構成、AI 連携サンプルの利用方法、および運用上の注意点を記載しています。  
後段で AI 推論、保存、再配信などを行うための最小構成例として、AI 連携サンプルプログラムも含めています。

利用にあたっては、まず `6. セットアップ手順` と `9. 設定ファイル` を確認し、必要に応じて `10. AI 連携サンプルプログラムの使い方` を参照してください。  
なお、Ap4726Decoder 本体は C++ で実装されており、AI サンプルプログラムは Python 3.x で構成されています。

## 4. 動作環境

以下の環境での利用を前提としています。

- x86_64 アーキテクチャの Linux 環境
- Docker
- Docker Compose

Docker コマンドを実行できる権限が必要です。

## 5. ディレクトリ構成

配布用の最小構成例です。

```text
release/
├── README_en.md
├── README_ja.md
├── appconfig.sample.json
├── docker-compose.yml
├── images
│   ├── ap4726_ai_sample_output.png
│   └── release_download_guide.png
└── licenses
    ├── FFmpeg-COPYING.LGPLv2.1.txt
    ├── FFmpeg-LICENSE.md
    ├── FFmpeg-ffprobe.txt
    ├── LICENSE_4726_en.txt
    ├── LICENSE_4726_ja.txt
    ├── OpenH264-LICENSE.txt
    ├── README_licenses_en.txt
    ├── README_licenses_ja.txt
    └── nlohmann_json-LICENSE.MIT.txt
```

実行時には、必要に応じて以下を同階層に配置します。
(docker-compose.ymlにて設定)

```text
release/
├── appconfig.json
└── log/
```

各ファイルの役割:

- docker-compose.yml  
    コンテナ起動設定です。ボリュームマウントやポート公開設定を含みます。

- appconfig.sample.json  
    設定ファイルのサンプルです。利用前に appconfig.json としてコピーして編集します。

- README_ja.md / README_en.md  
    セットアップ方法、使い方、注意点を記載します。

- images/  
    README 内で参照する画像ファイルを格納します。

- images/ap4726_ai_sample_output.png  
    AI 推論サンプルの出力例を示す画像です。

- images/release_download_guide.png  
    Releases ページから配布物をダウンロードする際の参照用スクリーンショットです。

- licenses/  
    同梱ライブラリや関連コンポーネントのライセンス情報を格納します。

## 6. セットアップ手順

動作のイメージは以下の通りです。

```text
Camera -> RTSP/RTSPS -> Ap4726Decoder -> BGR -> User Application (AI Sample etc.)
```

Ap4726Decoder を起動すると、appconfig.json の `decoder.rtsp_url` に設定された入力元へ接続し、H.264 ストリームの受信を開始します。  
起動時に接続できない場合は、接続できるまで接続を再試行します。  
また、動作中にカメラとの接続が切断された場合も、自動的に再接続を試みます。

受信したストリームは OpenH264 によりデコードされ、I420 形式から BGR 形式へ変換されます。  
変換後の BGR データは、Ap4726Decoder 内部の TCP server から 1 frame 単位で後段アプリケーションへ配信されます。

後段のユーザアプリケーションや AI サンプルは、この TCP server に接続することで frame データを受信できます。  
受信データは、先頭 4 byte に payload size、その後ろに packed BGR bytes が続く構成です。

### 6.1 パッケージの入手

Docker イメージアーカイブ `ap4726decoder_latest.tar` はリポジトリ本体には含まれていません。  
GitHub リポジトリページの **Releases** を開き、対象の Release をクリックしてください。  
Release 詳細ページの下部にある **Assets** から `ap4726decoder_latest.tar` をダウンロードし、`release/` ディレクトリに配置してください。  
※ `Assets` は Release 一覧ページには表示されず、各 Release の詳細ページに表示されます。

Releasesは画面右側の中段あたりに下記画像のように表示されています。

![Release download guide](images/release_download_guide.png)

1. 本リポジトリを `git clone` または `Download ZIP` で取得します。  
2. GitHub リポジトリページの **Releases** を開きます。  
3. 対象の Release をクリックします。  
4. Release 詳細ページの下部にある **Assets** から `ap4726decoder_latest.tar` をダウンロードします。  
5. ダウンロードした `ap4726decoder_latest.tar` を `release/` ディレクトリに配置します。

`ap4726decoder_latest.tar`を配置すると以下のようになります。

```text
release/
├── README_en.md
├── README_ja.md
├── ap4726decoder_latest.tar
├── appconfig.sample.json
├── docker-compose.yml
├── images
│   └── ap4726_ai_sample_output.png
└── licenses
    ├── FFmpeg-COPYING.LGPLv2.1.txt
    ├── FFmpeg-LICENSE.md
    ├── FFmpeg-ffprobe.txt
    ├── LICENSE_4726_en.txt
    ├── LICENSE_4726_ja.txt
    ├── OpenH264-LICENSE.txt
    ├── README_licenses_en.txt
    ├── README_licenses_ja.txt
    └── nlohmann_json-LICENSE.MIT.txt
```

### 6.2 docker-compose.yml の確認

コンテナの起動設定は docker-compose.yml で管理します。  
通常は、appconfig.json で指定した配信ポートに合わせて、ports: を設定します。

ユーザ側アプリケーションや AI サンプルは、この公開ポートに接続して BGR データを受信します。  
デフォルトの配信ポートを 4726 とする場合は、以下のように 4726:4726 を設定してください。

```yaml
services:
  ap4726decoder:
    image: ap4726decoder:latest
    container_name: ap4726decoder
    ports:
      - "4726:4726"
    volumes:
      - ./appconfig.json:/opt/ap4726/runtime/appconfig.json
      - ./log:/opt/ap4726/runtime/log
    restart: unless-stopped
```

ポート番号を変更する場合は、docker-compose.yml の ports: と appconfig.json の server.port を同じ値にそろえてください。

接続先の例:

- ユーザ側アプリケーションが Ap4726Decoder と同じ PC で動作する場合  
  127.0.0.1:4726

- ユーザ側アプリケーションが別の PC で動作する場合  
  <Ap4726Decoder が動作している PC の IP アドレス>:4726

YAML ファイルはインデントに意味があります。  
スペースの数や階層が崩れると正しく読み込まれないため、記述時はフォーマットを維持してください。通常はタブではなくスペースを使用してください。

### 6.3 設定ファイルの準備

Ap4726Decoder の動作設定は appconfig.json で行います。  
初期状態ではサンプルファイル appconfig.sample.json が含まれているため、これをコピーして appconfig.json を作成してください。

```bash
cp appconfig.sample.json appconfig.json
```

コピーした appconfig.json は、たとえば以下のような構成になっています。

```json
{
  "log_level": "INFO",
  "appVersion": "1.0.0",
  "logFile": "log/4726.det",
  "logFormat": "json",
  "decoder": {
    "rtsp_url": "rtsps://username:password@IP Address:port/stream",
    "transport": "tcp",
    "ffmpeg_path": "../bin/ffmpeg",
    "ffprobe_path": "../bin/ffprobe",
    "openh264_lib_path": "../lib/libopenh264.so",
    "max_frames": 300,
    "read_timeout_ms": 30000
  },
  "server": {
    "port": 4726
  }
}
```

少なくとも、以下の項目は利用環境に合わせて確認・設定してください。

- decoder.rtsp_url
- decoder.transport
- server.port

decoder.rtsp_url には、お使いのカメラに合わせた RTSP または RTSPS の URL を設定してください。  
ユーザー名、パスワード、IP アドレス、ポート番号、ストリームパスは、使用するカメラの設定に応じて変更が必要です。

例:

```text
rtsps://username:password@ip-address:port/stream-path
```

- `username` にはカメラのユーザー名を指定します。
- `password` にはカメラのパスワードを指定します。
- `ip-address` にはカメラの IP アドレスを指定します。
- `port` にはカメラのポート番号を指定します。
- `stream-path` にはカメラのストリームパスを指定します。

decoder.transport には tcp を設定してください。  
動作確認は TCP 構成を前提としています。

server.port には、Ap4726Decoder が BGR データ配信用 TCP server として待ち受けるポート番号を設定します。  
docker-compose.yml の ports: には、この値と同じポート番号を設定してください。

また、事前に以下を確認してください。

- カメラの電源が入っていること
- カメラと実行 PC が通信可能なネットワークに接続されていること
- カメラ側の RTSP/RTSPS 設定が有効になっていること
- カメラ側の転送設定が TCP になっていること

設定内容が環境に合っていない場合、Ap4726Decoder は正常に接続・受信できません。

設定項目の詳細は、9. 設定ファイル を参照してください。

### 6.4 ログディレクトリの作成

ログ保存先として log ディレクトリを作成します。

```bash
mkdir -p log
```

### 6.5 Docker イメージの準備

#### Docker のインストール

Docker がインストールされていない場合は、先に Docker Engine を導入してください。  
Ubuntu 22.04 では、以下の手順で Docker / Docker Compose をインストールできることを確認しています。

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable --now docker
```

ユーザー権限で実行できるように設定します。`groups`でdockerが追加されたことを確認します。

```bash
sudo usermod -aG docker $USER
newgrp docker
groups
```

Docker Composeをインストールします。

```bash
sudo apt install -y docker-compose
```

上記手順でも Docker Compose が利用できない環境では、別途 Compose のインストールが必要になる場合があります。

※ Docker / Docker Compose のインストール方法は、OS や環境によって異なる場合があります。
うまくインストールできない場合は、ご利用の環境に合わせて適宜読み替えてください。

#### イメージの読み込み

事前に GitHub Releases から取得した `ap4726decoder_latest.tar` を `release/` ディレクトリに配置してください。

その後、以下のコマンドで Docker イメージを読み込みます。

```bash
docker load -i ap4726decoder_latest.tar
```

権限エラーが発生する場合は、sudo を付けて実行するか、Docker グループ設定が反映されていることを確認してください。

### 6.6 起動

準備ができたら、以下のコマンドでコンテナを起動します。

```bash
docker compose up -d
```

### 6.7 起動確認

コンテナの状態を確認します。

```bash
docker compose ps
```

必要に応じてログを確認してください。

```bash
docker compose logs -f ap4726decoder
```

## 7. 通常の起動・停止

### 7.1 起動

```bash
docker compose up -d
```

### 7.2 停止

```bash
docker compose down
```

### 7.3 再起動

```bash
docker compose restart
```

## 8. 更新方法

新しいイメージで更新する場合は、以下の手順を実施します。

### 8.1 配布済み tar を差し替える場合

```bash
docker load -i ap4726decoder_latest.tar
docker compose up -d --force-recreate
```

### 8.2 補足

- docker load は毎回不要です。新しいイメージを取り込むときのみ必要です。
- docker compose up -d --force-recreate により、新しいイメージを使ってコンテナを再作成します。

## 9. 設定ファイル

Ap4726Decoder の設定は appconfig.json で管理します。  
6.3 設定ファイルの準備 では実行に必要な最低限の設定項目を説明しました。この章では、各設定項目の意味と注意点を説明します。

### 9.1 log_level

ログ出力レベルを指定します。  
通常は INFO を指定します。

### 9.2 appVersion

アプリケーションのバージョン情報です。  
通常は付属の値をそのまま使用してください。

### 9.3 logFile

ログ出力先のファイルパスを指定します。  
必要に応じて保存先を変更してください。

### 9.4 logFormat

ログ出力形式を指定します。  
通常は json を使用します。

### 9.5 decoder.rtsp_url

入力元となる RTSP または RTSPS の URL を指定します。  
カメラのユーザー名、パスワード、IP アドレス、ポート番号、ストリームパスに合わせて設定してください。

### 9.6 decoder.transport

RTSP/RTSPS 通信時の transport を指定します。  
通常は tcp を指定してください。本リポジトリの動作確認も TCP 構成を前提としています。

### 9.7 decoder.ffmpeg_path

使用する ffmpeg のパスを指定します。  
同梱している構成を使用する場合は、付属の設定値をそのまま使用してください。

### 9.8 decoder.ffprobe_path

使用する ffprobe のパスを指定します。  
同梱している構成を使用する場合は、付属の設定値をそのまま使用してください。

### 9.9 decoder.openh264_lib_path

使用する OpenH264 ライブラリのパスを指定します。  
同梱している構成を使用する場合は、付属の設定値をそのまま使用してください。

### 9.10 decoder.max_frames

保持する最大フレーム数を指定します。  
メモリ使用量や処理構成に応じて調整してください。

### 9.11 decoder.read_timeout_ms

ストリーム読み取り時のタイムアウト時間をミリ秒単位で指定します。  
通信環境やカメラ応答に応じて調整してください。

### 9.12 server.port

Ap4726Decoder が BGR データ配信用 TCP server として待ち受けるポート番号を指定します。  
docker-compose.yml の ports: に指定するポート番号と一致させてください。

## 10. AI 連携サンプルプログラムの使い方

本リポジトリには、Ap4726Decoder から TCP/IP 経由で配信される BGR フレームを受信し、ONNX Runtime を用いて AI 推論を実行するサンプルプログラムが含まれます。

このサンプルは、Ap4726Decoder と後段 AI アプリケーションの接続確認、および AI 推論処理の最小構成例として利用できます。

本サンプルは、以下の環境で動作確認済みです。

- OS: Ubuntu 22.04
  - Python: 3.10.12
- OS: Ubuntu 24.04
  - Python: 3.12.3

本 README に記載の手順は、Ubuntu 22.04 を前提としています。  
Ubuntu 24.04 やその他の環境で実行する場合は、環境差異に応じて適宜読み替えて対応してください。

本サンプルは OpenCV による表示を行うため、デスクトップ GUI 環境での実行を前提としています。  
SSH のみの環境や headless 環境では、表示部分がそのままでは利用できない場合があります。

<a id="disk-space-and-execution-environment"></a>
#### ディスク容量と実行環境について

モデル作成に必要な Python 依存パッケージのインストールには、環境によっては 10GB 程度の空き容量が必要になる場合があります。  
ディスク容量が不足している場合は、十分な空き容量のある別の PC または VM 上にサンプル実行環境を構築し、その環境でモデル作成とサンプルの動作確認を行ってください。

この方法により、容量制約のある環境と切り分けて検証できます。  
また、GPU を搭載した別 PC 上で AI を実行する構成を想定した事前確認にも利用できます。

### 10.1 ディレクトリ構成例

AI サンプルプログラムの構成例は以下の通りです。

```text
samples/
└── ai_inference_sample/
    ├── tcp_cl_4726_ai_onnx.py
    ├── config.json
    ├── requirements.txt
    ├── models/
    └── ppm_out/
```

各ファイル/ディレクトリの役割:

- tcp_cl_4726_ai_onnx.py  
  Ap4726Decoder に接続し、BGR フレーム受信、前処理、ONNX 推論、後処理、描画、表示を行うサンプルプログラムです。

- config.json  
  サンプルプログラムの接続先、画像サイズ、保存先、再接続条件、AI 推論設定を保持する設定ファイルです。

- requirements.txt  
  サンプル実行に必要な Python 依存ライブラリ一覧です。

- models/  
  推論に使用する ONNX モデルファイルを配置するディレクトリです。  
  学習済みモデルファイルはリポジトリに含まれていないため、10.6節を参照して利用者にて準備してください。

- ppm_out/  
  受信した先頭フレームを保存する出力先ディレクトリです。

### 10.2 このサンプルが行うこと

サンプルプログラムは、主に以下の処理を行います。

- Ap4726Decoder の TCP server に接続する
- 1 frame 分の画像データを受信する
- 受信した packed BGR bytes を画像配列に復元する
- ONNX モデル入力用の前処理を行う
- ONNX Runtime で推論を実行する
- 推論結果をフレームへ描画する
- 結果画像を OpenCV で表示する
- 必要に応じて、受信した先頭フレームを PPM 形式で保存する

本サンプルでは、YOLO 系 ONNX モデルを想定した最小構成を例として実装しています。  
モデルを差し替える場合は、必要に応じて前処理や後処理の調整が必要です。

### 10.3 動作の流れ

本サンプルを起動すると、まず config.json の app.host および app.port で指定した接続先へ接続を試みます。  
接続できない場合は、app.reconnect_interval_sec で指定した間隔ごとに再接続を試行します。

接続に成功すると、Ap4726Decoder から TCP/IP 経由で frame データの受信を開始します。  
受信したデータの payload size が width × height × 3 で表される期待サイズと一致する場合は、packed BGR bytes を NumPy 配列へ復元します。

復元した frame に対しては、必要に応じて先頭 frame の保存を行ったうえで、前処理、ONNX Runtime による推論、後処理、描画を順に実施します。  
その結果は、OpenCV のウィンドウ上に可視化表示されます。

受信データのサイズが期待値と一致しない場合は、その frame は処理せず警告を出力します。

### 10.4 Ap4726Decoder から受信するデータ形式

Ap4726Decoder からの出力は、TCP/IP 経由で送信される 1 frame 単位の BGR 生データです。  
受信側サンプルでは、各 frame を以下の形式で受け取ります。

フレーム構造

1. 先頭 4 byte  
   payload サイズを表す big-endian unsigned int

2. 続く payload  
   画像本体の packed BGR bytes

payload の内容

payload は、以下の順序で並んだ生の BGR 画素列です。

```text
B, G, R, B, G, R, B, G, R, ...
```

1 pixel あたり 3 byte を使用し、payload サイズは以下です。

```text
payload_size = width × height × 3
```

たとえば、画像サイズが 1920x1080 の場合は以下になります。

```text
1920 × 1080 × 3 = 6220800 bytes
```

受信側では、この payload を uint8 配列として読み込み、以下の形状の画像に復元します。

```text
(height, width, 3)
```

Python / NumPy では、概ね以下のように扱います。

```python
frame = np.frombuffer(payload, dtype=np.uint8).reshape((height, width, 3))
```

### 10.5 実行前準備

#### Python のインストール

AI 推論サンプルを実行するには、Python 3 および `venv` が必要です。  
Ubuntu 22.04 では、以下の手順でインストールできます。

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

#### 仮想環境の有効化と依存ライブラリのインストール
サンプルディレクトリへ移動し、必要に応じて仮想環境を有効化したうえで、依存ライブラリをインストールしてください。

```bash
cd samples/ai_inference_sample
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

主に以下のライブラリを使用します。

- ultralytics
- onnx
- onnxruntime
- numpy
- opencv-python

### 10.6 学習済みモデルの準備

本サンプルには学習済みモデルファイルは含まれていません。  
利用者にて学習済みモデルを取得し、ONNX 形式へ変換して models/ ディレクトリへ配置してください。

Python 依存パッケージのインストールには、環境によっては多くのディスク容量が必要になる場合があります。  
空き容量に不安がある場合は、事前に[ディスク容量と実行環境について](#disk-space-and-execution-environment)を確認してください。

以下は一例です。

```bash
cd samples/ai_inference_sample
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install ultralytics onnx onnxruntime
mkdir -p models
python3 -c "from ultralytics import YOLO; model = YOLO('yolo11n.pt'); model.export(format='onnx')"
mv yolo11n.onnx models/
```

モデルの取得、利用、変換にあたっては、各モデルの提供元が示すライセンス条件を確認してください。

### 10.7 設定ファイル

サンプルプログラムの動作設定は config.json で行います。  
接続先ホスト、ポート、画像サイズ、保存先、再接続条件、モデル設定などは、この設定ファイルで管理します。

設定例:

```json
{
  "app": {
    "host": "127.0.0.1",
    "port": 4726,
    "width": 1920,
    "height": 1080,
    "save_dir": "./ppm_out",
    "save_first_n": 1,
    "queue_size": 2,
    "reconnect_interval_sec": 2.0,
    "model_path": "./models/yolo11n.onnx"
  },
  "ai": {
    "model_input_size": 640,
    "score_thresh": 0.25,
    "nms_thresh": 0.45,
    "preview_width": 960
  }
}
```

主な設定項目:

- app.host  
  Ap4726Decoder が動作しているホストの IP アドレスまたはホスト名を指定します。

- app.port  
  Ap4726Decoder の配信ポート番号を指定します。

- app.width  
  受信する画像の幅を指定します。

- app.height  
  受信する画像の高さを指定します。

- app.save_dir  
  先頭フレーム保存先ディレクトリを指定します。

- app.save_first_n  
  先頭何フレーム保存するかを指定します。

- app.queue_size  
  受信フレームを保持するキュー数を指定します。

- app.reconnect_interval_sec  
  接続失敗時または切断時の再接続待機時間を指定します。

- app.model_path  
  使用する ONNX モデルファイルを指定します。

- ai.model_input_size  
  モデル入力画像サイズを指定します。

- ai.score_thresh  
  検出候補として採用する最小 score を指定します。

- ai.nms_thresh  
  NMS の IoU 閾値を指定します。

- ai.preview_width  
  OpenCV 表示時の縮小プレビュー幅を指定します。



### 10.8 実行例

サンプルプログラムの実行例です。

```bash
cd samples/ai_inference_sample
source .venv/bin/activate
python3 tcp_cl_4726_ai_onnx.py ./config.jso
```

別の PC 上で Ap4726Decoder を動かしている場合は、config.json の app.hostn にその PC の IP アドレスを指定してください。

実行画面の例です。受信したフレームに対して AI 推論結果を描画し、OpenCV ウィンドウで表示しています。

![Ap4726Decoder AI sample output](./images/ap4726_ai_sample_output.png)

上記サンプルは、結果画像を OpenCV のウィンドウで表示するため、Desktop の GUI 環境での実行を前提としています。

### 10.9 注意点

- app.width と app.height は、Ap4726Decoder から配信される画像サイズと一致させてください。
- app.port は、Ap4726Decoder の server.port と一致させてください。
- app.model_path には、実際に存在する ONNX モデルファイルを指定してください。
- モデルによっては、前処理、後処理、出力 shape、クラス名処理などの調整が必要です。
- 本サンプルは最小構成例であり、実運用向けには例外処理、監視、性能調整、表示方法の見直しなどを追加することを推奨します。
- 本サンプルは OpenCV による表示を行うため、Desktop の GUI 環境で実行してください。
- SSH のみの環境や headless 環境では、表示部分がそのままでは利用できない場合があります。

## 11. 注意点

### 11.1 設定ファイル
- docker-compose.yml の volumes:のappconfig.jsonの設定を確認してください
- appconfig.sample.json はテンプレートです。利用前に appconfig.json としてコピーし、環境に合わせて編集してください。
- decoder.rtsp_url、decoder.transport、server.port は利用前に確認してください。
- 設定値によっては期待通りに接続・配信・保存されない場合があります。

### 11.2 ポート設定
- 配信ポートを変更する場合は、appconfig.json の server.port と docker-compose.yml の ports: を同じ値にそろえてください。
- どちらか一方だけ変更すると、正常に接続できません。

### 11.3 ログディレクトリ
- docker-compose.yml の volumes:のlogの設定を確認してください
- 必要に応じてアクセス権も確認してください。

### 11.4 Docker イメージ更新
- docker build -t ap4726decoder:latest . 実行後は、既存コンテナに自動反映されません。
- docker compose up -d --force-recreate で再作成が必要です。

### 11.5 コンテナ内部 IP
- Docker コンテナの内部 IP は再起動などで変わることがあります。
- 通常は内部 IP ではなく、公開ポートまたはサービス名を利用してください。

### 11.6 パフォーマンス
- 入力解像度、フレームレート、同時接続数、保存有無、AI 処理負荷によって性能は変動します。
- 本番運用前に、対象条件で十分な評価を行ってください。

### 11.7 ライセンス

本リポジトリに含まれる自作コードおよび関連資料は、別途定める独自ライセンスに従います。  
商用利用は有料とし、別途契約を必要とします。  
詳細な利用条件は `LICENSE` を参照してください。

ただし、AI 接続サンプルコード `tcp_cl_4726_ai_onnx.py` に限り、非商用利用の範囲での利用、改変、ならびに参考またはベースとしての使用を認めます。  
本サンプルコードは、Ap4726Decoder から出力される Raw フレームを利用者アプリケーション側で受け取り、後段処理へ接続するための最小構成例として公開するものです。  
Docker イメージ本体およびその他の配布物は、この許可対象には含まれません。  
また、当該サンプルコードを含め、本リポジトリに含まれる内容の再配布は禁止します。

OpenH264 などの同梱コンポーネントには個別のライセンス条件が適用される場合があります。  
再配布時は、各コンポーネントの条件を確認し、必要に応じて `licenses/` の内容も含めて管理してください。

AI モデルを同梱する場合も、モデルごとの利用条件および再配布条件を別途確認してください。

## 12. トラブルシューティング

### 12.1 コンテナが起動しない

```bash
docker compose ps
docker compose logs -f ap4726decoder
```

### 12.2 イメージが存在しない

```bash
docker load -i ap4726decoder_latest.tar
```

### 12.3 設定ファイルが見つからない

```bash
cp appconfig.sample.json appconfig.json
```

### 12.4 ログ出力先がない

- docker-compose.yml の volumes:のlogの設定を確認してください

### 12.5 接続できない

以下を確認してください。

- decoder.rtsp_url が正しいこと
- decoder.transport が tcp になっていること
- server.port と docker-compose.yml の ports: が一致していること
- カメラの電源およびネットワーク接続が正常であること
- 接続先 IP アドレスとポート番号が正しいこと

### 12.6 依存ライブラリを確認したい

```bash
docker run --rm --entrypoint /bin/bash ap4726decoder:latest -lc \
'echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"; ldd /opt/ap4726/runtime/ap4726decoder; echo "----"; ldd /opt/ap4726/bin/ffmpeg'
```
## 13. お問い合わせ

質問、不具合報告、改善提案については、GitHub の Issue をご利用ください。
内容を確認のうえ、必要に応じて対応します。

商用利用や契約に関するご相談については、`licenses/LICENSE_4726_ja.txt` または `licenses/LICENSE_4726_en.txt` をご確認のうえ、各ファイルに記載のお問い合わせ先へお問い合わせください。

## 14. 免責

本リポジトリおよび配布物は、利用環境や設定内容によって期待通りに動作しない場合があります。  
利用者自身の責任において評価・検証のうえご利用ください。
