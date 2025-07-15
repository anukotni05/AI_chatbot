from flask import Blueprint, render_template, request, jsonify # type: ignore

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@dashboard_bp.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    prompt = data.get('prompt', '')
    mode = data.get('mode', '')
    
    # Replace with your AI logic
    response = f"Mock response for: {prompt} in {mode} mode."
    return jsonify({'response': response})

@dashboard_bp.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if file:
        # Handle file saving if needed
        return jsonify({'message': 'File uploaded successfully'})
    return jsonify({'error': 'No file provided'}), 400
