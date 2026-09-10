#!/usr/bin/env python3
"""
validate_geometric_closure.py

Performs architectural integrity and code verification checks against a
canonical Floor Plan Specification JSON file:
1. Polygon Closure: Ensures room boundaries are fully closed.
2. Area Verification: Computes room area via the Shoelace Formula and compares
   it with the reported gross area to report variance.
3. Portal Placement: Validates that doors/windows lie on the room boundaries.
4. Egress and Clearance: Checks that door frames have standard width clearance.
"""

import argparse
import json
import sys


def calculate_polygon_area(coords: list) -> float:
    """
    Computes the area of a 2D polygon using the Shoelace Formula.
    Coords is a list of [x, y] coordinates.
    """
    # If the polygon is not closed, close it temporarily for area calculation
    if coords[0] != coords[-1]:
        coords = coords + [coords[0]]
        
    n = len(coords)
    area = 0.0
    for i in range(n - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i+1]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def is_polygon_closed(coords: list) -> bool:
    """
    Checks if a polygon starts and ends at the exact same coordinate.
    """
    if len(coords) < 4:
        return False
    return coords[0][0] == coords[-1][0] and coords[0][1] == coords[-1][1]


def distance_point_to_segment(p, s1, s2):
    """
    Calculates the shortest distance from point p to line segment [s1, s2].
    """
    px, py = p
    x1, y1 = s1
    x2, y2 = s2
    
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return ((px - x1)**2 + (py - y1)**2)**0.5
        
    t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)
    t = max(0.0, min(1.0, t))
    
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    return ((px - closest_x)**2 + (py - closest_y)**2)**0.5


def is_portal_on_wall(portal_pos: list, room_polygon: list, tolerance: float = 0.5) -> bool:
    """
    Checks if a portal coordinate lies close to any wall segment of the room polygon.
    """
    coords = room_polygon
    if coords[0] != coords[-1]:
        coords = coords + [coords[0]]
        
    for i in range(len(coords) - 1):
        dist = distance_point_to_segment(portal_pos, coords[i], coords[i+1])
        if dist <= tolerance:
            return True
    return False


def validate_floorplan(spec: dict) -> dict:
    results = {
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "metrics": {}
    }
    
    metadata = spec.get("metadata", {})
    reported_gla = metadata.get("total_square_footage", 0.0)
    
    rooms = spec.get("rooms", [])
    portals = spec.get("portals", [])
    
    total_calculated_area = 0.0
    room_areas = {}
    
    # 1. Validate Rooms
    for rm in rooms:
        room_id = rm.get("id")
        name = rm.get("name", room_id)
        polygon = rm.get("polygon", [])
        
        # Closure check
        if not is_polygon_closed(polygon):
            results["errors"].append(f"Room '{name}' ({room_id}) polygon is not closed. Start: {polygon[0] if polygon else None}, End: {polygon[-1] if polygon else None}")
            results["status"] = "FAILED"
            
        # Area calculation
        area = calculate_polygon_area(polygon)
        room_areas[room_id] = area
        total_calculated_area += area
        
    results["metrics"]["calculated_area_sqft"] = round(total_calculated_area, 2)
    results["metrics"]["reported_gla_sqft"] = reported_gla
    
    # Area variance check
    if reported_gla > 0:
        variance_pct = abs((total_calculated_area - reported_gla) / reported_gla) * 100.0
        results["metrics"]["variance_percentage"] = round(variance_pct, 2)
        if variance_pct > 10.0:
            results["warnings"].append(f"Calculated square footage ({total_calculated_area:.2f}) varies from listing GLA ({reported_gla:.2f}) by {variance_pct:.2f}% (exceeds 10% tolerance).")
    else:
        results["metrics"]["variance_percentage"] = 0.0
        
    # 2. Validate Portals (Doors & Windows)
    for port in portals:
        port_id = port.get("id")
        port_type = port.get("type", "unknown")
        pos = port.get("position", [])
        width = port.get("width", 0.0)
        connects = port.get("connects_rooms", [])
        
        # Ingress / Egress Width Clearance Check
        if "door" in port_type or "entry" in port_type:
            if width < 2.6: # Minimum clear width per standard residential codes is usually 32 inches (~2.6 feet)
                results["warnings"].append(f"Portal '{port_id}' ({port_type}) width {width}ft is less than standard egress requirement (2.67ft / 32 inches).")
                
        # Portal placement alignment check: make sure portal is on the wall of connected rooms
        for r_id in connects:
            # Find the room object
            target_rm = next((r for r in rooms if r["id"] == r_id), None)
            if target_rm:
                if not is_portal_on_wall(pos, target_rm["polygon"]):
                    results["warnings"].append(f"Portal '{port_id}' at {pos} is not aligned with any wall of connected room '{r_id}'.")
            else:
                results["errors"].append(f"Portal '{port_id}' references non-existent room ID '{r_id}'.")
                results["status"] = "FAILED"
                
    return results


def main():
    parser = argparse.ArgumentParser(description="Validate structural and geometric integrity of Floor Plan Spec JSON.")
    parser.add_argument("file", nargs="?", type=argparse.FileType("r"), default=sys.stdin, help="Path to Floor Plan Spec JSON file (or stdin).")
    args = parser.parse_args()
    
    try:
        spec = json.load(args.file)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}", file=sys.stderr)
        sys.exit(1)
        
    results = validate_floorplan(spec)
    
    print(json.dumps(results, indent=2))
    if results["status"] == "FAILED":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
