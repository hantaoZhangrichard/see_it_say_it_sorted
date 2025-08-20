
VLM_scene_description_prompt = """
You are given an image composed of simple shape primitives. Your task is to describe each primitive in JSON only, adhering exactly to the schema and rules below. Do not add any prose outside the JSON.

Customer instructions:
{customer_instruction}

Schema:
{{
  "primitives": [
    {{
      "id": "<unique deterministic id>",
      "features": {{
        "shape": "rect", "ellipse", "circle", "triangle", or "star",
        "fill_color": "<one of red, blue, green, orange, purple, white, black, gray>",
        "stroke_color": "<one of red, blue, green, orange, purple, white, black, gray, none>",
        "pos_bin": "TL" | "TC" | "TR" | "CL" | "C" | "CR" | "BL" | "BC" | "BR"
      }},
      "description": "<In-detailed phrase describing its size, shape, and position relative to other primitives>"
    }}
  ],
  "bg_color": "<background color name from the same color set except 'none'>"
}}

Rules:
1. **ID construction:** Must be simple, deterministic, and unique. Compose it from its features: 
   format: `<shape>-<fill_color>-<stroke_color>-<pos_bin>[-N]`
   If multiple primitives would otherwise collide, append `-1`, `-2`, etc., to make them unique. Example: `ellipse-blue-black-TC-1`.
2. **pos_bin definition:** Divide the image into a 3x3 grid:
   - Rows: Top (T), Center (C), Bottom (B)
   - Columns: Left (L), Center (C), Right (R)
   Combine to get: TL, TC, TR, CL, C, CR, BL, BC, BR. 
   Assign each primitive to the bin corresponding to where its visual center lies.
3. **description:** Provide a in-detailed natural-language description about the relative position, size, shape comparing this primitive to other primitive(s). Examples: 
   - "to the left of red rectangle"
   - "above the green ellipse"
   - "slightly below and overlaps the large blue ellipse on top"
   - "slightly bigger than the red rectangle"
   - "flat rectangle"
   - "thin ellipse and smaller than the blue ellipse".
   Do not use raw coordinates.
4. **Color values:** Use only the allowed color names, lowercase. If a primitive has no stroke, use `"none"` for `stroke_color`.
5. **Output constraints:** 
   - Output valid JSON inside <answer> ... </answer>.
   - Ensure all `id` fields are unique.
   - Order of primitives does not matter.

Example:
<answer>
{{
  "primitives": [
    {{
      "id": "rect-yellow-black-TL",
      "features": {{
        "shape": "rect",
        "fill_color": "yellow",
        "stroke_color": "black",
        "pos_bin": "TL"
      }},
      "description": "above the green ellipse and bigger than the green ellipse"
    }},
    {{
      "id": "ellipse-green-none-CL",
      "features": {{
        "shape": "ellipse",
        "fill_color": "green",
        "stroke_color": "none",
        "pos_bin": "CL"
      }},
      "description": "to the right of yellow rectangle, very flat"
    }}
  ],
  "bg_color": "white"
}}
</answer>

**Strictly follow the customer instruction**
"""


VLM_edits_sys = """
You are analyzing two SVG graphics images to identify differences and suggest corrections to guide LLM to modify the current image step by step to match the target.

**Target Image (First Image)**: The desired final result

**Current Image (Second Image)**: The current state that needs modification

First, give an overall description of the target image. Consider the overall layout and metadata (e.g. how many shapes, what colors, how they are allocated on the canvas)

Then, focus on 1-3 shapes that need major adjustments.

## Analysis Task

1. **Shape-by-Shape Comparison**: 
   - Identify each shape in both images by type (rectangle, circle, ellipse) and visual properties
   - Match corresponding shapes between target and current images
   - Note any missing shapes in current image or extra shapes that shouldn't be there

2. **Detailed Difference Analysis**:
   For each shape, compare:
   - **Position**: Where is it located? (use qualitative relative descriptions)
   - **Size**: How big is it?
   - **Color**: Fill color and stroke color
   - **Orientation**: Any rotation or angle differences
   - **Visibility**: Is the shape present in both images?

3. **Spatial Relationships**:
   - How do shapes relate to each other spatially?
   - Are there alignment issues between target and current?
   - Note any overlapping or spacing problems

## Modification Suggestions

For all descriptions or modification suggestions, only use qualitative and relative descriptions, focusing on the relative size or positions to other shapes or the whole canvas.
E.g. The width should be around one half of the canvas; the size should be doubled; the blue rectangle should just touch the red circle on its left.


**Be specific about:**
- Which shape you're referring to (e.g., "the blue rectangle in the top-left", "the small red circle")
- Directional movements (left/right, up/down)
- Size changes (bigger/smaller)
- Exact color names when possible

**Strictly follow the customer instruction while giving your response**

Customer instructions:
{customer_instruction}
"""


VLM_edits_user_2 = """
Looking at the target image (first) and current generated image (second), suggest modifications to better align the current image with the target.
"""


VLM_edits_with_feedback_prompt = """
Looking at the target image (first) and current generated image (second), suggest modifications to better align the current image with the target.

IMPORTANT FEEDBACK: The previous suggestions below did NOT lead to better alignment with the target image:
{previous_suggestions}

Please update your suggestions that:
1. Correct what are inappropriate in the previous suggestions
2. Provide more details in your suggestions using more clear descriptions
3. Consider alternative modifications that might be more effective
4. Focus on the most critical differences between the images
"""