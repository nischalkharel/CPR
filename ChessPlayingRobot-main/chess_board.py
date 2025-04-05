import json
from ai_chess import AIChess
from chessboard import ChessSetupChecker  
import busio
import board
import os

i2c = busio.I2C(board.SCL, board.SDA)
setup_checker = ChessSetupChecker(i2c)
# Global variables for FEN generation
fullmove_number = 1  # Starts at 1 and increments after Black's turn
halfmove_clock = 0   # Number of halfmoves since last capture or pawn advance
last_move = None     # Tracks the last move made

# Global stack to track the last picked pieces
last_picked_piece = []

def check_initial_setup():
    # Expected initial setup for a chessboard
    expected_positions = {
        "a1": "white_rook", "b1": "white_knight", "c1": "white_bishop", "d1": "white_queen",
        "e1": "white_king", "f1": "white_bishop", "g1": "white_knight", "h1": "white_rook",
        "a2": "white_pawn", "b2": "white_pawn", "c2": "white_pawn", "d2": "white_pawn",
        "e2": "white_pawn", "f2": "white_pawn", "g2": "white_pawn", "h2": "white_pawn",
        "a7": "black_pawn", "b7": "black_pawn", "c7": "black_pawn", "d7": "black_pawn",
        "e7": "black_pawn", "f7": "black_pawn", "g7": "black_pawn", "h7": "black_pawn",
        "a8": "black_rook", "b8": "black_knight", "c8": "black_bishop", "d8": "black_king",
        "e8": "black_queen", "f8": "black_bishop", "g8": "black_knight", "h8": "black_rook"
    }

    while True:
        setup_checker.generate_initial_chess_setup()
        try:
            # Open and read the JSON file
            with open("chess_board.json", "r") as file:
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
            print("Error: chess_board.json file not found. Please ensure the file exists in the same directory.")
            return False
        except json.JSONDecodeError:
            print("Error: chess_board.json file is not a valid JSON file. Please check its contents.")
            return False

        input("Press Enter to retry...")

def handle_human_turn():
    import shutil

    global last_picked_piece
    last_picked_incomplete = []

    # Make a copy of the current board to progress_chess_board.json
    shutil.copy("chess_board.json", "progress_chess_board.json")
    
    # Open or create chess_board_incomplete.json with the current board state
    with open("chess_board.json", "r") as file:
        board_state = json.load(file)
    with open("chess_board_incomplete.json", "w") as file:
        json.dump(board_state, file, indent=4)

    print("White's turn.")  # Comment: This loop will later be going through the GPIO pins of all 64 pieces
                          # and seeing where in the copy there was a non-empty piece and now the GPIO pin is not active.

    # Continuously check for changes in progress board
    while True:
        setup_checker.track_progress_chessboard()
        with open("progress_chess_board.json", "r") as file:
            progress_board = json.load(file)

        for position, piece in board_state.items():
            if piece != "empty" and progress_board.get(position, "empty") == "empty":
                if last_picked_incomplete and last_picked_incomplete[-1]["position"] == position:
                    continue  # Avoid duplicate tracking of the same lifted piece
                print(f"{piece} is lifted from {position}.")
                piece_picked_detected(piece, position, last_picked_incomplete)
                with open("chess_board_incomplete.json", "r") as incomplete_file:
                    incomplete_board = json.load(incomplete_file)
                incomplete_board[position] = "empty"
                with open("chess_board_incomplete.json", "w") as incomplete_file:
                    json.dump(incomplete_board, incomplete_file, indent=4)

        for position, piece in progress_board.items():
            if piece == "unknown":
                if not last_picked_incomplete:
                    print("Error: No piece was picked up previously to be placed. Please check the board and press Enter to restart your turn.")
                    input("Press Enter to retry...")
                    return handle_human_turn()  # Restart the turn

                last_piece = last_picked_incomplete.pop()
                if last_piece["position"] == position:
                    print(f"{last_piece['piece']} was placed back on {position}. Ignoring this move.")
                else:
                    with open("chess_board_incomplete.json", "r") as incomplete_file:
                        incomplete_board = json.load(incomplete_file)
                    incomplete_board[position] = last_piece["piece"]
                    with open("chess_board_incomplete.json", "w") as incomplete_file:
                        json.dump(incomplete_board, incomplete_file, indent=4)

                print("Do you want to confirm your move? Press Enter for Yes, type 'no' for No.")
                confirm = input().strip().lower()
                if confirm == 'no':
                    print("Resetting the board to the previous state. Please make the board match the initial setup before your turn.")
                    return handle_human_turn()  # Restart the turn

                # Update the main board with the incomplete board state before returning
                with open("chess_board_incomplete.json", "r") as incomplete_file:
                    incomplete_board = json.load(incomplete_file)
                with open("chess_board.json", "w") as main_file:
                    json.dump(incomplete_board, main_file, indent=4)

                last_picked_piece = last_picked_incomplete.copy()
                return  # Exit after handling the "unknown" piece


def piece_picked_detected(piece_name, location, stack):
    stack.append({
        "piece": piece_name,
        "position": location
    })
    print(f"Tracking picked piece: {piece_name} from {location}.")


def handle_bot_turn():
    fen_string = create_FEN("b")  # Generate FEN for white to move
    print(f"Generated FEN: {fen_string}")

    # Initialize AIChess engine
    ai = AIChess(engine_path=os.getenv('STOCKFISH_PATH', '/usr/games/stockfish'))
    ai.set_position(fen_string)
    
    # Get the next move
    next_move = ai.get_next_move()
    print(f"AI recommends move: {next_move}")
    ai.close_engine()
    
    #this is same as the human handle one.
    import shutil

    global last_picked_piece
    last_picked_incomplete = []

    # Make a copy of the current board to progress_chess_board.json
    shutil.copy("chess_board.json", "progress_chess_board.json")

    # Open or create chess_board_incomplete.json with the current board state
    with open("chess_board.json", "r") as file:
        board_state = json.load(file)
    with open("chess_board_incomplete.json", "w") as file:
        json.dump(board_state, file, indent=4)

    print("Black's turn.")  # Comment: This loop will later be going through the GPIO pins of all 64 pieces
                          # and seeing where in the copy there was a non-empty piece and now the GPIO pin is not active.

    # Continuously check for changes in progress board
    while True:
        setup_checker.track_progress_chessboard()
        with open("progress_chess_board.json", "r") as file:
            progress_board = json.load(file)

        for position, piece in board_state.items():
            if piece != "empty" and progress_board.get(position, "empty") == "empty":
                if last_picked_incomplete and last_picked_incomplete[-1]["position"] == position:
                    continue  # Avoid duplicate tracking of the same lifted piece
                print(f"{piece} is lifted from {position}.")
                piece_picked_detected(piece, position, last_picked_incomplete)
                with open("chess_board_incomplete.json", "r") as incomplete_file:
                    incomplete_board = json.load(incomplete_file)
                incomplete_board[position] = "empty"
                with open("chess_board_incomplete.json", "w") as incomplete_file:
                    json.dump(incomplete_board, incomplete_file, indent=4)

        for position, piece in progress_board.items():
            if piece == "unknown":
                if not last_picked_incomplete:
                    print("Error: No piece was picked up previously to be placed. Please check the board and press Enter to restart your turn.")
                    input("Press Enter to retry...")
                    return handle_bot_turn()  # Restart the turn

                last_piece = last_picked_incomplete.pop()
                if last_piece["position"] == position:
                    print(f"{last_piece['piece']} was placed back on {position}. Ignoring this move.")
                else:
                    with open("chess_board_incomplete.json", "r") as incomplete_file:
                        incomplete_board = json.load(incomplete_file)
                    incomplete_board[position] = last_piece["piece"]
                    with open("chess_board_incomplete.json", "w") as incomplete_file:
                        json.dump(incomplete_board, incomplete_file, indent=4)

                # Update the main board with the incomplete board state before returning
                with open("chess_board_incomplete.json", "r") as incomplete_file:
                    incomplete_board = json.load(incomplete_file)
                with open("chess_board.json", "w") as main_file:
                    json.dump(incomplete_board, main_file, indent=4)

                last_picked_piece = last_picked_incomplete.copy()
                return  # Exit after handling the "unknown" piece
    
    
    #we do the rest same but just dont have to ask for confirmaion from the user.
    
    

def create_FEN(player_color):
    # Load the chess board
    with open("chess_board.json", "r") as file:
        board_state = json.load(file)

    # Generate FEN string (basic implementation without castling, en passant, etc.)
    ranks = ["8", "7", "6", "5", "4", "3", "2", "1"]
    files = ["a", "b", "c", "d", "e", "f", "g", "h"]
    fen_parts = []

    for rank in ranks:
        empty_count = 0
        rank_fen = ""
        for file in files:
            square = f"{file}{rank}"
            piece = board_state.get(square, "empty")
            if piece == "empty":
                empty_count += 1
            else:
                if empty_count > 0:
                    rank_fen += str(empty_count)
                    empty_count = 0
                rank_fen += piece_to_fen(piece)
        if empty_count > 0:
            rank_fen += str(empty_count)
        fen_parts.append(rank_fen)

    # Combine FEN parts
    fen_board = "/".join(fen_parts)
    side_to_move = player_color
    castling_availability = "-"  # No castling info yet
    en_passant_target = "-"  # No en passant info yet

    return f"{fen_board} {side_to_move} {castling_availability} {en_passant_target} {halfmove_clock} {fullmove_number}"


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


if __name__ == "__main__":
    if check_initial_setup():
        print("Initial checks are completed correctly.")
        while True:
            print("\nWhite's turn.")
            handle_human_turn()
            if is_checkmate_or_stalemate(json.load(open("chess_board.json")), "b"):
                break

            print("\nBlack's turn.")
            handle_bot_turn()
            if is_checkmate_or_stalemate(json.load(open("chess_board.json")), "w"):
                break
    else:
        print("Initial check failed.")
