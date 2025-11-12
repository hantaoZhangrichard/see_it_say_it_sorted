import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import math

#############
from color_utils import normalize_color
#################


try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False


@dataclass
class Shape:
    """Base class for all shapes"""
    shape_type: str
    x: float = 0
    y: float = 0
    scale_x: float = 1
    scale_y: float = 1
    stroke_color: str = "black"
    fill_color: str = "none"
    stroke_width: float = 1
    rotation: float = 0  # degrees
    opacity: float = 1.0
    
    # Text-specific properties
    text: str = ""
    font_size: float = 16
    font_family: str = "Arial, sans-serif"
    text_color: str = "black"
    text_anchor: str = "middle"  # start, middle, end
    
    # Polyline/Arrow-specific properties
    points: List[List[float]] = field(default_factory=list)  # [[x1,y1], [x2,y2], ...]
    
    # Arrow-specific properties
    arrow_start: str = "no"  # arrow at start point
    arrow_end: str = "no"  # arrow at end point
    arrowhead_type: str = "triangle"  # triangle, circle, diamond
    arrowhead_size: float = 10


class SVGRenderer:
    """Renders shapes to SVG format"""
    
    def __init__(self, width: int = 800, height: int = 600, background: str = "white"):
        self.width = width
        self.height = height
        self.background = background
        self.shapes: List[Shape] = []
        self.marker_counter = 0  # For unique marker IDs

    def _normalize_paint(self, paint: str | None) -> str | None:
        if paint is None:
            return None
        if isinstance(paint, str) and paint.lower() == "none":
            return "none"
        return normalize_color(paint)

    def _apply_fill_stroke(
        self,
        element,
        fill_raw: str | None = None,
        stroke_raw: str | None = None,
        stroke_width: float | None = None,
        opacity: float | None = None,
    ):
        fill = self._normalize_paint(fill_raw)
        stroke = self._normalize_paint(stroke_raw)
        if fill is not None:
            element.set("fill", fill)
        if stroke is not None:
            element.set("stroke", stroke)
        if stroke_width is not None:
            element.set("stroke-width", str(stroke_width))
        if opacity is not None:
            element.set("opacity", str(opacity))
    
    def add_shape(self, shape_data: Dict[str, Any]) -> bool:
        """Add a shape from JSON-like dictionary"""
        try:
            shape = Shape(**shape_data)
            self.shapes.append(shape)
            return True
        except Exception as e:
            print(f"Error adding shape: {e}")
            return False
    
    def add_shapes(self, shapes_data: List[Dict[str, Any]]) -> int:
        """Add multiple shapes, returns number successfully added"""
        count = 0
        for shape_data in shapes_data:
            if self.add_shape(shape_data):
                count += 1
        return count
    
    def _create_transform(self, shape: Shape) -> str:
        """Create SVG transform string"""
        transforms = []
        
        # Translation
        if shape.x != 0 or shape.y != 0:
            transforms.append(f"translate({shape.x},{shape.y})")
        
        # Rotation
        if shape.rotation != 0:
            transforms.append(f"rotate({shape.rotation})")

        return " ".join(transforms) if transforms else ""
    
    def _get_style(self, shape: Shape) -> str:
        fill = self._normalize_paint(shape.fill_color) or "none"
        stroke = self._normalize_paint(shape.stroke_color) or "none"
        return f"fill:{fill};stroke:{stroke};stroke-width:{shape.stroke_width};opacity:{shape.opacity}"
    
    def _render_circle(self, shape: Shape) -> ET.Element:
        """Render a circle"""
        circle = ET.Element("circle")
        circle.set("cx", "0")
        circle.set("cy", "0")
        circle.set("r", str(shape.scale_x * 0.5))  # base radius of 1
        return circle
    
    def _render_rectangle(self, shape: Shape) -> ET.Element:
        """Render a rectangle"""
        rect = ET.Element("rect")
        width = shape.scale_x * 1  # base width of 1
        height = shape.scale_y * 1  # base height of 1
        rect.set("x", str(-width/2))
        rect.set("y", str(-height/2))
        rect.set("width", str(width))
        rect.set("height", str(height))
        return rect
    
    def _render_ellipse(self, shape: Shape) -> ET.Element:
        """Render an ellipse"""
        ellipse = ET.Element("ellipse")
        ellipse.set("cx", "0")
        ellipse.set("cy", "0")
        ellipse.set("rx", str(shape.scale_x * 0.5))
        ellipse.set("ry", str(shape.scale_y * 0.5))
        return ellipse
    
    def _render_triangle(self, shape: Shape) -> ET.Element:
        """Render a (possibly non-equilateral) triangle.

        Uses scale_x for the base width and scale_y for the triangle height.
        The triangle is centered at (0,0) with the apex at the top.
        """
        base = float(shape.scale_x) * 1.0
        height = float(shape.scale_y) * 1.0
        half_base = base / 2.0

        points = f"0,{-height/2} {-half_base},{height/2} {half_base},{height/2}"

        triangle = ET.Element("polygon")
        triangle.set("points", points)
        return triangle
    
    def _render_text(self, shape: Shape) -> ET.Element:
        """Render text"""
        text = ET.Element("text")
        text.set("x", "0")
        text.set("y", "0")
        text.set("font-size", str(shape.font_size))
        text.set("font-family", shape.font_family)
        text_color = self._normalize_paint(shape.text_color) or "black"
        text.set("fill", text_color)
        text.set("text-anchor", shape.text_anchor)
        text.set("opacity", str(shape.opacity))
        text.set("dominant-baseline", "middle")  # Vertical centering
        text.text = shape.text
        return text
    
    def _render_polyline(self, shape: Shape) -> ET.Element:
        """Render a polyline"""
        polyline = ET.Element("polyline")
        
        # Convert points list to SVG points string
        if shape.points:
            points_str = " ".join([f"{pt[0]},{pt[1]}" for pt in shape.points])
            polyline.set("points", points_str)
        
        ############### --- CHANGE: style via helper (normalizes colors) ---
        polyline.set("fill", "none")
        self._apply_fill_stroke(
            polyline,
            fill_raw="none",
            stroke_raw=shape.stroke_color,
            stroke_width=shape.stroke_width,
            opacity=shape.opacity,
        )
        #################
        return polyline
    
    def _create_arrowhead_marker(self, svg_root: ET.Element, marker_id: str, 
                                arrowhead_type: str, color: str, size: float, 
                                is_start: bool = False) -> None:
        """Create an arrowhead marker definition
        
        Args:
            is_start: If True, creates a marker pointing backwards (for arrow start)
                    If False, creates a marker pointing forwards (for arrow end)
        """
        defs = svg_root.find("defs")
        if defs is None:
            defs = ET.SubElement(svg_root, "defs")
        
        marker = ET.SubElement(defs, "marker")
        marker.set("id", marker_id)
        marker.set("markerWidth", str(size))
        marker.set("markerHeight", str(size))
        
        if is_start:
            # For start arrow: point tip backwards, reference at the front (right side)
            marker.set("refX", "0")
            marker.set("orient", "auto-start-reverse")
        else:
            # For end arrow: point tip forwards, reference at the back (left side)
            marker.set("refX", "0")
            marker.set("orient", "auto")
        
        marker.set("refY", str(size / 2))
        marker.set("markerUnits", "userSpaceOnUse")
        
        if arrowhead_type == "triangle":
            path = ET.SubElement(marker, "path")
            path.set("d", f"M 0 0 L {size} {size/2} L 0 {size} Z")
            path.set("fill", color)
        elif arrowhead_type == "circle":
            circle = ET.SubElement(marker, "circle")
            circle.set("cx", str(size * 0.5))
            circle.set("cy", str(size / 2))
            circle.set("r", str(size / 3))
            circle.set("fill", color)
        elif arrowhead_type == "diamond":
            polygon = ET.SubElement(marker, "polygon")
            points = f"{size},{size/2} {size*0.6},{size*0.2} {size*0.2},{size/2} {size*0.6},{size*0.8}"
            polygon.set("points", points)
            polygon.set("fill", color)

##########################
    def _render_arrow(self, shape: Shape, svg_root: ET.Element) -> ET.Element:
        """Render an arrow (polyline with arrowheads)"""
        polyline = ET.Element("polyline")

        # Convert points list to SVG points string, adjusting for arrowheads
        if shape.points:
            points = shape.points.copy()

            # Shorten line at end to prevent overlap with arrowhead
            if shape.arrow_end == "yes" and len(points) >= 2:
                last = points[-1]
                second_last = points[-2]
                dx = last[0] - second_last[0]
                dy = last[1] - second_last[1]
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    shorten_by = shape.arrowhead_size
                    ratio = (length - shorten_by) / length
                    points[-1] = [second_last[0] + dx * ratio,
                                second_last[1] + dy * ratio]

            # Shorten line at start to prevent overlap with arrowhead
            if shape.arrow_start == "yes" and len(points) >= 2:
                first = points[0]
                second = points[1]
                dx = second[0] - first[0]
                dy = second[1] - first[1]
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    shorten_by = shape.arrowhead_size
                    ratio = shorten_by / length
                    points[0] = [first[0] + dx * ratio,
                                first[1] + dy * ratio]

            points_str = " ".join(f"{pt[0]},{pt[1]}" for pt in points)
            polyline.set("points", points_str)

        # ---- CHANGE #1: style via helper (normalizes stroke color) ----
        # Fill is always none for arrows; normalize stroke + set width/opacity.
        self._apply_fill_stroke(
            polyline,
            fill_raw="none",
            stroke_raw=shape.stroke_color,
            stroke_width=shape.stroke_width,
            opacity=shape.opacity,
        )

        # Normalize the stroke color once for markers so arrowheads match
        # ---- CHANGE #2: normalized color for marker creation ----
        color_for_marker = self._normalize_paint(shape.stroke_color) or "#000000"

        # Add arrowhead markers
        if shape.arrow_start == "yes":
            marker_id = f"arrow-start-{self.marker_counter}"
            self.marker_counter += 1
            self._create_arrowhead_marker(
                svg_root, marker_id, shape.arrowhead_type,
                color_for_marker, shape.arrowhead_size, is_start=True
            )
            polyline.set("marker-start", f"url(#{marker_id})")

        if shape.arrow_end == "yes":
            marker_id = f"arrow-end-{self.marker_counter}"
            self.marker_counter += 1
            self._create_arrowhead_marker(
                svg_root, marker_id, shape.arrowhead_type,
                color_for_marker, shape.arrowhead_size, is_start=False
            )
            polyline.set("marker-end", f"url(#{marker_id})")

        return polyline
##################
    
    def _render_shape(self, shape: Shape, svg_root: Optional[ET.Element] = None) -> Optional[ET.Element]:
        """Render a single shape"""
        shape_renderers = {
            "circle": self._render_circle,
            "rectangle": self._render_rectangle,
            "ellipse": self._render_ellipse,
            "triangle": self._render_triangle,
            "text": self._render_text,
            "polyline": self._render_polyline,
        }
        
        # Arrow needs special handling as it requires svg_root for markers
        if shape.shape_type == "arrow":
            if svg_root is None:
                print("Error: Arrow rendering requires svg_root")
                return None
            element = self._render_arrow(shape, svg_root)
        elif shape.shape_type in shape_renderers:
            element = shape_renderers[shape.shape_type](shape)
        else:
            print(f"Unknown shape type: {shape.shape_type}")
            return None
        
        # Apply transform (not for text if you want absolute positioning)
        if shape.shape_type != "text" or shape.rotation != 0:
            transform = self._create_transform(shape)
            if transform:
                element.set("transform", transform)
        else:
            # For text without rotation, use direct positioning
            if shape.x != 0:
                element.set("x", str(shape.x))
            if shape.y != 0:
                element.set("y", str(shape.y))
        
        # Apply style (except for text and polyline which handle their own styling)
        if shape.shape_type not in ["text", "polyline", "arrow"]:
            element.set("style", self._get_style(shape))
        
        return element
    
    def render_svg(self) -> str:
        """Render all shapes to SVG string"""
        # Create root SVG element
        svg = ET.Element(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            width=str(self.width),
            height=str(self.height),
            viewBox=f"0 0 {self.width} {self.height}",
            preserveAspectRatio="xMidYMid meet"
        )
        
        # Add background
        if self.background != "none":
            bg = ET.SubElement(svg, "rect")
            bg.set("width", "100%")
            bg.set("height", "100%")
            bg.set("fill", self.background)
        
        # Render all shapes
        for shape in self.shapes:
            element = self._render_shape(shape, svg)
            if element is not None:
                svg.append(element)
        
        # Convert to string
        return ET.tostring(svg, encoding='unicode')
    
    def save_svg(self, filename: str) -> bool:
        """Save SVG to file"""
        try:
            svg_content = self.render_svg()
            with open(filename, 'w') as f:
                f.write(svg_content)
            return True
        except Exception as e:
            print(f"Error saving SVG: {e}")
            return False
    
    def save_png(self, filename: str, width: Optional[int] = None, height: Optional[int] = None) -> bool:
        """Save SVG as PNG file using available conversion library"""
        try:
            svg_content = self.render_svg()
            
            # Use provided dimensions or fall back to canvas dimensions
            png_width = width or self.width
            png_height = height or self.height
            
            if CAIROSVG_AVAILABLE:
                cairosvg.svg2png(
                    bytestring=svg_content.encode('utf-8'),
                    write_to=filename,
                    output_width=png_width,
                    output_height=png_height
                )
                return True
            else:
                print("Error: No PNG conversion library available.")
                print("Install either: pip install cairosvg")
                return False
                
        except Exception as e:
            print(f"Error saving PNG: {e}")
            return False
    
    def clear(self):
        """Clear all shapes"""
        self.shapes = []


class SVGAgent:
    """Agent interface for creating SVG graphics"""
    
    def __init__(self, canvas_width: int = 800, canvas_height: int = 600):
        self.renderer = SVGRenderer(canvas_width, canvas_height)
    
    def create_from_json(self, json_data: str) -> bool:
        """Create graphics from JSON string"""
        try:
            data = json.loads(json_data)
            if isinstance(data, list):
                count = self.renderer.add_shapes(data)
                print(f"Added {count} shapes")
                return count > 0
            elif isinstance(data, dict):
                return self.renderer.add_shape(data)
            else:
                print("JSON must be a shape object or array of shapes")
                return False
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            return False
    
    def create_from_dict(self, shape_data: Dict[str, Any]) -> bool:
        """Create graphics from dictionary"""
        if isinstance(shape_data, list):
            count = self.renderer.add_shapes(shape_data)
            return count > 0
        else:
            return self.renderer.add_shape(shape_data)
    
    def render(self) -> str:
        """Get SVG string"""
        return self.renderer.render_svg()
    
    def save(self, filename: str) -> bool:
        """Save to file"""
        return self.renderer.save_svg(filename)
    
    def save_png(self, filename: str, width: Optional[int] = None, height: Optional[int] = None) -> bool:
        """Save as PNG file"""
        return self.renderer.save_png(filename, width, height)
    
    def save_json_as_png(self, json_data: str, filename: str, width: Optional[int] = None, height: Optional[int] = None) -> bool:
        """Create graphics from JSON and save directly as PNG"""
        # Clear current shapes
        self.clear()
        
        # Load shapes from JSON
        if not self.create_from_json(json_data):
            print("Failed to parse JSON data")
            return False
        
        # Save as PNG
        return self.save_png(filename, width, height)
    
    def clear(self):
        """Clear canvas"""
        self.renderer.clear()


# Example usage
if __name__ == "__main__":
    agent = SVGAgent(800, 600)
    
    # Example shapes
    shapes = [
    {
        "shape_type": "rectangle",
        "x": 400,
        "y": 50,
        "scale_x": 700,
        "scale_y": 40,
        "fill_color": "yellow",
        "stroke_color": "black",
        "stroke_width": 2
    },
    {
        "shape_type": "rectangle",
        "x": 120,
        "y": 260,
        "scale_x": 50,
        "scale_y": 50,
        "fill_color": "purple",
        "stroke_color": "black",
        "stroke_width": 1
    },
    {
        "shape_type": "rectangle",
        "x": 190,
        "y": 260,
        "scale_x": 50,
        "scale_y": 50,
        "fill_color": "purple",
        "stroke_color": "black",
        "stroke_width": 1
    },
    {
        "shape_type": "rectangle",
        "x": 120,
        "y": 360,
        "scale_x": 50,
        "scale_y": 50,
        "fill_color": "purple",
        "stroke_color": "black",
        "stroke_width": 1
    },
    {
        "shape_type": "rectangle",
        "x": 190,
        "y": 360,
        "scale_x": 50,
        "scale_y": 50,
        "fill_color": "purple",
        "stroke_color": "black",
        "stroke_width": 1
    },
    {
        "shape_type": "ellipse",
        "x": 280,
        "y": 300,
        "scale_x": 160,
        "scale_y": 110,
        "fill_color": "blue",
        "stroke_color": "black",
        "stroke_width": 2
    },
    {
        "shape_type": "rectangle",
        "x": 560,
        "y": 300,
        "scale_x": 120,
        "scale_y": 120,
        "fill_color": "red",
        "stroke_color": "black",
        "stroke_width": 2
    },
    {
        "shape_type": "triangle",
        "x": 650,
        "y": 500,
        "scale_x": 120,
        "scale_y": 10,
        "fill_color": "green",
        "stroke_color": "black",
        "stroke_width": 2
    },
    {
        "shape_type": "arrow",
        "points": [[370, 300], [490, 300]],
        "stroke_color": "black",
        "stroke_width": 2,
        "arrow_start": 'no',
        "arrow_end": 'yes',
        "arrowhead_size": 12
    },
    {
        "shape_type": "arrow",
        "points": [[700, 340], [700, 440]],
        "stroke_color": "black",
        "stroke_width": 2,
        "arrow_start": 'no',
        "arrow_end": 'yes',
        "arrowhead_size": 12
    },
    {
        "shape_type": "arrow",
        "points": [[580, 520], [230, 520]],
        "stroke_color": "black",
        "stroke_width": 2,
        "arrow_start": 'yes',
        "arrow_end": 'yes',
        "arrowhead_size": 12
    }
    ]
    
    agent.create_from_dict(shapes)
    agent.save("example.svg")
    agent.save_png("example.png")
    print("SVG saved to example.svg")