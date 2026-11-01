import platform

from importlib import metadata

package_version = metadata.version("boxfab")

default_headers = {
    "lang": "python",
    "lang_version": platform.python_version(),
    "package_version": metadata.version("boxfab"),
    "publisher": "boxfab",
    "sdk_runtime": "python",
    "system": platform.system(),
}
