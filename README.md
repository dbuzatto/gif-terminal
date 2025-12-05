# Terminal GIF para GitHub Profile

GIF animado com estatisticas do GitHub gerado automaticamente.

## Como usar

1. Faca fork deste repositorio
2. Adicione o secret `GH_TOKEN` nas configuracoes do repositorio:
   - Va em Settings > Secrets and variables > Actions
   - Clique em "New repository secret"
   - Nome: `GH_TOKEN`
   - Value: seu Personal Access Token do GitHub (com permissao `read:user`)

3. Edite `generate_with_stats.py` e mude o `USERNAME` para seu usuario

4. O GIF sera gerado automaticamente todo dia as 6h (UTC)

5. Use no seu README.md do perfil:

```markdown
![Terminal GIF](https://raw.githubusercontent.com/SEU_USER/SEU_REPO/main/output.gif)
```

## Rodar localmente

```bash
# Instalar dependencias
pip install github-readme-terminal requests python-dotenv

# Instalar ffmpeg (macOS)
brew install ffmpeg

# Configurar token (opcional, para stats completas)
cp .env.example .env
# Edite o .env com seu GITHUB_TOKEN

# Gerar GIF
python generate_with_stats.py
```

## Personalizar

Edite o arquivo `generate_with_stats.py` para:
- Mudar suas skills
- Ajustar cores
- Modificar o layout
- Adicionar mais comandos
