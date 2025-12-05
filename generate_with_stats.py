import gifos
from datetime import datetime
import os
import requests

# ============================================
# Terminal GIF com GitHub Stats
# ============================================
# 
# REQUISITOS:
# 1. Criar um arquivo .env na pasta do projeto
# 2. Adicionar: GITHUB_TOKEN=seu_token_aqui
#
# Para criar o token:
# - Va em: https://github.com/settings/tokens
# - Clique em "Generate new token (classic)"
# - Selecione apenas: read:user
# - Copie o token e coloque no .env
# ============================================

USERNAME = "dbuzatto"  # <- Seu username do GitHub

# Funcao para buscar numero real de repos
def get_total_repos(username):
    try:
        response = requests.get(f"https://api.github.com/users/{username}")
        if response.status_code == 200:
            return response.json().get("public_repos", 0)
    except:
        pass
    return None

# Tenta buscar estatisticas do GitHub
try:
    github_stats = gifos.utils.fetch_github_stats(user_name=USERNAME)
    has_stats = github_stats is not None
    if not has_stats:
        print("Aviso: Nao foi possivel buscar stats do GitHub")
        print("Configure GITHUB_TOKEN no arquivo .env")
except Exception as e:
    print(f"Aviso: Erro ao buscar stats do GitHub: {e}")
    print("Usando dados de exemplo...")
    has_stats = False
    github_stats = None

# Busca numero real de repos
total_repos = get_total_repos(USERNAME)

# Configuracoes do terminal
t = gifos.Terminal(width=700, height=450, xpad=10, ypad=10)

# -- Prompt inicial --
t.set_prompt(f"\x1b[91m{USERNAME}\x1b[0m@\x1b[93mgithub\x1b[0m ~> ")

# -- Boot sequence --
t.gen_text("Initializing terminal...", row_num=1)
t.clone_frame(5)
t.gen_text("\x1b[32m[OK]\x1b[0m System ready", row_num=2)
t.clone_frame(10)

# -- Comando para ver stats --
t.gen_prompt(row_num=3)
t.gen_typing_text("github-stats --user " + USERNAME, row_num=3, contin=True, speed=1)
t.clone_frame(5)

# -- Exibe as estatisticas --
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
    
    # Top linguagens
    if github_stats.languages_sorted:
        top_langs = github_stats.languages_sorted[:3]
        langs_str = ", ".join([f"{lang[0]} ({lang[1]}%)" for lang in top_langs])
        stats_lines.append(f"\x1b[93mTop Langs:\x1b[0m   {langs_str}")
else:
    # Dados de exemplo
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
    t.gen_text(line, row_num=6+i)
    t.clone_frame(3)

t.clone_frame(10)
t.gen_text("\x1b[96m================================\x1b[0m", row_num=6+len(stats_lines))
t.clone_frame(15)

# -- Clear e Skills --
t.gen_prompt(row_num=7+len(stats_lines))
t.gen_typing_text("clear", row_num=7+len(stats_lines), contin=True, speed=1)
t.clone_frame(5)
t.clear_frame()

t.gen_prompt(row_num=1)
t.gen_typing_text("cat skills.txt", row_num=1, contin=True, speed=1)
t.clone_frame(5)

t.gen_text("", row_num=2)
t.gen_text("\x1b[96m=== Tech Stack ===\x1b[0m", row_num=3)
t.clone_frame(3)

skills = [
    ("\x1b[94mCloud:\x1b[0m       ", "AWS, GCP, Cloudflare"),
    ("\x1b[94mDevOps:\x1b[0m      ", "Terraform, Kubernetes, Docker, Git"),
    ("\x1b[94mCI/CD:\x1b[0m       ", "GitLab"),
    ("\x1b[94mMonitoring:\x1b[0m  ", "Grafana, Prometheus"),
    ("\x1b[94mTools:\x1b[0m       ", "Postman, RabbitMQ, MongoDB"),
    ("\x1b[94mOS:\x1b[0m          ", "Linux"),
    ("\x1b[94mLanguages:\x1b[0m   ", "Python"),
]

for i, (label, value) in enumerate(skills):
    t.gen_text(f"{label}{value}", row_num=4+i)
    t.clone_frame(2)

t.clone_frame(10)
t.gen_text("\x1b[96m==================\x1b[0m", row_num=4+len(skills))
t.clone_frame(5)

# -- Mensagem final --
final_row = 5 + len(skills)
t.gen_prompt(row_num=final_row)
t.gen_typing_text("echo 'Thanks for visiting my profile!'", row_num=final_row, contin=True, speed=1)
t.clone_frame(5)
t.gen_text("\x1b[92mThanks for visiting my profile!\x1b[0m", row_num=final_row+1)
t.clone_frame(40)

# Gera o GIF
t.gen_gif()

print("\n GIF gerado: output.gif")
print("\nPara usar no seu README.md:")
print('![Terminal GIF](./output.gif)')
