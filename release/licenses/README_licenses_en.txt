Third-Party Licenses
====================

This directory contains license information for third-party software included in,
or used together with, this distribution, as well as the license terms applicable
to Ap4726Decoder itself.

License Terms for Ap4726Decoder
-------------------------------
Please refer to the following files for the license terms applicable to Ap4726Decoder itself.

- LICENSE_4726_ja.txt
  Japanese version of the license terms for Ap4726Decoder.

- LICENSE_4726_en.txt
  English version of the license terms for Ap4726Decoder.

If there is any difference or inconsistency in interpretation between the Japanese version
and the English version of the license terms for Ap4726Decoder, the Japanese version
(LICENSE_4726_ja.txt) shall prevail.

Included in this distribution
-----------------------------
This distribution directory includes the following third-party components.

- FFmpeg-related binaries and shared libraries
- OpenH264
- nlohmann_json

Please refer to the respective files in this directory for details.

FFmpeg-related components
-------------------------
This distribution includes FFmpeg-related binaries and shared libraries.
Please refer to the following files for details.

- FFmpeg-ffprobe.txt
- FFmpeg-LICENSE.md
- FFmpeg-COPYING.LGPLv2.1.txt

OpenH264
--------
This distribution includes OpenH264.
Please refer to the following file for details.

- OpenH264-LICENSE.txt

nlohmann_json
-------------
This distribution includes nlohmann_json.
Please refer to the following file for details.

- nlohmann_json-LICENSE.MIT.txt

Runtime dependencies
--------------------
Some runtime dependencies may be provided separately by the target operating system,
container base image, or execution environment, and may not be included directly
in this distribution directory.

For example, if FFmpeg-related binaries are built with GnuTLS support enabled,
the GnuTLS runtime library may be provided separately as a system package in the
container or operating system environment.

Such separately provided runtime dependencies are subject to their respective
license terms.

No Warranty
-----------
Each third-party component is provided under the license terms applicable to it.
Please refer to the individual license files for details.
