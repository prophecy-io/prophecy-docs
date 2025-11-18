#!/usr/bin/env python3
"""
Comprehensive script to fix all broken links including:
- Malformed .mdanalysts/.mdengineers links
- .md to .mdx conversions
- Relative to absolute path conversions
- Other broken link patterns
"""

import re
import subprocess
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).parent
DATA_ENGINEERING_DIR = BASE_DIR / "data-engineering"
DATA_ANALYTICS_DIR = BASE_DIR / "data-analytics"


def run_mint_broken_links() -> str:
    """Run mint broken-links and return the output."""
    try:
        result = subprocess.run(
            ["mint", "broken-links"],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        return result.stdout + result.stderr
    except FileNotFoundError:
        print("Error: 'mint' command not found.")
        return ""


def parse_all_broken_links(output: str) -> Dict[str, List[str]]:
    """Parse all broken links from mint output."""
    broken_links = defaultdict(list)
    current_file = None
    
    for line in output.split('\n'):
        if line.endswith('.mdx') and not line.strip().startswith('⎿'):
            current_file = line.strip()
        elif current_file and ('⎿' in line):
            link = line.split('⎿', 1)[1].strip() if '⎿' in line else line.strip()
            if link:
                broken_links[current_file].append(link)
    
    return dict(broken_links)


def build_file_index() -> Dict[str, List[str]]:
    """Build index of all .mdx files."""
    file_index = defaultdict(list)
    
    for base_dir in [DATA_ENGINEERING_DIR, DATA_ANALYTICS_DIR]:
        if not base_dir.exists():
            continue
        
        for mdx_file in base_dir.rglob("*.mdx"):
            rel_path = mdx_file.relative_to(BASE_DIR)
            path_str = str(rel_path.with_suffix('')).replace('\\', '/')
            
            # Index by full path
            file_index[path_str].append(path_str)
            
            # Index by filename
            filename = mdx_file.stem
            file_index[filename].append(path_str)
            
            # Index by path segments
            path_parts = path_str.split('/')
            for i in range(len(path_parts)):
                partial = '/'.join(path_parts[i:])
                file_index[partial].append(path_str)
    
    return dict(file_index)


def find_correct_path(broken_path: str, file_index: Dict[str, List[str]]) -> str:
    """Find the correct path for a broken link."""
    # Remove leading slash
    path = broken_path.lstrip('/')
    
    # Fix .mdanalysts and .mdengineers
    if path.endswith('.mdanalysts'):
        path = path.replace('.mdanalysts', '')
    elif path.endswith('.mdengineers'):
        path = path.replace('.mdengineers', '')
    
    # Remove .md extension
    if path.endswith('.md'):
        path = path[:-3]
    
    # Remove any trailing periods or slashes
    path = path.rstrip('./')
    
    # Try to find matching file by filename first (most reliable)
    path_parts = path.split('/')
    filename = path_parts[-1] if path_parts else path
    
    if filename in file_index:
        candidates = file_index[filename]
        if candidates:
            # Prefer match in same base directory (data-analytics or data-engineering)
            base_dir = path_parts[0] if path_parts and len(path_parts) > 1 else ''
            if base_dir:
                for candidate in candidates:
                    if candidate.startswith(base_dir):
                        return f"/{candidate}"
            # If no base match, return first candidate
            return f"/{candidates[0]}"
    
    # Try exact path match
    if path in file_index:
        candidates = file_index[path]
        if candidates:
            return f"/{candidates[0]}"
    
    # Try path segments (from end, most specific first)
    for i in range(len(path_parts), 0, -1):
        partial = '/'.join(path_parts[-i:])
        if partial in file_index:
            candidates = file_index[partial]
            if candidates:
                # Prefer match in same base directory
                base_dir = path_parts[0] if path_parts else ''
                for candidate in candidates:
                    if base_dir and candidate.startswith(base_dir):
                        return f"/{candidate}"
                return f"/{candidates[0]}"
    
    return None


def fix_links_in_file(file_path: Path, broken_links: List[str], 
                      file_index: Dict[str, List[str]]) -> Tuple[int, List[Tuple[str, str]]]:
    """Fix all broken links in a file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, []
    
    replacements = []
    new_content = content
    
    # Fix each broken link
    for broken_link in broken_links:
        # Skip image files and external URLs
        if (broken_link.startswith('http') or 
            broken_link.startswith('img/') or 
            broken_link.startswith('./img') or
            broken_link.endswith('.png') or
            broken_link.endswith('.jpg') or
            broken_link.endswith('.jpeg') or
            broken_link.endswith('.gif') or
            broken_link.endswith('.svg') or
            'img/' in broken_link or
            '/img' in broken_link):
            continue
        
        # Find correct path
        correct_path = find_correct_path(broken_link, file_index)
        if not correct_path:
            # Try without leading slash
            if broken_link.startswith('/'):
                correct_path = find_correct_path(broken_link[1:], file_index)
            if not correct_path:
                continue
        
        # Escape the broken link for regex
        escaped_link = re.escape(broken_link)
        
        # Pattern to match markdown links: [text](broken_link) or [text](broken_link#hash)
        pattern = rf'(\[[^\]]+\]\()({escaped_link})(#[^\)]*)?(\))'
        
        def make_replace_func(repl_path):
            def replace_func(match):
                link_text = match.group(1)  # [text](
                hash_part = match.group(3) if match.group(3) else ''  # #hash or empty
                closing = match.group(4)  # )
                new_link = f"{link_text}{repl_path}{hash_part}{closing}"
                replacements.append((broken_link, repl_path))
                return new_link
            return replace_func
        
        # Replace all occurrences
        new_content = re.sub(pattern, make_replace_func(correct_path), new_content)
    
    # Write back if changed
    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')
        return len(set(replacements)), list(set(replacements))
    
    return 0, []


def main():
    """Main execution."""
    print("=" * 60)
    print("Comprehensive Link Fix Script")
    print("=" * 60)
    
    # Step 1: Get all broken links
    print("\nStep 1: Getting all broken links...")
    broken_links_output = run_mint_broken_links()
    if not broken_links_output:
        print("Could not run mint broken-links")
        return
    
    # Step 2: Parse broken links
    print("\nStep 2: Parsing broken links...")
    broken_links_by_file = parse_all_broken_links(broken_links_output)
    total_broken = sum(len(links) for links in broken_links_by_file.values())
    print(f"Found {total_broken} broken links across {len(broken_links_by_file)} files")
    
    # Step 3: Build file index
    print("\nStep 3: Building file index...")
    file_index = build_file_index()
    print(f"Indexed {len(file_index)} file paths")
    
    # Step 4: Fix links in each file
    print("\nStep 4: Fixing links...")
    total_fixed = 0
    files_updated = 0
    all_replacements = []
    
    for file_path_str, broken_links in broken_links_by_file.items():
        file_path = BASE_DIR / file_path_str
        if not file_path.exists():
            continue
        
        count, replacements = fix_links_in_file(file_path, broken_links, file_index)
        if count > 0:
            files_updated += 1
            total_fixed += count
            all_replacements.extend(replacements)
            print(f"Fixed {file_path_str}: {count} links")
    
    print(f"\nFixed {total_fixed} links in {files_updated} files")
    
    # Step 5: Verify
    print("\nStep 5: Verifying fixes...")
    broken_links_after = run_mint_broken_links()
    broken_links_after_parsed = parse_all_broken_links(broken_links_after)
    remaining = sum(len(links) for links in broken_links_after_parsed.values())
    
    print(f"\nRemaining broken links: {remaining}")
    print(f"Fixed: {total_fixed}")
    print(f"Files updated: {files_updated}")


if __name__ == "__main__":
    main()

