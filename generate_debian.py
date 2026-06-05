import gifos
import os
import glob
import requests
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageChops
from gifos.utils.convert_ansi_escape import ConvertAnsiEscape

# ============================================
# ANSI colour overrides — Tango palette
# ============================================
# Debian's GNOME Terminal ships with Tango colours by default.
# These vivid values contrast sharply against the dark frosted glass
# rendered over the light Debian marble wallpaper.
ConvertAnsiEscape.ANSI_ESCAPE_MAP_TXT_COLOR.update({
    "39": "#F2F2F2",   # default fg — near-white
    "31": "#CC0000",   # Debian red
    "32": "#4EAA25",   # green
    "33": "#C4A000",   # gold / dark yellow
    "34": "#3465A4",   # blue
    "35": "#75507B",   # magenta
    "36": "#06989A",   # cyan
    "37": "#D3D7CF",   # light grey
    "91": "#EF2929",   # bright red
    "92": "#8AE234",   # bright green
    "93": "#FCE94F",   # bright yellow
    "94": "#729FCF",   # bright blue
    "95": "#AD7FA8",   # bright magenta
    "96": "#34E2E2",   # bright cyan
    "97": "#EEEEEC",   # bright white
})

# ============================================
# Debian Terminal Theme
# ============================================
#
# REQUIREMENTS:
# 1. Create a .env file: GITHUB_TOKEN=your_token_here
# 2. assets/debian_wallpaper.png must be present
#
# APPROACH (same engine as Liquid Glass):
# gifos generates terminal frames at default bg (#0c0e0f).
# post_process_frames() modifies each PNG before gen_gif() assembles them:
#   - Debian wallpaper fills the canvas
#   - Frosted glass (heavy dark tint) covers the window area
#   - Terminal content composited via chroma-key
#   - GNOME 2-style chrome: title bar + menu bar + right-side buttons
# ============================================

# Auto-detected from GitHub Actions context; falls back to env var or default.
USERNAME = (
    os.environ.get("GITHUB_REPOSITORY_OWNER")
    or os.environ.get("GIT_USERNAME")
    or "dbuzatto"
)

# Wallpaper file inside assets/. Override via WALLPAPER repo variable or env var.
# Example: WALLPAPER=debian_dark_wallpaper.jpg
_wallpaper_file = os.environ.get("WALLPAPER", "debian_wallpaper.png")
WALLPAPER_PATH  = os.path.join("assets", _wallpaper_file)
if not os.path.exists(WALLPAPER_PATH):
    print(f"Warning: wallpaper '{WALLPAPER_PATH}' not found — falling back to assets/debian_wallpaper.png")
    WALLPAPER_PATH = "assets/debian_wallpaper.png"

# ---- Layout constants ----
GIF_W, GIF_H  = 740, 540

WIN_X, WIN_Y  = 20, 20          # window top-left on canvas
WIN_W         = 700

TITLE_H       = 28              # window title bar
MENU_H        = 22              # GNOME Terminal menu bar (File Edit View…)
HEADER_H      = TITLE_H + MENU_H   # = 50 px total chrome above terminal

WIN_H         = HEADER_H + 450  # total window height
TERMINAL_X    = WIN_X
TERMINAL_Y    = WIN_Y + HEADER_H

CORNER_RADIUS = 6               # GNOME 2 uses tighter radius than macOS

# gifos default background used as chroma key
BG_COLOR = (12, 14, 15)

FRAMES_DIR     = "./frames"
FRAME_BASE     = "frame_"
OUTPUT_GIF     = "output.gif"
GIFOS_FPS      = 20


# ============================================
# GitHub stats
# ============================================

def get_total_repos(username):
    try:
        response = requests.get(f"https://api.github.com/users/{username}")
        if response.status_code == 200:
            return response.json().get("public_repos", 0)
    except Exception:
        pass
    return None

try:
    github_stats = gifos.utils.fetch_github_stats(user_name=USERNAME)
    has_stats = github_stats is not None
    if not has_stats:
        print("Warning: Could not fetch GitHub stats — configure GITHUB_TOKEN in .env")
except (Exception, SystemExit) as e:
    print(f"Warning: {e} — using placeholder data")
    has_stats = False
    github_stats = None

total_repos = get_total_repos(USERNAME)


# ============================================
# Debian theme helpers
# ============================================

def _scale_crop(img, target_w, target_h):
    """Scale to fill target dimensions, center-crop (no distortion)."""
    w, h = img.size
    if w / h > target_w / target_h:
        new_h, new_w = target_h, int(target_h * w / h)
    else:
        new_w, new_h = target_w, int(target_w * h / w)
    scaled = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return scaled.crop((left, top, left + target_w, top + target_h))


def _blend(base_rgb, overlay_rgba):
    return Image.alpha_composite(base_rgb.convert("RGBA"), overlay_rgba).convert("RGB")


def _default_font(size=11):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def prepare_debian_layers(wallpaper_path):
    """
    Build the static base_canvas (RGB) and chrome overlay (RGBA) reused
    for every frame.

    Window structure (top → bottom):
        ┌─────────────────────────── title bar (28 px) ───────────────────────┐
        │  dbuzatto@debian: ~                              [−][□][✕]          │
        ├─────── menu bar (22 px) ────────────────────────────────────────────┤
        │  File   Edit   View   Search   Terminal   Help                      │
        ├─────────────────────────── terminal (450 px) ───────────────────────┤
        │  (gifos content composited via chroma-key)                          │
        └─────────────────────────────────────────────────────────────────────┘
    """
    wallpaper    = Image.open(wallpaper_path).convert("RGB")
    wallpaper_bg = _scale_crop(wallpaper, GIF_W, GIF_H)

    # ── Drop shadow ──────────────────────────────────────────────────────────
    shadow = Image.new("RGBA", (GIF_W, GIF_H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [(WIN_X + 4, WIN_Y + 6), (WIN_X + WIN_W + 4, WIN_Y + WIN_H + 6)],
        radius=CORNER_RADIUS, fill=(0, 0, 0, 150),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
    wallpaper_with_shadow = _blend(wallpaper_bg, shadow)

    # ── Frosted glass regions ─────────────────────────────────────────────────
    def _frost(region, blur, tint_rgba):
        blurred = region.filter(ImageFilter.GaussianBlur(radius=blur))
        return _blend(blurred, Image.new("RGBA", blurred.size, tint_rgba))

    title_region   = wallpaper_bg.crop((WIN_X, WIN_Y,
                                        WIN_X + WIN_W, WIN_Y + TITLE_H))
    menu_region    = wallpaper_bg.crop((WIN_X, WIN_Y + TITLE_H,
                                        WIN_X + WIN_W, WIN_Y + HEADER_H))
    content_region = wallpaper_bg.crop((TERMINAL_X, TERMINAL_Y,
                                        TERMINAL_X + WIN_W, TERMINAL_Y + 450))

    frosted_title   = _frost(title_region,   blur=6,  tint_rgba=(32, 32, 36, 220))
    frosted_menu    = _frost(menu_region,    blur=4,  tint_rgba=(40, 40, 44, 215))
    frosted_content = _frost(content_region, blur=8,  tint_rgba=(18, 18, 23, 215))

    # ── Assemble window with rounded corners ─────────────────────────────────
    window_img = Image.new("RGB", (WIN_W, WIN_H))
    window_img.paste(frosted_title,   (0, 0))
    window_img.paste(frosted_menu,    (0, TITLE_H))
    window_img.paste(frosted_content, (0, HEADER_H))

    window_mask = Image.new("L", (WIN_W, WIN_H), 0)
    ImageDraw.Draw(window_mask).rounded_rectangle(
        [(0, 0), (WIN_W - 1, WIN_H - 1)], radius=CORNER_RADIUS, fill=255
    )

    base_canvas = wallpaper_with_shadow.copy()
    base_canvas.paste(window_img, (WIN_X, WIN_Y), window_mask)

    # ── Chrome overlay (RGBA) ─────────────────────────────────────────────────
    chrome = Image.new("RGBA", (GIF_W, GIF_H), (0, 0, 0, 0))
    d      = ImageDraw.Draw(chrome)

    # Outer window border
    d.rounded_rectangle(
        [(WIN_X, WIN_Y), (WIN_X + WIN_W - 1, WIN_Y + WIN_H - 1)],
        radius=CORNER_RADIUS, outline=(255, 255, 255, 40), width=1,
    )

    # Separator: title bar → menu bar
    d.line(
        [(WIN_X + CORNER_RADIUS, WIN_Y + TITLE_H),
         (WIN_X + WIN_W - CORNER_RADIUS, WIN_Y + TITLE_H)],
        fill=(255, 255, 255, 30), width=1,
    )

    # Separator: menu bar → terminal content
    d.line(
        [(WIN_X + CORNER_RADIUS, WIN_Y + HEADER_H),
         (WIN_X + WIN_W - CORNER_RADIUS, WIN_Y + HEADER_H)],
        fill=(255, 255, 255, 25), width=1,
    )

    # Window title text (left-aligned, GNOME 2 style)
    title_font = _default_font(11)
    title_text = f"{USERNAME}@debian: ~"
    d.text(
        (WIN_X + 10, WIN_Y + (TITLE_H - 11) // 2),
        title_text, fill=(210, 210, 210, 230), font=title_font,
    )

    # Window buttons — right-aligned, icon style (˅ ◇ ×)
    btn_y   = WIN_Y + TITLE_H // 2
    close_x = WIN_X + WIN_W - 14
    max_x   = close_x - 20
    min_x   = max_x   - 20

    icon_color = (215, 215, 215, 200)
    btn_bg     = (55, 55, 60, 170)
    btn_hw, btn_hh = 9, 7

    for bx in (min_x, max_x, close_x):
        d.rounded_rectangle(
            [(bx - btn_hw, btn_y - btn_hh), (bx + btn_hw, btn_y + btn_hh)],
            radius=3, fill=btn_bg,
        )

    # Minimize: chevron ˅
    d.line([(min_x - 4, btn_y - 2), (min_x,     btn_y + 2)], fill=icon_color, width=1)
    d.line([(min_x,     btn_y + 2), (min_x + 4, btn_y - 2)], fill=icon_color, width=1)

    # Maximize: diamond ◇
    d.line([(max_x,     btn_y - 4), (max_x + 4, btn_y    )], fill=icon_color, width=1)
    d.line([(max_x + 4, btn_y    ), (max_x,     btn_y + 4)], fill=icon_color, width=1)
    d.line([(max_x,     btn_y + 4), (max_x - 4, btn_y    )], fill=icon_color, width=1)
    d.line([(max_x - 4, btn_y    ), (max_x,     btn_y - 4)], fill=icon_color, width=1)

    # Close: ×
    d.line([(close_x - 4, btn_y - 4), (close_x + 4, btn_y + 4)], fill=icon_color, width=1)
    d.line([(close_x + 4, btn_y - 4), (close_x - 4, btn_y + 4)], fill=icon_color, width=1)

    # Menu bar items
    menu_font  = _default_font(10)
    menu_items = ["File", "Edit", "View", "Search", "Terminal", "Help"]
    menu_x     = WIN_X + 8
    menu_y     = WIN_Y + TITLE_H + (MENU_H - 10) // 2
    for item in menu_items:
        d.text((menu_x, menu_y), item, fill=(200, 200, 200, 220), font=menu_font)
        menu_x += len(item) * 6 + 12   # approximate advance

    return base_canvas, chrome


def chroma_mask(terminal_frame):
    """255 = keep terminal pixel / 0 = show frosted glass through."""
    bg_ref = Image.new("RGB", terminal_frame.size, BG_COLOR)
    diff   = ImageChops.difference(terminal_frame, bg_ref)
    r, g, b = diff.split()
    mask   = ImageChops.lighter(ImageChops.lighter(r, g), b)
    return mask.point(lambda p: 255 if p > 0 else 0)


def post_process_frames(base_canvas, chrome, frames_dir=FRAMES_DIR):
    """Composite Debian chrome onto every PNG frame gifos generated."""
    frame_files = sorted(
        glob.glob(f"{frames_dir}/{FRAME_BASE}*.png"),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split("_")[1]),
    )
    print(f"INFO: Post-processing {len(frame_files)} frames with Debian theme...")
    for frame_path in frame_files:
        terminal_frame = Image.open(frame_path).convert("RGB")
        canvas = base_canvas.copy()
        canvas.paste(terminal_frame, (TERMINAL_X, TERMINAL_Y), chroma_mask(terminal_frame))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), chrome).convert("RGB")
        canvas.save(frame_path, "PNG")
    print(f"INFO: Done — {len(frame_files)} frames processed.")


# Colours that must survive GIF quantisation — UI chrome + all Tango ANSI values.
_PALETTE_HINTS = [
    # Chrome
    ( 55,  55,  60),  # button backgrounds
    (215, 215, 215),  # button icons
    (210, 210, 210),  # title text
    (200, 200, 200),  # menu text
    # Tango ANSI (matches the overrides above)
    (204,   0,   0),  (239,  41,  41),  # red / bright red
    ( 78, 170,  37),  (138, 226,  52),  # green / bright green
    (196, 160,   0),  (252, 233,  79),  # gold / bright yellow
    ( 52, 101, 164),  (114, 159, 207),  # blue / bright blue
    (117,  80, 123),  (173, 127, 168),  # magenta / bright magenta
    (  6, 152, 154),  ( 52, 226, 226),  # cyan / bright cyan
    (211, 215, 207),  (238, 238, 236),  # grey / bright white
    (242, 242, 242),                    # default fg
]


def assemble_gif_with_pil(frames_dir=FRAMES_DIR, output=OUTPUT_GIF, fps=GIFOS_FPS):
    """
    Fallback GIF assembly using Pillow (no ffmpeg required).

    Mirrors ffmpeg's palettegen+paletteuse approach:
      1. Seed a hint strip with all important UI / ANSI colours.
      2. Build a global palette (FASTOCTREE, 250 colours) from the first
         frame + hints — this guarantees those colours are represented exactly.
      3. Quantise every frame against that global palette with
         Floyd-Steinberg dithering so gradients stay smooth.
    """
    frame_files = sorted(
        glob.glob(f"{frames_dir}/{FRAME_BASE}*.png"),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split("_")[1]),
    )
    if not frame_files:
        print("ERROR: No frames found for PIL assembly.")
        return False

    # Build colour-hint strip
    n = len(_PALETTE_HINTS)
    hint = Image.new("RGB", (n, 8))
    for i, c in enumerate(_PALETTE_HINTS):
        for y in range(8):
            hint.putpixel((i, y), c)

    # Build global palette from first frame + hints
    first = Image.open(frame_files[0]).convert("RGB")
    hinted = first.copy()
    hinted.paste(hint, (0, 0))
    palette_img = hinted.quantize(
        colors=250, method=Image.Quantize.FASTOCTREE, dither=0
    )

    # Quantise all frames against that palette
    duration_ms = max(1, round(1000 / fps))
    quantised = []
    for f in frame_files:
        img = Image.open(f).convert("RGB")
        quantised.append(img.quantize(palette=palette_img, dither=1))

    quantised[0].save(
        output,
        save_all=True,
        append_images=quantised[1:],
        loop=0,
        duration=duration_ms,
        optimize=False,
    )
    size_kb = os.path.getsize(output) // 1024
    print(f"INFO: PIL fallback — {output} ({len(quantised)} frames, {size_kb} KB)")
    return True


# ============================================
# Terminal content (gifos)
# ============================================

t = gifos.Terminal(width=WIN_W, height=450, xpad=10, ypad=10)

# Debian bash prompt: green user @ red hostname : blue path $
t.set_prompt(
    f"\x1b[92m{USERNAME}\x1b[0m@\x1b[91mdebian\x1b[0m:\x1b[94m~\x1b[0m$ "
)

# -- Boot sequence (systemd-style) --
t.gen_text("\x1b[92m[  OK  ]\x1b[0m Started Session Manager.", row_num=1)
t.clone_frame(4)
t.gen_text("\x1b[92m[  OK  ]\x1b[0m Reached target Graphical Interface.", row_num=2)
t.clone_frame(8)

# -- Stats command --
t.gen_prompt(row_num=3)
t.gen_typing_text("github-stats --user " + USERNAME, row_num=3, contin=True, speed=1)
t.clone_frame(5)

t.gen_text("", row_num=4)
t.gen_text(f"\x1b[96m=== GitHub Stats for {USERNAME} ===\x1b[0m", row_num=5)
t.clone_frame(3)

if has_stats:
    repos_count = total_repos if total_repos else github_stats.total_repo_contributions
    stats_lines = [
        f"\x1b[93mName:\x1b[0m        {github_stats.account_name or USERNAME}",
        f"\x1b[93mFollowers:\x1b[0m   {github_stats.total_followers}",
        f"\x1b[93mStars:\x1b[0m       {github_stats.total_stargazers}",
        f"\x1b[93mCommits:\x1b[0m     {github_stats.total_commits_last_year} (last year)",
        f"\x1b[93mPRs:\x1b[0m         {github_stats.total_pull_requests_made}",
        f"\x1b[93mIssues:\x1b[0m      {github_stats.total_issues}",
        f"\x1b[93mRepos:\x1b[0m       {repos_count}",
        f"\x1b[93mRank:\x1b[0m        {github_stats.user_rank.level} ({github_stats.user_rank.percentile:.1f}%)",
    ]
    if github_stats.languages_sorted:
        top_langs = github_stats.languages_sorted[:3]
        langs_str = ", ".join([f"{lang[0]} ({lang[1]}%)" for lang in top_langs])
        stats_lines.append(f"\x1b[93mTop Langs:\x1b[0m   {langs_str}")
else:
    stats_lines = [
        f"\x1b[93mName:\x1b[0m        {USERNAME}",
        "\x1b[93mFollowers:\x1b[0m   --",
        "\x1b[93mStars:\x1b[0m       --",
        "\x1b[93mCommits:\x1b[0m     -- (configure GITHUB_TOKEN)",
        "\x1b[93mPRs:\x1b[0m         --",
        "\x1b[93mIssues:\x1b[0m      --",
        "\x1b[93mRepos:\x1b[0m       --",
        "\x1b[93mRank:\x1b[0m        --",
    ]

for i, line in enumerate(stats_lines):
    t.gen_text(line, row_num=6 + i)
    t.clone_frame(3)

t.clone_frame(10)
t.gen_text("\x1b[96m================================\x1b[0m", row_num=6 + len(stats_lines))
t.clone_frame(15)

# -- Clear + Skills --
t.gen_prompt(row_num=7 + len(stats_lines))
t.gen_typing_text("clear", row_num=7 + len(stats_lines), contin=True, speed=1)
t.clone_frame(5)
t.clear_frame()

t.gen_prompt(row_num=1)
t.gen_typing_text("cat skills.txt", row_num=1, contin=True, speed=1)
t.clone_frame(5)

t.gen_text("", row_num=2)
t.gen_text("\x1b[96m=== Tech Stack ===\x1b[0m", row_num=3)
t.clone_frame(3)

skills = [
    ("\x1b[94mCloud:\x1b[0m       ", "AWS, GCP, OCI, Cloudflare"),
    ("\x1b[94mDevOps:\x1b[0m      ", "Terraform, Kubernetes, Docker, Git"),
    ("\x1b[94mCI/CD:\x1b[0m       ", "GitLab, GitHub Actions"),
    ("\x1b[94mMonitoring:\x1b[0m  ", "Grafana, Prometheus, Jaeger, Loki"),
    ("\x1b[94mTools:\x1b[0m       ", "Postman, RabbitMQ, MongoDB"),
    ("\x1b[94mOS:\x1b[0m          ", "macOS, Debian"),
    ("\x1b[94mLanguages:\x1b[0m   ", "Java, Python"),
]

for i, (label, value) in enumerate(skills):
    t.gen_text(f"{label}{value}", row_num=4 + i)
    t.clone_frame(2)

t.clone_frame(10)
t.gen_text("\x1b[96m==================\x1b[0m", row_num=4 + len(skills))
t.clone_frame(5)

final_row = 5 + len(skills)
t.gen_prompt(row_num=final_row)
t.gen_typing_text(
    "echo 'Thanks for visiting my profile!'", row_num=final_row, contin=True, speed=1
)
t.clone_frame(5)
t.gen_text("\x1b[92mThanks for visiting my profile!\x1b[0m", row_num=final_row + 1)
t.clone_frame(40)

# ============================================
# Post-process frames → Debian theme
# ============================================

base_canvas, chrome = prepare_debian_layers(WALLPAPER_PATH)
post_process_frames(base_canvas, chrome)

# ============================================
# Generate GIF (ffmpeg preferred, PIL fallback)
# ============================================

t.gen_gif()

if not os.path.exists(OUTPUT_GIF):
    print("INFO: ffmpeg not available — assembling GIF with PIL fallback...")
    assemble_gif_with_pil()

print(f"\n GIF generated: {OUTPUT_GIF}")
print("\nTo use in your README.md:")
print(f"![Terminal GIF](./{OUTPUT_GIF})")
