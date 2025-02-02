from flask import Blueprint, render_template, jsonify, request, current_app
from app.devbox.manager import DevboxManager
import asyncio

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