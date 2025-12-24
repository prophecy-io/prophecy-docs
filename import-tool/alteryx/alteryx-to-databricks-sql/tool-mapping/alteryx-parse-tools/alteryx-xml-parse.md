---
title: Alteryx XML Parse Tool > Prophecy XML Parse gem
id: alteryx-xml-parse
sidebar_label: XML Parse Tool
description: Mapping between Alteryx’s XML Parse Tool and Prophecy’s XML Parse Gem
tags: [alteryx, xml, parse, semi-structured, analyst, import]
---

The [Alteryx XML Parse tool](https://help.alteryx.com/current/en/designer/tools/parse/xml-parse-tool.html) extracts structured data from XML content stored in a field. It allows users to select which XML elements to parse, control whether child values or raw XML are returned, and determine how parsing errors are handled.

Prophecy implements this functionality through the [XMLParse gem](/data-analysis/gems/parse/xml-parse.mdx).

## Automated migration results

When Import detects an Alteryx XML Parse tool:

- It generates a Script gem containing XML parsing logic.
- The generated script reproduces the XML extraction behavior inferred from the Alteryx configuration.

:::note
Alteryx's XML parsing works differently than Prophecy's XMLParse gem, which is why the XML Parse tool imports as a Script gem.
:::

## Manually replicate in Prophecy

For manually-created workflows, Prophecy recommends using the **XMLParse** gem:

1. Add an **XMLParse** gem to the canvas.
2. Select the column containing XML data.
3. Select parsing method:
   - Parse from sample record. Prophecy uses the schema from the sample record you provide.
   - Parse from schema. Prophecy uses the schema you provide in the form of a schema struct.

## Configuration options

### In Alteryx (XML Parse tool)

- Select field containing XML-formatted string.
- Choose to keep or drop the original XML column.
- Choose XML element to parse: Root, Auto Detect Child, Specific Child Name
- Choose additional options:
  - Return Child Values
  - Return Outer XML
  - Ignore XML Errors and Continue

### In Prophecy (XMLParse gem)

Configure the gem with:

- Input column containing XML text
- Select parsing method:
  - Parse from sample record. Prophecy uses the schema from the sample record you provide.
  - Parse from schema. Prophecy uses the schema you provide in the form of a schema struct.

## Output behavior

Alteryx outputs a flattened, columnar dataset derived from the selected XML elements, optionally retaining the original XML field.

Prophecy outputs all of the input columns and the parsed content as a struct data type.

## Known caveats

- Automated migration uses a Script gem; users should validate results when replacing it with the XMLParse gem.
- Prophecy requires explicit output column configuration; schemas are not implicitly inferred.
- Invalid XML may fail parsing.

## Example

### Alteryx XML Parse example

Goal: Parse `<Order>` elements from XML stored in the `order_xml` field.

Configuration:

- Field: `order_xml`
- Include XML field in output: No
- XML element to parse: **Specific Child Name**
- Child name: `Order`
- Options: **Return Child Values**

Result: One output column per child element under `<Order>`.

### Prophecy equivalent (XMLParse gem)

Configuration:

- Input column: `order_xml`
- Parsed fields: `OrderID` `CustomerID` `OrderDate`
