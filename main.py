from graph_builder import build_graph

def main():
    agent_graph = build_graph()
    chat_history = []
    print("----- Welcome! Start chatting with the agent. Type 'exit' to quit. -----")
    while True:
        user_input = input("User: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        state = {
            'input': user_input,
            'emotion': "",
            'emotion_confidence': 0.0,
            'chat_history': chat_history.copy(),
            'persuasion_prompt': "",
            'output': ""
        }
        final_state = agent_graph.invoke(state)
        output = final_state.get("output", "Sorry, I didn't understand. Please try again.")
        print(f"Agent: {output}")
        chat_history.append(
            {"user": user_input, "agent": output}
        )

if __name__ == "__main__":
    main()