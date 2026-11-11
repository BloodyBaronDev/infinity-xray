# ⚡ Infinity Xray

**English** · [Русский](README.ru.md)

**A server-side Xray build: idle connections live longer, XHTTP stays responsive under load.**
Drop-in replacement for the Xray inside [Remnawave Node](https://github.com/remnawave/node). Works with stock clients. Based on the official [XTLS/Xray-core](https://github.com/XTLS/Xray-core).

![Status](https://img.shields.io/badge/status-stable-brightgreen)
[![Release](https://img.shields.io/github/v/release/BloodyBaronDev/infinity-xray)](https://github.com/BloodyBaronDev/infinity-xray/releases/latest)
![Xray](https://img.shields.io/badge/Xray-v26.11.9-informational)
![Go](https://img.shields.io/badge/Go-1.27.3-00ADD8)
![License](https://img.shields.io/badge/license-MPL%202.0-green)
[![Stars](https://img.shields.io/github/stars/BloodyBaronDev/infinity-xray?style=social)](https://github.com/BloodyBaronDev/infinity-xray/stargazers)

## 🐳 Quick install (Remnawave Node)

Change one line in your node's `docker-compose.yml`. Ports and secrets stay the same:

```yaml
services:
  remnanode:
    image: ghcr.io/bloodybarondev/infinity-xray:0.2.0   # instead of remnawave/node
```

```bash
docker compose pull && docker compose up -d
```

The restart drops current connections. To roll back, put the old image back and recreate the service.
Plain binaries (`linux/amd64`, `windows/amd64`) with `SHA256SUMS` are on the [releases page](https://github.com/BloodyBaronDev/infinity-xray/releases/latest).

## 📈 Results

| Check | Without | With |
|---|---|---|
| 💓 Idle Hysteria connection | dies by 45 s | alive at 330 s |
| 🔁 Idle XHTTP + mux via CDN | dies by 90 s | alive at 330 s |
| 🚦 p95 of neighbour requests during a download, RTT 50 ms | 2411 ms | 309 ms |
| 🚦 Throughput against competing TCP | 84.9 Mbit/s | **34.2 Mbit/s** (governor's cost) |

0.2.0-rc.3 on a production node: 0 restarts, ~32% of one core at ~130 Mbit/s.
Small samples, partly on earlier builds. Details and caveats: [TEST_RESULTS.md](TEST_RESULTS.md) (in Russian) and [reports](reports/).

## ✨ Features

| | Feature | What it does | Limits |
|---|---|---|---|
| 💓 | **Hysteria keepalive** | Server sends QUIC keepalive during silence | Dead clients are still closed by QUIC timeouts |
| 🔁 | **Mux keepalive** | Empty Mux.Cool frames keep a quiet downlink alive through CDNs | Needs mux on the client |
| 🧩 | **Mux over XHTTP** | Server-side ban removed | Still banned for MASQUE |
| 🚦 | **HTTP/2 governor** | Lower latency for parallel requests under load | More CPU, yields bandwidth to competing TCP |
| 🛑 | **Bounded shutdown** | At most 7 s per Close, 1 s per error message | — |
| 📊 | **icstats** | Hysteria and mux counters, no traffic content | Non-mux connections not measured |
| 🔐 | **REALITY validation** | Bad keys and short IDs rejected before the listener starts | — |
| 🧱 | **TCP-only Mux.Cool** | UDP to `v1.mux.cool` goes through normal routing | — |
| ⏳ | **Delayed VLESS revoke** | Closes a removed user's connections if the key doesn't return | Off; VLESS only |
| 🚧 | **Per-user limits** | VLESS connection cap and total rate per email | Off; one value for all; no Vision splice |
| 📈 | **Prometheus metrics** | Aggregates only, no users or addresses | Off; no auth |
| 🌙 | **Graceful drain** | Accepted connections finish before shutdown | Off; not for QUIC |
| ⏱ | **Start watchdog** | A hung Start exits the process with code 1 | — |

## ⚙️ Settings

| Variable | Default | Meaning |
|---|---|---|
| `XRAY_IC_QUIC_KEEPALIVE` | `10` | QUIC keepalive interval, s; ≤0 disables |
| `XRAY_IC_MUX_KEEPALIVE` | `5` | Silence before mux keepalive, s; ≤0 disables |
| `XRAY_IC_STATS` | `60` | icstats summary interval, s; ≤0 disables |
| `XRAY_XHTTP_FLOW` | `on` in Docker, off for the binary | Server-side governor |
| `XRAY_XHTTP_FLOW_COMPETE` | off | Experimental governor competition mode |
| `XRAY_IC_REVOKE_GRACE` | `0` | VLESS revoke delay, s; must exceed the panel's remove/add pause |
| `XRAY_IC_USER_MAX_CONNS` | `0` | VLESS connections per email, mux counts as one |
| `XRAY_IC_USER_RATE_DOWN_MBPS` | `0` | Total download limit per email, Mbit/s |
| `XRAY_IC_USER_RATE_UP_MBPS` | `0` | Total upload limit per email, Mbit/s |
| `XRAY_IC_METRICS_LISTEN` | unset | `/metrics` address, e.g. `127.0.0.1:9550`; don't expose publicly |
| `XRAY_IC_DRAIN_SECONDS` | `0` | Wait for connections on shutdown, s |
| `XRAY_IC_START_TIMEOUT` | `60` | Start limit, s; ≤0 disables |

An explicit `xhttpSettings.extra.h2Flow.enabled` overrides `XRAY_XHTTP_FLOW`.

## 🛠 Build from source

Requires Python 3.11+, git, Go with toolchain auto-download; Docker for the image.

```bash
bash build.sh                # linux/amd64 binary
bash build.sh --full-checks  # plus extended governor tests
bash build.sh image          # plus a local Remnawave Node image
```

On Windows: `python build.py build`. Output: `out/<version>/linux-amd64/`.
The build checks the upstream commit and patch SHA256 from [`release.json`](release.json).

| Xray-core | Commit | Go | Build tags | Remnawave Node |
|---|---|---|---|---|
| `v26.11.9` | `676eaf6` | `go1.27.3` | `http2legacy` | `3.4.5` |

## 📚 Docs

[Test results](TEST_RESULTS.md) · [Reports](reports/) · [Development](docs/DEVELOPMENT.md) · [Changelog](CHANGELOG.md) · [Code origin](NOTICE.md) — in Russian.

Found a bug or have a question? Open an [issue](https://github.com/BloodyBaronDev/infinity-xray/issues). If this build helps you, a ⭐ helps others find it.

## 📄 License

[Mozilla Public License 2.0](LICENSE)
