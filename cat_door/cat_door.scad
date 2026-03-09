/**
 * @author Maciej Urbanski (rooter@kyberian.net)
 * @brief  Cat door insert for interior doors
 * @license GPL
 * @date   March, 2026
 * @version 1.0
 *
 * Cat-shaped door insert with circular opening.
 * Three pieces: two face plates (cat head silhouette) and a tunnel sleeve.
 * Inspired by MakerWorld model 172868 by Eric Cardinal.
 */

// --- Parameters ---

door_thickness = 35; // door thickness in mm
opening_d = 190;     // diameter of cat passthrough opening (= opening height)
frame_border = 25;   // solid frame width around the opening
plate_thickness = 4; // thickness of each face plate
ear_height = 40;     // how far ears extend above the main circle
ear_width = 35;      // width of each ear at base
ear_spacing = 20;    // gap between the two ears at the top
tunnel_wall = 2;     // wall thickness of tunnel sleeve
tolerance = 0.3;     // press-fit tolerance

$fn = 100;
SMALL = 0.1;
INF = 1000;

// --- Derived ---

outer_r = opening_d / 2 + frame_border;
inner_r = opening_d / 2;
tunnel_outer_r = inner_r;
tunnel_inner_r = inner_r - tunnel_wall;

// --- Modules ---

module cat_head_profile() {
  // Main circular body
  circle(r = outer_r);

  // Left ear
  ear_cx = -ear_spacing / 2 - ear_width / 2;
  translate([ ear_cx, outer_r - ear_width / 3, 0 ]) polygon(points = [
    [ -ear_width / 2, 0 ],
    [ ear_width / 2, 0 ],
    [ 0, ear_height ],
  ]);

  // Right ear
  mirror([ 1, 0, 0 ]) translate([ ear_cx, outer_r - ear_width / 3, 0 ])
      polygon(points = [
        [ -ear_width / 2, 0 ],
        [ ear_width / 2, 0 ],
        [ 0, ear_height ],
      ]);
}

module face_plate() {
  difference() {
    linear_extrude(height = plate_thickness) cat_head_profile();
    translate([ 0, 0, -SMALL ])
        cylinder(h = plate_thickness + 2 * SMALL, r = inner_r);
  }
}

module tunnel() {
  difference() {
    cylinder(h = door_thickness, r = tunnel_outer_r - tolerance);
    translate([ 0, 0, -SMALL ])
        cylinder(h = door_thickness + 2 * SMALL, r = tunnel_inner_r);
  }
}

// --- Assembly / Render ---
// Lay out parts side by side for printing

// Face plate 1
translate([ -(outer_r + 5), 0, 0 ]) face_plate();

// Face plate 2
translate([ outer_r + 5, 0, 0 ]) face_plate();

// Tunnel
translate([ 0, -(outer_r + tunnel_outer_r + 10), 0 ]) tunnel();
