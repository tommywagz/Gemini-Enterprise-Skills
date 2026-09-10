---
name: real-estate-floorplan
description: "Orchestrates a two-stage spatial research and architectural drafting pipeline using Model Context Protocol (MCP) servers: researching property floor plans across real estate listing platforms (Zillow, Apartments.com, Redfin), and programmatically authoring vector CAD layouts via Floor Builder and CAD MCP servers. TRIGGER when users ask to 'research real estate floor plans', 'extract floor plan from Zillow, Redfin, or Apartments.com', 'generate CAD floor plan from property listing', 'draw floor plan with Floor Builder MCP', 'convert listing blueprint to DXF/SVG', or route queries through real estate research and CAD drafting MCP servers. DO NOT TRIGGER for property price estimation or mortgage calculations, general 3D video game level modeling, or mechanical CAD drafting unrelated to residential architecture."
version: 1.0.0
author: Actual Agentic Solutions
tags: [real-estate, floorplan, mcp, cad, drafting, dxf, svg, zillow, redfin, apartments]
license: Apache-2.0
compatibility: "MCP Specification >= 1.0, Python >= 3.12"
metadata: {}
---

# Real Estate Floor Plan Plugin Skill

## Overview
This skill implements a robust, two-stage spatial intelligence and architectural drafting pipeline using the Model Context Protocol (MCP). It allows autonomous agents to search property details, extract layout information from real-estate listing platforms (Zillow, Apartments.com, Redfin), synthesize these inputs into a canonical Floor Plan JSON Specification, and drive procedural drafting and CAD file generation via Floor Builder and CAD/BIM MCP servers.

### Architectural Two-Stage Pipeline

```
  Stage 1: DISCOVERY & EXTRACTION                Stage 2: AUTHORING & VERIFICATION
+---------------------------------+             +----------------------------------+
|   Zillow / Apartments.com /     |             |  Canonical Floor Plan Schema    |
|   Redfin MCP Servers            |             |  (Coordinates, Portals, Fixtures)|
+----------------+----------------+             +----------------+-----------------+
                 |                                               |
                 | (Listing Spatial Data)                        | (Drives Procedural CAD)
                 v                                               v
+----------------+----------------+             +----------------+-----------------+
|   normalize_listing_             |  =======>   |   validate_geometric_closure.py  |
|   spatial_data.py               |             |   (Verifies loops & clearances)  |
+---------------------------------+             +----------------+-----------------+
                                                                 |
                                                                 v
                                                +----------------+-----------------+
                                                |  Floor Builder / CAD MCP Server  |
                                                |  (Generates DXF/SVG/DWG files)   |
                                                +----------------------------------+
```

---

## Prerequisites
- **Python**: `>= 3.12`
- **Libraries**: `pytest`, `shapely`, `dxfwrite` (or `ezdxf` for production scripts).
- **MCP Servers Available**:
  - `zillow-mcp-server`
  - `apartments-mcp-server`
  - `redfin-mcp-server`
  - `floor-builder-mcp-server`
  - `cad-bim-mcp-server`

---

## Workflow

### Step 1: Query Listing Portals (Discovery)
When a property address or listing reference is provided, query the appropriate MCP toolchain:
- **Zillow MCP**: Use `get_property_by_address` or `get_property_by_zpid` to retrieve gross living area (GLA), lot shape, room counts, and URLs of floor plans or sketch media.
- **Redfin MCP**: Use `get_mls_record` to check municipal records, permit schematics, and tour galleries.
- **Apartments.com MCP**: Use `get_community_floorplans` to extract standardized multi-family floor plan configurations (Studio, 1B1B, etc.).

Reconcile dimensional data across multiple listing sources, flagging discrepancies in reported square footage or room boundaries.

### Step 2: Normalize Spatial Metadata
Pass the unstructured dimensional descriptions retrieved from Step 1 into the `scripts/normalize_listing_spatial_data.py` helper script. This tool:
1. Parses standard room name-dimension strings (e.g., "Primary Bedroom: 14ft x 16ft").
2. Approximates room boundary coordinates to fit within the overall gross living area.
3. Produces a payload conforming exactly to the canonical `assets/floorplan_spec_schema.json` schema.

### Step 3: Validate Spatial Integrity
Before drafting, execute the verification checks using `scripts/validate_geometric_closure.py`:
- **Closed Polygon Loops**: Ensure every room boundary polygon starts and ends at the exact same coordinate (no leaking room boundaries).
- **Clearance & Connectivity**: Verify that door and window portals align properly with room boundaries, and check that ingress/egress clearance guidelines are maintained.
- **Area Variance**: Compare the sum of calculated polygon areas against the listing-reported GLA. Flag variances greater than 10% as warning notifications.

### Step 4: Procedural Layout Construction
Invoke the **Floor Builder MCP** server tools:
- `create_room_polygon`: Construct 2D enclosures.
- `snap_adjacent_walls`: Automatically align shared boundaries between neighboring rooms (e.g., Bedroom and Hallway) to remove microscopic overlapping areas.
- `insert_portal`: Place door swings and window frames with clearances at coordinates matching the normalized schema.
- `add_annotation`: Stamp calculated dimension callouts and labels (e.g., "Kitchen 12' x 10'") onto the canvas.

### Step 5: Export CAD Artifacts
Drive precision drafting via the **CAD / BIM MCP** server to build layered vector geometry:
- Organize vectors onto standard layers according to standard AIA CAD guidelines (`WALLS`, `DOORS`, `WINDOWS`, `DIMENSIONS`, `FIXTURES`, `TEXT`).
- Use block definitions from `assets/standard_cad_symbols.dxf` to place doors, windows, and fixture blocks.
- Export to `.dxf` (Drawing Exchange Format), `.svg` (for immediate web rendering/previewing), or `.dwg`.

---

## Gotchas and Edge Cases
- **Non-Rectangular Rooms**: Standard listings describe rooms as simple bounding rectangles (e.g., "12 x 15"). If the home has bay windows or L-shaped layouts, look up permit or SVG sketches to refine coordinates; do not assume all rooms are perfect rectangles if the total area does not balance.
- **Micro-gaps**: When placing rooms next to each other, a gap of 0.01 inches will break CAD hatching and area calculations. Always use the `snap_adjacent_walls` tool rather than raw coordinates.
- **Door Swings**: Ensure door swing arcs do not collide with adjacent walls, cabinets, or toilets. The validation script checks clearance zones.
