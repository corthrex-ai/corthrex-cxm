from flask import Flask, render_template, request, jsonify
import requests
from ai_logic import AgentManager
import benchmark_corthrex  # <--- CRITICAL IMPORT

# CONFIGURATION
app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

# Initialize the Corthrex Logic Core
manager = AgentManager()
OLLAMA_HOST = "http://localhost:11434"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/tags')
def get_tags():
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags")
        return jsonify(resp.json())
    except:
        return jsonify({"models": []})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    user_input = messages[-1].get('content', '') if messages else ""
    model = data.get('model', 'llama3')
    
    if not user_input: return jsonify({"error": "No input provided"}), 400

    response_text = manager.process(user_input, model)
    
    return jsonify({
        "message": { "content": response_text, "role": "assistant" },
        "done": True
    })

@app.route('/api/stats')
def stats():
    return jsonify(manager.get_dashboard_stats())

# --- THIS IS THE MISSING ROUTE ---
@app.route('/api/benchmark', methods=['POST'])
def run_benchmark():
    stats = benchmark_corthrex.run_benchmark_return_stats()
    return jsonify(stats)

if __name__ == '__main__':
    print("---------------------------------------")
    print(" CORTHREX AI - LOCAL MEMORY NODE")
    print("---------------------------------------")
    print(" * Interface: http://localhost:5000")
    print(" * Memory:    corthrex.cxm")
    app.run(host='0.0.0.0', port=5000, debug=True)