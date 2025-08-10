CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    emotion VARCHAR(50),
    emotion_confidence FLOAT,
    feedback_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interaction_outcomes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    chat_id INTEGER REFERENCES interactions(id),
    outcome VARCHAR(255) NOT NULL,
    feedback_score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    preference_key VARCHAR(255) NOT NULL,
    preference_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_id ON interactions(user_id);
CREATE INDEX idx_chat_id ON interaction_outcomes(chat_id);
CREATE INDEX idx_user_id_pref ON user_preferences(user_id);