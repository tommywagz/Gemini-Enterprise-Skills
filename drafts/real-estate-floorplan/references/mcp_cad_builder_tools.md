# Floor Builder & CAD MCP Tool Reference

This reference documents the signatures, parameters, schemas, and behavior for the Floor Builder and CAD/BIM Model Context Protocol (MCP) servers. These tools are used in Stage 2 of the pipeline to construct vector assets and generate standard architectural exports.

---

## 1. Floor Builder MCP Server

The Floor Builder MCP server handles procedural room layout generation, geometric alignment, wall snapping, and structural/door clearance adjustments.

### Tool Signatures

#### `create_room_polygon`
Constructs a room enclosure representing a 2D closed loop coordinate polygon.
- **Parameters**:
  - `room_id` (string, required): Unique identifier for the room.
  - `name` (string, required): Label of the room (e.g. "Primary Bedroom").
  - `dimensions` (array of numbers, optional): Width and length in units (e.g. `[12, 14]`) for quick auto-generation from center.
  - `polygon` (array of 2D coordinates, optional): Direct array of `[x, y]` coordinate pairs defining vertices (e.g., `[[0,0], [12,0], [12,14], [0,14], [0,0]]`).
- **Output**:
  ```json
  {
    "status": "success",
    "room_id": "room_01",
    "polygon": [[0.0, 0.0], [12.0, 0.0], [12.0, 14.0], [0.0, 14.0], [0.0, 0.0]],
    "area_sqft": 168.0
  }
  ```

#### `snap_adjacent_walls`
Snaps adjacent wall polylines together within a threshold tolerance to ensure clean geometry and prevent microscopic gaps.
- **Parameters**:
  - `room_id_primary` (string, required): Anchor room.
  - `room_id_secondary` (string, required): Room to snap to primary.
  - `tolerance` (number, optional): Maximum distance to trigger a snap. Defaults to `0.2` (inches/feet units).
- **Output**:
  ```json
  {
    "status": "success",
    "snapped_edges": 1,
    "adjusted_vertices_count": 2
  }
  ```

#### `insert_portal`
Places a door, window, or opening into an existing wall edge.
- **Parameters**:
  - `portal_type` (string, required): Type of opening (`door_single_swing`, `window_double_hung`, `open_archway`).
  - `width` (number, required): Width of the portal.
  - `position` (array of 2 numbers, required): Exact center `[x, y]` coordinates.
  - `orientation_angle` (number, required): Orientation rotation in degrees.
  - `connects_rooms` (array of strings, optional): ID of room(s) connected.
- **Output**:
  ```json
  {
    "portal_id": "port_01",
    "status": "placed",
    "clearance_check": "passed"
  }
  ```

---

## 2. CAD / BIM MCP Server

The CAD / BIM MCP server translates the composite Floor Plan Specification into standard vector CAD documents and exports them.

### Tool Signatures

#### `initialize_drawing`
Initializes a new CAD vector canvas with standard layer sheets and metadata.
- **Parameters**:
  - `units` (string, optional): `"feet"` or `"meters"`. Defaults to `"feet"`.
  - `title` (string, optional): "Property Floor Plan Layout".
- **Output**:
  ```json
  {
    "drawing_id": "dwg_2026_09",
    "status": "initialized",
    "layers_created": ["WALLS", "DOORS", "WINDOWS", "DIMENSIONS", "FIXTURES", "TEXT"]
  }
  ```

#### `add_vector_geometry`
Draws points, lines, polylines, arcs, or blocks onto a specified layer.
- **Parameters**:
  - `drawing_id` (string, required): ID returned by `initialize_drawing`.
  - `layer` (string, required): Layer name (must match standard AIA naming: `WALLS`, `DOORS`, `WINDOWS`, `DIMENSIONS`, `FIXTURES`, `TEXT`).
  - `geometry_type` (string, required): `"LINE"`, `"POLYLINE"`, `"ARC"`, `"INSERT_BLOCK"`.
  - `coordinates` (array, required): Vertex coordinates corresponding to geometry type.
  - `block_name` (string, optional): The name of a standard block if type is `"INSERT_BLOCK"`.
- **Output**:
  ```json
  {
    "status": "added",
    "geometry_id": "geom_102"
  }
  ```

#### `export_drawing`
Exports the drawing session into a standard portable vector file.
- **Parameters**:
  - `drawing_id` (string, required): Drawing ID.
  - `format` (string, required): Export format (`"DXF"`, `"SVG"`, `"DWG"`).
- **Output**:
  ```json
  {
    "status": "exported",
    "format": "DXF",
    "file_size_bytes": 10482,
    "download_url": "http://localhost:3000/exports/dwg_2026_09.dxf",
    "file_path": "/home/tow73/AAS/skills-worker-creator/exports/dwg_2026_09.dxf"
  }
  ```
