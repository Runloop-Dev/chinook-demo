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
        devbox_manager = DevboxManager(
            current_app.config['DEVBOX_ID'],
            current_app.config['RUNLOOP_API_KEY'],
        )
        
        files_uploaded = devbox_manager.ensure_mcp_files(current_app.config['MCP_FILES_DIR'])
        
        if files_uploaded:
            result = await devbox_manager.run_mcp_query(query)
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/analyze', methods=['POST'])
async def handle_analysis():
    """Handle data analysis requests."""
    data = request.json.get('data')
    if not data:
        return jsonify({'error': 'Data is required'}), 400
        
    try:
        viz_manager = VisualizationManager(
            openai_api_key=current_app.config.get('OPENAI_API_KEY')
        )
        
        # Get data analysis
        analysis = viz_manager.analyze_data_structure(json.dumps(data))
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/visualize', methods=['POST'])
async def handle_visualize():
    """Handle visualization requests."""
    data = request.json.get('data')
    visualization_type = request.json.get('visualization_type')
    
    if not data or not visualization_type:
        return jsonify({'error': 'Both data and visualization_type are required'}), 400
        
    try:
        viz_manager = VisualizationManager(
            openai_api_key=current_app.config.get('OPENAI_API_KEY')
        )
        
        # Get visualization code and metadata
        viz_data = viz_manager.get_visualization_data(json.dumps(data), visualization_type)
        
        if 'error' in viz_data:
            return jsonify(viz_data), 500
            
        # Execute visualization code in devbox
        devbox_manager = DevboxManager(
            current_app.config['DEVBOX_ID'],
            current_app.config['RUNLOOP_API_KEY'],
        )
        
        # Run the visualization code and get the JSON output
        result = await devbox_manager.run_visualization_code(viz_data['code'])
        
        # Parse the JSON output from the visualization code
        visualization_result = json.loads(result)
        
        return jsonify(visualization_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500