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

