#!/usr/bin/env python3
# Discord bot for GitHub repository analysis
# Uses the GitHub analyzer to check if crypto projects are "larping"
# Implements slash commands and improved embeds

import os
import re
import json
import sys
import asyncio
import requests
from dotenv import load_dotenv
import discord
from discord import app_commands, Embed, Color
from discord.ext import commands
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure tokens and API keys
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Set up Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="analyze", description="Analyze a GitHub repository for crypto project due diligence")
async def slash_analyze(interaction: discord.Interaction, github_url: str):
    """Analyze a GitHub repository to check if it's legitimate or larping (slash command)"""
    # Check if the URL is a valid GitHub URL
    if not re.search(r'github\.com/([^/]+)/([^/]+)', github_url):
        await interaction.response.send_message('Please provide a valid GitHub repository URL.', ephemeral=True)
        return
    
    # Send initial response (defer since analysis will take time)
    await interaction.response.defer(thinking=True)
    
    try:
        # Run the analysis in a separate thread to avoid blocking
        result = await asyncio.to_thread(analyze_github_repo, github_url)
        
        # Create and send the embed with results
        embeds = create_analysis_embeds(github_url, result)
        await interaction.followup.send(embeds=embeds)
        
    except Exception as e:
        await interaction.followup.send(f'❌ Error analyzing repository: {str(e)}')

def create_analysis_embeds(repo_url, result):
    """Create Discord embeds with the analysis results (improved formatting)"""
    repo_info = result["repo_info"]
    repo_structure = result["repo_structure"]
    analysis_text = result["analysis"]
    
    # Extract ratings if they exist in the analysis
    ratings = extract_ratings(analysis_text)
    
    # Determine the embed color based on the verdict
    color = Color.light_grey()
    verdict = extract_verdict(analysis_text)
    if verdict:
        if "LEGITIMATE" in verdict.upper():
            color = Color.green()
        elif "LARPING" in verdict.upper():
            color = Color.red()
        elif "BORDERLINE" in verdict.upper():
            color = Color.gold()
    
    # Create the main embed
    main_embed = Embed(
        title=f"Analysis: {repo_info['name']}",
        url=repo_url,
        color=color
    )
    
    # Set author information
    owner_login = repo_info.get('owner', {}).get('login', 'Unknown')
    owner_avatar = repo_info.get('owner', {}).get('avatar_url', None)
    owner_url = repo_info.get('owner', {}).get('html_url', repo_url)
    main_embed.set_author(name=f"Repository by {owner_login}", url=owner_url, icon_url=owner_avatar)
    
    # Add basic repo info
    main_embed.add_field(
        name="Repository Info",
        value=f"⭐ **Stars:** {repo_info['stargazers_count']}\n"
              f"🍴 **Forks:** {repo_info['forks_count']}\n"
              f"📂 **Files:** {repo_structure['total_files']}\n"
              f"🔄 **Last Updated:** {repo_info['updated_at'][:10]}",
        inline=False
    )
    
    # Add verdict field with appropriate emoji
    if verdict:
        if "LEGITIMATE" in verdict.upper():
            verdict_display = f"✅ **{verdict}**"
        elif "LARPING" in verdict.upper():
            verdict_display = f"❌ **{verdict}**"
        elif "BORDERLINE" in verdict.upper():
            verdict_display = f"⚠️ **{verdict}**"
        else:
            verdict_display = verdict
            
        main_embed.add_field(name="Verdict", value=verdict_display, inline=False)
    
    # Add ratings if available
    if ratings:
        ratings_text = ""
        for k, v in ratings.items():
            rating_value = v.split('/')[0]
            stars = "★" * int(rating_value) + "☆" * (5 - int(rating_value))
            ratings_text += f"**{k}:** {stars} ({v})\n"
        
        main_embed.add_field(name="Ratings", value=ratings_text, inline=False)
    
    # Create a second embed for the analysis summary
    summary_embed = Embed(
        title="Analysis Summary",
        color=color
    )
    
    # Extract and format the analysis summary
    summary = extract_summary(analysis_text)
    
    # Format the summary with proper markdown for Discord
    formatted_summary = format_summary_for_discord(summary)
    
    # Split the summary into chunks if it's too long for one embed
    chunks = split_text_into_chunks(formatted_summary, 4000)  # Discord embed limit is 4096 chars
    
    summary_embed.description = chunks[0]
    
    # Set footer
    summary_embed.set_footer(text="GitHub Analyzer | Crypto Due Diligence")
    
    # Return both embeds as a list
    embeds = [main_embed, summary_embed]
    
    # Add more embeds if the summary is too long
    for i in range(1, len(chunks)):
        extra_embed = Embed(
            title=f"Analysis Summary (continued {i})",
            description=chunks[i],
            color=color
        )
        embeds.append(extra_embed)
    
    return embeds

def extract_ratings(analysis_text):
    """Extract ratings from the analysis text"""
    ratings = {}
    rating_patterns = [
        (r"CODE QUALITY:\s*(\d+)/5", "Code Quality"),
        (r"COMPLETENESS:\s*(\d+)/5", "Completeness"),
        (r"SECURITY:\s*(\d+)/5", "Security"),
        (r"ORIGINALITY:\s*(\d+)/5", "Originality"),
        (r"ACTIVITY:\s*(\d+)/5", "Activity")
    ]
    
    for pattern, label in rating_patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            ratings[label] = f"{match.group(1)}/5"
    
    return ratings

def extract_verdict(analysis_text):
    """Extract the verdict from the analysis text"""
    verdict_match = re.search(r"VERDICT:?\s*(.+?)(?:\n|$)", analysis_text, re.IGNORECASE | re.DOTALL)
    if verdict_match:
        verdict = verdict_match.group(1).strip()
        return verdict
    return None

def extract_summary(analysis_text):
    """Extract the summary part of the analysis, excluding ratings and verdict"""
    # Remove the ratings section
    text = re.sub(r"(CODE QUALITY|COMPLETENESS|SECURITY|ORIGINALITY|ACTIVITY):\s*\d+/5", "", analysis_text)
    
    # Remove the verdict section
    text = re.sub(r"VERDICT:?\s*.+?(?:\n|$)", "", text, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up and return
    return "\n".join(line for line in text.split("\n") if line.strip())

def format_summary_for_discord(summary):
    """Format the summary text for Discord's markdown"""
    # Format section headers (like "Assessment" or "Key questions")
    formatted = re.sub(r"#+\s+(.+)", r"**\1**", summary)
    
    # Format subsection headers (like a, b, c, d in your example)
    formatted = re.sub(r"####\s+([a-z])\)\s+(.+)", r"**\1) \2**", formatted)
    
    # Replace any HTML-like tags that might cause issues in Discord
    formatted = re.sub(r"<[^>]+>", "", formatted)
    
    # Ensure proper spacing
    formatted = formatted.replace("\n\n\n", "\n\n")
    
    return formatted

def split_text_into_chunks(text, max_length):
    """Split text into chunks of maximum length, trying to split at paragraph breaks"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        if current_pos + max_length >= len(text):
            chunks.append(text[current_pos:])
            break
        
        # Try to find a paragraph break
        split_pos = text.rfind('\n\n', current_pos, current_pos + max_length)
        
        if split_pos == -1 or split_pos <= current_pos:
            # If no paragraph break, try to find a line break
            split_pos = text.rfind('\n', current_pos, current_pos + max_length)
            
        if split_pos == -1 or split_pos <= current_pos:
            # If no line break, just split at the max length
            split_pos = current_pos + max_length
        
        chunks.append(text[current_pos:split_pos])
        current_pos = split_pos + 1
    
    return chunks

# The following functions are from the GitHub analyzer script

# Parse GitHub URL to extract owner and repo name
def parse_github_url(url):
    try:
        # Handle different GitHub URL formats
        # Format: https://github.com/owner/repo
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if match:
            return match.group(1), match.group(2).replace('.git', '')
        
        # Format: git@github.com:owner/repo.git
        match = re.search(r'github\.com:([^/]+)/([^/]+)\.git', url)
        if match:
            return match.group(1), match.group(2)
        
        return None, None
    except Exception as e:
        print(f"Error parsing GitHub URL: {str(e)}")
        return None, None

# Get repository information
def get_repo_info(owner, repo):
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching repository information: {str(e)}")
        raise

# Get repository activity metrics (commits, contributors, etc.)
def get_repo_activity(owner, repo):
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        
        # Get commits (limited to last 100)
        commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=100"
        commits_response = requests.get(commits_url, headers=headers)
        commits_response.raise_for_status()
        commits = commits_response.json()
        
        # Get contributors
        contributors_url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
        contributors_response = requests.get(contributors_url, headers=headers)
        contributors_response.raise_for_status()
        contributors = contributors_response.json()
        
        # Get issues
        issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100"
        issues_response = requests.get(issues_url, headers=headers)
        issues = []
        if issues_response.status_code == 200:  # Some repos don't have issues enabled
            issues = issues_response.json()
        
        # Calculate some metrics
        commit_frequency = {}
        for commit in commits:
            if 'commit' in commit and 'author' in commit['commit'] and 'date' in commit['commit']['author']:
                date = commit['commit']['author']['date'][:10]  # YYYY-MM-DD
                commit_frequency[date] = commit_frequency.get(date, 0) + 1
        
        return {
            "total_commits": len(commits),
            "total_contributors": len(contributors),
            "total_issues": len(issues),
            "commit_dates": list(commit_frequency.keys()),
            "recent_activity": len([d for d in commit_frequency.keys() if d >= "2024-01-01"]) > 0
        }
    except Exception as e:
        print(f"Error fetching repository activity: {str(e)}")
        # Return empty data if we can't get activity info
        return {
            "total_commits": 0,
            "total_contributors": 0,
            "total_issues": 0,
            "commit_dates": [],
            "recent_activity": False
        }

# Get all files in the repository recursively
def get_all_files(owner, repo, path=''):
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}", headers=headers)
        response.raise_for_status()
        data = response.json()
        
        files = []
        
        for item in data:
            if item['type'] == 'file':
                files.append(item)
            elif item['type'] == 'dir':
                sub_files = get_all_files(owner, repo, item['path'])
                files.extend(sub_files)
        
        return files
    except Exception as e:
        print(f"Error fetching files from {path}: {str(e)}")
        return []

# Determine if a file is a code file based on extension
def is_code_file(file_path):
    code_extensions = [
        # Common programming languages
        '.js', '.ts', '.jsx', '.tsx', '.py', '.rb', '.java', '.c', '.cpp', '.cs', '.go', '.rs', '.php',
        '.swift', '.kt', '.scala', '.sh', '.bash', '.pl', '.lua', '.sol', '.ex', '.exs', '.erl', '.hrl',
        # Web files
        '.html', '.css', '.scss', '.sass', '.less',
        # Config files
        '.json', '.yml', '.yaml', '.toml', '.xml', '.ini', '.env.example', '.gitignore',
        # Documentation
        '.md', '.txt'
    ]
    
    _, extension = os.path.splitext(file_path.lower())
    return extension in code_extensions

# Analyze repository structure
def analyze_repo_structure(files):
    file_types = {}
    directory_structure = {}
    
    for file in files:
        # Count file types
        _, extension = os.path.splitext(file['path'].lower())
        file_types[extension] = file_types.get(extension, 0) + 1
        
        # Build directory structure
        parts = file['path'].split('/')
        current = directory_structure
        
        for i in range(len(parts) - 1):
            part = parts[i]
            if part not in current:
                current[part] = {}
            current = current[part]
    
    return {
        "file_types": file_types,
        "total_files": len(files),
        "directory_structure": directory_structure
    }

# Get code contents for files
def get_code_contents(owner, repo, files):
    code_contents = []
    
    # We need to limit the number of files to analyze to avoid rate limits and excessive processing
    files_to_analyze = files[:50]  # Limit to 50 files
    
    for file in files_to_analyze:
        try:
            # Skip large files
            if file['size'] > 500000:  # Skip files larger than 500KB
                code_contents.append({
                    "path": file['path'],
                    "content": "File too large to analyze",
                    "size": file['size']
                })
                continue
            
            headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
            response = requests.get(file['download_url'], headers=headers)
            response.raise_for_status()
            
            content = response.text if response.text else json.dumps(response.json())
            
            code_contents.append({
                "path": file['path'],
                "content": content,
                "size": file['size']
            })
        except Exception as e:
            print(f"Error fetching content for {file['path']}: {str(e)}")
            code_contents.append({
                "path": file['path'],
                "content": "Error fetching content",
                "error": str(e),
                "size": file['size']
            })
    
    return code_contents

# Analyze code with LLM
def analyze_code_with_llm(repo_info, repo_structure, repo_activity, code_contents):
    try:
        # Create a simplified representation of the code for analysis
        code_overview = [
            {
                "path": file["path"],
                "size": file["size"],
                # Only include first 1000 chars for the prompt to prevent token limit issues
                "content": file["content"][:1000] + ("...[truncated]" if len(file["content"]) > 1000 else "")
            }
            for file in code_contents
        ]
        
        # Create the prompt for the LLM
        prompt = f"""
Analyze this cryptocurrency/blockchain GitHub repository to determine if the project is "larping" (pretending to be more substantial than it actually is).

REPOSITORY OVERVIEW:
- Name: {repo_info['name']}
- Description: {repo_info.get('description', 'No description')}
- Stars: {repo_info['stargazers_count']}
- Forks: {repo_info['forks_count']}
- Total files: {repo_structure['total_files']}
- File types: {json.dumps(repo_structure['file_types'])}
- Total commits: {repo_activity['total_commits']}
- Total contributors: {repo_activity['total_contributors']}
- Recent activity: {'Yes' if repo_activity['recent_activity'] else 'No'}

ANALYSIS INSTRUCTIONS:
1. Provide a concise assessment (max 500 words total) focused on these key questions:
   a) Is this a real, functional project or just empty promises?
   b) Does the code actually implement what the project claims?
   c) Are there specific red flags indicating a scam or incompetence?
   d) Is this a copy/paste of another project with minimal modifications?

2. Rate each of the following on a scale of 1-5 (1=Very Poor, 5=Excellent):
   - CODE QUALITY: Is the code well-written or amateurish?
   - COMPLETENESS: Is it a complete implementation or just a skeleton?
   - SECURITY: Are there obvious security flaws?
   - ORIGINALITY: Is this unique code or copied/forked?
   - ACTIVITY: Is this an actively maintained project?

3. VERDICT: Explicitly state whether this project is LEGITIMATE or LARPING, with a 1-2 sentence explanation.

Here are excerpts from key files:

"""
        
        for file in code_overview:
            prompt += f"""
--- {file['path']} ---
{file['content']}
"""
        
        # Call the OpenAI API for analysis
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",  # Use the most capable model
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior blockchain security expert conducting due diligence on cryptocurrency projects. Your task is to analyze GitHub repositories to determine if they contain legitimate code or are 'larping' (pretending to be more substantial than they are). Be brutally honest and concise in your assessment."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,  # Lower temperature for more consistent analysis
            max_tokens=2000  # Reduced token count for concise output
        )

        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error analyzing code with LLM: {str(e)}")
        return f"Error analyzing code with LLM: {str(e)}"

# Main function to analyze a GitHub repository
def analyze_github_repo(repo_url):
    try:
        print(f"Starting analysis of repository: {repo_url}")
        
        # Parse GitHub repository URL
        owner, repo = parse_github_url(repo_url)
        if not owner or not repo:
            raise ValueError("Invalid GitHub repository URL")
        
        # Get repository information
        repo_info = get_repo_info(owner, repo)
        print(f"Repository: {repo_info['name']}")
        print(f"Description: {repo_info.get('description', 'No description')}")
        print(f"Stars: {repo_info['stargazers_count']}")
        print(f"Forks: {repo_info['forks_count']}")
        print(f"Last updated: {repo_info['updated_at']}")
        
        # Get all files recursively
        files = get_all_files(owner, repo)
        print(f"Found {len(files)} files in the repository")
        
        # Analyze repository structure
        repo_structure = analyze_repo_structure(files)
        
        # Get repository activity metrics
        repo_activity = get_repo_activity(owner, repo)
        
        # Get code content for relevant files
        code_files = [file for file in files if is_code_file(file['path'])]
        code_contents = get_code_contents(owner, repo, code_files)
        
        # Analyze code with LLM
        analysis = analyze_code_with_llm(repo_info, repo_structure, repo_activity, code_contents)
        
        return {
            "repo_info": repo_info,
            "repo_structure": repo_structure,
            "analysis": analysis
        }
    except Exception as e:
        print(f"Error analyzing repository: {str(e)}")
        raise

# Run the bot
if __name__ == "__main__":
    # Check if Discord token is available
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN is not set in the .env file")
        sys.exit(1)
    
    bot.run(DISCORD_TOKEN)