# h2c-rewriter-nginx

![vibe coded](https://img.shields.io/badge/vibe-coded-ff69b4)
![python 3](https://img.shields.io/badge/python-3-3776AB)
![heresy: 1/10](https://img.shields.io/badge/heresy-1%2F10-brightgreen)
![stdlib only](https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen)
![public domain](https://img.shields.io/badge/license-public%20domain-brightgreen)

Nginx ingress annotation rewriter for [helmfile2compose](https://github.com/helmfile2compose).

Excluded from the core because you shouldn't use nginx-ingress anymore, it's deprecated.
Still, it's here if you want it, I know legacy is hard to fight.

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
python3 h2c-manager.py nginx
```

Or manually:

```bash
cp nginx_rewriter.py /path/to/extensions-dir/
```

## Dependencies

None (stdlib only).
