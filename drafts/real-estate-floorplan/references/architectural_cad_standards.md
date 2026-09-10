# Architectural CAD Standards Reference

This document outlines the standard layering naming, line weights, color index values, and line types utilized in standard architectural drafting, aligning with the American Institute of Architects (AIA) CAD Layer Guidelines. 

These standards ensure consistency, readability, and compatibility when exporting to vector formats (DXF, SVG, DWG) via the CAD / BIM MCP server.

---

## 1. AIA Standard Layering Table

| Layer Name | Color Index (ACI) | Hex Code | Line Weight (mm) | Line Type | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`WALLS`** (A-WALL) | 1 (Red) | `#FF0000` | 0.50 mm (Thick) | `CONTINUOUS` | Main structural walls, interior partitions, load-bearing walls. |
| **`DOORS`** (A-DOOR) | 2 (Yellow) | `#FFFF00` | 0.25 mm (Thin) | `CONTINUOUS` | Door frames, leaves, swings, sliding door tracks. |
| **`WINDOWS`** (A-GLAZ) | 3 (Green) | `#00FF00` | 0.25 mm (Thin) | `CONTINUOUS` | Window glass frames, sills, and glazing. |
| **`FIXTURES`** (A-EQPM) | 4 (Cyan) | `#00FFFF` | 0.18 mm (Extra-Thin) | `CONTINUOUS` | Plumbing fixtures, kitchen appliances, cabinets, counters. |
| **`DIMENSIONS`** (A-ANNO-DIM) | 5 (Blue) | `#0000FF` | 0.13 mm (Extra-Thin) | `CONTINUOUS` | Dimension lines, ticks, witness lines, boundary limits. |
| **`TEXT`** (A-ANNO-TEXT) | 6 (Magenta) | `#FF00FF` | 0.25 mm (Thin) | `CONTINUOUS` | Room labels, tags, notes, square footage text annotations. |

---

## 2. Line Weight Application Guide

To maintain excellent legibility when plotting, line weights must follow a hierarchy of depth:
- **Major Profile (0.50mm / 0.020")**: Use for cut boundaries (walls that partition the building structure). This is the thickest line on a floor plan.
- **Minor Details (0.25mm / 0.010")**: Use for portals (doors/windows) and annotations (room labels). This shows operable or architectural fittings.
- **Background Symbols (0.18mm / 0.007")**: Use for furniture, plumbing fixtures, countertops, and appliances. These are non-structural elements that sit on the floor.
- **Reference & Utilities (0.13mm / 0.005")**: Use for dimension ticks/lines, centerlines, and leader lines.

---

## 3. Block Symbol Library Conventions

When placing blocks (inserts) from the library (e.g., `assets/standard_cad_symbols.dxf`), blocks must be drawn on Layer `0` (ByBlock/ByLayer settings) so that they inherit the layer characteristics of the layer they are placed into:
- **`DOOR_SWING`**: Place on `DOORS` layer. It should contain:
  - Door jamb width (typically 4-6 inches thick).
  - Main door panel thickness (typically 1.5 - 2 inches).
  - Swing arc (90-degree swing circle portion).
- **`WINDOW_SYMBOL`**: Place on `WINDOWS` layer. It should represent double line glazing with frame ends.
- **`SINK_SYMBOL`**: Place on `FIXTURES` layer. Represents standard kitchen and vanity washbasins.
- **`TOILET_SYMBOL`**: Place on `FIXTURES` layer. Represents standard water closets and tanks.
