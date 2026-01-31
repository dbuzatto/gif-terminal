# Terminal GIF for GitHub Profile
Animated GIF with GitHub stats, automatically generated.

## How to Use
1. Fork this repository
2. Add the `GH_TOKEN` secret in your repository settings:
   - Go to Settings > Secrets and variables > Actions
   - Click "New repository secret"
   - Name: `GH_TOKEN`
   - Value: your GitHub Personal Access Token (with `read:user` permission)
3. Edit `generate_with_stats.py` and change `USERNAME` to your username
4. The GIF will be automatically generated every day at 6am (UTC)
5. Use it in your profile README.md:
```markdown
![Terminal GIF](https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/output.gif)
```

## Run Locally

### Install dependencies
```bash
pip install github-readme-terminal requests python-dotenv

# Install ffmpeg (macOS)
brew install ffmpeg
```

### Configure GitHub Token
**Required step before running the script:**

```bash
export GITHUB_TOKEN=your_github_token_here
```

**Alternative:** Create a `.env` file in the project root:
```bash
cp .env.example .env
# Edit .env and add: GITHUB_TOKEN=your_github_token_here
```

### Generate GIF
```bash
python generate_with_stats.py
```

## Customize
Edit `generate_with_stats.py` to:
- Change your skills
- Adjust colors
- Modify the layout
- Add more commands