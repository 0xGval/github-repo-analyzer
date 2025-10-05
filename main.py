#!/usr/bin/env python3
# GitHub Repository Code Analyzer - Improved for crypto project authenticity assessment
# Focuses on detecting "larping" projects (pretending to be more substantial than they are)

import os
import re
import json
import sys
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure GitHub API token and OpenAI API key
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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

# Example usage
def main():
    if len(sys.argv) < 2:
        print("Usage: python github_analyzer.py <github-repo-url>")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    try:
        result = analyze_github_repo(repo_url)
        
        print("\n--- REPOSITORY ANALYSIS ---\n")
        print(result["analysis"])
        
    except Exception as e:
        print(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    main()