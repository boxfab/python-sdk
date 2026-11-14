
BoxFab sandboxes are [Firecracker](https://firecracker-microvm.github.io/) microVMs, run on the
open-source [E2B](https://github.com/e2b-dev/infra) sandbox infrastructure. This package is derived
from the open-source E2B Desktop SDK;
[UPSTREAM.md](https://github.com/boxfab/python-sdk/blob/main/UPSTREAM.md) lists every change.

**Using the E2B Desktop SDKs.** BoxFab serves the same API and provides the `desktop` template, so
the E2B Desktop SDKs work with it as well. Set both variables, the domain first:

```bash
export E2B_DOMAIN=boxfab.io
export E2B_API_KEY="<your BoxFab API key>"
```

Without `E2B_DOMAIN`, the E2B SDKs send requests, including the key, to E2B's own service.

Tested against BoxFab with `e2b-desktop` 2.7.2 (Python) and `@e2b/desktop` 2.5.0 (JavaScript).

## License

MIT, as the E2B Desktop SDK it is derived from; see [LICENSE](LICENSE).

BoxFab is a product of ContextFab, Inc.
