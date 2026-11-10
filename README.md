# YCast Home Assistant Addon

Self-hosted [vTuner](https://en.wikipedia.org/wiki/V-Tuner) replacement for
AVR receivers, powered by [YCast](https://github.com/milaq/YCast).

The original vTuner service is gone, which leaves the internet radio feature
of older sound stations (e.g. Denon AVR-X1000, Marantz NR1506,
Onkyo TX-NR5009, Yamaha RX-V773) with dead links. This addon brings those
devices back:

**You need your own DNS server with rewrite capability** (the AVRs only know
fixed `*.vtuner.com` hostnames, those must be pointed to your server).

- your AVR keeps using its built-in vTuner internet radio exactly as before,
  just pointed at your own server
- "My Stations" is managed from the Home Assistant Web UI (or a YAML file)
- the [Radio Browser](https://www.radio-browser.info) index is available from
  the AVR out of the box
- no proprietary service, no downtime, no fees

> **Attention:** this addon is mostly vibe coded - i tested it and its
> working :P

## How it works

```
+---------+      +--------------------------+
|         |  1  | Router (DNS)              |
| Denon   | --->| denon.vtuner.com          |
| AVR     |     +--------------------------+
| (vTuner)|  2  <--- Homeassistant-IP
|         |
|         |  3  http://denon.vtuner.com:80
|         |     /setupapp/...  /ycast/...
|         | -----------------> +--------------------------+
|         |                    | HA server                |
|         |  4  station list   | Homeassistant-IP         |
|         | <----------------- |   :80  proxy (NPM)       |
|         |                    |     -> :2080 YCast addon |
|         |                    +--------------------------+
|         |
|         |  5  mp3 stream (direct)
|         | -----------------> +--------------------------+
|         |                    | Internet                 |
|         |                    | radio provider (mp3 url) |
+---------+                    +--------------------------+
```

- vTuner-capable AVRs query fixed hostnames (`denon.vtuner.com`,
  `radioyamaha.vtuner.com`, `onkyo.vtuner.com`, ...) over plain HTTP on port 80
- your DNS points those names to your Home Assistant server
- a reverse proxy on port 80 forwards the requests to this addon;
  YCast speaks the vTuner protocol itself, so no path rewriting is needed
- the station management UI runs through Home Assistant ingress - it is part
  of the HA Web UI and needs no extra port or proxy

## Requirements

- an AVR with vTuner support (see
  [confirmed devices](https://github.com/milaq/YCast#confirmed-working))
- DNS entries for the vtuner hostnames of your AVR brand pointing to your HA
  server IP, e.g. `denon.vtuner.com` for Denon/Marantz,
  `radioyamaha.vtuner.com` for Yamaha, `onkyo.vtuner.com` for Onkyo
- a reverse proxy on port 80 - tested with the
  [Nginx Proxy Manager](https://github.com/NginxProxyManager/nginx-proxy-manager)
  addon, configured via its Web UI:
  1. create a proxy host for the vtuner domain (e.g. `denon.vtuner.com`)
  2. backend: `<ha-server-ip>:<addon-port>` (e.g. port `2080`)
  3. no custom locations needed

## Installation

1. Add this repo as a custom repository in HA (Settings > Add-ons > Repositories)
2. Install the YCast addon
3. Set the host port in the Network tab (e.g. 2080)
4. Create the DNS entry and the reverse proxy host

## Configuration

### Stations (Web UI)

The addon registers a **YCast** panel in the Home Assistant UI. Open it from
the addon page (**Open Web UI**) or enable it as a sidebar entry. There you
can:

- add stations by hand (category, name, stream URL)
- search the [Radio Browser](https://www.radio-browser.info) index and add
  stations with one click
- edit or remove existing stations

Changes are written to `/data/stations.yml` and take effect immediately, no
restart needed.

### Stations (manual)

Alternatively edit `/data/stations.yml` directly (accessible via the addon's
share mapping or Samba):

```yaml
Category Name:
  Station Name: http://stream-url.mp3
  Another Station: http://another-url.mp3
```

### Options (Konfiguration tab)

| Option | Description | Default |
|--------|-------------|---------|
| port_avr | Port YCast listens on inside container | 80 |
| log_level | Log verbosity | info |

## Troubleshooting

- vTuner AVRs do not support HTTPS, and some older devices only play plain
  HTTP MP3 streams. YCast rewrites HTTPS stream URLs to HTTP automatically;
  if a station does not play, the stream may be too new for the device
  (HTTPS-only, or an AAC/other non-MP3 codec) - pick a plain HTTP MP3 stream
  instead.
- the proxy must forward requests with the original `Host` header
  (`*.vtuner.com`) intact.
- station not showing on the AVR: check `/data/stations.yml` and the addon log.
