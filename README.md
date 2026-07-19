# Remote Linux Player

**Convierte tu PC con Linux en una Smart TV.** Control remoto completo desde el teléfono: touchpad, teclado, apps de streaming en modo kiosk y control por voz con IA — todo en tu red local, sin hardware extra y sin cuentas.

A plug & play remote-control ecosystem for Linux HTPCs: a mobile PWA client talking to a local FastAPI backend over secure WebSockets.

🌐 **Website:** [linux-remote-player.vercel.app](https://linux-remote-player.vercel.app/)

---

## Screenshot Placeholder
![App Logo Preview](website/icon-512.png)

---

## Features

* **Virtual input emulation** — mouse pointer, clicks, scroll, long-press right click, full keyboard bridge and media keys (transport, volume, mute) injected via `uinput`.
* **Streaming apps in kiosk mode** — Netflix, YouTube, Max, Disney+, Spotify, Twitch and any custom web app, launched full-screen in Firefox. Native Linux apps are auto-discovered from `.desktop` entries.
* **Installable PWA** — offline-capable app shell, no address bar, no stores. Network-first service worker keeps clients up to date automatically. *(Nota iOS: iOS hornea las metas del PWA al instalar — tras actualizaciones que toquen manifest o metas apple-*, es necesario reinstalar la app en el teléfono).*
* **Resilient connection** — ping/pong heartbeat, reconnect-on-wake, exponential backoff, and an actionable troubleshooting banner when something is wrong.
* **Self-healing HTTPS** — local two-tier CA (`ca.pem` + leaf certs) regenerated automatically for the current IP and `hostname.local` (mDNS via avahi). Install the CA once on your phone and never see a warning again.
* **Secure pairing** — no unauthenticated mode. A pairing token is auto-provisioned and delivered as a one-tap link at install time.
* **Voice intent engine** *(license-gated)* — speech-to-text plus LLM intent parsing (cloud NVIDIA NIM / OpenRouter, or fully local Whisper + Ollama).

---

## Architecture

```
              +---------------------------+
              |    Mobile PWA client      |
              |  (vanilla JS, offline)    |
              +-------------+-------------+
                            |  WSS + auth frame / REST + token header
                            v
              +-------------+-------------+
              |   FastAPI backend (HTPC)  |
              |       backend/main.py     |
              +------+-------------+------+
                     |             |
        +------------v---+   +-----v------------------+
        | input_emulator |   |      ai_pipeline       |
        | uinput virtual |   | ASR + LLM intent       |
        | mouse/keyboard |   | (cloud or local)       |
        +----------------+   +------------------------+
```

---

## Installation

On the Linux PC connected to your TV (Debian/Ubuntu and derivatives, systemd required), install everything with a single command:

```bash
curl -fsSL https://linux-remote-player.vercel.app/install.sh | sudo bash
```

Run the setup script. When asked "¿Esta PC está dedicada a la TV?", answer **S** (Yes) to install as a system service (Appliance mode), or **n** (No) for a user service (Desktop mode). The installer sets up dependencies, `uinput` permissions, Firefox, mDNS, the firewall rule and the systemd service. Reboot or re-login once after the first install.

---

## Licensing & Voice Activation

While basic touchpad and keyboard control are 100% free and open-source, the **Voice Intent Engine** requires a personal license key.

1. Buy a license from the [Official Website](https://linux-remote-player.vercel.app/).
2. You will receive a code `LRP-XXXX-XXXX-XXXX` instantly in your email.
3. Open the app on your mobile device, navigate to **Ajustes** (gear icon), paste the code under **Clave de licencia**, and tap **Activar**.
4. The microphone row will automatically appear in your app remote!

---

## Operational Scripts

### Updating the App
You can trigger an update directly from the mobile app's **Ajustes** page by clicking **Buscar actualización** then **Actualizar**, or run the script on the HTPC:
```bash
./scripts/update.sh
```

### Uninstalling the App
To completely remove all services, firewall rules, modules, and directories from your system:
```bash
sudo ./scripts/uninstall.sh
```

---

## Pairing your phone

The installer (and every backend start) prints a pairing link:

```
https://<hostname>.local:8000/?token=<token>   or   https://<ip>:8000/?token=<token>
```

1. Open the link in your phone's browser (same WiFi) and accept the certificate once — or install the CA from **Ajustes → Descargar Certificado CA** to trust it permanently.
2. Add the app to your home screen ("Add to Home Screen" / "Instalar app").
3. Open it from the icon. The token is stored in `localStorage` + `IndexedDB`; if the app ever shows *No autorizado*, re-enter the token from `backend/.pairing_token` in **Ajustes**.

---

## Troubleshooting

| Symptom | Check | Fix |
| :--- | :--- | :--- |
| Phone won't connect after a while | `ip -4 addr` — did the HTPC IP change? | Use `https://<hostname>.local:8000` (mDNS) or set a DHCP reservation. |
| TLS errors in the PWA | Open `https://<ip>:8000` in the phone *browser* | Re-accept the cert, or install the CA from `/api/ca` once. |
| "No autorizado" | WS closes with code 1008 | Enter the token from `backend/.pairing_token` in Ajustes. |
| Buttons do nothing | `curl -k https://127.0.0.1:8000/api/debug` | `evdev_available` must be `true`; ensure your user is in the `input` group and reboot. |
| Service down | `systemctl --user status linuxremoteplayer` | Logs: `journalctl --user -u linuxremoteplayer -n 100`. |

More detail in the project's internal test plan (`.agents/TESTING.md`).

---

## Configuration

All backend options live in `backend/.env` (see [`backend/.env.example`](backend/.env.example)): voice on/off, cloud vs local AI endpoints, pairing token override, log level.

---

## Repository layout

```
├── backend/            FastAPI server, input emulation, kiosk launcher, AI pipeline, licensing
│   ├── certs/          Auto-generated local HTTPS certificates
│   ├── auth.py         Access control gates (pairing tokens, licensing checks, grace caching)
│   ├── main.py         Websocket and HTTP controllers
│   └── requirements.txt
├── frontend/           PWA client (index.html, app.js, sw.js, offline CSS, icons)
├── scripts/            Operational system scripts
│   ├── bootstrap.sh    One-line curl bootstrap installer
│   ├── install.sh      Main setup installer for services and devices
│   ├── update.sh       Self-updating git release runner
│   └── uninstall.sh    System uninstaller script
├── supabase/           Database configuration and Edge Functions
│   └── functions/
│       ├── stripe-webhook/
│       └── validate-license/
├── website/            Stripe-integrated marketing pages deployed on Vercel
│   ├── index.html
│   └── gracias.html
├── CHANGELOG.md        Semantic version release log
└── VERSION             Current release version
```

---

## License

Source-available under the [Elastic License 2.0](LICENSE): free to use, copy and
modify; you may not offer it as a managed service, circumvent the license-key
functionality, or remove notices.

Third-party components: [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
