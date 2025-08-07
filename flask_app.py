from flask import Flask, render_template, request, jsonify
from graph_builder import build_graph

app = Flask(__name__)
agent_graph = build_graph()
chat_history = []

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    state = {
        'input': user_input,
        'emotion': "",
        'emotion_confidence': 0.0,
        'chat_history': chat_history.copy(),
        'persuasion_prompt': "",
        'output': ""
    }
    final_state = agent_graph.invoke(state)
    output = final_state.get("output", "Sorry, I didn’t catch that. Can you rephrase?")
    chat_history.append({"user": user_input, "agent": output})
    return jsonify({'response': output})

if __name__ == '__main__':
    app.run(debug=True)
