# 🔍 GitHub Repository Analyzer

A simple tool to analyze GitHub repositories and detect "larping" crypto projects using AI.

## 🚀 Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the analyzer**
   ```bash
   python main.py https://github.com/owner/repository
   ```

4. **Or run the Discord bot**
   ```bash
   python bot.py
   ```

## 📋 Required API Keys

- **OpenAI API Key**: Get from https://platform.openai.com/api-keys
- **Discord Bot Token**: Get from https://discord.com/developers/applications (for bot)
- **GitHub Token**: Optional, for higher rate limits

## 🎯 What It Does

- Analyzes GitHub repositories for crypto project legitimacy
- Uses AI to detect "larping" (fake/empty projects)
- Provides ratings for code quality, completeness, security, etc.
- Works via command line or Discord bot

## 📞 Support

- Open an issue for bugs or feature requests
- Check the code for examples of usage

## 📄 License

MIT License - see LICENSE file for details.

---

**Made for the crypto community** 🚀
