from board_manager import read_chessboard, validate_initial_setup
from move_logic import detect_move, validate_move


CHESSBOARD_FILE_PATH = "C:/Users/nisch/Desktop/CPR/chessboard.json" #TODO: CHANGE THIS TO THE CORRECT PATH IN RASPBERY PI


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
    print("Human's turn")
    old_chessboard= read_chessboard(CHESSBOARD_FILE_PATH)
    
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
    print("AI's turn")
    # AI player's move logic
    return "a7a5"

def check_game_over():
    # Game over logic
    return True

def start_game():
    start_condition = True
    while(start_condition):
        chessboard = initialize_game()
        if chessboard is None:
            input("press enter to try again")
        else:
            start_condition = False
    
    
    game_over = False
    current_turn = "human"
    
    while not game_over:
        if current_turn == "human":
            move = handle_human_turn()
            print(f"Human moved: {move}")
            current_turn = "ai"
        else:
            ai_move = handle_ai_turn()
            print(f"AI moved: {ai_move}")
            current_turn = "human"
        
        game_over = check_game_over()

    print("Game Over!")
if __name__ == "__main__":
    
    start_game()