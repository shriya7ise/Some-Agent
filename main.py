import asyncio
import uuid
from utils import validate_env_vars, logger
from graph_builder import build_graph

async def main():
    try:
        validate_env_vars()
        agent_graph = build_graph()
        chat_history = []
        user_id = "cli_user"
        logger.info("Starting CLI session")
        
        print("----- Welcome! Start chatting with the fashion sales agent. Type 'exit' to quit. -----")
        while True:
            user_input = input("User: ")
            if user_input.lower() in {"exit", "quit"}:
                print("Goodbye!")
                logger.info("CLI session ended")
                break
            state = {
                "user_message": user_input,
                "emotion": "",
                "emotion_confidence": 0.0,
                "chat_history": chat_history.copy(),
                "persuasion_prompt": "",
                "response": "",
                "user_id": user_id,
                "chat_id": str(uuid.uuid4()),
                "entities": [],
                "entities_from_graph": [],
                "recent_memories": []
            }
            try:
                print("Invoking graph with state:", state)
                final_state = await agent_graph.ainvoke(state)  # Use ainvoke
                output = final_state.get("response", "Sorry, I didn't understand. Please try again.")
                print(f"Agent: {output}")
                chat_history.append({"user": user_input, "agent": output})
                logger.info(f"User {user_id} input: {user_input}, Response: {output}")
            except Exception as e:
                logger.error(f"Error processing input for user {user_id}: {str(e)}")
                print(f"Error: {str(e)}. Please check ./some-agent.log for details.")
    except Exception as e:
        logger.error(f"Failed to start CLI: {str(e)}")
        print(f"Failed to start: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())