"""dekube-rewriter-nginx — Nginx ingress annotation rewriter."""

import re

from dekube import IngressRewriter, get_ingress_class, resolve_backend  # pylint: disable=import-error  # h2c resolves at runtime


def _extract_strip_prefix_nginx(annotations, path):
    """Extract strip prefix from nginx rewrite-target annotation."""
    rewrite = annotations.get("nginx.ingress.kubernetes.io/rewrite-target", "")
    if rewrite in ("/$1", r"/\1"):
        prefix = re.sub(r'\(\.?\*\)$', '', path)
        if prefix and prefix != "/":
            return prefix.rstrip("/")
    return None


class NginxRewriter(IngressRewriter):
    """Rewrite nginx ingress annotations to structured ingress entries."""
    name = "nginx"

    def match(self, manifest, ctx):
        """Return True if manifest uses nginx ingress class or annotations."""
        ingress_types = ctx.config.get("ingress_types") or {}
        cls = get_ingress_class(manifest, ingress_types)
        if cls == "nginx":
            return True
        annotations = (manifest.get("metadata") or {}).get("annotations") or {}
        return any(k.startswith("nginx.ingress.kubernetes.io/") for k in annotations)

    def rewrite(self, manifest, ctx):
        """Rewrite nginx ingress manifest to structured ingress entries."""
        entries = []
        annotations = (manifest.get("metadata") or {}).get("annotations") or {}
        spec = manifest.get("spec") or {}

        for rule in spec.get("rules") or []:
            host = rule.get("host", "")
            if not host:
                continue
            for path_entry in (rule.get("http") or {}).get("paths") or []:
                path = path_entry.get("path", "/")
                backend = resolve_backend(path_entry, manifest, ctx)

                # Backend protocol annotation
                backend_ssl = str(annotations.get(
                    "nginx.ingress.kubernetes.io/backend-protocol", ""
                )).upper() == "HTTPS"
                scheme = "https" if backend_ssl else "http"

                strip_prefix = _extract_strip_prefix_nginx(annotations, path)

                entry = {
                    "host": host,
                    "path": path,
                    "upstream": backend["upstream"],
                    "scheme": scheme,
                    "strip_prefix": strip_prefix,
                }

                # Response headers from CORS and configuration-snippet
                response_headers = {}

                # CORS
                cors_enabled = str(annotations.get(
                    "nginx.ingress.kubernetes.io/enable-cors", "")).lower()
                if cors_enabled == "true":
                    response_headers["Access-Control-Allow-Origin"] = annotations.get(
                        "nginx.ingress.kubernetes.io/cors-allow-origin", "*")
                    response_headers["Access-Control-Allow-Methods"] = annotations.get(
                        "nginx.ingress.kubernetes.io/cors-allow-methods",
                        "GET, PUT, POST, DELETE, PATCH, OPTIONS")
                    response_headers["Access-Control-Allow-Headers"] = annotations.get(
                        "nginx.ingress.kubernetes.io/cors-allow-headers",
                        "DNT,X-CustomHeader,Keep-Alive,User-Agent,"
                        "X-Requested-With,If-Modified-Since,Cache-Control,"
                        "Content-Type,Authorization")

                # Custom headers from configuration-snippet
                config_snippet = annotations.get(
                    "nginx.ingress.kubernetes.io/configuration-snippet") or ""
                for line in config_snippet.splitlines():
                    line = line.strip().rstrip(";")
                    if line.startswith("more_set_headers"):
                        parts = line.split(None, 1)
                        if len(parts) == 2:
                            header_val = parts[1].strip("\"' ")
                            if ":" in header_val:
                                hk, hv = header_val.split(":", 1)
                                response_headers[hk.strip()] = hv.strip()

                if response_headers:
                    entry["response_headers"] = response_headers

                # Proxy body size
                body_size = annotations.get(
                    "nginx.ingress.kubernetes.io/proxy-body-size", "")
                if body_size and body_size != "0":
                    entry["max_body_size"] = body_size

                entries.append(entry)

        return entries
