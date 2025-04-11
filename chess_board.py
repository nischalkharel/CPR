import json
from ai_chess import AIChess
from chessboard import ChessSetupChecker  
import busio
import board
import os
import lgpio
import time
import shutil
from arm import pick_place_from_to, open_gripper
i2c = busio.I2C(board.SCL, board.SDA)
setup_checker = ChessSetupChecker(i2c)
#gpio pins
WHITE_BUTTON_PIN = 17
BLACK_BUTTON_PIN = 27

# Open GPIO chip (chip 4 is standard for Raspberry Pi 5)
h = lgpio.gpiochip_open(4)

# Set pins as input with pull-up resistors
lgpio.gpio_claim_input(h, WHITE_BUTTON_PIN, lgpio.SET_PULL_UP)
lgpio.gpio_claim_input(h, BLACK_BUTTON_PIN, lgpio.SET_PULL_UP)

def wait_buttons():
    while True:
        white_state = lgpio.gpio_read(h, WHITE_BUTTON_PIN)
        black_state = lgpio.gpio_read(h, BLACK_BUTTON_PIN)
        
        if white_state == 0:  # Pressed (Active Low)
            while(white_state == 0):
                white_state = lgpio.gpio_read(h, WHITE_BUTTON_PIN)
                time.sleep(.03)
            return "white_button_pressed"
        if black_state == 0:  # Pressed (Active Low)
            while(black_state == 0):
                black_state = lgpio.gpio_read(h, BLACK_BUTTON_PIN)
                time.sleep(.03)
            return "black_button_pressed"
        
        time.sleep(0.05)  # Debounce delay


def press_white():
    print("\npress white button to confirm\n")

def press_black():
    print("\npress Black button to deny and move again\n")

# Global variables for FEN generation
fullmove_number = 1  # Starts at 1 and increments after Black's turn
halfmove_clock = 0   # Number of halfmoves since last capture or pawn advance
last_move = None     # Tracks the last move made

# Global stack to track the last picked pieces
last_picked_piece = []

def check_initial_setup():
    # Expected initial setup for a chessboard
    expected_positions = {
        "a1": "black_rook", "b1": "black_knight", "c1": "black_bishop", "d1": "black_queen",
        "e1": "black_king", "f1": "black_bishop", "g1": "black_knight", "h1": "black_rook",
        "a2": "black_pawn", "b2": "black_pawn", "c2": "black_pawn", "d2": "black_pawn",
        "e2": "black_pawn", "f2": "black_pawn", "g2": "black_pawn", "h2": "black_pawn",
        "a7": "white_pawn", "b7": "white_pawn", "c7": "white_pawn", "d7": "white_pawn",
        "e7": "white_pawn", "f7": "white_pawn", "g7": "white_pawn", "h7": "white_pawn",
        "a8": "white_rook", "b8": "white_knight", "c8": "white_bishop", "d8": "white_king",
        "e8": "white_queen", "f8": "white_bishop", "g8": "white_knight", "h8": "white_rook"
    }

    while True:
        setup_checker.generate_initial_chess_setup()
        try:
            # Open and read the JSON file
            with open("chessboard.json", "r") as file:
                board_state = json.load(file)

            # Check for missing or incorrect spots
            incorrect_spots = []
            for position, expected_piece in expected_positions.items():
                if position not in board_state or board_state[position] != expected_piece:
                    incorrect_spots.append(position)

            # Check for unexpected pieces in empty spots
            for position in board_state:
                if position not in expected_positions and board_state[position] != "empty":
                    incorrect_spots.append(position)

            if not incorrect_spots:
                print("Initial setup is correct.")
                return True
            else:
                print("The following spots do not meet the initial setup requirements:")
                for spot in incorrect_spots:
                    print(f"- {spot}: Expected '{expected_positions.get(spot, 'empty')}', Found '{board_state.get(spot, 'missing')}')")

        except FileNotFoundError:
            print("Error: chessboard.json file not found. Please ensure the file exists in the same directory.")
            return False
        except json.JSONDecodeError:
            print("Error: chessboard.json file is not a valid JSON file. Please check its contents.")
            return False

        input("Press Enter to retry...")

def handle_human_turn():
    
    # Make a copy of the current board to pre_turn_board.json
    shutil.copy("chessboard.json", "pre_turn_board.json")
    
    # Open or create chess_board_incomplete.json with the current board state
    with open("pre_turn_board.json", "r") as file:
        board_state = json.load(file)

    print("White's turn.")  # ANNOUNCE

    # Continuously check for changes in progress board
    while True:
        print("Make your Move!")
        press_white()
        time.sleep(1)
        button_pressed = wait_buttons()
        if(button_pressed == "black_button_pressed"):
            continue
        
        changed_squares = setup_checker.currentVSprevious_board_states()

        if len(changed_squares) == 1:
            print("You Removed/Added: ") #ANNOUNCE
            for position, piece in changed_squares.items():
                print(position)
            press_white()
            press_black()
            button_pressed = wait_buttons()
            if(button_pressed == "black_button_pressed"):
                print("\nReset and try again!\n")
                continue
            
            positions = list(changed_squares.keys())
            board_state[positions[0]]= "empty"

            # Save the updated state back to the file
            with open("pre_turn_board.json", 'w') as file:
                json.dump(board_state, file, indent=4)
            continue
        elif len(changed_squares) == 2:
            print("You Moved: ") #ANNOUNCE
            for position, piece in changed_squares.items():
                print(position)
            press_white()
            press_black()
            
            time.sleep(1)
            button_pressed = wait_buttons()
            time.sleep(1)
            if(button_pressed == "black_button_pressed"):
                print("\nReset and try again!\n")
                continue
        elif len(changed_squares) == 0:
            print("\n no piece move detected\n")
            continue
            
        else:
            print(f"{len(changed_squares)} squares changed.")
            print("Did you intend to interact with the following squares?")
            print("Fix any squares on the list you did not intend to change:")
            for position, piece in changed_squares.items():
                print(f"{position}")
                print("Press White button to hear the next one")
                button_pressed = wait_buttons()
                
            continue

        for position, piece in changed_squares.items():
            if(changed_squares.get(position) == "empty"):
                from_position = position
            else:
                to_position = position

        swap_pieces_in_file("pre_turn_board.json","chessboard.json", from_position, to_position)
        
        ### VALIDATION CHECK HERE ###
        
        print(f"White moved {from_position} to {to_position}!")
        return

def handle_bot_turn():
    shutil.copy("chessboard.json", "pre_turn_board.json")
    with open("pre_turn_board.json", "r") as file:
        board_state = json.load(file)
    
    ai_move = get_ai_move()
    ai_move[0] = engine_to_physical(ai_move[0])
    ai_move[1] = engine_to_physical(ai_move[1])
    print(f"{ai_move[0]}")
    print(f"{ai_move[1]}")
    if(board_state[ai_move[1]] != "empty"): #make sure "to" position is empty
        emptied = False
        arm_move(ai_move[1], "out") 
        while(not(emptied)):
            print(f"{ai_move[1]} should be emptied")
            button = wait_buttons() 
            changed_squares = setup_checker.currentVSprevious_board_states()
            if(changed_squares.get(ai_move[1]) == "empty"):
                board_state[ai_move[1]]= "empty"

                # Save the updated state back to the file
                with open("pre_turn_board.json", 'w') as file:
                    json.dump(board_state, file, indent=4)
                emptied = True
            else:
                speak(f"I was trying to empty out {ai_move[1]}. Help and press a button")
                button = wait_buttons()
                continue
            
            
    with open("pre_turn_board.json", "r") as file:
        board_state = json.load(file)
        
    arm_move(ai_move[0], ai_move[1])
    arm_not_done = True
    while(arm_not_done):
        changed_squares = setup_checker.currentVSprevious_board_states()
        to_square = False #only true if we have made sure there is a piece here
        from_square = False #only true if its empty now
        all_good = True
        for position, piece in changed_squares.items():
            if(position == ai_move[0]) and (piece == "empty"):
                print("empty")
                from_square = True
            
            if(position == ai_move[1]) and (piece == "piece"):
                print("piece")
                to_square = True
                
            if(position != ai_move[0]) and (position != ai_move[1]):
                speak(f"can you please help me fix {position}")
                speak("press a button when done!")
                button_pressed = wait_buttons()
                all_good = False
                break
            if(position == ai_move[1]) and (piece == "empty"):
                speak(f"I was trying to place {board_state[ai_move[0]]} in f{position}. Can you fix it for me?")
                speak("press a button when done!")
                button_pressed = wait_buttons()
                all_good = False
                break
                
        if not(all_good):
            continue        
        if not(from_square) or not(to_square):
            speak("Something might have gone wrong")
            speak(f"I was trying to move f{board_state[ai_move[0]]} from {ai_move[0]} to {ai_move[1]}")
            speak("Let me know by clicking the button when done helping me. Thank you")
            button = wait_buttons()
            continue
                
        arm_not_done = False
    print("out of loop in bot")
    swap_pieces_in_file("pre_turn_board.json","chessboard.json", ai_move[0], ai_move[1])
    speak("ALRIGHT I AM DONE! Your TURN!")
  
def get_ai_move():
    # Load the chess board
    with open("chessboard.json", "r") as file:
        board_state = json.load(file)
    fen_string = chessboard_to_fen(rotate_board(board_state), ai_color="black")
    print(f"Generated FEN: {fen_string}")

    # Initialize AIChess engine
    ai = AIChess(engine_path=os.getenv('STOCKFISH_PATH', '/usr/games/stockfish'))
    ai.set_position(fen_string)
    
    # Get the next move
    next_move = ai.get_ai_move()
    print(f"AI recommends move: {next_move[0]}{next_move[1]}")
    ai.close_engine()
    return next_move

def arm_move(pos_from, pos_to):
    #INTEGRATE THE ARM MOVEMENT HERE
    print(f"arm moving from {pos_from} to {pos_to}")
    open_gripper()
    pick_place_from_to("pickup",pos_from)
    pick_place_from_to("placedown", pos_to)

def chessboard_to_fen(board_state,ai_color = "black"):
    rows = []
    for rank in range(8, 0, -1):
        row = ""
        empty_count = 0
        for file in "abcdefgh":
            square = f"{file}{rank}"
            piece = board_state.get(square, "empty")

            if piece == "empty":
                empty_count += 1
            else:
                if empty_count > 0:
                    row += str(empty_count)
                    empty_count = 0
                row += piece_to_fen(piece)

        if empty_count > 0:
            row += str(empty_count)
        rows.append(row)

    turn = "w" if ai_color == "white" else "b"
    fen = "/".join(rows) + f" {turn} - - 0 1"
    return fen


def piece_to_fen(piece):
    mapping = {
        "white_pawn": "P", "white_rook": "R", "white_knight": "N", "white_bishop": "B",
        "white_queen": "Q", "white_king": "K",
        "black_pawn": "p", "black_rook": "r", "black_knight": "n", "black_bishop": "b",
        "black_queen": "q", "black_king": "k"
    }
    return mapping.get(piece, "")


def is_checkmate_or_stalemate(board_state, player_color):
    """Check for checkmate or stalemate using AIChess."""
    fen_string = create_FEN(player_color)
    ai = AIChess(engine_path=os.getenv('STOCKFISH_PATH', '/usr/games/stockfish'))
    ai.set_position(fen_string)
    
    if ai.is_checkmate():
        print("Checkmate!")
        ai.close_engine()
        return True
    elif ai.is_stalemate():
        print("Stalemate!")
        ai.close_engine()
        return True
    
    ai.close_engine()
    return False
def swap_pieces_in_file(file_path_from,file_path_to, position1, position2):
    # Load the JSON data from file
    with open(file_path_from, 'r') as file:
        board_state = json.load(file)

    # Swap the pieces
    board_state[position1], board_state[position2] = board_state[position2], board_state[position1]

    # Save the updated state back to the file
    with open(file_path_to, 'w') as file:
        json.dump(board_state, file, indent=4)

def speak(message):
    print(message)

def rotate_board(board_dict: dict) -> dict:
    """Return a new dict with ranks (and optionally files) flipped."""
    new_board = {}
    for square, piece in board_dict.items():
        f, r = square[0], int(square[1])
        new_square = f"{f}{9 - r}"     # 1 ↔ 8, 2 ↔ 7, …
        new_board[new_square] = piece
    return new_board
    

def engine_to_physical(pos):
    return f"{pos[0]}{9-int(pos[1])}"
    
if __name__ == "__main__":
    if check_initial_setup():
        print("Initial checks are completed correctly.")
        while True:
            
            print("\nWhite's turn.")
            handle_human_turn()
            #if is_checkmate_or_stalemate(json.load(open("chessboard.json")), "b"):
             #   break

            print("\nBlack's turn.")
            handle_bot_turn()
            #if is_checkmate_or_stalemate(json.load(open("chessboard.json")), "w"):
             #   break
    else:
        print("Initial check failed.")
