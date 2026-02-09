import os
import re
from .storage import Storage
from .llm import TAG_HIERARCHY

def parse_markdown_categories(md_path):
    """
    Parses the PROJECT_CATEGORIES.md file.
    Returns a dict: { "owner/repo": { "primary": str, "secondary": set() } }
    """
    if not os.path.exists(md_path):
        print(f"Markdown file not found: {md_path}")
        return {}
        
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    projects = {}
    current_primary = None
    current_secondary = None
    
    # Regex to match headers
    primary_re = re.compile(r'^##\s+(.+)$')
    secondary_re = re.compile(r'^###\s+(.+)$')
    # Regex to match project list items: "- owner/repo" or "- owner/repo - desc"
    # Matches start of line, dash, space, then capturing group for owner/repo
    # owner/repo allows alphanumeric, -, ., _
    project_re = re.compile(r'^-\s+([a-zA-Z0-9\-\._]+/[a-zA-Z0-9\-\._]+)')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for Primary Header
        p_match = primary_re.match(line)
        if p_match:
            current_primary = p_match.group(1).strip()
            current_secondary = None
            continue
            
        # Check for Secondary Header
        s_match = secondary_re.match(line)
        if s_match:
            current_secondary = s_match.group(1).strip()
            continue
            
        # Check for Project Item
        proj_match = project_re.match(line)
        if proj_match:
            full_name = proj_match.group(1).strip()
            
            if not current_primary:
                continue 
                
            if full_name not in projects:
                projects[full_name] = {
                    "primary": current_primary,
                    "secondary": set()
                }
            
            # If a project is listed under a new primary, update it (last one wins or first one?)
            # Usually it shouldn't be duplicated across primary categories.
            # If it is, we assume the user moved it and we are seeing the new location.
            # But since we scan linearly, we just update.
            projects[full_name]["primary"] = current_primary
                
            if current_secondary and current_secondary != "Unspecified":
                projects[full_name]["secondary"].add(current_secondary)

    return projects

def sync_categories(md_path="PROJECT_CATEGORIES.md"):
    print("Starting Category Sync from Markdown...")
    storage = Storage()
    
    new_categories = parse_markdown_categories(md_path)
    if not new_categories:
        print("No categories found in markdown or file missing.")
        return

    print(f"Loaded {len(new_categories)} projects from markdown.")
    
    updated_count = 0
    
    for full_name, cats in new_categories.items():
        try:
            parts = full_name.split('/')
            if len(parts) != 2:
                continue
            owner, repo = parts
            file_key = f"data/projects/{owner}/{repo}.json"
            
            repo_data = storage.get_json(file_key)
            if not repo_data:
                continue
                
            current_tags = repo_data.get('tags', {})
            current_primary_list = current_tags.get('primary_tags', [])
            current_primary = current_primary_list[0] if current_primary_list else None
            current_secondary = set(current_tags.get('secondary_tags', []))
            
            new_primary = cats["primary"]
            new_secondary = cats["secondary"]
            
            # Validation
            if new_primary not in TAG_HIERARCHY and new_primary != "Uncategorized":
                print(f"Warning: Invalid primary tag '{new_primary}' for {full_name}. Skipping.")
                continue

            if new_primary != "Uncategorized":
                valid_subs = TAG_HIERARCHY.get(new_primary, {}).get("children", {}).keys()
                valid_new_secondary = {s for s in new_secondary if s in valid_subs}
                
                if len(valid_new_secondary) != len(new_secondary):
                    # print(f"Warning: Filtered invalid secondary tags for {full_name}.")
                    new_secondary = valid_new_secondary
            else:
                new_secondary = set()

            # Check for changes
            primary_changed = (current_primary != new_primary)
            secondary_changed = (current_secondary != new_secondary)
            
            if primary_changed or secondary_changed:
                print(f"Updating categories for {full_name}:")
                if primary_changed:
                    print(f"  Primary: {current_primary} -> {new_primary}")
                if secondary_changed:
                    print(f"  Secondary: {current_secondary} -> {new_secondary}")
                
                if 'tags' not in repo_data:
                    repo_data['tags'] = {}
                
                repo_data['tags']['primary_tags'] = [new_primary]
                repo_data['tags']['secondary_tags'] = list(new_secondary)
                
                storage.upload_json(file_key, repo_data)
                updated_count += 1
                
        except Exception as e:
            print(f"Error syncing {full_name}: {e}")
            
    print(f"Sync complete. Updated {updated_count} projects.")
