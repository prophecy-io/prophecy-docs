#!/usr/bin/env python3
"""CI check for the change log page and the .changelog/ state files.

Usage: validate_changelog.py --base SHA [--head-ref BRANCH] [--page-changed-file PATH]
Run from the repo root with history for SHA available. Compares SHA with the
checked-out HEAD. Exits 0 with a note when no change log file changed.

Checks:
  * state.json and held-items.json are valid JSON; state.json has its required keys.
  * The page holds the {/* changelog-entries */} marker once, and below it only
    <Update> blocks, each passing the same entry check the job runs before
    pushing (mintlify_entry.py, kept identical to the skill's copy).
  * Labels are Sundays (YYYY-MM-DD), unique, and newest first.
  * On changelog/* branches: only the page and .changelog/ files change, and the
    page change is exactly one new entry at the top, with nothing else altered.
Writes "true" or "false" to --page-changed-file so the workflow knows whether
to compile the page as MDX.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mintlify_entry as me  # noqa: E402

REQUIRED_STATE_KEYS = ['last_entry_date', 'cutoff_sha', 'changelog_path']
BLOCK = re.compile(r'<Update\b[^\n]*>\n.*?\n</Update>', re.S)


def fail(msg):
    print(f'::error::{msg}')
    sys.exit(1)


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True)


def at_base(base, path):
    r = git('show', f'{base}:{path}')
    return r.stdout if r.returncode == 0 else None


def split_page(text, where):
    if text.count(me.MARKER) != 1:
        fail(f'{where}: the marker {me.MARKER} must appear exactly once')
    head, body = text.split(me.MARKER, 1)
    blocks = BLOCK.findall(body)
    leftover = BLOCK.sub('', body).strip()
    if leftover:
        fail(f'{where}: only <Update> blocks may follow the marker; found: {leftover[:120]!r}')
    return head, blocks


def label_of(block):
    m = re.search(r'\blabel="([^"]*)"', block.split('\n', 1)[0])
    return m.group(1) if m else ''


def check_blocks(blocks, where):
    labels = []
    for b in blocks:
        lab = label_of(b)
        try:
            d = dt.date.fromisoformat(lab)
        except ValueError:
            fail(f'{where}: entry label "{lab}" is not a YYYY-MM-DD date')
        if d.isoweekday() != 7:
            fail(f'{where}: entry label {lab} is not a Sunday')
        print(f'checking entry {lab}')
        me.check_draft(b.rstrip('\n') + '\n', lab)  # exits non-zero with a message on failure
        labels.append(lab)
    if len(set(labels)) != len(labels):
        fail(f'{where}: duplicate entry labels {labels}')
    if labels != sorted(labels, reverse=True):
        fail(f'{where}: entries must be newest first, found {labels}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--head-ref', default='')
    ap.add_argument('--page-changed-file')
    a = ap.parse_args()

    def page_changed(v):
        if a.page_changed_file:
            open(a.page_changed_file, 'w').write('true' if v else 'false')

    try:
        state = json.load(open('.changelog/state.json'))
        json.load(open('.changelog/held-items.json'))
    except (OSError, json.JSONDecodeError) as e:
        fail(f'.changelog state files missing or invalid: {e}')
    missing = [k for k in REQUIRED_STATE_KEYS if k not in state]
    if missing:
        fail(f'.changelog/state.json is missing {missing}')
    page = state['changelog_path']
    if not re.fullmatch(r'[A-Za-z0-9._/-]+\.mdx', page) or page.startswith('/') or '..' in page:
        fail(f'changelog_path must be a repo-relative .mdx path, got {page!r}')

    r = git('diff', '--name-only', f'{a.base}...HEAD')
    if r.returncode != 0:
        r = git('diff', '--name-only', a.base, 'HEAD')
    if r.returncode != 0:
        fail(f'git diff against {a.base} failed: {r.stderr.strip()}')
    changed = [p for p in r.stdout.split('\n') if p]
    ours = [p for p in changed if p == page or p.startswith('.changelog/')]
    if not ours:
        print('No change log files changed; nothing to check.')
        page_changed(False)
        return

    if a.head_ref.startswith('changelog/'):
        outside = [p for p in changed if p not in ours]
        if outside:
            fail(f'changelog/* branches may change only {page} and .changelog/; also changed: {outside}')

    if not os.path.exists(page):
        fail(f'change log page {page} not found')
    head_text = open(page, encoding='utf-8').read()
    header, blocks = split_page(head_text, page)
    check_blocks(blocks, page)

    if a.head_ref.startswith('changelog/') and page in changed:
        base_text = at_base(a.base, page)
        if base_text is not None:
            b_header, b_blocks = split_page(base_text, f'{page} on the base branch')
            if b_header != header:
                fail('changelog/* branches must not change anything above the marker')
            if len(blocks) != len(b_blocks) + 1 or blocks[1:] != b_blocks:
                fail('changelog/* branches may only add one new entry at the top; existing entries must stay unchanged')

    print(f'Change log OK: {len(blocks)} entries on {page}.')
    page_changed(page in changed)


if __name__ == '__main__':
    main()
