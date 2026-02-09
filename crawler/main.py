import datetime
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import Config
from .storage import Storage
from .github_client import GitHubClient
from .llm import LLMClient, TAG_HIERARCHY
from .ossinsight_client import OSSInsightClient
from .analysis_utils import extract_project_info, group_and_rank_projects, calculate_growth_metrics

def main():
    print("Starting AI Trending Crawler...")
    
    storage = Storage()
    gh_client = GitHubClient()
    llm_client = LLMClient()
    oss_client = OSSInsightClient()
    
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Track processed repos to avoid double work
    processed_full_names = set()

    def process_trending_repo(repo_summary):
        try:
            owner = repo_summary['owner']
            repo_name = repo_summary['repo']
            full_name = f"{owner}/{repo_name}"
            file_key = f"data/projects/{owner}/{repo_name}.json"
            
            print(f"Processing Trending: {full_name}...")
            
            existing_data = storage.get_json(file_key)
            repo_data = None
            
            if existing_data:
                print(f"  - Found existing data for {full_name}. Updating...")
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
                print(f"  - New project {full_name}. Fetching full details...")
                details = gh_client.get_repo_details(owner, repo_name)
                if not details:
                    print(f"  - Failed to get details for {full_name}. Skipping.")
                    return None
                    
                print("  - Generating tags...")
                tags = llm_client.generate_tags(details)
                details['tags'] = tags
                
                print("  - Fetching star history (initial)...")
                history = gh_client.get_star_history(owner, repo_name)
                details['star_history'] = history
                
                repo_data = details
            
            # Topics cleanup
            topics_raw = repo_data.get("topics") or []
            if isinstance(topics_raw, str):
                topics_raw = [topics_raw]
            topics = [topic for topic in topics_raw if isinstance(topic, str) and topic.strip()]
            repo_data['topics'] = topics

            storage.upload_json(file_key, repo_data)
            
            processed_full_names.add(full_name)
            
            analysis_info = extract_project_info(repo_data)

            return {
                "owner": owner,
                "repo": repo_name,
                "description": repo_data.get('description'),
                "language": repo_data.get('language'),
                "topics": topics,
                "stars": repo_data.get('stargazers_count'),
                "forks": repo_data.get('forks_count'),
                "growth": repo_summary.get('growth'),
                "tags": repo_data.get('tags', {}),
                "_analysis_info": analysis_info
            }
        except Exception as e:
            print(f"  - Failed processing {repo_summary.get('owner')}/{repo_summary.get('repo')}: {e}")
            return None

    def process_trending_list(time_range):
        trending_repos = gh_client.get_trending(time_range=time_range)
        print(f"Found {len(trending_repos)} trending repos for {time_range}.")
        results = []
        max_workers = gh_client.max_concurrency
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_trending_repo, repo) for repo in trending_repos]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        return results

    # --- Part 1: Process Trending Repos ---
    all_projects_info = []
    trending_results = {} # map full_name -> repo_info
    for time_range in ["daily", "weekly", "monthly"]:
        processed_repos = process_trending_list(time_range)
        for repo in processed_repos:
            full_name = f"{repo['owner']}/{repo['repo']}"
            trending_results[full_name] = repo
            if repo.get('_analysis_info'):
                all_projects_info.append(repo['_analysis_info'])
        time_range_key = f"data/{time_range}/{today_str}.json"
        storage.upload_json(time_range_key, processed_repos)

    # --- Part 2: Maintenance (Existing Projects) ---
    print("Starting maintenance of all existing projects...")
    
    def process_existing_file(file_key):
        try:
            # Extract owner/repo from key: data/projects/owner/repo.json
            parts = file_key.split('/')
            # Handle possible variations if prefix changes, but assuming data/projects/owner/repo.json
            if len(parts) < 4: return None
            owner = parts[-2]
            repo_name = parts[-1].replace('.json', '')
            full_name = f"{owner}/{repo_name}"
            
            if full_name in processed_full_names:
                return None
            
            repo_data = storage.get_json(file_key)
            if not repo_data: return None
            
            history = repo_data.get('star_history', [])
            
            needs_update = False
            needs_backfill = False
            
            # Condition for backfill: empty or only 1 record
            if not history or len(history) <= 1:
                needs_backfill = True
            
            last_date = history[-1]['date'] if history else None
            if last_date != today_str:
                needs_update = True
                
            if needs_backfill or needs_update:
                print(f"Maintenance: {full_name} (Backfill={needs_backfill}, Update={needs_update})")
                
                data_changed = False

                if needs_backfill:
                    print(f"  - Fetching full history from OSSInsight for {full_name}...")
                    full_history = oss_client.fetch_star_history(owner, repo_name)
                    if full_history:
                        repo_data['star_history'] = full_history
                        repo_data['stargazers_count'] = full_history[-1]['count']
                        repo_data['updated_at'] = datetime.datetime.now().isoformat()
                        data_changed = True
                        # If backfill successful, we likely have the latest data (up to today or yesterday)
                        # We can re-check if we still need a daily update (if OSS data is stale by 1 day)
                        history = full_history
                
                # Re-evaluate update need
                last_date = history[-1]['date'] if history else None
                if last_date != today_str:
                    print(f"  - Fetching current stars from GitHub for {full_name}...")
                    current_stars = gh_client.get_repo_stars(owner, repo_name)
                    if current_stars is not None:
                        history.append({
                            "date": today_str,
                            "count": current_stars
                        })
                        repo_data['star_history'] = history
                        repo_data['stargazers_count'] = current_stars
                        repo_data['updated_at'] = datetime.datetime.now().isoformat()
                        data_changed = True
                
                if data_changed:
                    storage.upload_json(file_key, repo_data)
            
            return extract_project_info(repo_data)
        except Exception as e:
            print(f"Error maintaining {file_key}: {e}")
            return None

    all_files = storage.list_files("data/projects/")
    print(f"Found {len(all_files)} total projects in storage.")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_existing_file, key) for key in all_files]
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_projects_info.append(res)

    # --- Part 3: Update Index (Refactored) ---
    print("Starting Index Update & Top Project Analysis...")
    
    index_projects = []
    
    def process_index_entry(file_key):
        try:
            repo_data = storage.get_json(file_key)
            if not repo_data: return None
            
            owner = repo_data.get('owner')
            repo = repo_data.get('repo')
            if not owner or not repo: return None
            
            full_name = f"{owner}/{repo}"
            
            # Calculate 90d metrics
            star_history = repo_data.get('star_history', [])
            delta_90d, growth_rate_90d = calculate_growth_metrics(star_history)
            
            current_stars = repo_data.get('stargazers_count', 0)
            
            # Optimized entry for index.json
            entry = {
                "owner": owner,
                "repo": repo,
                "description": (repo_data.get('description') or "")[:250], # Truncate description
                "language": repo_data.get('language'),
                "tags": repo_data.get('tags', {}),
                "topics": (repo_data.get('topics') or [])[:10], # Limit topics to top 10
                "stars": current_stars,
                "forks": repo_data.get('forks_count', 0),
                "growth_90d": delta_90d,
                "last_updated": repo_data.get('updated_at', today_str)
            }
            return entry
        except Exception as e:
            print(f"Error processing index for {file_key}: {e}")
            return None

    # Use ThreadPool to fetch and process all files
    # Note: all_files was retrieved in Part 2
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_index_entry, key) for key in all_files]
        for future in as_completed(futures):
            res = future.result()
            if res:
                index_projects.append(res)
    
    # Upload Index
    index_key = "data/index.json"
    print(f"Uploading index.json with {len(index_projects)} projects...")
    storage.upload_json(index_key, index_projects)

    # --- Part 4: Top Project Analysis (Refactored) ---
    try:
        print("Generating Top Project Analysis (Leaderboard Structure)...")
        
        # 1. Structure Initialization
        categories_map = {}
        for p_name, p_info in TAG_HIERARCHY.items():
            categories_map[p_name] = {
                "name": p_name,
                "subcategories": {}
            }
            if "children" in p_info:
                for s_name in p_info["children"].keys():
                    categories_map[p_name]["subcategories"][s_name] = []

        # 2. Score & Distribute Projects
        for project in index_projects:
            # Calculate Score
            stars = project.get('stars', 0)
            forks = project.get('forks', 0)
            growth_90d = project.get('growth_90d', 0)
            
            # Weighted Score = Stars + (Forks * 2) + (90d Growth * 10)
            score = stars + (forks * 2) + (growth_90d * 10)
            project['score'] = score
            
            # Get Tags
            tags = project.get('tags', {})
            if not isinstance(tags, dict):
                continue
                
            p_tags = tags.get('primary_tags', [])
            s_tags = tags.get('secondary_tags', [])
            
            # Distribute
            for p_tag in p_tags:
                if p_tag not in categories_map:
                    continue
                
                valid_s_tags = [s for s in s_tags if s in categories_map[p_tag]["subcategories"]]
                
                for s_tag in valid_s_tags:
                    categories_map[p_tag]["subcategories"][s_tag].append(project)

        # 3. Sort & Format Output
        final_categories = []
        
        for p_name, p_data in categories_map.items():
            formatted_subcategories = []
            
            # Iterate through defined subcategories to maintain order
            defined_subs = TAG_HIERARCHY.get(p_name, {}).get("children", {}).keys()
            
            for s_name in defined_subs:
                projects_list = p_data["subcategories"].get(s_name, [])
                if not projects_list:
                    continue
                
                # Sort by Score Descending
                projects_list.sort(key=lambda x: x['score'], reverse=True)
                
                # Assign Rank
                ranked_projects = []
                for idx, proj in enumerate(projects_list):
                    # Optimization: Only include fields strictly needed by TopLeaderboard.tsx
                    r_proj = {
                        "rank": idx + 1,
                        "owner": proj['owner'],
                        "repo": proj['repo'],
                        "name": proj['repo'],  # Used as key in frontend
                        "url": f"https://github.com/{proj['owner']}/{proj['repo']}",
                        "description": proj.get('description'),
                        "stargazers_count": proj['stars'],
                        "forks_count": proj['forks'],
                        "growth_90d": proj.get('growth_90d', 0),
                        "score": proj.get('score', 0)
                    }
                    ranked_projects.append(r_proj)
                
                # Limit to Top 30
                ranked_projects = ranked_projects[:30]
                
                formatted_subcategories.append({
                    "name": s_name,
                    "projects": ranked_projects
                })
            
            if formatted_subcategories:
                final_categories.append({
                    "name": p_name,
                    "subcategories": formatted_subcategories
                })

        output_data = {
            "date": today_str,
            "categories": final_categories
        }
        
        output_dir = "output/top"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, f"top_projects_{today_str}.json")
        abs_path = os.path.abspath(output_file)
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"Top Project Analysis JSON generated: {abs_path}")
        
        # Upload to S3
        s3_key = f"data/top/top_projects_{today_str}.json"
        print(f"Uploading Top Project Analysis to S3: {s3_key}...")
        storage.upload_json(s3_key, output_data)
        
    except Exception as e:
        print(f"ERROR: Top Project Analysis failed: {e}")

    print("Done!")

if __name__ == "__main__":
    main()
