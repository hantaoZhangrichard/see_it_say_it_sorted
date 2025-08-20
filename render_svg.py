import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import math

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


class SVGRenderer:
    """Renders shapes to SVG format"""
    
    def __init__(self, width: int = 800, height: int = 600, background: str = "white"):
        self.width = width
        self.height = height
        self.background = background
        self.shapes: List[Shape] = []
    
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
        """Get SVG style string"""
        return f"fill:{shape.fill_color};stroke:{shape.stroke_color};stroke-width:{shape.stroke_width};opacity:{shape.opacity}"
    
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
        """Render a triangle"""
        size = shape.scale_x * 1
        height = size * math.sqrt(3) / 2
        points = f"0,{-height/2} {-size/2},{height/2} {size/2},{height/2}"
        
        triangle = ET.Element("polygon")
        triangle.set("points", points)
        return triangle
    
    def _render_shape(self, shape: Shape) -> Optional[ET.Element]:
        """Render a single shape"""
        shape_renderers = {
            "circle": self._render_circle,
            "rectangle": self._render_rectangle,
            "ellipse": self._render_ellipse,
            "triangle": self._render_triangle
        }
        
        if shape.shape_type not in shape_renderers:
            print(f"Unknown shape type: {shape.shape_type}")
            return None
        
        element = shape_renderers[shape.shape_type](shape)
        
        # Apply transform
        transform = self._create_transform(shape)
        if transform:
            element.set("transform", transform)
        
        # Apply style
        element.set("style", self._get_style(shape))
        
        return element
    
    def render_svg(self) -> str:
        """Render all shapes to SVG string"""
        # Create root SVG element
        svg = ET.Element(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            width=str(self.width),               # canvas size in px
            height=str(self.height),
            viewBox=f"0 0 {self.width} {self.height}",
            preserveAspectRatio="xMidYMid meet"  # keep square pixels if w ≠ h
        )
        
        # Add background
        if self.background != "none":
            bg = ET.SubElement(svg, "rect")
            bg.set("width", "100%")
            bg.set("height", "100%")
            bg.set("fill", self.background)
        
        # Render all shapes
        for shape in self.shapes:
            element = self._render_shape(shape)
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
                return filename
            else:
                print("Error: No PNG conversion library available.")
                print("Install either: pip install cairosvg")
                return False
                
        except Exception as e:
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