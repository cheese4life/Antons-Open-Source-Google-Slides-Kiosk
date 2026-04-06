# Antons-Open-Source-Google-Slides-Kiosk-System
Bulletproof kiosk system complete with install scripts for first-time Linux setup, and a very simple control panel UI for managing active slideshows. Works by driving embedded Google Slides links, making the system free, easy to use, with no operational headaches.

# First-Time Linux Setup Guide

This guide walks you through setting up a fresh Linux machine as a Google Slides kiosk.

---

## Requirements

- A machine running **Ubuntu** or **Debian** (fresh install recommended)
- Internet connection
- A Google Slides presentation published to the web (see step 1)

---

## Step 1 — Publish Your Google Slides Presentation

1. Open your presentation in Google Slides
2. Go to **File → Share → Publish to web**
3. Select **Embed**, then configure your loop/delay settings
4. Click **Publish** and copy the embed URL
5. Open `kiosk.py` and paste your URL into the `DEFAULT_URL` field at the top of the file

---

## Step 2 — Get the Files onto the Machine

Copy the three project files onto the Linux machine into `/opt/kiosk/`:

```bash
sudo mkdir -p /opt/kiosk
sudo cp kiosk.py panel.py setup.sh /opt/kiosk/
```

If you're pulling from GitHub directly:

```bash
sudo apt-get install -y git
sudo git clone https://github.com/cheese4life/Antons-Open-Source-Google-Slides-Kiosk /opt/kiosk
```

---

## Step 3 — Configure the Setup Script

Open `setup.sh` and set the two variables at the top:

```bash
sudo nano /opt/kiosk/setup.sh
```

| Variable | What to set it to |
|---|---|
| `KIOSK_USER` | The Linux username the kiosk will run under (e.g. `zadmin2`) |
| `KIOSK_DIR` | Directory where the files live — leave as `/opt/kiosk` unless you moved them |

---

## Step 4 — Run the Setup Script

```bash
sudo bash /opt/kiosk/setup.sh
```

This script will automatically:
- Install `xorg`, `openbox`, `chromium-browser`, and `unclutter`
- Configure **auto-login** on TTY1 for your kiosk user
- Configure **auto-start of X** on login
- Create the `xinitrc` that launches Chromium in kiosk mode
- Disable screen blanking and console blanking
- Set the graphical systemd target

---

## Step 5 — Reboot

```bash
sudo reboot
```

The machine will boot directly into the kiosk display. No keyboard or mouse interaction is needed.

---

## Control Panel

The kiosk exposes a web-based control panel for managing the display without touching the machine.

| Service | Port | Purpose |
|---|---|---|
| Control Panel UI | `8080` | Change slides URL, show clock, refresh |
| Kiosk API | `8081` | Internal API used by the control panel |

Access the control panel from any device on the same network:

```
http://<machine-ip>:8080
```

> **Tip:** To find the machine's IP, run `ip a` on the kiosk machine.

---

## Auto-Refresh

The kiosk automatically refreshes Chromium every night at **midnight** to pick up any changes made to the Google Slides presentation. No manual intervention needed.

---

## Troubleshooting

**Kiosk didn't start after reboot**
- Make sure `KIOSK_USER` in `setup.sh` matches the actual Linux username exactly
- Check that the files are in `/opt/kiosk/`

**Chromium shows an error page**
- Confirm the `DEFAULT_URL` in `kiosk.py` is the published embed URL, not the edit URL
- Make sure the machine has internet access

**Control panel unreachable**
- The kiosk must be fully booted and running before the panel is accessible
- Check your firewall — ports `8080` and `8081` must be open on the kiosk machine
