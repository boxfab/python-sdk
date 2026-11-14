# BoxFab Desktop (Python)

A virtual Linux desktop in a [BoxFab](https://boxfab.io) sandbox, for computer-use agents: mouse
and keyboard control, screenshots, application windows, and a live stream of the screen in the
browser.

## Getting started

### 1. Get a BoxFab API key

Get a key from the [BoxFab dashboard](https://dashboard.boxfab.io) and set it as
`BOXFAB_API_KEY`. The SDK reads only `BOXFAB_*` variables.

### 2. Install the SDK

```bash
pip install boxfab-desktop
```

> **Stream access.** `desktop.stream.start()` runs without a password unless you pass
> `require_auth=True`. The stream URL contains the sandbox ID, and anyone who has the URL can see
> and control the desktop. Pass `require_auth=True` whenever the URL leaves your backend; the auth
> key is then part of the URL returned by `get_url(auth_key=...)`, so share that URL only with the
> intended viewer.

### 3. Create Desktop Sandbox

```python
from boxfab_desktop import Sandbox

# Create a new desktop sandbox
desktop = Sandbox.create()

# Launch an application
desktop.launch('google-chrome')  # or vscode, firefox, etc.

# Wait 10s for the application to open
desktop.wait(10000)

# Stream the application's window
# Note: There can be only one stream at a time
# You need to stop the current stream before streaming another application
desktop.stream.start(
    window_id=desktop.get_current_window_id(), # if not provided the whole desktop will be streamed
    require_auth=True
)

# Get the stream auth key
auth_key = desktop.stream.get_auth_key()

# Print the stream URL
print('Stream URL:', desktop.stream.get_url(auth_key=auth_key))

# Kill the sandbox after the tasks are finished
# desktop.kill()
```

### 4. Bind the configuration to a client

The top-level `Sandbox` export reads its configuration from the environment variables. To use an explicit configuration — e.g. several API keys or domains in one process — create a `BoxFab` client and use the resource classes it exposes:

```python
from boxfab_desktop import BoxFab

client = BoxFab(api_key="e2b_***", domain="boxfab.io")

desktop = client.Sandbox.create()
desktop.stream.start()

# The core resources are bound to the client's configuration as well.
volume = client.Volume.create("my-volume")
exists = client.Template.exists("my-template")
secret = client.Secret.create("openai-api-key", "sk-***")

# The classes can be assigned and used like the top-level ones.
Sandbox = client.Sandbox
paginator = Sandbox.list()
```

Per-call params still take precedence over the client's params, and clients are isolated from each other and from the env-configured top-level exports.

## Features

### Streaming desktop's screen

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

# Start the stream
desktop.stream.start()

# Get stream URL
url = desktop.stream.get_url()
print(url)

# Stop the stream
desktop.stream.stop()
```

### Streaming with password protection

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

# Start the stream
desktop.stream.start(
    require_auth=True  # Enable authentication with an auto-generated key
)

# Retrieve the authentication key
auth_key = desktop.stream.get_auth_key()

# Get stream URL
url = desktop.stream.get_url(auth_key=auth_key)
print(url)

# Stop the stream
desktop.stream.stop()
```

### Streaming specific application

> [!WARNING]
>
> - Will raise an error if the desired application is not open yet
> - The stream will close once the application closes
> - Creating multiple streams at the same time is not supported, you may have to stop the current stream and start a new one for each application

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

# Get current (active) window ID
window_id = desktop.get_current_window_id()

# Get all windows of the application
window_ids = desktop.get_application_windows("Firefox")

# Start the stream
desktop.stream.start(window_id=window_ids[0])

# Stop the stream
desktop.stream.stop()
```

### Mouse control

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

desktop.double_click()
desktop.left_click()
desktop.left_click(x=100, y=200)
desktop.right_click()
desktop.right_click(x=100, y=200)
desktop.middle_click()
desktop.middle_click(x=100, y=200)
desktop.scroll(10) # Scroll by the amount. Positive for up, negative for down.
desktop.move_mouse(100, 200) # Move to x, y coordinates
desktop.drag((100, 100), (200, 200)) # Drag using the mouse
desktop.mouse_press("left") # Press the mouse button
desktop.mouse_release("left") # Release the mouse button
```

### Keyboard control

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

# Write text at the current cursor position with customizable typing speed
desktop.write("Hello, world!")  # Default: chunk_size=25, delay_in_ms=75
desktop.write("Fast typing!", chunk_size=50, delay_in_ms=25)  # Faster typing

# Press keys
desktop.press("enter")
desktop.press("space")
desktop.press("backspace")
desktop.press(["ctrl", "c"]) # Key combination
```

### Window control

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

# Get current (active) window ID
window_id = desktop.get_current_window_id()

# Get all windows of the application
window_ids = desktop.get_application_windows("Firefox")

# Get window title
title = desktop.get_window_title(window_id)
```

### Screenshot

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

# Take a screenshot and save it as "screenshot.png" locally
image = desktop.screenshot()
# Save the image to a file
with open("screenshot.png", "wb") as f:
    f.write(image)
```

### Open file

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

# Open file with default application
desktop.files.write("/home/user/index.js", "console.log('hello')") # First create the file
desktop.open("/home/user/index.js") # Then open it
```

### Launch applications

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

# Launch the application
desktop.launch('google-chrome')
```

### Run any bash commands

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

# Run any bash command
out = desktop.commands.run("ls -la /home/user")
print(out)
```

### Wait

```python
from boxfab_desktop import Sandbox
desktop = Sandbox.create()

desktop.wait(1000) # Wait for 1 second
```

## Under the hood

The desktop-like environment is based on Linux and [Xfce](https://www.xfce.org/) at the moment. We chose Xfce because it's a fast and lightweight environment that's also popular and actively supported. However, this Sandbox template is fully customizable and you can create your own desktop environment.
BoxFab's template is in [boxfab/desktop](https://github.com/boxfab/desktop/tree/main/template), generated from [e2b-dev/desktop](https://github.com/e2b-dev/desktop/tree/main/template).

BoxFab sandboxes are [Firecracker](https://firecracker-microvm.github.io/) microVMs, run on the
open-source [E2B](https://github.com/e2b-dev/infra) sandbox infrastructure. This package is derived
from the open-source E2B Desktop SDK;
[UPSTREAM.md](https://github.com/boxfab/python-sdk/blob/main/UPSTREAM.md) lists every change.

## License

MIT, as the E2B Desktop SDK it is derived from; see [LICENSE](LICENSE).

BoxFab is a product of ContextFab, Inc.
