# YCast Home Assistant Addon

vTuner internet radio replacement for AVR devices, powered by [YCast](https://github.com/milaq/YCast).

## Requirements

- DNS entry: `denon.vtuner.com` (or `yamaha.vtuner.com` etc.) pointing to your HA server IP
- Reverse proxy (tested with [Nginx Proxy Manager](https://github.com/NginxProxyManager/nginx-proxy-manager)) with custom location in Advanced tab:
  ```nginx
  location = / {
      proxy_pass http://<ha-server-ip>:<addon-port>/ycast/;
      proxy_set_header Host $host;
  }
  ```

## Installation

1. Add this repo as a custom repository in HA (Settings > Add-ons > Repositories)
2. Install the YCast addon
3. Set the host port in the Network tab (e.g. 2080)
4. Configure your DNS and reverse proxy

## Configuration

### Stations (Web UI)

The addon registers a **YCast** panel in the Home Assistant UI. Open it from the
addon page (**Open Web UI**) or enable it as a sidebar entry. There you can:

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
