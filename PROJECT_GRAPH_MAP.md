# 🗺️ IPL Akinator AI: System Graph & Knowledge Map

This document provides a structured, graphical representation of the entire repository. It is designed to be **AI-consumable** while remaining visually intuitive for humans.

---

## 🏗️ 1. High-Level Architecture

The system follows a classic **Client-Server** architecture with a specialized **Probabilistic Engine** and a **Global Leaderboard**.

![System Architecture](file:///C:/Users/noush/.gemini/antigravity/brain/4df0b049-cf6c-4f74-9d01-a417b83190a7/ipl_akinator_architecture_1778005892039.png)

```mermaid
graph TD
    subgraph Frontend [React Web App]
        UI[User Interface] --> Hooks[useGame Hook]
        Hooks --> Services[Axios API Client]
    end

    subgraph Backend [FastAPI Server]
        API[API Endpoints] --> Session[Session & Scoring Manager]
        Session --> Logic[Game Logic]
    end

    subgraph Engine [Bayesian Logic Engine]
        Logic --> Selector[Entropy Selector]
        Logic --> Prob[Bayesian Probabilities]
        Logic --> Trick[Trick Detection System]
    end

    subgraph External [External Services]
        API --> Supabase[(Supabase Leaderboard)]
    end
```

---

## 🎮 2. Game Mechanics & Scoring

The project has been extended with a competitive game layer.

### 🧮 Scoring Logic
*   **Base Score**: `question_count * 10`
*   **Penalty/Bonus**: `wrong_guess_attempts * 50` (AI failure rewards the user)
*   **Trick Bonus**: Rewards users who successfully lead the AI into unlikely search paths while remaining consistent to a player.

### 😈 Trick Detection
The system monitors the **Probability Mass** of user answers. If a user provides an answer that is highly improbable given the current top candidates (P < 0.1), the `inconsistency_score` increases, contributing to the `trick_bonus` if the user wins.

---

## 📂 3. Repository Structure (Visual Tree)

The game operates on a cycle of **Question Selection** and **Probability Updates**.

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant E as Engine

    Note over U, E: Start Session
    B->>E: load_dataset()
    E->>E: Calculate Initial Entropy
    E->>B: Return Best First Question
    B->>F: StartResponse (Question + Attr)
    F->>U: Display Question

    loop Game Loop
        U->>F: Provide Answer (Yes/No/Maybe)
        F->>B: AnswerRequest
        B->>E: update_probabilities(answer)
        Note right of E: P(Player|Answer) = (P(Answer|Player) * P(Player)) / P(Answer)
        E->>E: select_next_attribute()
        Note right of E: Minimize |P_mass(Attr) - 0.5|
        E->>B: Next Question OR Final Guess
        B->>F: NextQuestionResponse / GuessResponse
        F->>U: Update UI
    end
```

---

## 📂 3. Repository Structure (Visual Tree)

```text
IPL_Akinator/
├── backend/                # 🐍 Python FastAPI Backend
│   ├── api/                # API Layer
│   │   ├── routes.py       # REST Endpoints
│   │   └── models.py       # Pydantic Schemas
│   ├── engine/             # 🧠 Mathematical Engine
│   │   ├── probability.py  # Bayesian Inference Logic
│   │   ├── selector.py     # Entropy-based Question Selection
│   │   └── constraints.py  # Hard filtering logic
│   ├── data/               # 📊 Dataset & Schemas
│   │   ├── players.json    # 250+ IPL Player Profiles
│   │   └── schema.json     # Question/Attribute mapping
│   └── main.py             # Server Entry Point
├── frontend/               # ⚛️ React/Vite Frontend
│   ├── src/
│   │   ├── components/     # UI Components (Cards, Chat, Progress)
│   │   ├── api/            # Backend communication logic
│   │   └── App.jsx         # Main Application Logic
│   └── package.json        # Dependencies
├── AI_CONTEXT.md           # Deep context for LLM agents
└── setup plan.md           # Deployment/Setup Guide
```

---

## 📊 4. Data Relationship Map

How the attributes and players are linked within the system.

```mermaid
erDiagram
    PLAYER ||--o{ ATTRIBUTE_VALUE : possesses
    ATTRIBUTE ||--o{ ATTRIBUTE_VALUE : defines
    QUESTION ||--|| ATTRIBUTE : "asks about"
    
    PLAYER {
        string name
        string id
        float probability
    }
    
    ATTRIBUTE {
        string key
        string type "Binary/Categorical"
    }
    
    QUESTION {
        string text
        string banter_template
    }
```

---

## 🛠️ 5. Technology Stack Summary

| Layer | Technology | Primary Purpose |
| :--- | :--- | :--- |
| **Frontend** | React + Vite | Interactive, fast UI with state management. |
| **Backend** | Python + FastAPI | High-performance asynchronous API. |
| **Intelligence** | Bayesian Math | Probabilistic reasoning (handles uncertainty). |
| **Information** | Shannon Entropy | Optimizing question count (Binary search style). |
| **Styling** | Vanilla CSS/Tailwind | Premium look and feel. |

---

## 💡 AI Consumption Guide

If you are an AI assistant analyzing this repo:
1. **To modify questions**: Check `backend/data/schema.json`.
2. **To improve guessing logic**: Look at the likelihood matrix in `backend/engine/probability.py`.
3. **To change the UI flow**: Edit the state machine in `frontend/src/App.jsx`.
4. **To add players**: Run `backend/data/build_real_ipl_players.py`.

---
*Created by Antigravity AI*
