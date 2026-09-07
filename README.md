# Ap4726Decoder

Ap4726Decoder is a C++ decoder runtime environment for building real-time video pipelines in a Non-GPL configuration.  
It receives H.264 streams over RTSP/RTSPS, decodes them with OpenH264, and delivers the decoded data as BGR frames to downstream applications over TCP/IP.

Provided as a Docker-based package, it isolates the video decoding process inside a container while keeping external applications loosely coupled through raw frame transfer.  
Because decoded frames are delivered over TCP/IP, downstream applications can run on a different PC from Ap4726Decoder.  
This makes it possible to build downstream processing on Windows, macOS, or Linux.

It is designed to work well with downstream processing such as AI inference, recording, and redistribution, while also simplifying license management.

For the overall design policy and background of this project, please also refer to the top-level GitHub README, especially the section [Real-time Video Pipeline Architect](https://github.com/lastec-akimaru/lastec-akimaru/blob/main/README.md#real-time-video-pipeline-architect).

## Documentation

- [Japanese README](release/README_ja.md)
- [English README](release/README_en.md)

## Package contents

This repository contains documentation, configuration examples, license documents, images, and sample programs.

The Docker image archive `ap4726decoder_latest.tar` is not included in the repository itself.  
Please download it from GitHub Releases and place it in the `release/` directory.

## Sample program

The AI inference sample is included in:

- `samples/ai_inference_sample/`

## License

Please refer to the files in the `release/licenses/` directory for detailed license information.
