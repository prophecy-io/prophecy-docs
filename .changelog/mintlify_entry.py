#!/usr/bin/env python3
"""Check a weekly change log draft (one Mintlify <Update> block) and insert it into the change log page.

Usage:
  mintlify_entry.py check DRAFT END_DATE          validate the draft only
  mintlify_entry.py insert PAGE DRAFT END_DATE    validate, then insert below the marker in PAGE (in place)

The page must contain the marker line below exactly once, directly above the newest entry:
  {/* changelog-entries */}
"""
import json
import re
import sys

MARKER = '{/* changelog-entries */}'
SUBSECTIONS = ['New features', 'Improvements', 'Bug fixes']  # tags must match the ### subsections present


def fail(msg):
    print(f'entry check failed: {msg}', file=sys.stderr)
    sys.exit(1)


def strip_code(text):
    """Remove fenced and inline code, where MDX special characters are safe."""
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    return re.sub(r'`[^`\n]*`', '', text)


def read_draft(path):
    return open(path, encoding='utf-8').read().strip('\n') + '\n'


def check_draft(e, end):
    lines = e.rstrip('\n').split('\n')
    head, last = lines[0], lines[-1].strip()

    if not re.fullmatch(r'<Update\s.*>', head.strip()):
        fail('first line must be the whole opening <Update ...> tag')
    if last != '</Update>':
        fail('last line must be </Update>')
    if e.count('<Update') != 1 or e.count('</Update>') != 1:
        fail('draft must contain exactly one Update block')

    m = re.search(r'\blabel="([^"]*)"', head)
    if not m or m.group(1) != end:
        fail(f'label must be "{end}" (the covered week\'s Sunday, YYYY-MM-DD)')

    t = re.search(r'\btags=\{(\[[^\]]*\])\}', head)
    if not t:
        fail('opening tag needs tags={["..."]}')
    try:
        tags = json.loads(t.group(1))
    except json.JSONDecodeError:
        fail('tags must be a list of double-quoted strings')

    body = '\n'.join(lines[1:-1])

    if re.search(r'^# ', body, re.M):
        fail('no # headings inside an entry; use ## for the headline')
    heads = re.findall(r'^## (.+)$', body, re.M)
    if len(heads) != 1:
        fail(f'need exactly one ## headline, found {len(heads)}')
    if re.search(r'\d{4}-\d{2}-\d{2}|^Week of', heads[0]):
        fail('## must be a headline, not a date')

    subs = re.findall(r'^### (.+)$', body, re.M)
    if not subs or any(s not in SUBSECTIONS for s in subs):
        fail(f'subsections must be from {SUBSECTIONS}, found {subs}')
    if len(set(subs)) != len(subs):
        fail(f'duplicate subsection in {subs}')
    if sorted(tags) != sorted(subs):
        fail(f'tags {tags} must match subsections {subs}')

    prose = strip_code(body)
    for target in re.findall(r'\]\(([^)\s]+)', prose):
        if not (target.startswith('https://') or target.startswith('/')):
            fail(f'link must be root-relative (/page) or https://, got {target}')
        if re.search(r'\.mdx?(#|$)', target):
            fail(f'link must not include the .md/.mdx extension: {target}')
    if re.search(r'<[A-Za-z/!]', prose):
        fail('raw HTML/JSX tag in prose; wrap literal tags in backticks')
    if re.search(r'[{}]', prose):
        fail('curly brace in prose breaks MDX; wrap it in backticks')


def insert(page_path, e, end):
    page = open(page_path, encoding='utf-8').read()
    if f'label="{end}"' in page:
        fail(f'an entry labeled {end} is already on the page')
    if page.count(MARKER) != 1:
        fail(f'marker {MARKER} must appear exactly once in {page_path}')
    i = page.index(MARKER) + len(MARKER)
    new = page[:i] + '\n\n' + e.rstrip('\n') + page[i:]
    if new.replace('\n\n' + e.rstrip('\n'), '', 1) != page:
        fail('existing content altered')
    open(page_path, 'w', encoding='utf-8').write(new)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == 'check':
        check_draft(read_draft(a[1]), a[2])
        print('draft OK')
    elif len(a) == 4 and a[0] == 'insert':
        e = read_draft(a[2])
        check_draft(e, a[3])
        insert(a[1], e, a[3])
        print(f'inserted entry {a[3]} into {a[1]}')
    else:
        sys.exit(__doc__)
