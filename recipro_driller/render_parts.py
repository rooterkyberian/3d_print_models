"""
Rendering script for Recipro Driller parts.
Generates SVG images from multiple perspectives.
"""

import os
import subprocess

import cadquery as cq

import recipro_driller as rd


def render_part(name, shape, output_dir):
    views = {
        "isometric": (1, -1, 1),
        "front": (0, -1, 0),
        "top": (0, 0, 1),
        "right": (1, 0, 0),
        "bottom": (0, 0, -1),
    }

    print(f"Rendering {name}...")
    for view_name, direction in views.items():
        base_filename = f"{name}_{view_name}"
        svg_path = os.path.join(output_dir, f"{base_filename}.svg")
        png_path = os.path.join(output_dir, f"{base_filename}.png")

        # Ultra low-res SVG Export
        opts = {
            "projectionDir": direction,
            "showAxes": False,
            "strokeWidth": 1.2,
            "strokeColor": (0, 0, 0),
            "width": 300,
            "height": 300,
            "marginLeft": 10,
            "marginTop": 10,
            "fitSize": True,
        }

        try:
            cq.exporters.export(shape, svg_path, opt=opts)

            # Convert SVG to PNG using ImageMagick 'convert'
            subprocess.run(["convert", svg_path, png_path], check=True)

            # Clean up intermediate SVG
            os.remove(svg_path)

            print(f"  Saved {png_path}")
        except Exception as e:  # noqa: BLE001 - keep rendering the other views
            print(f"  Error rendering {view_name} for {name}: {e}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    render_dir = os.path.join(script_dir, "renders")

    if not os.path.exists(render_dir):
        os.makedirs(render_dir)

    print("Generating parts for rendering...")
    screw = rd.make_screw()

    # Create a sectioned version of the screw to show the groove clearly
    # We cut the screw in half along the XZ plane
    screw_section = screw.cut(
        cq.Workplane("XY").rect(100, 100).extrude(200).translate((50, 0, -50))
    )

    parts = {
        "screw": screw,
        "screw_section": screw_section,
        "slider": rd.make_slider(),
        "housing": rd.make_housing(),
    }

    for name, shape in parts.items():
        render_part(name, shape, render_dir)

    print(f"\nAll renders saved to: {render_dir}")
