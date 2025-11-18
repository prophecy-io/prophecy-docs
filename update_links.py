#!/usr/bin/env python3
"""
Script to migrate links from old Docusaurus paths (/engineers/, /analysts/) 
to new Mintlify paths (/data-engineering/, /data-analytics/).

Uses `mint broken-links` to identify broken links and verifies fixes.
"""

import re
import json
import subprocess
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Base directories
BASE_DIR = Path(__file__).parent
DATA_ENGINEERING_DIR = BASE_DIR / "data-engineering"
DATA_ANALYTICS_DIR = BASE_DIR / "data-analytics"


def run_mint_broken_links() -> str:
    """Run mint broken-links and return the output."""
    print("Running mint broken-links...")
    try:
        result = subprocess.run(
            ["mint", "broken-links"],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        return result.stdout + result.stderr
    except FileNotFoundError:
        print("Error: 'mint' command not found. Make sure Mintlify CLI is installed.")
        return ""


def parse_broken_links(output: str) -> Dict[str, List[str]]:
    """
    Parse mint broken-links output to extract broken links.
    Returns a dict mapping file paths to lists of broken links.
    """
    broken_links = defaultdict(list)
    current_file = None
    
    for line in output.split('\n'):
        # File path indicator (ends with .mdx, no leading special chars)
        if line.endswith('.mdx') and not line.strip().startswith('⎿'):
            current_file = line.strip()
        # Broken link (starts with ⎿ or has leading spaces with ⎿)
        elif current_file and ('⎿' in line):
            # Extract link after the ⎿ character
            link = line.split('⎿', 1)[1].strip() if '⎿' in line else line.strip()
            if link and ('/engineers/' in link or '/analysts/' in link or 
                        link.startswith('docs/engineers/') or link.startswith('docs/analysts/')):
                broken_links[current_file].append(link)
    
    return dict(broken_links)


def build_file_index() -> Dict[str, str]:
    """
    Build an index of all .mdx files in data-engineering and data-analytics.
    Returns a dict mapping file names (without extension) to full paths.
    """
    file_index = {}
    
    for base_dir in [DATA_ENGINEERING_DIR, DATA_ANALYTICS_DIR]:
        if not base_dir.exists():
            continue
        
        for mdx_file in base_dir.rglob("*.mdx"):
            # Get relative path from base_dir
            rel_path = mdx_file.relative_to(BASE_DIR)
            # Convert to path format (without .mdx extension)
            path_str = str(rel_path.with_suffix('')).replace('\\', '/')
            
            # Index by filename
            filename = mdx_file.stem
            if filename not in file_index:
                file_index[filename] = []
            file_index[filename].append(path_str)
            
            # Also index by full path segments for better matching
            path_parts = path_str.split('/')
            for i in range(len(path_parts)):
                partial_path = '/'.join(path_parts[i:])
                if partial_path not in file_index:
                    file_index[partial_path] = []
                file_index[partial_path].append(path_str)
    
    return file_index


def find_target_path(old_path: str, file_index: Dict[str, List[str]], 
                     is_engineer: bool) -> Optional[str]:
    """
    Find the new path for an old path.
    
    Args:
        old_path: Old path like '/engineers/dependencies' or '/analysts/csv'
        file_index: Index of available files
        is_engineer: True if path starts with /engineers/, False if /analysts/
    
    Returns:
        New path or None if not found
    """
    # Remove leading slash and prefix
    path_without_prefix = old_path.lstrip('/')
    # Handle docs/ prefix
    if path_without_prefix.startswith('docs/'):
        path_without_prefix = path_without_prefix[5:]  # Remove 'docs/'
    # Determine if engineer or analyst based on path
    if path_without_prefix.startswith('engineers/'):
        path_without_prefix = path_without_prefix[10:]  # Remove 'engineers/'
        is_engineer = True
    elif path_without_prefix.startswith('analysts/'):
        path_without_prefix = path_without_prefix[9:]   # Remove 'analysts/'
        is_engineer = False
    # If path doesn't have prefix, use the is_engineer parameter passed in
    
    # Split hash fragment if present
    if '#' in path_without_prefix:
        path_part, hash_fragment = path_without_prefix.split('#', 1)
    else:
        path_part = path_without_prefix
        hash_fragment = None
    
    # Determine base directory
    base_prefix = '/data-engineering' if is_engineer else '/data-analytics'
    
    # Try exact filename match first
    if path_part in file_index:
        candidates = file_index[path_part]
        if len(candidates) == 1:
            result = f"/{candidates[0]}"
            if hash_fragment:
                result += f"#{hash_fragment}"
            return result
        elif len(candidates) > 1:
            # Multiple matches - try to find best match
            # Prefer matches in the correct base directory
            for candidate in candidates:
                if is_engineer and candidate.startswith('data-engineering'):
                    result = f"/{candidate}"
                    if hash_fragment:
                        result += f"#{hash_fragment}"
                    return result
                elif not is_engineer and candidate.startswith('data-analytics'):
                    result = f"/{candidate}"
                    if hash_fragment:
                        result += f"#{hash_fragment}"
                    return result
    
    # Try directory-based matching
    # Split path into segments and search
    path_segments = path_part.split('/')
    
    # Try matching from the end (most specific first)
    for i in range(len(path_segments), 0, -1):
        partial = '/'.join(path_segments[-i:])
        if partial in file_index:
            candidates = file_index[partial]
            for candidate in candidates:
                if is_engineer and candidate.startswith('data-engineering'):
                    result = f"/{candidate}"
                    if hash_fragment:
                        result += f"#{hash_fragment}"
                    return result
                elif not is_engineer and candidate.startswith('data-analytics'):
                    result = f"/{candidate}"
                    if hash_fragment:
                        result += f"#{hash_fragment}"
                    return result
    
    # Fallback: simple prefix replacement with path inference
    # Common mappings based on file structure
    common_mappings = {
        # Engineers mappings
        'dependencies': 'data-engineering/extensibility/dependencies',
        'pipelines': 'data-engineering/development/pipelines/pipelines',
        'data-sampling': 'data-engineering/development/runs/data-sampling',
        'execution': 'data-engineering/development/runs/execution',
        'execution-metrics': 'data-engineering/fabrics/execution-metrics',
        'gems': 'data-engineering/gems/gems',
        'git': 'data-engineering/ci-cd/git/git',
        'git-workflow': 'data-engineering/ci-cd/git/git-workflow',
        'resolve-git-conflicts': 'data-engineering/ci-cd/git/git-resolve',
        'git-pull-requests': 'data-engineering/ci-cd/git/git',
        'deployment': 'data-engineering/ci-cd/deployment/deployment',
        'package-hub': 'data-engineering/extensibility/package-hub/package-hub',
        'user-defined-functions': 'data-engineering/development/functions/user-defined-functions',
        'business-rules': 'data-engineering/development/functions/business-rules-engine/business-rules-engine',
        'source-target': 'data-engineering/gems/source-target',
        'transform': 'data-engineering/gems/transform',
        'join-split': 'data-engineering/gems/join-split',
        'subgraph': 'data-engineering/gems/subgraph/subgraph',
        'basic-subgraph': 'data-engineering/gems/subgraph/basicSubgraph',
        'table-iterator': 'data-engineering/gems/subgraph/tableIterator',
        'configurations': 'data-engineering/development/pipelines/configuration',
        'pipeline-settings': 'data-engineering/development/pipelines/pipeline-settings',
        'delta': 'data-engineering/gems/source-target/file/delta',
        'csv': 'data-engineering/gems/source-target/file/csv',
        'json': 'data-engineering/gems/source-target/file/json',
        'parquet': 'data-engineering/gems/source-target/file/parquet',
        'avro': 'data-engineering/gems/source-target/file/avro',
        'orc': 'data-engineering/gems/source-target/file/orc',
        'text': 'data-engineering/gems/source-target/file/text',
        'xlsx': 'data-engineering/gems/source-target/file/xlsx',
        'xml': 'data-engineering/gems/source-target/file/xml',
        'fixed-format': 'data-engineering/gems/source-target/file/fixed-format',
        'seed': 'data-engineering/gems/source-target/file/seed',
        'databricks-jobs': 'data-engineering/orchestration/databricks-jobs',
        'prophecy-build-tool': 'data-engineering/ci-cd/prophecy-build-tool/prophecy-build-tool',
        'github-actions-prophecy-build-tool': 'data-engineering/ci-cd/prophecy-build-tool/pbt-github-actions',
        'jenkins-prophecy-build-tool': 'data-engineering/ci-cd/prophecy-build-tool/pbt-jenkins',
        'unit-tests': 'data-engineering/ci-cd/tests',
        'data-explorer': 'data-engineering/development/data-explorer/data-explorer',
        'data-diff': 'data-engineering/ci-cd/data-diff',
        'lineage': 'data-engineering/lineage/lineage',
        'expression-builder': 'data-engineering/gems/expression-builder',
        'aggregate': 'data-engineering/gems/transform/aggregate',
        'deduplicate': 'data-engineering/gems/transform/deduplicate',
        'join': 'data-engineering/gems/join-split/join',
        'reformat': 'data-engineering/gems/transform/reformat',
        'order-by': 'data-engineering/gems/transform/order-by',
        'repartition': 'data-engineering/gems/join-split/repartition',
        'schema-transform': 'data-engineering/gems/transform/schema-transform',
        'filter': 'data-engineering/gems/transform/filter',
        'limit': 'data-engineering/gems/transform/limit',
        'secrets': 'data-engineering/fabrics/livy',  # This might need adjustment
        'prophecy-libraries': 'data-engineering/extensibility/dependencies/prophecy-libs',
        'spark-dependencies': 'data-engineering/extensibility/dependencies/spark-dependencies',
        'gem-builder-reference': 'data-engineering/extensibility/gem-builder/gem-builder-reference',
        'optimization-functions': 'data-engineering/extensibility/gem-builder/optimization-functions',
        'models': 'data-engineering/development/models/models',
        'model-sources-and-targets': 'data-engineering/development/models/sources-target/sources-target',
        'data-model-configurations': 'data-engineering/development/models/configuration',
        'dataset': 'data-engineering/development/dataset',
        'orchestration': 'data-engineering/orchestration',
        'develop-and-deploy': 'data-engineering/ci-cd/deployment/deployment',
        'ci-cd': 'data-engineering/ci-cd/reliable-ci-cd',
        
        # Analysts mappings
        'secrets': 'data-analytics/environment/secrets/secrets',
        'csv': 'data-analytics/gems/source-target/file/file-types/csv',
        'json': 'data-analytics/gems/source-target/file/file-types/json',
        'parquet': 'data-analytics/gems/source-target/file/file-types/parquet',
        'excel': 'data-analytics/gems/source-target/file/file-types/excel',
        'xml': 'data-analytics/gems/source-target/file/file-types/xml',
        'fixed-width': 'data-analytics/gems/source-target/file/file-types/fixed-width',
        'source-target': 'data-analytics/gems/source-target/source-target',
        'gems': 'data-analytics/gems/gems',
        'connections': 'data-analytics/environment/connections/connections',
        'versioning': 'data-analytics/development/versioning/version-control',
        'scheduling': 'data-analytics/production/scheduling/scheduling',
        'triggers': 'data-analytics/production/scheduling/triggers',
        'monitoring': 'data-analytics/production/monitoring',
        'project-publication': 'data-analytics/production/publication',
        'pipeline-parameters': 'data-analytics/development/pipeline-params',
        'pipeline-execution': 'data-analytics/development/runs/execution',
        'pipeline-trigger-gem': 'data-analytics/production/scheduling/pipeline-trigger-gem',
        'project-editor': 'data-analytics/development/studio/studio',
        'containers': 'data-analytics/development/studio/containers',
        'charts': 'data-analytics/development/runs/data-explorer/charts/charts',
        'data-explorer': 'data-analytics/development/runs/data-explorer/data-explorer',
        'business-applications': 'data-analytics/collaboration/prophecy-apps/apps',
        'create-business-applications': 'data-analytics/collaboration/prophecy-apps/app-creation',
        'business-application-components': 'data-analytics/collaboration/prophecy-apps/app-components',
        'run-apps': 'data-analytics/collaboration/prophecy-apps/run-apps',
        'app-builder': 'data-analytics/collaboration/prophecy-apps/app-builder',
        'app-settings': 'data-analytics/collaboration/prophecy-apps/app-settings',
        'project-sharing': 'data-analytics/collaboration/project-sharing',
        'migrate-managed-projects': 'data-analytics/development/versioning/migrate-managed',
        'import-projects': 'data-analytics/development/versioning/import-projects',
        'clone-projects': 'data-analytics/development/versioning/clone-projects',
        'collaboration-modes': 'data-analytics/development/versioning/collaboration-modes',
        'visual-expression-builder': 'data-analytics/gems/visual-expression-builder/visual-expression-builder',
        'visual-expression-builder-reference': 'data-analytics/gems/visual-expression-builder/visual-expression-builder-reference',
        'variant-schema': 'data-analytics/gems/visual-expression-builder/variant-schema',
        'flatten-schema': 'data-analytics/gems/prepare/flatten-schema',
        'join': 'data-analytics/gems/join-split/join',
        'union': 'data-analytics/gems/join-split/union',
        'union-by-name': 'data-analytics/gems/join-split/union-by-name',
        'filter': 'data-analytics/gems/prepare/filter',
        'aggregate': 'data-analytics/gems/transform/aggregate',
        'order-by': 'data-analytics/gems/prepare/order-by',
        'reformat': 'data-analytics/gems/prepare/reformat',
        'data-cleansing': 'data-analytics/gems/prepare/data-cleansing',
        'window': 'data-analytics/gems/transform/window',
        'pivot': 'data-analytics/gems/transform/pivot',
        'unpivot': 'data-analytics/gems/transform/unpivot',
        'buffer': 'data-analytics/gems/spatial/buffer',
        'find-nearest': 'data-analytics/gems/spatial/nearest-point',
        'simplify': 'data-analytics/gems/spatial/simplify',
        'heatmap': 'data-analytics/gems/spatial/heatmap',
        'polybuild': 'data-analytics/gems/spatial/polybuild',
        'spatial-match': 'data-analytics/gems/spatial/spatial-match',
        'create-point': 'data-analytics/gems/spatial/create-point',
        'distance': 'data-analytics/gems/spatial/distance',
        'nearest-point': 'data-analytics/gems/spatial/nearest-point',
        'count-records': 'data-analytics/gems/transform/count-records',
        'directory': 'data-analytics/gems/custom/directory',
        'data-masking': 'data-analytics/gems/prepare/masking',
        'encode-decode': 'data-analytics/gems/transform/encoder-decoder',
        'find-duplicates': 'data-analytics/gems/prepare/find-duplicates',
        'record-id': 'data-analytics/gems/prepare/record-id',
        'dynamic-input': 'data-analytics/gems/custom/dynamic-input',
        'stored-procedure': 'data-analytics/gems/custom/stored-procedure',
        'stored-procedure-gem': 'data-analytics/gems/custom/stored-procedure',
        'bigquery': 'data-analytics/gems/source-target/table/bigquery',
        'bigquery-table': 'data-analytics/gems/source-target/table/bigquery',
        'databricks': 'data-analytics/gems/source-target/table/databricks',
        'databricks-table': 'data-analytics/gems/source-target/table/databricks',
        'snowflake': 'data-analytics/gems/source-target/external-table/snowflake',
        'redshift': 'data-analytics/gems/source-target/external-table/redshift',
        'mssql': 'data-analytics/gems/source-target/external-table/mssql',
        'oracle': 'data-analytics/gems/source-target/external-table/oracle',
        'mongodb': 'data-analytics/gems/source-target/external-table/mongodb',
        'salesforce': 'data-analytics/gems/source-target/external-table/salesforce',
        'synapse': 'data-analytics/gems/source-target/external-table/synapse',
        'hana-gem': 'data-analytics/gems/source-target/external-table/hana/hana',
        'hana-generated-columns': 'data-analytics/gems/source-target/external-table/hana/identity-columns',
        'adls-gem': 'data-analytics/gems/source-target/file/adls',
        'gcs-gem': 'data-analytics/gems/source-target/file/gcs',
        's3-gem': 'data-analytics/gems/source-target/file/s3',
        'sftp-gem': 'data-analytics/gems/source-target/file/sftp',
        'onedrive-gem': 'data-analytics/gems/source-target/file/onedrive',
        'sharepoint-gem': 'data-analytics/gems/source-target/file/sharepoint',
        'smartsheet-gem': 'data-analytics/gems/source-target/file/smartsheet',
        'email': 'data-analytics/gems/report/email',
        'power-bi-write': 'data-analytics/gems/report/power-bi',
        'tableau': 'data-analytics/gems/report/tableau',
        'file-types': 'data-analytics/gems/source-target/file',
        'data-types': 'data-analytics/gems/data-types',
        'logs': 'data-analytics/development/runs/runtime-logs',
        'ai-chat': 'data-analytics/ai/agent/agent',
        'ai-explore': 'data-analytics/ai/agent/explore',
        'dependencies': 'data-analytics/development/extensibility/dependencies',
        'script': 'data-analytics/gems/custom/script',
        'macro': 'data-analytics/gems/custom/macro',
        'sql-statement': 'data-analytics/gems/custom/sql-statement',
        'rest-api': 'data-analytics/gems/custom/rest-api',
        'schedule-email-alerts': 'data-analytics/production/scheduling/alerts',
    }
    
    # Try common mappings
    if path_part in common_mappings:
        result = f"/{common_mappings[path_part]}"
        if hash_fragment:
            result += f"#{hash_fragment}"
        return result
    
    # Last resort: simple prefix replacement
    if is_engineer:
        result = f"/data-engineering/{path_part}"
    else:
        result = f"/data-analytics/{path_part}"
    
    if hash_fragment:
        result += f"#{hash_fragment}"
    
    return result


def update_links_in_file(file_path: Path, mappings: Dict[str, str], file_index: Dict[str, List[str]]) -> Tuple[int, List[Tuple[str, str]]]:
    """
    Update all old links in a file.
    Returns (number of replacements, list of (old, new) pairs).
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, []
    
    replacements = []
    new_content = content
    
    # Pattern to match markdown links with /engineers/ or /analysts/
    # Matches: [text](/engineers/path) or [text](/analysts/path) or [text](/engineers/path#hash)
    pattern = r'(\[([^\]]+)\]\((/engineers|/analysts)([^)]+)\))'
    
    def replace_link(match):
        full_match = match.group(0)
        link_text = match.group(2)
        prefix = match.group(3)  # /engineers or /analysts
        path_part = match.group(4)  # rest of the path
        
        old_path = prefix + path_part
        
        # Get mapping
        new_path = mappings.get(old_path)
        if not new_path:
            # Try to find mapping on the fly if not in pre-built mappings
            is_engineer = prefix == '/engineers'
            new_path = find_target_path(old_path, file_index, is_engineer)
            if new_path:
                mappings[old_path] = new_path  # Cache it
        
        if new_path:
            new_link = f"[{link_text}]({new_path})"
            replacements.append((old_path, new_path))
            return new_link
        return full_match
    
    new_content = re.sub(pattern, replace_link, new_content)
    
    # Also handle relative paths like docs/analysts/...
    pattern2 = r'(\[([^\]]+)\]\((docs/(engineers|analysts)([^)]+))\))'
    
    def replace_relative_link(match):
        full_match = match.group(0)
        link_text = match.group(2)
        prefix = match.group(3)  # engineers or analysts
        path_part = match.group(4)  # rest of the path
        
        old_path = f"/{prefix}{path_part}"
        
        # Get mapping
        new_path = mappings.get(old_path)
        if not new_path:
            # Try to find mapping on the fly if not in pre-built mappings
            is_engineer = prefix == 'engineers'
            new_path = find_target_path(old_path, file_index, is_engineer)
            if new_path:
                mappings[old_path] = new_path  # Cache it
        
        if new_path:
            new_link = f"[{link_text}]({new_path})"
            replacements.append((old_path, new_path))
            return new_link
        return full_match
    
    new_content = re.sub(pattern2, replace_relative_link, new_content)
    
    # Write back if changed
    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')
        return len(replacements), replacements
    
    return 0, []


def main():
    """Main execution function."""
    print("=" * 60)
    print("Link Migration Script")
    print("=" * 60)
    
    # Step 1: Run mint broken-links
    print("\nStep 1: Identifying broken links...")
    broken_links_output = run_mint_broken_links()
    
    if not broken_links_output:
        print("Warning: Could not run mint broken-links. Continuing with file scan...")
    
    # Step 2: Parse broken links
    print("\nStep 2: Parsing broken links...")
    broken_links_by_file = parse_broken_links(broken_links_output)
    
    # Extract all unique broken links
    all_broken_links = set()
    for links in broken_links_by_file.values():
        all_broken_links.update(links)
    
    print(f"Found {len(all_broken_links)} unique broken links with /engineers/ or /analysts/")
    
    # Step 3: Build file index
    print("\nStep 3: Building file index...")
    file_index = build_file_index()
    print(f"Indexed {len(file_index)} file paths")
    
    # Step 4: Build mappings
    print("\nStep 4: Building path mappings...")
    mappings = {}
    unmapped = []
    
    for old_path in all_broken_links:
        is_engineer = '/engineers/' in old_path
        new_path = find_target_path(old_path, file_index, is_engineer)
        if new_path:
            mappings[old_path] = new_path
        else:
            unmapped.append(old_path)
    
    print(f"Created {len(mappings)} mappings")
    if unmapped:
        print(f"Warning: {len(unmapped)} paths could not be mapped automatically")
        print("Unmapped paths:")
        for path in sorted(unmapped)[:10]:  # Show first 10
            print(f"  - {path}")
        if len(unmapped) > 10:
            print(f"  ... and {len(unmapped) - 10} more")
    
    # Save mappings
    with open(BASE_DIR / "broken_links_before.json", "w") as f:
        json.dump({
            "broken_links_by_file": broken_links_by_file,
            "all_broken_links": list(all_broken_links),
            "mappings": mappings,
            "unmapped": unmapped
        }, f, indent=2)
    
    # Step 5: Find all .mdx files and update them
    print("\nStep 5: Updating files...")
    all_mdx_files = list(BASE_DIR.rglob("*.mdx"))
    total_replacements = 0
    files_updated = 0
    all_replacements = []
    
    for mdx_file in all_mdx_files:
        count, replacements = update_links_in_file(mdx_file, mappings, file_index)
        if count > 0:
            files_updated += 1
            total_replacements += count
            all_replacements.extend([(str(mdx_file.relative_to(BASE_DIR)), old, new) 
                                    for old, new in replacements])
            print(f"Updated {mdx_file.relative_to(BASE_DIR)}: {count} replacements")
    
    print(f"\nUpdated {files_updated} files with {total_replacements} total replacements")
    
    # Step 6: Run mint broken-links again to verify
    print("\nStep 6: Verifying fixes...")
    broken_links_after = run_mint_broken_links()
    broken_links_after_parsed = parse_broken_links(broken_links_after)
    
    # Count remaining broken links with /engineers/ or /analysts/
    remaining_broken = set()
    for links in broken_links_after_parsed.values():
        remaining_broken.update([l for l in links if '/engineers/' in l or '/analysts/' in l])
    
    print(f"Remaining broken links with /engineers/ or /analysts/: {len(remaining_broken)}")
    
    # Save after state
    with open(BASE_DIR / "broken_links_after.json", "w") as f:
        json.dump({
            "broken_links_by_file": broken_links_after_parsed,
            "remaining_broken": list(remaining_broken)
        }, f, indent=2)
    
    # Generate report
    report = {
        "summary": {
            "total_replacements": total_replacements,
            "files_updated": files_updated,
            "mappings_created": len(mappings),
            "unmapped_paths": len(unmapped),
            "remaining_broken": len(remaining_broken)
        },
        "replacements": all_replacements[:100],  # First 100
        "unmapped": unmapped,
        "remaining_broken": list(remaining_broken)
    }
    
    with open(BASE_DIR / "migration_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Files updated: {files_updated}")
    print(f"  - Total replacements: {total_replacements}")
    print(f"  - Mappings created: {len(mappings)}")
    print(f"  - Unmapped paths: {len(unmapped)}")
    print(f"  - Remaining broken links: {len(remaining_broken)}")
    print(f"\nReports saved to:")
    print(f"  - broken_links_before.json")
    print(f"  - broken_links_after.json")
    print(f"  - migration_report.json")


if __name__ == "__main__":
    main()

