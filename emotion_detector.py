import os
import requests
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

ENDPOINT = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def detect_emotion(state):
    text = state['input']
    response = requests.post(ENDPOINT, headers=headers, json={"inputs": text})
    result = response.json()

    if isinstance(result, dict) and "error" in result:
        state['emotion'] = "unknown"
        state['emotion_confidence'] = 0.0
    elif isinstance(result, list) and isinstance(result[0], list):
        scores = sorted(result[0], key=lambda d: d['score'], reverse=True)
        state['emotion'] = scores[0]['label']
        state['emotion_confidence'] = scores[0]['score']
    else:
        state['emotion'] = "unknown"
        state['emotion_confidence'] = 0.0

    emotion = state['emotion']
    persuasive_style = {
        "joy": "Celebrate their excitement, and anchor it to your product as the next joyful step.",
        "sadness": "Be empathetic and show how this product can bring comfort or improvement.",
        "anger": "Stay calm, offer solutions and make them feel understood.",
        "fear": "Reduce uncertainty, emphasize safety, and promise a better outcome.",
        "surprise": "Fuel their curiosity and reveal something unexpected about the offer.",
        "disgust": "Acknowledge concerns and redirect to better alternatives or solutions.",
        "neutral": "Use logic with a slight emotional appeal to guide the decision.",
        "unknown": "Use a friendly, neutral pitch that is helpful and concise."
    }

    strategy = persuasive_style.get(emotion, persuasive_style["unknown"])

    base_persona = (
        "You are an expert, friendly, emotionally intelligent sales agent. "
        "You understand user emotion and respond with powerful, short persuasive messages that motivate the user toward action."
    )

    state['persuasion_prompt'] = (
        f"{base_persona}\n"
        f"User emotion: {emotion}\n"
        f"Persuasive strategy: {strategy}\n"
        f"User message: {state['input']}\n"
        f"Your persuasive reply:"
    )
    return state