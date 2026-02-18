"""h2c-rewriter-nginx — Nginx ingress annotation rewriter for helmfile2compose."""

import re

from helmfile2compose import IngressRewriter, get_ingress_class, resolve_backend


def _extract_strip_prefix_nginx(annotations, path):
    """Extract strip prefix from nginx rewrite-target annotation."""
    rewrite = annotations.get("nginx.ingress.kubernetes.io/rewrite-target", "")
    if rewrite in ("/$1", r"/\1"):
        prefix = re.sub(r'\(\.?\*\)$', '', path)
        if prefix and prefix != "/":
            return prefix.rstrip("/")
    return None


class NginxRewriter(IngressRewriter):
    """Rewrite nginx ingress annotations to Caddy entries."""
    name = "nginx"

    def match(self, manifest, ctx):
        ingress_types = ctx.config.get("ingressTypes", {})
        cls = get_ingress_class(manifest, ingress_types)
        if cls == "nginx":
            return True
        annotations = manifest.get("metadata", {}).get("annotations") or {}
        return any(k.startswith("nginx.ingress.kubernetes.io/") for k in annotations)

    def rewrite(self, manifest, ctx):
        entries = []
        annotations = manifest.get("metadata", {}).get("annotations") or {}
        spec = manifest.get("spec") or {}

        for rule in spec.get("rules") or []:
            host = rule.get("host", "")
            if not host:
                continue
            http = rule.get("http", {})
            for path_entry in http.get("paths", []):
                path = path_entry.get("path", "/")
                backend = resolve_backend(path_entry, manifest, ctx)

                # Backend protocol annotation
                backend_ssl = annotations.get(
                    "nginx.ingress.kubernetes.io/backend-protocol", ""
                ).upper() == "HTTPS"
                scheme = "https" if backend_ssl else "http"

                strip_prefix = _extract_strip_prefix_nginx(annotations, path)

                entry = {
                    "host": host,
                    "path": path,
                    "upstream": backend["upstream"],
                    "scheme": scheme,
                    "strip_prefix": strip_prefix,
                }

                # Collect extra directives from nginx annotations
                extra = []

                # CORS
                cors_enabled = annotations.get(
                    "nginx.ingress.kubernetes.io/enable-cors", "").lower()
                if cors_enabled == "true":
                    origins = annotations.get(
                        "nginx.ingress.kubernetes.io/cors-allow-origin", "*")
                    methods = annotations.get(
                        "nginx.ingress.kubernetes.io/cors-allow-methods",
                        "GET, PUT, POST, DELETE, PATCH, OPTIONS")
                    headers = annotations.get(
                        "nginx.ingress.kubernetes.io/cors-allow-headers",
                        "DNT,X-CustomHeader,Keep-Alive,User-Agent,"
                        "X-Requested-With,If-Modified-Since,Cache-Control,"
                        "Content-Type,Authorization")
                    extra.append(f"header Access-Control-Allow-Origin \"{origins}\"")
                    extra.append(f"header Access-Control-Allow-Methods \"{methods}\"")
                    extra.append(f"header Access-Control-Allow-Headers \"{headers}\"")

                # Custom headers
                config_snippet = annotations.get(
                    "nginx.ingress.kubernetes.io/configuration-snippet", "")
                for line in config_snippet.splitlines():
                    line = line.strip().rstrip(";")
                    if line.startswith("more_set_headers"):
                        # more_set_headers "X-Key: value" → header X-Key value
                        parts = line.split(None, 1)
                        if len(parts) == 2:
                            header_val = parts[1].strip("\"' ")
                            if ":" in header_val:
                                hk, hv = header_val.split(":", 1)
                                extra.append(
                                    f"header {hk.strip()} \"{hv.strip()}\"")

                # Proxy body size → request_body max_size
                body_size = annotations.get(
                    "nginx.ingress.kubernetes.io/proxy-body-size", "")
                if body_size and body_size != "0":
                    extra.append(f"request_body max_size {body_size}")

                if extra:
                    entry["extra_directives"] = extra

                entries.append(entry)

        return entries
