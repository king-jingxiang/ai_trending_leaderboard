import datetime
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import Config
from .storage import Storage
from .github_client import GitHubClient
from .llm import LLMClient

def main():
    print("Starting AI Trending Crawler...")
    
    storage = Storage()
    gh_client = GitHubClient()
    llm_client = LLMClient()
    
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    def process_repo(repo_summary):
        try:
            owner = repo_summary['owner']
            repo_name = repo_summary['repo']
            file_key = f"data/projects/{owner}/{repo_name}.json"
            
            print(f"Processing {owner}/{repo_name}...")
            
            existing_data = storage.get_json(file_key)
            
            if existing_data:
                print("  - Found existing data. Updating...")
                repo_data = existing_data
                current_stars = repo_summary['stars']
                
                history = repo_data.get('star_history', [])
                if not history or history[-1]['date'] != today_str:
                    history.append({
                        "date": today_str,
                        "count": current_stars
                    })
                    repo_data['star_history'] = history
                    
                repo_data['stargazers_count'] = current_stars
                repo_data['forks_count'] = repo_summary['forks']
                repo_data['updated_at'] = datetime.datetime.now().isoformat()
                
            else:
                print("  - New project. Fetching full details...")
                details = gh_client.get_repo_details(owner, repo_name)
                if not details:
                    print("  - Failed to get details. Skipping.")
                    return None
                    
                print("  - Generating tags...")
                tags = llm_client.generate_tags(details)
                details['tags'] = tags
                
                print("  - Fetching star history...")
                history = gh_client.get_star_history(owner, repo_name)
                details['star_history'] = history
                
                repo_data = details
            
            topics_raw = repo_data.get("topics") or []
            if isinstance(topics_raw, str):
                topics_raw = [topics_raw]
            topics = [topic for topic in topics_raw if isinstance(topic, str) and topic.strip()]

            storage.upload_json(file_key, repo_data)
            
            return {
                "owner": owner,
                "repo": repo_name,
                "description": repo_data.get('description'),
                "language": repo_data.get('language'),
                "topics": topics,
                "stars": repo_data.get('stargazers_count'),
                "forks": repo_data.get('forks_count'),
                "growth": repo_summary.get('growth'),
                "tags": repo_data.get('tags', {})
            }
        except Exception as e:
            print(f"  - Failed processing {repo_summary.get('owner')}/{repo_summary.get('repo')}: {e}")
            return None

    def process_trending(time_range):
        trending_repos = gh_client.get_trending(time_range=time_range)
        print(f"Found {len(trending_repos)} trending repos for {time_range}.")
        processed_repos = []
        max_workers = gh_client.max_concurrency
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_repo, repo) for repo in trending_repos]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    processed_repos.append(result)
        return processed_repos

    all_processed_repos = {}
    for time_range in ["daily", "weekly", "monthly"]:
        processed_repos = process_trending(time_range)
        for repo in processed_repos:
            full_name = f"{repo['owner']}/{repo['repo']}"
            all_processed_repos[full_name] = repo
        time_range_key = f"data/{time_range}/{today_str}.json"
        storage.upload_json(time_range_key, processed_repos)
    
    # 5. Update Index (All Projects Summary)
    # Ideally, we should read the existing index and merge.
    # But listing all files in S3 is expensive if there are many.
    # For now, let's just assume we might want to rebuild it or maintain it incrementally.
    # A simple approach for this MVP:
    # Read index.json, update entries for processed_repos, write back.
    
    index_key = "data/index.json"
    index_data = storage.get_json(index_key) or []
    
    # Create a map for faster lookup
    index_map = {f"{item['owner']}/{item['repo']}": item for item in index_data}
    
    for repo in all_processed_repos.values():
        full_name = f"{repo['owner']}/{repo['repo']}"
        index_map[full_name] = {
            "owner": repo['owner'],
            "repo": repo['repo'],
            "description": repo['description'],
            "stars": repo['stars'],
            "tags": repo['tags'],
            "topics": repo.get('topics', []),
            "language": repo['language'],
            "last_seen": today_str
        }
        
    new_index_data = list(index_map.values())
    storage.upload_json(index_key, new_index_data)
    
    print("Done!")

if __name__ == "__main__":
    main()
