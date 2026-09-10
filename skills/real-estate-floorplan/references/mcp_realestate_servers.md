# Real Estate Research MCP Servers

## Contents
- MCP tool-call fundamentals (grounding)
- Zillow MCP Server (illustrative tool contract)
- Apartments.com MCP Server (illustrative tool contract)
- Redfin MCP Server (illustrative tool contract)
- Multi-source reconciliation rules

## MCP tool-call fundamentals (grounding)

The Model Context Protocol (MCP) defines a JSON-RPC transport between a
client (the agent runtime) and a server. Every server, regardless of what it
wraps, exposes the same two calls that matter here:

- `tools/list` — returns each tool's `name`, `description`, and
  `inputSchema` (a JSON Schema object). This is the **authoritative** source
  of truth for what a given deployment actually accepts — schemas drift
  between server versions.
- `tools/call` — invokes `{name, arguments}` and returns a `content` array
  (typically `TextContent` blocks with JSON payloads) plus an `isError` flag.
  A failing tool answers with `isError: true` rather than raising a
  transport-level exception — check that flag explicitly, don't assume a
  clean return means success.

**Before trusting any tool name below**, call `tools/list` against the
actual configured server and diff it against this file. The tool names,
argument shapes, and response fields documented here are the illustrative,
canonical contract this skill is designed against — treat them as the
expected shape to map real responses onto, not a guarantee that a given
deployment matches byte-for-byte. If a real server's schema differs, adapt
the mapping in Step 1 of the SKILL.md workflow rather than silently
assuming your normalization script will paper over it.

## Zillow MCP Server (illustrative tool contract)

| Tool | Arguments | Returns |
|---|---|---|
| `get_property_by_address` | `{address: string}` | Property record (see below) |
| `get_property_by_zpid` | `{zpid: string}` | Property record |
| `get_floorplan_media` | `{zpid: string}` | Array of `{url, media_type, caption}` — floor plan sketches, if the listing has any |

Property record fields to extract for Step 2 normalization:
- `address`, `zpid`, `lot_size_sqft`, `gross_living_area_sqft` (GLA — the
  reported total, used as `metadata.total_square_footage`)
- `architectural_style`, `year_built`
- `rooms`: array of `{name, dimensions_text}` where `dimensions_text` is a
  free-text string like `"14 x 16"` or `"14'2\" x 16'0\""` — **not**
  pre-parsed coordinates. `normalize_listing_spatial_data.py` parses this.
- `room_count`, `bedroom_count`, `bathroom_count` (sanity-check against the
  `rooms` array length; a mismatch usually means the listing groups rooms
  Zillow doesn't itemize, e.g. closets)

## Apartments.com MCP Server (illustrative tool contract)

Apartments.com describes **unit models**, not single physical units — a
"2B2B" model applies to every unit of that layout in the community.

| Tool | Arguments | Returns |
|---|---|---|
| `search_communities` | `{location: string, filters?: object}` | Array of `{community_id, name, address}` |
| `get_community_floorplans` | `{community_id: string}` | Array of unit models |

Each unit model returns:
- `model_name` (e.g. `"Studio"`, `"1B1B"`, `"2B2B Penthouse"`)
- `square_footage` (model-level average/typical, not per-unit exact)
- `bedroom_count`, `bathroom_count`
- `floorplan_image_url` — usually a rendered marketing floor plan image, not
  a to-scale CAD source. Treat dimensions extracted from it as approximate
  unless a `room_dimensions` array is also present on the response.
- `amenities`: unit-specific fixtures (in-unit washer/dryer, balcony) that
  map to the `fixtures` array in the canonical schema, not `rooms`.

**Gotcha:** because a model applies to many physical units, `square_footage`
is often a range or an average. When normalizing, record the reported value
as `metadata.total_square_footage` but flag in output notes that it is a
model-level figure, not a surveyed single-unit measurement — this changes
how much variance is acceptable in Step 3 validation.

## Redfin MCP Server (illustrative tool contract)

| Tool | Arguments | Returns |
|---|---|---|
| `get_mls_record` | `{mls_id: string}` OR `{address: string}` | MLS listing record |
| `get_permit_records` | `{address: string}` | Array of municipal permit filings |
| `get_tour_media` | `{listing_id: string}` | Array of `{url, media_type}` — walkthrough video, photo gallery, sketch |

Redfin's MLS record is the best source for **public permit schematics** —
official floor plans filed with a municipality, which are far more reliable
for exact wall placement than a marketing sketch. When `get_permit_records`
returns a schematic, prefer its dimensions over Zillow's free-text room
strings for any room where both sources disagree.

## Multi-source reconciliation rules

When two or more of the above return data for the same property:

1. **Square footage conflicts:** if Zillow's GLA and Redfin's MLS square
   footage differ by more than 5%, record both in `metadata` (add
   `reported_square_footage_by_source`) and surface the discrepancy in the
   Step 1 output rather than silently averaging them — an average can hide
   the more likely explanation (one source includes a finished basement,
   the other doesn't).
2. **Room count conflicts:** trust whichever source enumerates individual
   rooms with dimensions (Zillow `rooms`, Redfin permit schematic) over one
   that only reports aggregate `bedroom_count`/`bathroom_count`
   (Apartments.com model-level data).
3. **Missing floor plan media:** if none of the three sources return a
   `floorplan_media`/`get_tour_media` sketch, proceed with text-derived room
   dimensions only, and flag every room as `boundary_confidence: "estimated"`
   in the normalization output (see `normalize_listing_spatial_data.py`) so
   Step 3 validation treats a large variance as expected, not a bug.
</content>
