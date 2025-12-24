---
title: Alteryx RegEx Tool > Prophecy Regex Gem (Analysts)
id: alteryx-regex-tool
sidebar_label: RegEx Tool
description: Mapping between Alteryx’s RegEx Tool and Prophecy’s Regex Gem
tags: [alteryx, regex, analyst, parse, match, replace, tokenize]
---

The Alteryx [RegEx tool](https://help.alteryx.com/current/en/designer/tools/parse/regex-tool.html) applies regular-expression logic to text fields in order to detect, extract, split, or transform string values. It supports four modes—Match, Parse, Replace, and Tokenize—each of which produces different output structures depending on the operation.

Prophecy implements this functionality through the [Regex gem](/data-analysis/gems/parse/regex). The gem supports the same four operations and applies regex logic across the input dataset, producing a single output dataset whose schema depends on the selected mode and configuration.

## Automated migration results

When Import detects an Alteryx RegEx tool:

- It generates a **Regex** gem in Prophecy.
- The selected Alteryx operation (Match, Parse, Replace, or Tokenize) is mapped directly to the corresponding Regex gem mode.
- The regex pattern is copied verbatim.
- Capture groups are expanded into output columns when using **Parse** mode.
- Replace operations are implemented as appended columns rather than in-place overwrites.

## Manually replicate in Prophecy

To reproduce Alteryx RegEx behavior manually:

1. Add a **Regex** gem to the canvas.
2. Select the **Mode** that matches the Alteryx configuration:
   - Match
   - Parse
   - Replace
   - Tokenize
3. Specify the input column and regex pattern.
4. Configure output columns (for Parse, Replace, or Tokenize) as needed.

The Regex gem runs SQL-backed regex expressions under the hood but exposes configuration through a low-code interface.

## Configuration options

### In Alteryx (RegEx tool)

Configure the tool by selecting:

- **Operation**: Match, Parse, Replace, or Tokenize
- **Field**: Input text column
- **Regular Expression**: Perl-compatible regex pattern
- **Case sensitivity**: Optional “Case Insensitive” toggle
- **Replacement string** (Replace mode only)
- **Output fields**: Automatically created from capture groups (Parse / Tokenize)

### In Prophecy (Regex gem)

Configure the gem with:

- **Mode**: Match, Parse, Replace, or Tokenize
- **Input column**
- **Regex pattern**
- **Case-insensitive matching** toggle
- **Output column configuration**:
  - Capture groups explicitly listed and named (Parse)
  - New column for replaced values (Replace)
  - Split to columns or rows (Tokenize)

Options

- **Match**
  - Alteryx outputs a Boolean (`True` / `False`)
  - Prophecy outputs an integer flag (`1` / `0`)
- **Parse**
  - Capture groups become separate output columns in both tools
- **Replace**
  - `$1`, `$2`, etc. supported in both tools
  - Prophecy appends a new column by default
- **Tokenize**
  - Alteryx splits into columns only
  - Prophecy supports split to **columns** or **rows**

## Output behavior

- **Alteryx** output structure varies by mode and may include multiple output anchors.
- **Prophecy** always produces a single output dataset (`out`) with added or expanded columns depending on the selected operation.
- Field data types in Prophecy are explicitly configurable for parsed outputs.

## Known caveats

- **Boolean vs numeric flags:** Match results differ in type (Boolean vs 1/0).
- **Overwrite behavior:** Replace operations append new columns in Prophecy; Alteryx workflows may overwrite fields.
- **Tokenization shape:** Only Prophecy supports row-based tokenization.
- **Invalid patterns:** Regex compilation errors surface at validation or SQL-compile time in Prophecy.
- **Null handling:** Null input values are not evaluated by regex logic unless explicitly handled upstream.

## Example

### Goal

Extract phone-number components from a string like `"(212) 555-0199"`.

### Alteryx RegEx tool (Parse)

- **Regular Expression**:
  `(\d{3})[)\s-](\d{3})[-](\d{4})`
- **Resulting fields**:
  `AreaCode`, `Exchange`, `Number`

### Prophecy equivalent (Regex gem)

- **Mode**: Parse
- **Regex**:
  `(\d{3})[)\s-](\d{3})[-](\d{4})`
- **Configured outputs**:

| Capture group | Column name | Type   |
| ------------- | ----------- | ------ |
| `$1`          | area_code   | String |
| `$2`          | exchange    | String |
| `$3`          | number      | String |

The resulting dataset matches the logical output of the Alteryx workflow, with explicit column naming and typing handled in the Regex gem configuration.
