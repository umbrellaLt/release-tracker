from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime
import re

app = Flask(__name__)

def extract_repo_info(github_url):
    """
    Extract owner and repo name from GitHub URL
    """
    # Handle different GitHub URL formats with regex
    patterns = [
        r'github\.com/([^/]+)/([^/]+)/?(?:releases)?/?$',
        r'github\.com/([^/]+)/([^/]+)/releases/?$',
        r'github\.com/([^/]+)/([^/]+)\.git/?$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, github_url)
        if match:
            return match.group(1), match.group(2)
    
    return None, None

def fetch_releases_from_api(owner, repo, count=3):
    """
    Fetch releases using GitHub API
    """
    try:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        # Header auth with personal git account
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Releases-Dashboard',
            'Authorization': 'Bearer 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'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        releases_data = response.json()
        
        releases = []
        for release in releases_data[:count]:
            # Parse and format the date and sorts 
            published_date = datetime.fromisoformat(release['published_at'].replace('Z', '+00:00'))
            
            release_info = {
                'title': release['name'] or release['tag_name'],
                'tag_name': release['tag_name'],
                'tag_url': release['html_url'],
                'date': release['published_at'],
                'date_formatted': published_date.strftime('%B %d, %Y'),
                'description': release['body'][:300] + '...' if release['body'] and len(release['body']) > 300 else release['body'] or 'No description available',
                'is_prerelease': release['prerelease'],
                'is_draft': release['draft'],
                'author': release['author']['login'] if release['author'] else 'Unknown',
                'download_count': sum(asset['download_count'] for asset in release['assets']),
                'assets_count': len(release['assets'])
            }
            
            releases.append(release_info)
        
        return releases, None
    
    except requests.exceptions.RequestException as e:
        return [], f"Network error: {str(e)}"
    except KeyError as e:
        return [], f"API response format error: {str(e)}"
    except Exception as e:
        return [], f"Error fetching releases: {str(e)}"

@app.route('/')
def dashboard():
    """
    Main dashboard route - shows multiple repositories
    """
    # Default repositories and new one can be added after need
    default_repos = [
        "https://github.com/metallb/metallb",
        "https://github.com/siderolabs/talos",
        "https://github.com/cloudnative-pg/cloudnative-pg",
        "https://github.com/keycloak/keycloak/",
        "https://github.com/argoproj/argo-cd/",
        "https://github.com/rabbitmq/cluster-operator/",
        "http://github.com/OT-CONTAINER-KIT/redis-operator/"
    ]
    
    repo_data = []
    
    for repo_url in default_repos:
        owner, repo = extract_repo_info(repo_url)
        
        if owner and repo:
            releases, error = fetch_releases_from_api(owner, repo)
            repo_data.append({
                'repo_name': f"{owner}/{repo}",
                'repo_url': repo_url,
                'releases': releases,
                'error': error
            })
        else:
            repo_data.append({
                'repo_name': "Invalid Repository",
                'repo_url': repo_url,
                'releases': [],
                'error': "Invalid repository URL"
            })
    
    return render_template('dashboard.html', repo_data=repo_data)

@app.route('/api/releases')
def api_releases():
    """
    API endpoint to fetch releases for a given repository
    """
    repo_url = request.args.get('repo', 'https://github.com/metallb/metallb')
    count = int(request.args.get('count', 3))
    
    owner, repo = extract_repo_info(repo_url)
    
    if owner and repo:
        releases, error = fetch_releases_from_api(owner, repo, count)
        return jsonify({
            'releases': releases,
            'error': error,
            'repo': f"{owner}/{repo}"
        })
    else:
        return jsonify({
            'releases': [],
            'error': 'Invalid repository URL',
            'repo': None
        })

@app.route('/repo/<owner>/<repo>')
def custom_repo(owner, repo):
    """
    Show releases for a specific repository
    """
    releases, error = fetch_releases_from_api(owner, repo)
    repo_url = f"https://github.com/{owner}/{repo}"
    
    return render_template('dashboard.html', 
                         releases=releases, 
                         repo_url=repo_url,
                         repo_name=f"{owner}/{repo}",
                         error=error)

# HTML Template with enhanced features
dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Releases Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .repo-section {
            margin-bottom: 50px;
        }
        
        .repo-info {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .repo-url {
            color: #e0e7ff;
            text-decoration: none;
            font-weight: 500;
            font-size: 1.1rem;
        }
        
        .repo-url:hover {
            color: white;
        }
        
        .search-section {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .search-form {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .search-input {
            flex: 1;
            min-width: 300px;
            padding: 12px 16px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            background: rgba(255,255,255,0.9);
        }
        
        .search-btn {
            padding: 12px 24px;
            background: #4c51bf;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: background 0.3s;
        }
        
        .search-btn:hover {
            background: #434190;
        }
        
        .error-message {
            background: #fed7d7;
            color: #c53030;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #c53030;
        }
        
        .releases-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
        }
        
        .release-card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .release-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        
        .release-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .release-header {
            margin-bottom: 15px;
        }
        
        .release-title {
            font-size: 1.4rem;
            font-weight: 600;
            color: #2d3748;
            text-decoration: none;
            display: block;
            margin-bottom: 8px;
        }
        
        .release-title:hover {
            color: #667eea;
        }
        
        .release-tag {
            font-size: 0.9rem;
            color: #718096;
            font-family: 'Courier New', monospace;
            background: #f7fafc;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .release-meta {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
            font-size: 0.9rem;
            color: #666;
            flex-wrap: wrap;
        }
        
        .release-date, .release-author {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .badge-prerelease {
            background: #fef3cd;
            color: #b45309;
        }
        
        .badge-draft {
            background: #f3f4f6;
            color: #6b7280;
        }
        
        .release-stats {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            font-size: 0.85rem;
            color: #718096;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .release-description {
            color: #4a5568;
            line-height: 1.6;
            font-size: 0.95rem;
            white-space: pre-line;
        }
        
        .no-releases {
            text-align: center;
            color: white;
            font-size: 1.2rem;
            margin-top: 50px;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50px;
            padding: 15px 20px;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .refresh-btn:hover {
            background: #5a67d8;
            transform: scale(1.05);
        }
        
        @media (max-width: 768px) {
            .releases-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .search-input {
                min-width: 200px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 CCS Releases Dashboard</h1>
        </div>
        
        <div class="search-section">
            <form class="search-form" onsubmit="searchRepo(event)">
                <input type="text" 
                       class="search-input" 
                       id="repoUrl" 
                       placeholder="Enter GitHub repository URL (e.g., https://github.com/owner/repo)"
                       value="">
                <button type="submit" class="search-btn">Search Releases</button>
            </form>
        </div>
        
        {% if repo_data %}
            {% for repo in repo_data %}
            <div class="repo-section">
                <div class="repo-info">
                    <strong>Repository:</strong> 
                    <a href="{{ repo.repo_url }}" target="_blank" class="repo-url">{{ repo.repo_name }}</a>
                </div>
                
                {% if repo.error %}
                <div class="error-message">
                    <strong>Error:</strong> {{ repo.error }}
                </div>
                {% endif %}
                
                {% if repo.releases %}
                <div class="releases-grid">
                    {% for release in repo.releases %}
                    <div class="release-card">
                        <div class="release-header">
                            <a href="{{ release.tag_url }}" target="_blank" class="release-title">
                                {{ release.title }}
                            </a>
                            <span class="release-tag">{{ release.tag_name }}</span>
                        </div>
                        
                        <div class="release-meta">
                            <div class="release-date">
                                📅 {{ release.date_formatted }}
                            </div>
                            
                            <div class="release-author">
                                👤 {{ release.author }}
                            </div>
                            
                            {% if release.is_prerelease %}
                            <span class="badge badge-prerelease">Pre-release</span>
                            {% endif %}
                            
                            {% if release.is_draft %}
                            <span class="badge badge-draft">Draft</span>
                            {% endif %}
                        </div>
                        
                        <div class="release-stats">
                            <div class="stat-item">
                                📦 {{ release.assets_count }} assets
                            </div>
                            <div class="stat-item">
                                ⬇️ {{ release.download_count }} downloads
                            </div>
                        </div>
                        
                        {% if release.description %}
                        <div class="release-description">
                            {{ release.description }}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="no-releases">
                    <p>{% if repo.error %}Unable to fetch releases due to error above.{% else %}No releases found for this repository.{% endif %}</p>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
        <div class="no-releases">
            <p>No repositories configured.</p>
        </div>
        {% endif %}
    </div>
    
    <button class="refresh-btn" onclick="location.reload()">
        🔄 Refresh
    </button>
    
    <script>
        function searchRepo(event) {
            event.preventDefault();
            const repoUrl = document.getElementById('repoUrl').value.trim();
            
            if (!repoUrl) {
                alert('Please enter a repository URL');
                return;
            }
            
            // Extract owner and repo from URL
            const match = repoUrl.match(/github\.com\/([^\/]+)\/([^\/]+)/);
            if (match) {
                const owner = match[1];
                const repo = match[2];
                window.location.href = `/repo/${owner}/${repo}`;
            } else {
                alert('Please enter a valid GitHub repository URL');
            }
        }
        
        // Auto-refresh every 5 minutes
        setTimeout(() => {
            location.reload();
        }, 300000);
    </script>
</body>
</html>
'''

# Create templates directory and file
import os
if not os.path.exists('templates'):
    os.makedirs('templates')

with open('templates/dashboard.html', 'w') as f:
    f.write(dashboard_html)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)