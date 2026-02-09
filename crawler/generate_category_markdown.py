import os
import json
import sys

# Add the parent directory to sys.path to allow imports from crawler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.storage import Storage
from crawler.llm import TAG_HIERARCHY

def generate_markdown():
    storage = Storage()
    print("Listing all projects...")
    all_files = storage.list_files("data/projects/")
    
    projects_by_category = {}
    
    # Initialize structure based on TAG_HIERARCHY
    for p_tag in TAG_HIERARCHY:
        projects_by_category[p_tag] = {}
        if "children" in TAG_HIERARCHY[p_tag]:
            for s_tag in TAG_HIERARCHY[p_tag]["children"]:
                projects_by_category[p_tag][s_tag] = []
        # Add a catch-all for undefined secondary tags
        projects_by_category[p_tag]["_other"] = []

    projects_by_category["_uncategorized"] = []

    print(f"Found {len(all_files)} projects. Processing...")
    
    for file_key in all_files:
        try:
            repo_data = storage.get_json(file_key)
            if not repo_data:
                continue
                
            owner = repo_data.get('owner')
            repo = repo_data.get('repo')
            full_name = f"{owner}/{repo}"
            
            tags = repo_data.get('tags', {})
            primary_tags = tags.get('primary_tags', [])
            secondary_tags = tags.get('secondary_tags', [])
            
            # Use first primary tag if available, else _uncategorized
            if not primary_tags:
                projects_by_category["_uncategorized"].append(full_name)
                continue
                
            p_tag = primary_tags[0]
            
            if p_tag not in projects_by_category:
                # Should not happen if TAG_HIERARCHY is consistent, but handle it
                projects_by_category.setdefault(p_tag, {})
                projects_by_category[p_tag].setdefault("_other", [])
            
            # If no secondary tags, put in _other
            if not secondary_tags:
                 projects_by_category[p_tag]["_other"].append(full_name)
            else:
                for s_tag in secondary_tags:
                    if s_tag in projects_by_category[p_tag]:
                        projects_by_category[p_tag][s_tag].append(full_name)
                    else:
                        projects_by_category[p_tag]["_other"].append(full_name)
                        
        except Exception as e:
            print(f"Error processing {file_key}: {e}")

    # Generate Markdown
    md_lines = ["# Project Categories", "", "This file is auto-generated but can be manually edited to correct categories.", ""]
    
    for p_tag, p_info in TAG_HIERARCHY.items():
        md_lines.append(f"## {p_tag}")
        
        # Sort secondary tags as defined in hierarchy
        s_tags_ordered = list(p_info.get("children", {}).keys())
        
        # Process defined secondary tags
        for s_tag in s_tags_ordered:
            projects = projects_by_category[p_tag].get(s_tag, [])
            if projects:
                md_lines.append(f"### {s_tag}")
                for proj in sorted(list(set(projects))): # Dedupe just in case
                    md_lines.append(f"- {proj}")
                md_lines.append("")
        
        # Process projects with primary tag but no valid secondary tag
        other_projects = projects_by_category[p_tag].get("_other", [])
        if other_projects:
            md_lines.append(f"### Unspecified")
            for proj in sorted(list(set(other_projects))):
                md_lines.append(f"- {proj}")
            md_lines.append("")
            
    # Handle uncategorized
    uncategorized = projects_by_category.get("_uncategorized", [])
    if uncategorized:
        md_lines.append("## Uncategorized")
        for proj in sorted(list(set(uncategorized))):
            md_lines.append(f"- {proj}")
            
    with open("PROJECT_CATEGORIES.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print("Generated PROJECT_CATEGORIES.md")

if __name__ == "__main__":
    generate_markdown()
