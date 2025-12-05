import gifos
from datetime import datetime

# ============================================
# Terminal GIF para GitHub README
# ============================================
# Ajuste seu username e personalize as informacoes!

USERNAME = "dbuzatto"  # <- Seu username do GitHub

# Configuracoes do terminal
t = gifos.Terminal(width=600, height=400, xpad=10, ypad=10)

# -- Comando whoami --
t.gen_typing_text("$ whoami", row_num=1, contin=False, speed=2)
t.clone_frame(5)

t.gen_text(text=f"\x1b[32m{USERNAME}\x1b[0m", row_num=2)
t.clone_frame(10)

# -- Comando neofetch --
t.gen_typing_text("$ neofetch", row_num=3, contin=False, speed=2)
t.clone_frame(5)

# Informacoes estilo neofetch (sem caracteres especiais)
info_lines = [
    "",
    f"\x1b[91m{USERNAME}\x1b[0m@\x1b[93mgithub\x1b[0m",
    "--------------------",
    "\x1b[91mOS:\x1b[0m macOS Developer",
    "\x1b[91mHost:\x1b[0m GitHub Universe",
    "\x1b[91mKernel:\x1b[0m Code-5.0",
    "\x1b[91mUptime:\x1b[0m " + datetime.now().strftime("%Y") + " days",
    "\x1b[91mPackages:\x1b[0m npm, pip, brew",
    "\x1b[91mShell:\x1b[0m zsh 5.9",
    "\x1b[91mEditor:\x1b[0m VS Code",
    "\x1b[91mLanguages:\x1b[0m Python, TypeScript, Go",
    "",
]

for i, line in enumerate(info_lines):
    t.gen_text(text=line, row_num=4+i)
    t.clone_frame(3)

t.clone_frame(15)

# -- Mensagem final --
t.gen_typing_text("$ echo 'Thanks for visiting!'", row_num=16, contin=False, speed=1)
t.clone_frame(5)
t.gen_text(text="\x1b[93mThanks for visiting!\x1b[0m", row_num=17)
t.clone_frame(30)

# Gera o GIF
t.gen_gif()

print("\n GIF gerado: output.gif")
print(" Frames em: frames/")