# Sketch to SVG Diagram Agent

Transform sketches into clean SVG diagrams using AI in minutes.

Read our paper: [See it. Say it. Sorted: Agentic System for Compositional Diagram Generation](https://arxiv.org/abs/2508.15222)


# Symbology
<p align="center">
  <img src="imgs/logo_final.png" width="300"><br>
  <strong>A web-based collaborative symbolic SVG editor with AI assistance.</strong>
</p>

Unleash a new form of creativity where code meets canvas. Symbology transforms your prompts into editable, symbolic structures, allowing you to craft everything from intricate flowcharts to bold, blocky abstract art without touching a bezier curve. Because every diagram is built on a programmable language of shapes, you aren't just getting a static image—you’re getting a living design. Collaborate with AI to iterate instantly, dive into the code to fine-tune the details, and download clean SVGs that fit perfectly into your projects. It’s design, decoded.

![Symbology Workflow](imgs/symbology_workflow.png)


Example Usage: Flowchart generation from machine learning project description
![Example Usage](imgs/flowchart_editor.jpg)



## Quick Start (2 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Keys
```python
# In run_agent_svg.ipynb, first cell:
os.environ['GEMINI_API_KEY'] = 'your-gemini-api-key-here'
# or
os.environ['OPENAI_API_KEY'] = 'your-gpt-api-key-here'
# In flowchart editor we used OPENAI API
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
model_name = "gemini-2.5-pro"
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

## Using Flowchart Editor

### 1. Start the Web Server
- Open your terminal and run:
  ```bash
  python flowchart_editor/svg_server.py
  ```
- To use a custom port:
  ```bash
  python flowchart_editor/svg_server.py --port 8080
  ```
  (Default port is 8080)

### 2. Open the Webpage
- Visit `http://localhost:8080` in your browser.

### 3. How to Use
- **Draw:** Select a tool and draw on the canvas.
- **Generate:** Click "Generate JSON" to create a JSON representation of your diagram.
- **Save:** Click "Save" to store your diagram in the database.
- **Agent:** Enter text and/or image instructions, then click to let the AI generate or optimize your diagram.
  - Make sure to click "Generate JSON" before interacting with the agent.
  - You can generate an empty JSON and let the agent create a flowchart from scratch.


### Acknowledgement

**Special thanks to Jiaruo Liu, Xiaowen Yin, Yayan Jiang, and Yidan Mei for their valuable contributions to the Flowchart Editor.**


### License
