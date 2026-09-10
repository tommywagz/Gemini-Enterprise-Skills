# Floor Builder & CAD MCP Tool Signatures

## Contents
- Floor Builder MCP Server (illustrative tool contract)
- CAD / BIM MCP Server (illustrative tool contract)
- Call ordering and dependency rules

Both servers below follow the same MCP `tools/list` / `tools/call` contract
described in `mcp_realestate_servers.md` — confirm the live schema with
`tools/list` before trusting an argument name here verbatim. These are the
canonical, illustrative shapes this skill's workflow is written against.

## Floor Builder MCP Server (illustrative tool contract)

Procedural 2D/2.5D layout generation — consumes the canonical Floor Plan
Specification (`assets/floorplan_spec_schema.json`) and produces a snapped,
annotated layout ready for CAD export.

| Tool | Arguments | Effect |
|---|---|---|
| `create_room_polygon` | `{room_id, polygon: [[x,y],...], ceiling_height?}` | Registers one room's boundary loop |
| `snap_adjacent_walls` | `{tolerance_inches?: number}` (default `0.5`) | Aligns shared edges between rooms whose boundaries are within `tolerance_inches` of each other, eliminating micro-gaps and overlaps |
| `insert_portal` | `{portal_id, type, width, position, orientation_angle, connects_rooms}` | Places a door/window cutout and, for doors, the swing arc geometry |
| `add_annotation` | `{room_id, text, position?}` | Stamps a dimension/label callout; if `position` is omitted, centers it in the room's bounding box |
| `generate_layout` | `{}` | Finalizes the current session's rooms/portals into a single layout graph; call once after all `create_room_polygon` and `insert_portal` calls |

**Call order matters:** `snap_adjacent_walls` must run *after* all
`create_room_polygon` calls for the layout but *before* `insert_portal` —
inserting a portal against an unsnapped wall bakes the micro-gap into the
door frame geometry, and `validate_geometric_closure.py` will report a false
clearance violation that no CAD-side fix can correct without re-running this
step.

## CAD / BIM MCP Server (illustrative tool contract)

Takes the finalized layout graph from `generate_layout` and produces layered
vector geometry in industry-standard exchange formats.

| Tool | Arguments | Effect |
|---|---|---|
| `create_layer` | `{name, color?, lineweight?}` | Declares a named CAD layer (see `architectural_cad_standards.md` for the naming convention to use) |
| `add_polyline` | `{layer, points: [[x,y],...], closed: bool}` | Draws vector geometry onto a layer |
| `add_block_reference` | `{layer, block_name, insertion_point, rotation?, scale?}` | Places a symbol block (door swing, window, fixture) — `block_name` must be one of the names defined in `assets/standard_cad_symbols.dxf`'s block table (currently `DOOR_SWING`, `WINDOW_SYMBOL`, `SINK_SYMBOL` — see `architectural_cad_standards.md` for substitution rules when no exact block exists) |
| `add_dimension` | `{layer, start, end, text?}` | Draws a dimension line with extension lines and text |
| `export` | `{format: "dxf"|"svg"|"dwg", path}` | Serializes all layers/geometry to the requested format |

**Layer discipline:** call `create_layer` for every layer in
`architectural_cad_standards.md`'s table before the first `add_polyline` —
some CAD MCP server implementations silently drop geometry addressed to an
undeclared layer instead of erroring, which produces a DXF that looks
complete in a naive line-count check but is missing whole categories of
elements. Verify layer population by re-querying entity counts per layer
after `export`, not just checking the export call's return status.

## Call ordering and dependency rules

The full Stage 2 pipeline, in required order:

1. `create_room_polygon` for every room in the spec.
2. `snap_adjacent_walls` once, across the whole layout.
3. `insert_portal` for every portal in the spec (after snapping).
4. `add_annotation` for room labels/dimensions.
5. `generate_layout` to finalize.
6. `create_layer` for each required AIA-convention layer.
7. `add_polyline` / `add_block_reference` / `add_dimension`, addressed to the
   layers from step 6.
8. `export` to the requested format(s).

Run `scripts/validate_geometric_closure.py` against the Floor Plan
Specification **before** step 1 — catching an unclosed polygon before it
enters the Floor Builder session is cheap; catching it after `export` means
re-running the entire Stage 2 pipeline.
</content>
