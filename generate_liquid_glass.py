import gifos
import os
import glob
import requests
from PIL import Image, ImageFilter, ImageDraw, ImageChops
from gifos.utils.convert_ansi_escape import ConvertAnsiEscape

# Override with high-contrast colors for blue glass background.
# Avoid cyan/blue tones — they blend with the wallpaper.
ConvertAnsiEscape.ANSI_ESCAPE_MAP_TXT_COLOR.update({
    "39": "#FFFFFF",   # default fg → pure white
    "31": "#FF3355",   # red
    "32": "#00FF88",   # neon green
    "33": "#FFE500",   # pure yellow
    "34": "#FF9500",   # orange (blue would blend)
    "35": "#FF44DD",   # magenta
    "36": "#FFFFFF",   # cyan → white (cyan blends with wallpaper)
    "37": "#FFFFFF",   # white
    "91": "#FF3355",   # bright red
    "92": "#00FF88",   # bright neon green
    "93": "#FFE500",   # bright yellow
    "94": "#FF9500",   # bright orange
    "95": "#FF44DD",   # bright magenta
    "96": "#FFE500",   # bright cyan → yellow (cyan blends)
    "97": "#FFFFFF",   # bright white
})

# ============================================
# Liquid Glass Theme — macOS-style terminal
# ============================================
#
# REQUIREMENTS:
# 1. Create a .env file in the project folder
# 2. Add: GITHUB_TOKEN=your_token_here
# 3. assets/wallpaper.jpg must be present
#
# APPROACH:
# gifos generates terminal frames with the default background (#0c0e0f).
# Before assembling the GIF, each PNG frame is post-processed:
#   - wallpaper fills the GIF canvas
#   - frosted glass (blurred wallpaper + dark overlay) covers the terminal window
#   - terminal content is composited using chroma-key (bg pixels show glass through)
#   - macOS chrome (rounded border, shadow, traffic lights) is drawn on top
# ============================================

USERNAME = "dbuzatto"

# ---- Layout constants ----
GIF_W, GIF_H     = 740, 520   # full canvas including margin
WIN_X, WIN_Y     = 20, 25     # window top-left in canvas
WIN_W            = 700        # window width (matches gifos terminal width)
TITLE_H          = 30         # macOS title bar height
WIN_H            = TITLE_H + 450  # total window height (480)
TERMINAL_X       = WIN_X      # gifos frame is pasted here
TERMINAL_Y       = WIN_Y + TITLE_H
CORNER_RADIUS    = 10

# Default gifos background color (ANSI code 49 → #0c0e0f) — used as chroma key
BG_COLOR_HEX = "#0c0e0f"
BG_COLOR     = (12, 14, 15)


# ============================================
# GitHub stats (same as original)
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
        print("Warning: Could not fetch GitHub stats")
        print("Configure GITHUB_TOKEN in .env file")
except (Exception, SystemExit) as e:
    print(f"Warning: Error fetching GitHub stats: {e}")
    print("Using example data...")
    has_stats = False
    github_stats = None

total_repos = get_total_repos(USERNAME)


# ============================================
# Liquid Glass helpers
# ============================================

def _scale_crop(img, target_w, target_h):
    """Scale image to fill target dimensions (maintain aspect ratio, center-crop)."""
    w, h = img.size
    ratio = w / h
    target_ratio = target_w / target_h
    if ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * ratio)
    else:
        new_w = target_w
        new_h = int(new_w / ratio)
    scaled = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return scaled.crop((left, top, left + target_w, top + target_h))


def _blend_overlay(base_rgb, overlay_rgba):
    """Alpha-composite an RGBA overlay onto an RGB base."""
    result = Image.alpha_composite(base_rgb.convert("RGBA"), overlay_rgba)
    return result.convert("RGB")


def prepare_glass_layers(wallpaper_path):
    """
    Build the static base canvas and chrome overlay used for every frame.

    Returns:
        base_canvas  — RGB image (GIF_W × GIF_H): wallpaper + shadow + frosted window
        chrome       — RGBA image (GIF_W × GIF_H): window border + traffic lights
    """
    wallpaper = Image.open(wallpaper_path).convert("RGB")
    wallpaper_bg = _scale_crop(wallpaper, GIF_W, GIF_H)

    # ---- Drop shadow (rendered beneath window) ----
    shadow = Image.new("RGBA", (GIF_W, GIF_H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [(WIN_X + 4, WIN_Y + 6), (WIN_X + WIN_W + 3, WIN_Y + WIN_H + 5)],
        radius=CORNER_RADIUS,
        fill=(0, 0, 0, 130),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))

    wallpaper_with_shadow = _blend_overlay(wallpaper_bg, shadow)

    # ---- Frosted glass — title bar ----
    title_region = wallpaper_bg.crop((WIN_X, WIN_Y, WIN_X + WIN_W, WIN_Y + TITLE_H))
    frosted_title = title_region.filter(ImageFilter.GaussianBlur(radius=5))
    title_overlay = Image.new("RGBA", frosted_title.size, (255, 255, 255, 30))
    frosted_title = _blend_overlay(frosted_title, title_overlay)

    # ---- Frosted glass — content area ----
    content_region = wallpaper_bg.crop(
        (TERMINAL_X, TERMINAL_Y, TERMINAL_X + WIN_W, TERMINAL_Y + 450)
    )
    frosted_content = content_region.filter(ImageFilter.GaussianBlur(radius=4))
    content_overlay = Image.new("RGBA", frosted_content.size, (255, 255, 255, 22))
    frosted_content = _blend_overlay(frosted_content, content_overlay)

    # ---- Assemble frosted window (with rounded corners) ----
    window_img = Image.new("RGB", (WIN_W, WIN_H))
    window_img.paste(frosted_title, (0, 0))
    window_img.paste(frosted_content, (0, TITLE_H))

    window_mask = Image.new("L", (WIN_W, WIN_H), 0)
    ImageDraw.Draw(window_mask).rounded_rectangle(
        [(0, 0), (WIN_W - 1, WIN_H - 1)], radius=CORNER_RADIUS, fill=255
    )

    # ---- Composite: wallpaper_with_shadow + frosted window ----
    base_canvas = wallpaper_with_shadow.copy()
    base_canvas.paste(window_img, (WIN_X, WIN_Y), window_mask)

    # ---- Chrome overlay (RGBA): border + title separator + traffic lights ----
    chrome = Image.new("RGBA", (GIF_W, GIF_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(chrome)

    # Window border
    draw.rounded_rectangle(
        [(WIN_X, WIN_Y), (WIN_X + WIN_W - 1, WIN_Y + WIN_H - 1)],
        radius=CORNER_RADIUS,
        outline=(255, 255, 255, 55),
        width=1,
    )

    # Title bar bottom separator
    draw.line(
        [
            (WIN_X + CORNER_RADIUS, WIN_Y + TITLE_H),
            (WIN_X + WIN_W - CORNER_RADIUS, WIN_Y + TITLE_H),
        ],
        fill=(255, 255, 255, 35),
        width=1,
    )

    # Traffic lights
    tl_y = WIN_Y + TITLE_H // 2
    traffic_lights = [
        ("#FF5F57", "#E0443E"),  # red
        ("#FFBD2E", "#DFA223"),  # yellow
        ("#28C840", "#1DAD2B"),  # green
    ]
    tl_r = 6
    for i, (fill, outline) in enumerate(traffic_lights):
        cx = WIN_X + 15 + i * 20 + tl_r
        draw.ellipse(
            [(cx - tl_r, tl_y - tl_r), (cx + tl_r, tl_y + tl_r)],
            fill=fill,
            outline=outline,
        )

    return base_canvas, chrome


def chroma_mask(terminal_frame):
    """
    Returns an 'L' mask:  255 = terminal pixel (keep)  /  0 = background (show glass).
    Any pixel exactly equal to BG_COLOR becomes 0 (transparent).
    """
    bg_ref = Image.new("RGB", terminal_frame.size, BG_COLOR)
    diff   = ImageChops.difference(terminal_frame, bg_ref)
    r, g, b = diff.split()
    # 255 if ANY channel differs from BG_COLOR
    mask = ImageChops.lighter(ImageChops.lighter(r, g), b)
    return mask.point(lambda p: 255 if p > 0 else 0)


def post_process_frames(base_canvas, chrome, frames_dir="./frames"):
    """Composite the liquid glass effect onto every PNG frame gifos generated."""
    frame_files = sorted(
        glob.glob(f"{frames_dir}/frame_*.png"),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split("_")[1]),
    )
    print(f"INFO: Post-processing {len(frame_files)} frames with liquid glass effect...")
    for frame_path in frame_files:
        terminal_frame = Image.open(frame_path).convert("RGB")
        canvas = base_canvas.copy()

        # Paste only non-background pixels (chroma key)
        mask = chroma_mask(terminal_frame)
        canvas.paste(terminal_frame, (TERMINAL_X, TERMINAL_Y), mask)

        # Apply chrome overlay (border + traffic lights)
        canvas = Image.alpha_composite(canvas.convert("RGBA"), chrome).convert("RGB")

        canvas.save(frame_path, "PNG")

    print(f"INFO: Liquid glass post-processing complete ({len(frame_files)} frames).")


# ============================================
# Terminal — content generation (gifos)
# ============================================

t = gifos.Terminal(width=WIN_W, height=450, xpad=10, ypad=10)
t.set_prompt(f"\x1b[91m{USERNAME}\x1b[0m@\x1b[93mgithub\x1b[0m ~> ")

# -- Boot sequence --
t.gen_text("Initializing terminal...", row_num=1)
t.clone_frame(5)
t.gen_text("\x1b[32m[OK]\x1b[0m System ready", row_num=2)
t.clone_frame(10)

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

# -- Final message --
final_row = 5 + len(skills)
t.gen_prompt(row_num=final_row)
t.gen_typing_text(
    "echo 'Thanks for visiting my profile!'", row_num=final_row, contin=True, speed=1
)
t.clone_frame(5)
t.gen_text("\x1b[92mThanks for visiting my profile!\x1b[0m", row_num=final_row + 1)
t.clone_frame(40)

# ============================================
# Post-process frames → Liquid Glass effect
# ============================================

base_canvas, chrome = prepare_glass_layers("assets/wallpaper.jpg")
post_process_frames(base_canvas, chrome)

# ============================================
# Generate GIF
# ============================================

t.gen_gif()

print("\n GIF generated: output.gif")
print("\nTo use in your README.md:")
print("![Terminal GIF](./output.gif)")
