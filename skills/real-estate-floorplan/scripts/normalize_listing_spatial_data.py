#!/usr/bin/env python3
"""
normalize_listing_spatial_data.py

Converts unstructured real estate listing spatial data (address, gross area,
and raw room dimension strings) into a canonical JSON payload conforming to the
FloorPlanSpecification schema (floorplan_spec_schema.json).

Supported Room Dimension Formats:
- "Primary Bedroom: 14x16"
- "Kitchen: 12' 6\" x 10' 0\""
- "Living Room: 18 ft. x 15 ft."
- "Bath: 8.5 x 6"
"""

import argparse
import json
import re
import sys


def parse_dimensions(dim_string: str):
    """
    Parses various room dimension string formats and extracts (width, length) as floats.
    Returns (None, None) if parsing fails.
    """
    # Clean the string: replace double quotes, feet indicators, etc.
    cleaned = dim_string.lower().strip()
    
    # Try regex matching common patterns
    # Pattern 1: 14x16, 14.5x16.2, 14 x 16
    pattern_cross = r'([\d\.]+)\s*(?:x|by|\*)\s*([\d\.]+)'
    match = re.search(pattern_cross, cleaned)
    if match:
        try:
            return float(match.group(1)), float(match.group(2))
        except ValueError:
            pass

    # Pattern 2: 14' 6" x 10' 0" or 14ft x 10ft
    pattern_feet = r'([\d\.]+)\s*(?:ft|feet|\')?\s*[\d\.\"]*\s*(?:x|by)\s*([\d\.]+)\s*(?:ft|feet|\')?'
    match = re.search(pattern_feet, cleaned)
    if match:
        try:
            return float(match.group(1)), float(match.group(2))
        except ValueError:
            pass

    return None, None


def normalize_rooms(raw_rooms_str: str) -> list:
    """
    Parses a comma-separated list or semicolon-separated list of rooms.
    E.g. "Primary Bedroom: 14x16; Kitchen: 12x12; Bath: 8x6"
    """
    rooms = []
    # Split on semicolons or commas
    delimiters = re.compile(r'[;,]')
    parts = delimiters.split(raw_rooms_str)
    
    for part in parts:
        if not part.strip():
            continue
        
        # Split room name from dimensions
        if ":" in part:
            name, dims_str = part.split(":", 1)
        elif "-" in part:
            name, dims_str = part.split("-", 1)
        else:
            # Fallback if no colon/hyphen exists: try to extract dimensions from the end
            name = part
            dims_str = part
            
        name = name.strip()
        width, length = parse_dimensions(dims_str)
        
        if width and length:
            rooms.append({
                "name": name,
                "width": width,
                "length": length
            })
    return rooms


def layout_rooms(rooms: list) -> tuple:
    """
    Arranges parsed rooms sequentially on a 2D coordinate space.
    Ensures they are contiguous (sharing edges) rather than overlapping.
    Returns (placed_rooms, portals, fixtures)
    """
    placed_rooms = []
    portals = []
    fixtures = []
    
    current_x = 0.0
    current_y = 0.0
    
    for i, rm in enumerate(rooms):
        room_id = f"room_{i+1:02d}"
        w = rm["width"]
        h = rm["length"]
        
        # Define polygon coordinates as closed loop: [x, y]
        # Coordinates: bottom-left, bottom-right, top-right, top-left, bottom-left
        polygon = [
            [current_x, current_y],
            [current_x + w, current_y],
            [current_x + w, current_y + h],
            [current_x, current_y + h],
            [current_x, current_y]
        ]
        
        # Sequence of wall types matching the polygon edges
        # 5 coordinates = 4 segments
        wall_types = [
            "exterior_siding" if current_y == 0 else "interior_standard",
            "exterior_siding",
            "exterior_siding",
            "interior_standard" if current_x > 0 else "exterior_siding"
        ]
        
        placed_rooms.append({
            "id": room_id,
            "name": rm["name"],
            "ceiling_height": 9.0,
            "polygon": polygon,
            "wall_types": wall_types
        })
        
        # Add a default portal (door) connecting to adjacent rooms or exterior
        portal_id = f"port_{i+1:02d}"
        if i == 0:
            # Exterior main entry door on bottom wall of the first room
            portals.append({
                "id": portal_id,
                "type": "exterior_entry",
                "width": 3.0,
                "height": 6.8,
                "position": [current_x + (w / 2.0), current_y],
                "orientation_angle": 0.0,
                "connects_rooms": [room_id]
            })
        else:
            # Connecting interior door with previous room along the shared boundary
            portals.append({
                "id": portal_id,
                "type": "door_single_swing",
                "width": 2.8,
                "height": 6.8,
                "position": [current_x, current_y + (min(h, rooms[i-1]["length"]) / 2.0)],
                "orientation_angle": 90.0,
                "connects_rooms": [f"room_{i:02d}", room_id]
            })

        # Add windows (portals) on exterior walls
        window_id = f"win_{i+1:02d}"
        portals.append({
            "id": window_id,
            "type": "window_double_hung",
            "width": 3.0,
            "sill_height": 3.0,
            "height": 4.5,
            "position": [current_x + (w / 2.0), current_y + h],
            "orientation_angle": 180.0,
            "connects_rooms": [room_id]
        })

        # Add high-value fixture placeholders based on room type
        name_lower = rm["name"].lower()
        if "kitchen" in name_lower:
            fixtures.append({
                "id": f"fix_{room_id}_sink",
                "type": "sink_kitchen",
                "position": [current_x + w - 1.5, current_y + h - 1.5],
                "dimensions": [2.5, 2.0, 3.0],
                "orientation_angle": 0.0,
                "room_id": room_id
            })
            fixtures.append({
                "id": f"fix_{room_id}_fridge",
                "type": "refrigerator",
                "position": [current_x + 1.5, current_y + h - 1.5],
                "dimensions": [3.0, 3.0, 6.0],
                "orientation_angle": 0.0,
                "room_id": room_id
            })
        elif "bath" in name_lower or "powder" in name_lower:
            fixtures.append({
                "id": f"fix_{room_id}_toilet",
                "type": "toilet",
                "position": [current_x + 1.5, current_y + 1.5],
                "dimensions": [1.8, 2.5, 2.5],
                "orientation_angle": 180.0,
                "room_id": room_id
            })
            fixtures.append({
                "id": f"fix_{room_id}_sink",
                "type": "sink_bathroom",
                "position": [current_x + w - 1.5, current_y + 1.5],
                "dimensions": [2.0, 1.8, 2.8],
                "orientation_angle": 180.0,
                "room_id": room_id
            })
            
        # Move current_x so next room is placed directly to the right
        current_x += w
        
    return placed_rooms, portals, fixtures


def main():
    parser = argparse.ArgumentParser(
        description="Normalize raw real estate listing spatial metadata into canonical Floor Plan Specification schema."
    )
    parser.add_argument("--address", type=str, required=True, help="Street address of the property.")
    parser.add_argument("--gla", type=float, required=True, help="Reported Gross Living Area (GLA) in sq ft.")
    parser.add_argument("--rooms", type=str, required=True, help="Semicolon or comma-separated room dimension list.")
    parser.add_argument("--zpid", type=str, default="", help="Zillow Property ID (optional).")
    parser.add_argument("--redfin-id", type=str, default="", help="Redfin Property ID (optional).")
    parser.add_argument("--mls-id", type=str, default="", help="MLS ID (optional).")
    
    args = parser.parse_args()
    
    # 1. Parse rooms
    rooms = normalize_rooms(args.rooms)
    if not rooms:
        print(json.dumps({"error": "No valid room dimensions could be parsed from inputs."}, indent=2))
        sys.exit(1)
        
    # 2. Layout rooms
    placed_rooms, portals, fixtures = layout_rooms(rooms)
    
    # 3. Calculate metrics
    calculated_area = sum(rm["width"] * rm["length"] for rm in rooms)
    variance_pct = abs((calculated_area - args.gla) / args.gla) * 100.0 if args.gla > 0 else 0.0
    
    # 4. Construct response payload
    spec = {
      "metadata": {
        "address": args.address,
        "zpid": args.zpid if args.zpid else None,
        "redfin_id": args.redfin_id if args.redfin_id else None,
        "mls_id": args.mls_id if args.mls_id else None,
        "total_square_footage": args.gla,
        "calculated_square_footage": calculated_area,
        "variance_percentage": round(variance_pct, 2),
        "units": "feet"
      },
      "rooms": placed_rooms,
      "portals": portals,
      "fixtures": fixtures
    }
    
    print(json.dumps(spec, indent=2))


if __name__ == "__main__":
    main()
