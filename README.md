# Sketch to SVG Diagram Agent

Transform sketches into clean SVG diagrams using AI in seconds.

## Quick Start (2 minutes)

### 1. Install Dependencies
```bash
pip install google-genai pillow opencv-python cairosvg numpy
```

### 2. Set API Keys
```python
# In run_agent_svg.ipynb, first cell:
os.environ['GEMINI_API_KEY'] = 'your-gemini-api-key-here'
# Get key at: https://makersuite.google.com/app/apikey
```

### 3. Add Your Sketch
Save your sketch/diagram as `sketch.jpg` in the project folder

### 4. Run the Agent
Open `run_agent_svg.ipynb` and update:
```python
task_id = 'sketch'  # Your image name without extension
tgt_img_path = f"./{task_id}.jpg"
```

Run all cells → Your SVG appears in `agent_svg/sketch/` folder

## What It Does

- Converts hand-drawn sketches to clean vector graphics
- Supports diagrams with shapes, arrows, and text
- Iteratively improves output to match your sketch
- Works with flowcharts, system diagrams, UI mockups

## Example Usage

```python
# Basic usage
model_name = "gemini-2.0-flash-exp"  # or "gemini-1.5-pro"
agent = Agent(model_name=model_name, 
              target_image_path="./diagram.jpg",
              canvas_w=800, canvas_h=600)

# Generate initial SVG
init_svg = agent.initialize()

# Optimize (runs 5 iterations)
for i in range(5):
    new_svg, info, improved = agent.optimization_step_vlm(
        current_image_path=f"./output/step_{i}.png",
        current_expression=new_svg,
        output_path="./output"
    )
```

## Tips

- **Clear sketches work best**: Use dark lines on white background
- **Add text instructions**: Include labels like "red circle" or "blue arrow"
- **Custom instructions**: Add specific guidance:
  ```python
  cus_instruct = "Focus on arrow directions and text alignment"
  ```

## Output

Find your results in `agent_svg/[task_id]/`:
- `initial.png` - First attempt
- `optimized_1.png` through `optimized_5.png` - Refined versions
- `candidate_*.png` - Alternative options considered

## Troubleshooting

- **No output?** Check API key is valid
- **Poor results?** Try clearer sketch or add custom instructions
- **Installation issues?** Use Python 3.8+
