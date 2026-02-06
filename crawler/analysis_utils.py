import datetime
from collections import defaultdict

def calculate_growth_metrics(star_history: list[dict]) -> tuple[int, float]:
    """Calculates 90-day star growth (delta) and growth rate."""
    if not star_history:
        return 0, 0.0
    
    # Sort by date just in case
    try:
        sorted_history = sorted(star_history, key=lambda x: x['date'])
    except Exception:
        return 0, 0.0

    if not sorted_history:
        return 0, 0.0

    latest_entry = sorted_history[-1]
    latest_count = latest_entry['count']
    
    try:
        latest_date = datetime.datetime.strptime(latest_entry['date'], "%Y-%m-%d")
    except ValueError:
        return 0, 0.0

    target_date = latest_date - datetime.timedelta(days=90)
    
    start_count = 0
    closest_entry = None
    
    # Find the entry closest to (but not after) the target date
    # OR find the entry exactly 90 days ago or the first one before it
    # Actually, we want the count at "90 days ago".
    # If we have an entry on target_date, use it.
    # If not, use the latest entry BEFORE target_date.
    
    # Optimized search
    for entry in reversed(sorted_history):
        try:
            entry_date = datetime.datetime.strptime(entry['date'], "%Y-%m-%d")
            if entry_date <= target_date:
                closest_entry = entry
                break
        except ValueError:
            continue
            
    if closest_entry:
        start_count = closest_entry['count']
    else:
        # If all history is newer than 90 days, start_count is effectively the first recorded count?
        # Or 0?
        # If the repo is younger than 90 days, growth is "all stars gained since start".
        # But if the first record is e.g. 100 stars (from backfill), we don't know if they had 0 or 90 stars 90 days ago.
        # Assuming 0 if no history before 90 days might be wrong if the repo is old but we only have recent history.
        # But based on "Backfill" logic in main.py, we try to fetch full history.
        # If history is present but starts < 90 days ago, we use the first entry.
        if sorted_history:
            start_count = sorted_history[0]['count']
            # However, if the first entry is > 90 days ago (handled above)
            # If the first entry is < 90 days ago (e.g. 30 days ago), it means we only have data for 30 days.
            # We can assume start_count at 90 days ago was 0? Or just use the first entry?
            # Using first entry is safer to avoid inflating growth if we missed data.
            pass

    delta = latest_count - start_count
    
    growth_rate = 0.0
    if start_count > 0:
        growth_rate = delta / start_count
    elif start_count == 0 and delta > 0:
        # Infinite growth? Or 100%?
        # Usually for ranking, we might cap it or handle it.
        # For now, return a high value or just delta as rate? 
        # User definition: growth rate = delta / 90 days ago star count.
        # If denominator is 0, mathematically undefined.
        # Let's return 0.0 or 1.0? 
        # If a project went from 0 to 100, growth rate is infinite.
        # Let's return delta if start is 0? No that's different units.
        # Let's return 0.0 to avoid issues, or handle specially.
        # But wait, if a new project starts at 0 and goes to 1000, it's trending.
        # I'll return 0.0 for now to be safe, or maybe I should check how it's used.
        # The user sorts by growth rate.
        # I'll stick to 0.0 if start_count is 0 to avoid breaking sort.
        growth_rate = 0.0
        
    return delta, growth_rate

def calculate_growth_90d(star_history: list[dict]) -> int:
    if not star_history:
        return 0
    
    # Sort by date just in case
    try:
        sorted_history = sorted(star_history, key=lambda x: x['date'])
    except Exception:
        return 0

    if not sorted_history:
        return 0

    latest_entry = sorted_history[-1]
    latest_date_str = latest_entry['date']
    latest_count = latest_entry['count']
    
    try:
        latest_date = datetime.datetime.strptime(latest_date_str, "%Y-%m-%d")
    except ValueError:
        return 0

    target_date = latest_date - datetime.timedelta(days=90)
    
    start_count = 0
    closest_entry = None
    
    for entry in sorted_history:
        try:
            entry_date = datetime.datetime.strptime(entry['date'], "%Y-%m-%d")
            if entry_date <= target_date:
                closest_entry = entry
            else:
                break
        except ValueError:
            continue
            
    if closest_entry:
        start_count = closest_entry['count']
    else:
        # If all history is newer than 90 days, assume start was 0 or take the first recorded
        if sorted_history:
            start_count = sorted_history[0]['count']
            
    return latest_count - start_count

def calculate_score(item: dict) -> float:
    stars = item.get('stargazers_count', 0)
    forks = item.get('forks_count', 0)
    growth = item.get('growth_90d', 0)
    
    score = stars * 1.0 + forks * 2.0 + growth * 10.0
    return score

def extract_project_info(repo_data: dict) -> dict:
    """Extracts relevant fields for the leaderboard from the raw repo data."""
    if not repo_data:
        return None
        
    tags = repo_data.get('tags', {})
    primary_tags = tags.get('primary_tags', [])
    
    # Filter Non-AI
    if not primary_tags or "Non-AI" in primary_tags:
        return None
        
    star_history = repo_data.get('star_history', [])
    growth_90d = calculate_growth_90d(star_history)
    
    owner = repo_data.get('owner')
    repo = repo_data.get('repo')
    # fallback for full_name
    full_name = repo_data.get('full_name', f"{owner}/{repo}")
    
    info = {
        'name': full_name,
        'owner': owner,
        'repo': repo,
        'url': repo_data.get('html_url', f"https://github.com/{full_name}"),
        'description': repo_data.get('description', ''),
        'stargazers_count': repo_data.get('stargazers_count', 0),
        'forks_count': repo_data.get('forks_count', 0),
        'growth_90d': growth_90d,
        'primary_tags': primary_tags,
        'secondary_tags': tags.get('secondary_tags', []),
        'language': repo_data.get('language'),
        'topics': repo_data.get('topics', [])
    }
    
    info['score'] = calculate_score(info)
    return info

def group_and_rank_projects(projects: list) -> dict:
    """Groups projects by tags and ranks them."""
    nested_projects = defaultdict(lambda: defaultdict(list))
    
    for p in projects:
        primary_tags_list = p['primary_tags']
        secondary_tags_list = p['secondary_tags']
        
        if not secondary_tags_list:
            secondary_tags_list = ["Others"]
            
        for p_tag in primary_tags_list:
            for s_tag in secondary_tags_list:
                nested_projects[p_tag][s_tag].append(p)
                
    # Sort structure
    result = []
    sorted_primary = sorted(nested_projects.keys())
    
    for p_tag in sorted_primary:
        secondary_dict = nested_projects[p_tag]
        sorted_secondary = sorted(secondary_dict.keys())
        
        subcategories = []
        for s_tag in sorted_secondary:
            items = secondary_dict[s_tag]
            if not items:
                continue
                
            # Sort by score descending
            items.sort(key=lambda x: x['score'], reverse=True)
            
            # Top 20
            top_items = items[:20]
            
            # Add rank
            ranked_items = []
            for idx, item in enumerate(top_items, 1):
                item_copy = item.copy()
                item_copy['rank'] = idx
                ranked_items.append(item_copy)
                
            subcategories.append({
                "name": s_tag,
                "projects": ranked_items
            })
            
        if subcategories:
            result.append({
                "name": p_tag,
                "subcategories": subcategories
            })
            
    return result
