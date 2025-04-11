from ai_chess import AIChess

# Path to your Stockfish executable
engine_path = r"C:\Users\nisch\stockfish\stockfish.exe" 

# Initialize the AI
chess_ai = AIChess(engine_path=engine_path)

# Set the current board position (FEN for starting position)
fen = "rnbqkbnr/pppppppp/8/8/8/7N/PPPPPPPP/RNBQKB1R b - - 0 1"
chess_ai.set_position(fen)

# Get the bot's next move
next_move = chess_ai.get_next_move(depth=20)
print("Bot's next move:", next_move)

# Close the engine
chess_ai.close_engine()
