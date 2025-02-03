from flask import Blueprint, render_template, jsonify, request, current_app
from app.devbox.manager import DevboxManager
from app.devbox.visualization_manager import VisualizationManager
import json

bp = Blueprint('chat', __name__)

@bp.route('/chat')
def chat():
    return render_template('chat/chat.html')

@bp.route('/api/query', methods=['POST'])
async def handle_query():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
        
    try:
        # Initialize DevboxManager
        devbox_manager = DevboxManager(
            current_app.config['DEVBOX_ID'],
            current_app.config['RUNLOOP_API_KEY'],
        )
        
        # devbox_manager.run_mcp_query("Some query")
        
        # Ensure MCP files are in devbox
        files_uploaded = devbox_manager.ensure_mcp_files(current_app.config['MCP_FILES_DIR'])
        
        # Execute query
        if files_uploaded:
            result = await devbox_manager.run_mcp_query(query)
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@bp.route('/api/visualize', methods=['POST'])
async def handle_visualize():
    query = request.json.get('query')
    data = request.json.get('data')
    if not query or not data:
        return jsonify({'error': 'Both query and data are required'}), 400
        
    try:
        # Initialize VisualizationManager with OpenAI API key from config
        viz_manager = VisualizationManager(
            openai_api_key=current_app.config.get('OPENAI_API_KEY')
        )
        
        # Generate visualization
        result = viz_manager.visualize_query_results(json.dumps(data), query)
        
        # If there was an error, return the error details
        return jsonify(result), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500