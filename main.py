from board_manager import read_chessboard, validate_initial_setup
from move_logic import detect_move, validate_move
from ai_turn import chessboard_to_fen, get_ai_move, check_game_status
import chess

CHESSBOARD_FILE_PATH = "C:/Users/nisch/Desktop/CPR/chessboard.json" #TODO: CHANGE THIS TO THE CORRECT PATH IN RASPBERY PI
HUMAN_COLOR = "white"
AI_COLOR = "black"

def initialize_game():
    print("Initializing CPR...")
    chessboard = read_chessboard(CHESSBOARD_FILE_PATH)
    is_valid, message = validate_initial_setup(chessboard)
    
    if not is_valid:
        print(f"Board Validation Failed: {message}")
        return None
    print("Board setup is valid. Starting the game!")
    return chessboard

def handle_human_turn():
    old_chessboard= read_chessboard(CHESSBOARD_FILE_PATH)
    
    chessboard_fen = chessboard_to_fen(old_chessboard, HUMAN_COLOR)
    game_status = check_game_status(chess.Board(chessboard_fen))
    
    if game_status:
        print(f"Game Over: {game_status}")
        return None
    
    
    print("Human's turn")
    
    # To prevent infinite loops, seting a maximum number of retries
    retry_count = 0
    max_retries = 5 
    
    while True:
        
        retry_count += 1
        if retry_count > max_retries:
            print("Too many retries. Exiting...")
            return None
        
        input("Press Enter when finished with your move") #TODO: FOR DEBUG PURPOSES WILL LATER BE RPELACED BY GPIO INPUT OF A BUTTON TO SIGNAL THE END OF THE MOVE
        new_chessboard = read_chessboard(CHESSBOARD_FILE_PATH)
        
        move = detect_move(old_chessboard, new_chessboard)
        
        if move is None:
            print("No move detected. Please try again.")
            continue
        elif isinstance(move, list) and len(move) > 1:
            print("Error: Multiple moves detected. Please try again.")
            continue
        
        is_valid_move, message = validate_move(old_chessboard, move)
        
        if not is_valid_move:
            print(f"Invalid move: {message}")
            print("Please correct the move. Waiting for a valid move...")
        else:
            print(f"Valid move detected: {move['piece']} from {move['from']} to {move['to']}")
            if move['captured']:
                print(f"Captured: {move['captured']}")
            break  # Exit the loop once a valid move is made
    
    return f"{move['from']}{move['to']}"


def handle_ai_turn():
    print("\nAI's turn\n")
    chessboard = read_chessboard(CHESSBOARD_FILE_PATH)
    chessboard_fen = chessboard_to_fen(chessboard, AI_COLOR)
    game_status = check_game_status(chess.Board(chessboard_fen))
    
    if game_status:
        print(f"Game Over: {game_status}")
        return None
    
    ai_move = get_ai_move(chessboard_fen, AI_COLOR, difficulty="hard")
    
    return ai_move


def start_game():
    start_condition = False
    while(start_condition):
        chessboard = initialize_game()
        if chessboard is None:
            input("press enter to try again")
        else:
            start_condition = False
    
    
    game_over = False
    if HUMAN_COLOR == "white":
        current_turn = "human"
    else:
        current_turn = "ai"
    
    while not game_over:
        if current_turn == "human":
            move = handle_human_turn()
            if move is None:
                game_over = True
                break
            print(f"Human moved: {move}")
            current_turn = "ai"
        else:
            ai_move = handle_ai_turn()
            if ai_move is None:
                game_over = True
                break
            print(f"AI moved: {ai_move}")
            input("Press Enter to continue")
            current_turn = "human"


    print("Game Over!")
if __name__ == "__main__":
    
    start_game()