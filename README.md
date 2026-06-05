<div align="center">

# Terminal GIF for GitHub Profile

**An animated terminal GIF showcasing your GitHub stats — auto-generated daily.**

![Terminal GIF](./output.gif)

[![Stars](https://img.shields.io/github/stars/dbuzatto/gif-terminal?style=flat-square&color=yellow)](https://github.com/dbuzatto/gif-terminal/stargazers)
[![Forks](https://img.shields.io/github/forks/dbuzatto/gif-terminal?style=flat-square&color=blue)](https://github.com/dbuzatto/gif-terminal/network/members)
[![License](https://img.shields.io/github/license/dbuzatto?style=flat-square)](LICENSE)

</div>

---

## Features

- Fetches **real-time GitHub stats** (commits, stars, PRs, followers, rank, languages)
- **Three themes** — classic terminal, macOS Liquid Glass, or Debian GNOME
- **Custom wallpaper** — drop any image into `assets/` and point to it with one variable
- **Username auto-detected** — no code editing needed after forking
- **Auto-regenerated daily** via GitHub Actions

---

## Themes

| Value | Theme | Description |
|-------|-------|-------------|
| `default` | **Classic dark** *(default)* | Clean dark terminal, no wallpaper |
| `macos` | **macOS Liquid Glass** | Frosted glass terminal over a macOS wallpaper |
| `debian` | **Debian GNOME** | GNOME terminal with title bar, menu bar, and Tango colors |

---

## Quick Start (fork & use)

### 1. Fork this repository

Click the **Fork** button at the top right of this page.

### 2. Add your GitHub Token

Go to **Settings → Secrets and variables → Actions** and add a new **secret**:

| Name | Value |
|------|-------|
| `GH_TOKEN` | Your GitHub Personal Access Token |

> Generate a token at [github.com/settings/tokens](https://github.com/settings/tokens) — only the `read:user` scope is needed.

### 3. Choose your theme

Go to **Settings → Secrets and variables → Actions**, open the **Variables** tab and add:

| Name | Value |
|------|-------|
| `THEME` | `macos` or `debian` or `default` |

> If you skip this step the `default` theme is used.

### 4. (Optional) Set your wallpaper

Upload any image to `assets/` in your fork, then add a second variable:

| Name | Value |
|------|-------|
| `WALLPAPER` | filename inside `assets/` — e.g. `debian_dark_wallpaper.jpg` |

This works for the `debian` theme. If `WALLPAPER` is not set, `debian_wallpaper.png` is used.

For the `macos` theme, replace `assets/macos_wallpaper.jpg` directly.

### 5. Trigger the first run

Go to **Actions → Generate Terminal GIF → Run workflow**.

### 6. Add to your profile README

```markdown
![Terminal GIF](https://raw.githubusercontent.com/YOUR_USERNAME/gif-terminal/main/output.gif)
```

---

## Running Locally

### Install dependencies

```bash
pip install github-readme-terminal requests python-dotenv Pillow

# ffmpeg (optional — PIL fallback is used if not installed)
brew install ffmpeg        # macOS
sudo apt install ffmpeg    # Ubuntu / Debian
```

### Configure

```bash
cp .env.example .env
# fill in GITHUB_TOKEN and GIT_USERNAME
```

### Generate

```bash
# Debian theme — default wallpaper
python3 generate_debian.py

# Debian theme — custom wallpaper
WALLPAPER=debian_dark_wallpaper.jpg python3 generate_debian.py

# macOS theme
python3 generate_liquid_glass.py

# Classic dark
python3 generate_with_stats.py
```

---

## Project Structure

```
.
├── generate_debian.py            # Debian GNOME theme
├── generate_liquid_glass.py      # macOS Liquid Glass theme
├── generate_with_stats.py        # Classic dark theme
├── assets/
│   ├── debian_wallpaper.png      # Default Debian wallpaper
│   ├── debian_dark_wallpaper.jpg # Dark Debian wallpaper
│   └── macos_wallpaper.jpg       # macOS wallpaper (replace with your own)
├── output.gif                    # Generated GIF (auto-updated by CI)
├── .env.example
└── .github/workflows/generate-gif.yml
```

---

## Updating from a previous version

If you already forked this repo, sync with upstream and you're done — nothing breaks:

- `THEME=debian` keeps working exactly as before
- The window buttons changed visually from colored circles to `˅ ◇ ×` icons
- **New:** add a `WALLPAPER` variable pointing to any image in `assets/` to use a custom wallpaper (see step 4 above)

No code edits required.

---

## Contributing

Contributions, issues, and feature requests are welcome.
Feel free to open an [issue](../../issues) or submit a pull request.

---

<div align="center">

If this project helped you, consider leaving a ⭐

</div>
