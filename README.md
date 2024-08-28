# LLM-Chessmaster
![Second Move](images/robot-playing-chess.png?raw=true "Second Move")

LLM Chessmaster is a unique program that offers an interactive chess-playing experience powered by a Large Language Model (LLM). This application not only allows you to play chess against various AI models but also provides insightful commentary and strategic explanations throughout the game.

## Features

- **Diverse AI Models**: Select from a variety of AI models, including OpenAI's GPT-4o, GPT-4o-mini, or locally hosted models like Llama 3.1.
- **Versatile Player Options**: Configure player types for both white and black pieces, choosing between Human, AI (driven by the chosen LLM), or a Random move generator.
- **Custom Game Configurations**: Begin a game from any desired position using Forsyth–Edwards Notation (FEN).
- **Engaging Gameplay**: Communicate with the AI for detailed move explanations and strategic discussions.

## Getting Started

### Prerequisites

- Python (required for the backend)
- Django (required for the backend server)
- Node.js and npm (required for the frontend)

### Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/LLM-Chessmaster.git
   cd LLM-Chessmaster
   ```

2. **Backend Setup**:
   - Navigate to the `chess` directory:
     ```bash
     cd chess
     ```
   - Install the necessary Python dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Launch the backend server:
     ```bash
     python manage.py runserver
     ```

3. **Frontend Setup**:
   - Navigate to the `chess/chessapp` directory:
     ```bash
     cd chess/chessapp
     ```
   - Install the necessary Node.js dependencies:
     ```bash
     npm install
     ```
   - Start the frontend server:
     ```bash
     npm start
     ```

### How to Play

1. **Choose an LLM for the AI Player**:
   - Select the AI model to act as the computer player. Note that OpenAI models like GPT-4o and GPT-4o-mini require an OpenAI API key.

2. **Select Player Roles**:
   - Determine the player types for both white and black: Human, AI, or Random. The AI player is controlled by the selected LLM model, while the Random player makes arbitrary moves.

3. **Set the Starting Position**:
   - Input the initial position using Forsyth–Edwards Notation (FEN) to configure a custom game setup.

4. **Begin the Game**:
   - Press the "Start" button to commence the game!

### Example

#### Start Page
![Start Page](images/chessapp%20start.png?raw=true "Start Page")

#### User (White) Moves f2 to f4 and LLM AI (Black) Responds with g8 to h6, Along with an Explanation
![Second Move](images/chessapp%202nd%20move.png?raw=true "Second Move")

#### User (White) Moves g1 to f3 and LLM AI (Black) Responds with g7 to g6, Along with an Explanation
![Fourth Move](images/chessapp%204th%20move.png?raw=true "Fourth Move")
