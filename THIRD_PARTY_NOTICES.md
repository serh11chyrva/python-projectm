# Third-party components

The original Python bindings, C++ wrapper, and demonstration preset are MIT
licensed; see `LICENSE`. Binary distributions also contain separately licensed
native components. The distribution's SPDX expression includes their terms;
it does not change the license of the original binding code.

| Component | Distribution | Terms / included notice |
| --- | --- | --- |
| projectM 4.1.6 | Shared library, all wheels | LGPL-2.1-or-later; `licenses/projectM-LGPL-2.1.txt` |
| projectM-eval 1.0.5 | Incorporated into projectM | MIT; `licenses/projectm-eval.txt` |
| HLSLParser | Incorporated into projectM | MIT; `licenses/hlslparser.txt` |
| GLM 0.9.9.0 | Headers compiled into projectM | MIT alternative; `licenses/GLM.txt` |
| SOIL2, stb image code, image helpers, PVRTC code | Incorporated into projectM | Original notices and public-domain/MIT terms; `licenses/SOIL2.txt` |
| ETC1 utilities within SOIL2 | Incorporated into projectM | Apache-2.0; `licenses/Apache-2.0.txt` |
| GLEW 2.2.0 | Shared library, Windows wheels | Upstream BSD-style/MIT-style terms; `licenses/GLEW.txt` |
| Microsoft Visual C++ Release runtime | Windows wheels | Microsoft redistribution terms; `licenses/MSVC-RUNTIME.txt` |

`LicenseRef-Bundled-Dependencies` refers to the additional component-specific
terms listed in `licenses/LicenseRef-Bundled-Dependencies.txt`. Python packages
installed as dependencies and system graphics libraries are separate distributions.
Mesa is used by CI and is not shipped in the wheel.

## projectM modification and corresponding source

The native build compiles projectM 4.1.6 with one framebuffer adaptation: it
preserves the caller's draw framebuffer during final composition instead of
always rendering to framebuffer zero. `cmake/ProjectMFramebuffer.cmake` generates
the modified `ProjectM.cpp`, with a dated modification notice, in the build tree.
The original extracted upstream files are not overwritten.

Every binary release is accompanied by the `python_projectm-<version>.tar.gz`
source archive at https://github.com/serh11chyrva/python-projectm/releases.
It contains the corresponding projectM release sources, bundled vendors, GLEW
sources, wrapper, adaptation, dependency pins, and build instructions. See
`python_projectm/native/native-build.txt` in each wheel for its compiler and flags.
The release workflow uploads source access before publishing the wheels to PyPI.

projectM remains dynamically linked. To use a modified projectM, rebuild it with
the wrapper and place the compatible shared libraries together, then set
`PYTHON_PROJECTM_LIBRARY` to the rebuilt wrapper's absolute path before its first
use. Keep the C ABI and framebuffer adaptation compatible. Modification and
debugging for such replacement are permitted under the applicable licenses.
