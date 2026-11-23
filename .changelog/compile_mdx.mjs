// Compile one MDX page to catch syntax errors Mintlify would hit at build time.
// The page is excluded from the build by .mintignore while hidden, so nothing else checks it.
// Usage: node compile_mdx.mjs <page.mdx> [repo-relative path for error annotations]
import { readFile } from 'node:fs/promises';
import { compile } from '@mdx-js/mdx';

const path = process.argv[2];
const shown = process.argv[3] ?? path;
let text = await readFile(path, 'utf8');
text = text.replace(/^---\n[\s\S]*?\n---\n/, (fm) => '\n'.repeat(fm.split('\n').length - 1)); // drop frontmatter, keep line numbers
try {
  await compile(text);
  console.log(`MDX OK: ${shown}`);
} catch (e) {
  const pos = e.place?.start ?? e.place;
  const where = pos?.line ? `,line=${pos.line},col=${pos.column ?? 1}` : '';
  console.log(`::error file=${shown}${where}::${e.reason ?? e.message}`);
  process.exit(1);
}
