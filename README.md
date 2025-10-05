# 🔍 GitHub Repository Analyzer

A powerful AI-powered tool for analyzing GitHub repositories, specifically designed for cryptocurrency and blockchain project due diligence. Detects "larping" projects that make grandiose claims without substantial code backing.

## ✨ Features

- **🤖 AI-Powered Analysis**: Uses OpenAI GPT-4 to intelligently assess repository quality
- **📊 Comprehensive Metrics**: Analyzes code quality, completeness, security, originality, and activity
- **🎯 Crypto-Focused**: Specifically designed to detect blockchain project red flags
- **💬 Discord Bot**: Interactive Discord interface with rich embeds
- **⚡ CLI Tool**: Command-line interface for quick analysis
- **📈 Activity Tracking**: Monitors commit history, contributors, and project activity

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/0xGval/github-repo-analyzer.git
   cd github-repo-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## 📋 Required API Keys

- **OpenAI API Key**: Get from https://platform.openai.com/api-keys
- **Discord Bot Token**: Get from https://discord.com/developers/applications (for bot mode)
- **GitHub Token**: Optional, for higher rate limits

## 🎮 Usage Modes

### Mode 1: Command Line Interface (CLI)

Perfect for quick analysis or automation:

```bash
python main.py https://github.com/owner/repository
```

**Example Output:**
```
Starting analysis of repository: https://github.com/owner/repository
Repository: MyAwesomeCryptoProject
Description: Revolutionary blockchain solution
Stars: 1,234
Forks: 56
Last updated: 2024-01-15
Found 89 files in the repository

--- REPOSITORY ANALYSIS ---

ASSESSMENT:
This project appears to be a legitimate blockchain implementation with substantial code...

RATINGS:
- CODE QUALITY: 4/5
- COMPLETENESS: 3/5
- SECURITY: 4/5
- ORIGINALITY: 4/5
- ACTIVITY: 5/5

VERDICT: LEGITIMATE - This is a well-maintained project with real functionality.
```

### Mode 2: Discord Bot

Interactive Discord bot with rich embeds and slash commands:

```bash
python bot.py
```

**Discord Commands:**
- `/analyze <github-url>` - Analyze a GitHub repository

**Discord Bot Features:**
- 🎨 **Rich Embeds**: Color-coded results with stars, forks, and ratings
- ⚡ **Real-time Analysis**: Instant feedback with progress indicators
- 📊 **Visual Ratings**: Star ratings for each criterion
- 🎯 **Color-coded Verdicts**: Green (legitimate), Red (larping), Gold (borderline)
- 📱 **Mobile Friendly**: Optimized for Discord mobile app

## 🔧 Configuration

The analyzer can be configured by modifying these parameters in the code:

- **File limit**: Maximum files to analyze (default: 50)
- **File size limit**: Maximum file size to analyze (default: 500KB)
- **Content truncation**: Maximum characters per file (default: 1000)

## 📊 Analysis Criteria

The AI analyzes repositories based on five key criteria:

1. **Code Quality** (1-5): Is the code well-written or amateurish?
2. **Completeness** (1-5): Is it a complete implementation or just a skeleton?
3. **Security** (1-5): Are there obvious security flaws?
4. **Originality** (1-5): Is this unique code or copied/forked?
5. **Activity** (1-5): Is this an actively maintained project?

## 🎯 Supported File Types

The analyzer recognizes these file types as "code files":

- **Programming languages**: `.js`, `.ts`, `.py`, `.java`, `.c`, `.cpp`, `.go`, `.rs`, `.sol`, etc.
- **Web files**: `.html`, `.css`, `.scss`, `.sass`
- **Config files**: `.json`, `.yml`, `.yaml`, `.toml`, `.xml`
- **Documentation**: `.md`, `.txt`

## 🚨 What It Detects

**"Larping" Red Flags:**
- Empty repositories with only README files
- Copy-pasted code from other projects
- Skeleton implementations that don't match claims
- Inactive projects with no recent commits
- Poor code quality despite grandiose claims
- Fake metrics or inflated star counts

## 💡 Use Cases

- **Crypto Investors**: Due diligence before investment
- **Blockchain Developers**: Evaluating project quality
- **Crypto Communities**: Identifying scam projects
- **Researchers**: Academic analysis of blockchain projects
- **Due Diligence Firms**: Professional project assessment

## 🛠️ Development

### Project Structure
```
github-repo-analyzer/
├── main.py              # CLI interface
├── bot.py               # Discord bot
├── requirements.txt     # Dependencies
├── .env.example        # Environment template
├── README.md           # This file
└── LICENSE             # MIT license
```

### Key Functions
- `analyze_github_repo()`: Main analysis function
- `parse_github_url()`: URL parsing
- `get_repo_info()`: GitHub API integration
- `analyze_code_with_llm()`: AI analysis
- `create_analysis_embeds()`: Discord formatting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/0xGval/github-repo-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/0xGval/github-repo-analyzer/discussions)

## ⚠️ Disclaimer

This tool is for educational and due diligence purposes only. It should not be the sole basis for investment decisions. Always conduct thorough research before investing in any cryptocurrency project.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-4 API
- Discord.py for the Discord bot framework
- GitHub for the comprehensive API
- The crypto community for identifying the need for better due diligence tools

---

**Made with ❤️ for the crypto community** 🚀
