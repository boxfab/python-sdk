"""Minimal Boxfab example. Needs BOXFAB_API_KEY in the environment."""

from boxfab import Sandbox

with Sandbox.create() as sandbox:
    result = sandbox.commands.run("echo Hello from Boxfab && uname -a")
    print(result.stdout)
