# dekube-rewriter-nginx

![vibe coded](https://img.shields.io/badge/vibe-coded-ff69b4)
![python 3](https://img.shields.io/badge/python-3-3776AB)
![heresy: 1/10](https://img.shields.io/badge/heresy-1%2F10-brightgreen)
![stdlib only](https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen)
![public domain](https://img.shields.io/badge/license-public%20domain-brightgreen)

Nginx ingress annotation rewriter for [dekube](https://dekube.io).

Excluded from the core because nginx-ingress is deprecated. Still here, because legacy doesn't care about deprecation notices — and neither does your helmfile.

## Handled annotations

| Annotation | Caddy equivalent |
|------------|-----------------|
| `nginx.ingress.kubernetes.io/rewrite-target: /$1` | `uri strip_prefix` |
| `nginx.ingress.kubernetes.io/backend-protocol: HTTPS` | `reverse_proxy https://...` |
| `nginx.ingress.kubernetes.io/enable-cors: "true"` | `header Access-Control-Allow-*` |
| `nginx.ingress.kubernetes.io/cors-allow-origin` | `header Access-Control-Allow-Origin` |
| `nginx.ingress.kubernetes.io/cors-allow-methods` | `header Access-Control-Allow-Methods` |
| `nginx.ingress.kubernetes.io/cors-allow-headers` | `header Access-Control-Allow-Headers` |
| `nginx.ingress.kubernetes.io/proxy-body-size` | `request_body max_size` |
| `nginx.ingress.kubernetes.io/configuration-snippet` | Partial: `more_set_headers` directives extracted as `header` |

## Matching

Matches Ingress manifests with:

- `ingressClassName: nginx` (or mapped via `ingressTypes` in config)
- Any `nginx.ingress.kubernetes.io/*` annotation

## Installation

```bash
python3 dekube-manager.py nginx
```

Or manually:

```bash
cp nginx_rewriter.py /path/to/extensions-dir/
```

## Code quality

*Last updated: 2026-02-23*

| Metric | Value |
|--------|-------|
| Pylint | 9.66/10 |
| Pyflakes | clean |
| Radon MI | 55.88 (A) |
| Radon avg CC | 10.0 (B) |

Worst CC: `NginxRewriter.rewrite` (18, C).

The `E0401: Unable to import 'dekube'` is expected — extensions import from dekube-engine at runtime, not at lint time.

## Dependencies

None (stdlib only).
