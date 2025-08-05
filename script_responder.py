import os
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def script_response(state):
    system_prompt = state.get("persuasion_prompt", "You are a persuasive sales agent for a DTC product brand.")

    blueprint = (
        "\nYou are an expert DTC sales agent. Always follow this proven sales strategy:"
        "\n- Use lifestyle language: tie the product to how it makes the customer feel or live better."
        "\n- Use emotion first, logic second. Connect the product to a personal benefit or dream."
        "\n- Use FOMO or urgency: limited stock, seasonal deals, special offer ending soon."
        "\n- Offer bundles or upsells: 'If you're getting this, you’ll love the matching... at 20% off.'"
        "\n- Use analogies: 'Buying this is like investing in your weekend comfort.'"
        "\n- Never sound pushy. Be confident, helpful, and motivating."
    )

    # Update system prompt with DTC persuasion strategy
    system_prompt += blueprint

    messages = [{"role": "system", "content": system_prompt}]
    chat_history = state.get("chat_history", [])
    user_message = state['input']

    for turn in chat_history[-3:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["agent"]})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "messages": messages,
        "model": "llama3-70b-8192"
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        data = resp.json()
        if "choices" in data and len(data["choices"]) > 0:
            reply = data["choices"][0]["message"]["content"].strip()
        else:
            reply = "Our team is here to help you find your perfect fit. Could you tell me what you're shopping for today?"
    except Exception as e:
        reply = "Sorry, I’m having trouble pulling up our product options. Please try again soon."

    new_state = state.copy()
    new_state['output'] = reply
    return new_state