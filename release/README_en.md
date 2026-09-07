<p align="right">
  <a href="README_ja.md">日本語版はこちら</a>
</p>

# Ap4726Decoder

Ap4726Decoder is a C++ decoder runtime environment for building real-time video pipelines in a Non-GPL configuration.  
It receives H.264 streams over RTSP/RTSPS, decodes them with OpenH264, and delivers them as BGR frames to downstream applications over TCP/IP.

Provided as a Docker-based package, it isolates the video decoding process inside a container while maintaining a loosely coupled architecture with external applications through raw frame transfer.
Because BGR frames are delivered over TCP/IP, the receiving application can run on a different PC from Ap4726Decoder.  
This allows downstream processing to be built not only on Linux, but also on Windows and macOS.

It can be easily combined with downstream processing such as AI inference, recording, and redistribution, while also simplifying license management.

For the overall design policy and background of this project, please also refer to the top-level GitHub README, especially the section [Real-time Video Pipeline Architect](https://github.com/lastec-akimaru/lastec-akimaru/blob/main/README.md#real-time-video-pipeline-architect).

## INDEX

1. [Features](#1-features)
2. [Expected Use Cases](#2-expected-use-cases)
3. [About This Repository](#3-about-this-repository)
4. [System Requirements](#4-system-requirements)
5. [Directory Structure](#5-directory-structure)
6. [Setup Procedure](#6-setup-procedure)
7. [Normal Start and Stop](#7-normal-start-and-stop)
8. [How to Update](#8-how-to-update)
9. [Configuration File](#9-configuration-file)
10. [How to Use the AI Integration Sample Program](#10-how-to-use-the-ai-integration-sample-program)
11. [Notes](#11-notes)
12. [Troubleshooting](#12-troubleshooting)
13. [Contact](#13-contact)
14. [Disclaimer](#14-disclaimer)

## 1. Features

- Can receive H.264 streams over RTSP/RTSPS  
- Decodes H.264 using OpenH264  
- Converts decoded I420 data into BGR format for downstream use  
- Delivers converted BGR data to client applications over TCP/IP  
- Supports separating the receiving application onto another PC over TCP/IP  
- Allows downstream processing to be built on Windows, macOS, or Linux  
- Implemented in C++ with a structure designed for real-time video processing  
- LGPL-based configuration without GPL dependency  
- Docker-based for easy deployment, distribution, and reproducibility  
- Input sources and delivery conditions can be switched through the configuration file  

## 2. Expected Use Cases

Ap4726Decoder can be used when you want to pass video obtained from a camera or video input to a downstream application as raw data.  
It is particularly suitable for cases where you want to make use of existing video input assets while connecting them to AI processing or simple evaluation flows.

### 2.1 Reuse of Existing Cameras

Existing cameras can be used for AI processing. There is no need to prepare a new camera dedicated to AI.

Ap4726Decoder can extract raw frames from camera video and pass them to downstream applications.  
This makes it possible to connect existing or spare cameras to downstream AI applications and make use of them.

### 2.2 Connection to AI Training and Inference Workloads

You can use your existing camera input or video data such as MP4 as an input source and use Ap4726Decoder as the front-end component for connecting to downstream AI training or inference processing.  
Because the video reception, decoding, and raw frame acquisition parts can be separated, users can focus on implementing downstream preprocessing and inference logic.

### 2.3 Simple Operational Verification

Because raw data decoded from camera input can be retrieved easily, it is possible to confirm the operational image with relatively little effort in PoC or simple implementation scenarios.  
For example, by adding simple drawing, recording, AI inference, or transfer processing on the downstream side, it becomes easier to perform an initial evaluation of the overall configuration.

### 2.4 Replacement from an Existing Configuration

It is also designed so that it can be easily replaced into existing configurations that have so far implemented their own decoding process and obtained raw data.  
By separating the part from video input to raw frame acquisition, it becomes easier to change the configuration while continuing to make use of existing downstream application assets.

## 3. About This Repository

This repository is the distribution package for the C++ decoder side in a Non-GPL real-time video pipeline.  
Ap4726Decoder decodes H.264 streams received over RTSP/RTSPS using OpenH264, converts them from I420 to BGR, and sends the image data to downstream applications over TCP/IP.

This repository describes how to run and configure Ap4726Decoder, the distribution structure, how to use the AI integration sample, and operational notes.  
It also includes an AI integration sample program as a minimal example for performing downstream AI inference, recording, or redistribution.

Before using it, first check 6. Setup Procedure and 9. Configuration File, and refer to 10. How to Use the AI Integration Sample Program if necessary.  
Ap4726Decoder itself is implemented in C++, while the AI sample program is written in Python 3.x.

## 4. System Requirements

The following environment is assumed.

- Linux environment on x86_64 architecture
- Docker
- Docker Compose

You need permission to execute Docker commands.

## 5. Directory Structure

This is a minimal example of the distribution structure.

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

At runtime, place the following in the same directory level as needed.  
(configured in docker-compose.yml)

```text
release/
├── appconfig.json
└── log/
```

Roles of each file and directory:

- `docker-compose.yml`  
    This file defines the container startup settings, including volume mounts and published ports.

- `appconfig.sample.json`  
    This is a sample configuration file. Before use, copy it to `appconfig.json` and edit it as needed.

- `README_ja.md` / `README_en.md`  
    These documents describe the setup procedure, usage, and important notes.

- `images/`  
    This directory stores image files referenced in the README.

- `images/ap4726_ai_sample_output.png`  
    This image shows an example output of the AI inference sample.

- `images/release_download_guide.png`  
   Reference screenshot showing how to download the distributed files from the Releases page. 

- `licenses/`  
    This directory contains license information for bundled libraries and related components.

## 6. Setup Procedure

The operational image is as follows.

```text
Camera -> RTSP/RTSPS -> Ap4726Decoder -> BGR -> User Application (AI Sample etc.)
```

When Ap4726Decoder starts, it connects to the input source set in decoder.rtsp_url in appconfig.json and starts receiving the H.264 stream.  
If it cannot connect at startup, it retries until a connection is established.  
If the connection to the camera is lost during operation, it also automatically attempts to reconnect.

The received stream is decoded by OpenH264 and converted from I420 format to BGR format.  
The converted BGR data is then delivered frame by frame from the internal TCP server in Ap4726Decoder to downstream applications.

User applications or the AI sample on the downstream side can receive frame data by connecting to this TCP server.  
The received data consists of a 4-byte payload size at the beginning, followed by packed BGR bytes.

### 6.1 Obtaining the Package

The Docker image archive `ap4726decoder_latest.tar` is not included in this repository itself.  
Open **Releases** on the GitHub repository page, then click the target release.  
Download `ap4726decoder_latest.tar` from **Assets** on the lower section of the release details page, and place it in the `release/` directory.  
*Note: **Assets** are not shown on the releases list page. They are shown on each release's details page.*

As shown in the image below, **Releases** is displayed around the middle-right area of the repository page.  

![Release download guide](images/release_download_guide.png)

1. Get this repository using `git clone` or **Download ZIP**.  
2. Open **Releases** on the GitHub repository page.  
3. Click the target release.  
4. Download `ap4726decoder_latest.tar` from **Assets** in the lower section of the release details page.  
5. Place the downloaded `ap4726decoder_latest.tar` in the `release/` directory.

After placing `ap4726decoder_latest.tar`, the directory structure will be as follows.

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

### 6.2 Check docker-compose.yml

Container startup settings are managed in docker-compose.yml.  
Normally, set ports: according to the delivery port specified in appconfig.json.

The user-side application or AI sample connects to this published port to receive BGR data.  
If you use the default delivery port 4726, set 4726:4726 as follows.

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

If you change the port number, make sure that ports: in docker-compose.yml and server.port in appconfig.json are set to the same value.

Examples of connection destinations:

- If the user-side application runs on the same PC as Ap4726Decoder  
  127.0.0.1:4726

- If the user-side application runs on a different PC  
  <IP address of the PC running Ap4726Decoder>:4726

Indentation matters in YAML files.  
If the number of spaces or the hierarchy is broken, the file may not be read correctly, so keep the formatting intact when editing. Normally, use spaces instead of tabs.

### 6.3 Prepare the Configuration File

The operational settings of Ap4726Decoder are configured in appconfig.json.  
Initially, the sample file appconfig.sample.json is included, so copy it and create appconfig.json.

```bash
cp appconfig.sample.json appconfig.json
```

The copied appconfig.json has a structure like the following.

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

At a minimum, check and configure the following items according to your environment.

- decoder.rtsp_url
- decoder.transport
- server.port

Set decoder.rtsp_url to the RTSP or RTSPS URL for your camera.  
The username, password, IP address, port number, and stream path must be changed according to the camera settings you use.

Example:

```text
rtsps://username:password@ip-address:port/stream-path
```

- username specifies the camera username.
- password specifies the camera password.
- ip-address specifies the camera IP address.
- port specifies the camera port number.
- stream-path specifies the camera stream path.

Set decoder.transport to tcp.  
Operational verification assumes a TCP-based configuration.

Set server.port to the port number on which Ap4726Decoder listens as a TCP server for BGR data delivery.  
Set the same port number in ports: in docker-compose.yml.

Also check the following in advance.

- The camera is powered on
- The camera and the execution PC are connected to a network where they can communicate
- RTSP/RTSPS is enabled on the camera side
- The transport setting on the camera side is TCP

If the settings do not match your environment, Ap4726Decoder will not be able to connect and receive data properly.

For details of the configuration items, refer to 9. Configuration File.

### 6.4 Create the Log Directory

Create the log directory as the log destination.

```bash
mkdir -p log
```

### 6.5 Prepare the Docker Image

#### Install Docker

If Docker is not installed, install Docker Engine first.  
On Ubuntu 22.04, the following procedure has been confirmed to install Docker / Docker Compose.

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable --now docker
```

Configure Docker so that it can be used without sudo. Confirm that docker has been added by running `groups`.

```bash
sudo usermod -aG docker $USER
newgrp docker
groups
```

Install Docker Compose.

```bash
sudo apt install -y docker-compose
```

Even after the steps above, Docker Compose may still require a separate installation depending on the environment.

Note: The installation procedure for Docker / Docker Compose may vary depending on your OS and environment.
If the installation does not work as described above, please adapt the steps as needed for your environment.

#### Load the Image

Place ap4726decoder_latest.tar, obtained in advance from GitHub Releases, in the release/ directory.

Then load the Docker image with the following command:

```bash
docker load -i ap4726decoder_latest.tar
```

If a permission error occurs, run the command with sudo or make sure that the Docker group settings have been applied.

### 6.6 Start

When preparation is complete, start the container with the following command.

```bash
docker compose up -d
```

### 6.7 Confirm Startup

Check the container status.

```bash
docker compose ps
```

Check the logs if necessary.

```bash
docker compose logs -f ap4726decoder
```

## 7. Normal Start and Stop

### 7.1 Start

```bash
docker compose up -d
```

### 7.2 Stop

```bash
docker compose down
```

### 7.3 Restart

```bash
docker compose restart
```

## 8. How to Update

If you want to update with a new image, perform the following steps.

### 8.1 Replacing the Distributed TAR

```bash
docker load -i ap4726decoder_latest.tar
docker compose up -d --force-recreate
```

### 8.2 Supplement

- docker load is not required every time. It is only needed when importing a new image.
- docker compose up -d --force-recreate recreates the container using the new image.

## 9. Configuration File

The Ap4726Decoder configuration is managed in appconfig.json.  
6.3 Prepare the Configuration File explained the minimum settings required for execution. This section explains the meaning of each configuration item and the points to note.

### 9.1 log_level

Specifies the log output level.  
Normally, use INFO.

### 9.2 appVersion

Version information for the application.  
Normally, use the bundled value as is.

### 9.3 logFile

Specifies the output file path for logs.  
Change the destination as necessary.

### 9.4 logFormat

Specifies the log output format.  
Normally, use json.

### 9.5 decoder.rtsp_url

Specifies the RTSP or RTSPS URL of the input source.  
Set it according to the camera username, password, IP address, port number, and stream path.

### 9.6 decoder.transport

Specifies the transport used for RTSP/RTSPS communication.  
Normally, set it to tcp. Operational verification in this repository also assumes a TCP-based configuration.

### 9.7 decoder.ffmpeg_path

Specifies the path to the ffmpeg executable to be used.  
If you use the bundled configuration, use the included setting value as is.

### 9.8 decoder.ffprobe_path

Specifies the path to the ffprobe executable to be used.  
If you use the bundled configuration, use the included setting value as is.

### 9.9 decoder.openh264_lib_path

Specifies the path to the OpenH264 library to be used.  
If you use the bundled configuration, use the included setting value as is.

### 9.10 decoder.max_frames

Specifies the maximum number of frames to retain.  
Adjust it according to memory usage and processing structure.

### 9.11 decoder.read_timeout_ms

Specifies the timeout for stream reading in milliseconds.  
Adjust it according to the communication environment and camera response.

### 9.12 server.port

Specifies the port number on which Ap4726Decoder listens as a TCP server for BGR data delivery.  
Make it match the port number specified in ports: in docker-compose.yml.

## 10. How to Use the AI Integration Sample Program

This repository includes a sample program that receives BGR frames distributed from Ap4726Decoder over TCP/IP and performs AI inference using ONNX Runtime.

This sample can be used to verify the connection between Ap4726Decoder and a downstream AI application, and also serves as a minimal example of an AI inference pipeline.

This sample has been verified in the following environments.

- OS: Ubuntu 22.04
  - Python: 3.10.12
- OS: Ubuntu 24.04
  - Python: 3.12.3

The procedure described in this README assumes Ubuntu 22.04.  
If you use Ubuntu 24.04 or another environment, please adapt the procedure as needed according to your environment.

This sample uses OpenCV for display, so it is intended to run in a desktop GUI environment.  
In an SSH-only or headless environment, the display part may not work as-is.

<a id="disk-space-and-execution-environment"></a>
#### Disk Space and Execution Environment

Installing the Python dependencies required for model preparation may require approximately 10 GB of free disk space, depending on the environment.  
If sufficient disk space is not available, prepare the sample execution environment on another PC or VM with enough free space, and perform model preparation and sample verification there.

This approach allows you to verify the sample separately from environments with limited disk capacity.  
It can also be used as a preliminary check for configurations where AI processing is intended to run on another PC equipped with a GPU.

### 10.1 Example Directory Structure

An example structure of the AI sample program is as follows.

```text
samples/
└── ai_inference_sample/
    ├── tcp_cl_4726_ai_onnx.py
    ├── config.json
    ├── requirements.txt
    ├── models/
    └── ppm_out/
```

Role of each file/directory:

- tcp_cl_4726_ai_onnx.py  
  Sample program that connects to Ap4726Decoder and performs BGR frame reception, preprocessing, ONNX inference, postprocessing, drawing, and display.

- config.json  
  Configuration file that stores the connection destination, image size, save destination, reconnection conditions, and AI inference settings for the sample program.

- requirements.txt  
  List of Python dependency libraries required to run the sample.

- models/  
  Directory for placing the ONNX model files used for inference.  
  Since pretrained model files are not included in the repository, please prepare them yourself by referring to Section 10.6.

- ppm_out/  
  Output directory for saving the first received frame.

### 10.2 What This Sample Does

The sample program mainly performs the following processing.

- Connects to the TCP server of Ap4726Decoder
- Receives image data for one frame
- Restores the received packed BGR bytes into an image array
- Performs preprocessing for ONNX model input
- Runs inference with ONNX Runtime
- Draws the inference results on the frame
- Displays the result image with OpenCV
- Saves the first received frame in PPM format if necessary

This sample implements a minimal example assuming a YOLO-family ONNX model.  
If you replace the model, you may need to adjust the preprocessing and postprocessing as necessary.

### 10.3 Processing Flow

When this sample starts, it first attempts to connect to the destination specified by app.host and app.port in config.json.  
If it cannot connect, it retries at the interval specified by app.reconnect_interval_sec.

Once the connection is established, it starts receiving frame data from Ap4726Decoder over TCP/IP.  
If the payload size of the received data matches the expected size represented by width × height × 3, the packed BGR bytes are restored into a NumPy array.

For the restored frame, the sample optionally saves the first frame, then performs preprocessing, inference with ONNX Runtime, postprocessing, and drawing in sequence.  
The result is visualized in an OpenCV window.

If the size of the received data does not match the expected value, that frame is not processed and a warning is output.

### 10.4 Data Format Received from Ap4726Decoder

The output from Ap4726Decoder is raw BGR data for each frame sent over TCP/IP.  
On the receiving side, the sample receives each frame in the following format.

Frame structure

1. First 4 bytes  
   Big-endian unsigned integer representing the payload size

2. Following payload  
   Packed BGR bytes of the image body

Payload content

The payload is a raw BGR pixel sequence arranged in the following order.

```text
B, G, R, B, G, R, B, G, R, ...
```

Each pixel uses 3 bytes, and the payload size is as follows.

```text
payload_size = width × height × 3
```

For example, if the image size is 1920x1080, it becomes:

```text
1920 × 1080 × 3 = 6220800 bytes
```

On the receiving side, this payload is read as a uint8 array and restored into an image with the following shape.

```text
(height, width, 3)
```

In Python / NumPy, it is handled approximately as follows.

```python
frame = np.frombuffer(payload, dtype=np.uint8).reshape((height, width, 3))
```

### 10.5 Preparation Before Execution

To run the AI sample program, a Python execution environment and installation of dependent libraries are required.  
Move to the sample directory, activate a virtual environment if necessary, and install the dependent libraries.

```bash
cd samples/ai_inference_sample
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

The following libraries are mainly used.

- ultralytics
- onnx
- onnxruntime
- numpy
- opencv-python

### 10.6 Prepare a Pretrained Model

This sample does not include a pre-trained model file.  
Users must obtain a pre-trained model, convert it to ONNX format, and place it in the `models/` directory.

Installing the required Python dependencies may consume a large amount of disk space depending on the environment.  
If you are concerned about available disk space, please check [Disk Space and Execution Environment](#disk-space-and-execution-environment) before proceeding.

The following is one example.

```bash
cd samples/ai_inference_sample
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install ultralytics onnx onnxruntime
mkdir -p models
python3 -c "from ultralytics import YOLO; model = YOLO('yolo11n.pt'); model.export(format='onnx')"
mv yolo11n.onnx models/
```

When obtaining, using, and converting a model, please check the license terms specified by the provider of each model.

### 10.7 Configuration File

The operational settings of the sample program are configured in config.json.  
The destination host, port, image size, save destination, reconnection conditions, model settings, and so on are managed in this configuration file.

Example configuration:

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

Main configuration items:

- app.host  
  Specifies the IP address or host name of the host running Ap4726Decoder.

- app.port  
  Specifies the delivery port number of Ap4726Decoder.

- app.width  
  Specifies the width of the image to be received.

- app.height  
  Specifies the height of the image to be received.

- app.save_dir  
  Specifies the directory where the first frame is saved.

- app.save_first_n  
  Specifies how many initial frames to save.

- app.queue_size  
  Specifies the number of queued received frames to retain.

- app.reconnect_interval_sec  
  Specifies the wait time before reconnection after a connection failure or disconnection.

- app.model_path  
  Specifies the ONNX model file to use.

- ai.model_input_size  
  Specifies the model input image size.

- ai.score_thresh  
  Specifies the minimum score to adopt a detection candidate.

- ai.nms_thresh  
  Specifies the IoU threshold for NMS.

- ai.preview_width  
  Specifies the resized preview width used for OpenCV display.

### 10.8 Example Execution

This is an example of running the sample program.

```bash
cd samples/ai_inference_sample
source .venv/bin/activate
python3 tcp_cl_4726_ai_onnx.py ./config.json
```

If Ap4726Decoder is running on a different PC, specify the IP address of that PC in app.host in config.json.

The following is an example of the execution screen. The AI inference result is drawn on the received frame and displayed in an OpenCV window.

![Ap4726Decoder AI sample output](./images/ap4726_ai_sample_output.png)

Because the above sample displays the result image in an OpenCV window, it assumes execution in a desktop GUI environment.

### 10.9 Notes

- Make sure app.width and app.height match the image size delivered from Ap4726Decoder.
- Make sure app.port matches server.port of Ap4726Decoder.
- Set app.model_path to an ONNX model file that actually exists.
- Depending on the model, adjustments may be required for preprocessing, postprocessing, output shape, class-name handling, and so on.
- This sample is a minimal configuration example. For production use, it is recommended to add exception handling, monitoring, performance tuning, and a review of the display method.
- Because this sample displays output using OpenCV, run it in a desktop GUI environment.
- In SSH-only or headless environments, the display part may not be usable as is.

## 11. Notes

### 11.1 Configuration File
- Check the appconfig.json setting in volumes: of docker-compose.yml.
- appconfig.sample.json is a template. Before use, copy it as appconfig.json and edit it according to your environment.
- Check decoder.rtsp_url, decoder.transport, and server.port before use.
- Depending on the setting values, connection, delivery, or saving may not work as expected.

### 11.2 Port Settings
- If you change the delivery port, make sure server.port in appconfig.json and ports: in docker-compose.yml are set to the same value.
- If you change only one of them, the connection will not work properly.

### 11.3 Log Directory
- Check the log setting in volumes: of docker-compose.yml.
- Also check access permissions if necessary.

### 11.4 Docker Image Updates
- After running docker build -t ap4726decoder:latest ., the existing container is not updated automatically.
- You need to recreate it with docker compose up -d --force-recreate.

### 11.5 Internal Container IP
- The internal IP address of a Docker container may change after restart and so on.
- Normally, use the published port or service name instead of the internal IP address.

### 11.6 Performance
- Performance varies depending on input resolution, frame rate, number of simultaneous connections, whether saving is enabled, and AI processing load.
- Before production use, perform sufficient evaluation under your target conditions.

### 11.7 License

The original code and related materials included in this repository are subject to a separately defined proprietary license.  
Commercial use is paid and requires a separate contract.  
For detailed terms of use, refer to LICENSE.

However, only for the AI connection sample code tcp_cl_4726_ai_onnx.py, use, modification, and use as a reference or base are permitted within the scope of non-commercial use.  
This sample code is published as a minimal configuration example for receiving raw frames output from Ap4726Decoder on the user application side and connecting them to downstream processing.  
The Docker image itself and other distribution materials are not included in this permission.  
Redistribution of the contents included in this repository, including this sample code, is prohibited.

Bundled components such as OpenH264 may be subject to their own individual license terms.  
When redistributing, check the terms of each component and manage the contents of licenses/ as necessary.

If you bundle AI models, also check the terms of use and redistribution conditions for each model separately.

## 12. Troubleshooting

### 12.1 The Container Does Not Start

```bash
docker compose ps
docker compose logs -f ap4726decoder
```

### 12.2 The Image Does Not Exist

```bash
docker load -i ap4726decoder_latest.tar
```

### 12.3 Configuration File Not Found

```bash
cp appconfig.sample.json appconfig.json
```

### 12.4 No Log Output Destination

- Check the log setting in volumes: of docker-compose.yml.

### 12.5 Cannot Connect

Check the following.

- decoder.rtsp_url is correct
- decoder.transport is set to tcp
- server.port and ports: in docker-compose.yml match
- The camera power and network connection are normal
- The destination IP address and port number are correct

### 12.6 Want to Check Dependent Libraries

```bash
docker run --rm --entrypoint /bin/bash ap4726decoder:latest -lc \
'echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"; ldd /opt/ap4726/runtime/ap4726decoder; echo "----"; ldd /opt/ap4726/bin/ffmpeg'
```

## 13. Contact

For questions, bug reports, and suggestions for improvement, please use GitHub Issues.  
I will review the content and respond as necessary.

For inquiries regarding commercial use or contracts, please review `licenses/LICENSE_4726_ja.txt` or `licenses/LICENSE_4726_en.txt`, and contact the address listed in those files.

## 14. Disclaimer

This repository and distribution materials may not work as expected depending on the usage environment and configuration details.  
Please evaluate and verify them at your own responsibility before use.
