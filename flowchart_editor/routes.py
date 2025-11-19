"""
API Routes for the SVG Editor application
Separated from main server file for better organization
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import base64
from render_svg import SVGAgent
from agent.agent_svg import Agent
from agent.api_call_gpt import call_llm

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Global conversation history for agent
conversation_history = []


# ============================================================================
# Static File Routes
# ============================================================================

@app.route('/')
def serve_index():
    """Serve the index page as the entry point"""
    return send_from_directory('.', 'index.html')


# @app.route('/<path:path>')
# def serve_static(path):
#     """Serve other static files (CSS, JS, images)"""
#     return send_from_directory('.', path)


# ============================================================================
# API Routes
# ============================================================================

@app.route('/json-to-svg', methods=['POST', 'OPTIONS'])
def json_to_svg():
    """Convert JSON dictionary to SVG"""
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        return '', 204
    
    try:
        data = request.get_json()
        shapes = data.get('shapes', [])
        width = data.get('width', 800)
        height = data.get('height', 600)
        background = data.get('background', 'white')
        
        # Use your existing Python SVG renderer
        agent = SVGAgent(width, height)
        agent.renderer.background = background
        agent.create_from_dict(shapes)
        svg = agent.render()
        
        return jsonify({
            'success': True,
            'svg': svg
        })
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/agent', methods=['POST'])
def agent():
    # Read image if present
    image = request.files.get('image')
    description = ""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    user_message = data.get('message', '').strip()
    svg_json = data.get('svg_json')

    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    agent = Agent(model_name="gpt-5")

    if image:
        print("Image received in request.")
        mime_type = image.mimetype or "application/octet-stream"
        b64 = base64.b64encode(image.read()).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"
        
        # thought, response = agent.optimization_step_user(current_expression=svg_json, actions=user_message, image_base64=data_url)
        thought, response, description = agent.optimization_step_vlm(current_expression=svg_json, actions=user_message, image_base64=data_url)
        print("Generated description:", description)
    else:
        thought, response = agent.optimization_step_user(current_expression=svg_json, actions=user_message)

    return jsonify({'reply': thought, 'shapes': response, 'description': description})
