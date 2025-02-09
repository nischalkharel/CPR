import json

def read_chessboard(file_path):
    try:
        with open(file_path, 'r') as file:
            chessboard = json.load(file)
            return chessboard
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return None
    
    

def validate_initial_setup(chessboard):
    if chessboard is None:
        return False, "Invalid chessboard data. Cannot validate."
    
    # Expected starting position for all pieces
    expected_pieces = {
        "a8": "black_rook", "b8": "black_knight", "c8": "black_bishop", "d8": "black_queen",
        "e8": "black_king", "f8": "black_bishop", "g8": "black_knight", "h8": "black_rook",
        "a7": "black_pawn", "b7": "black_pawn", "c7": "black_pawn", "d7": "black_pawn",
        "e7": "black_pawn", "f7": "black_pawn", "g7": "black_pawn", "h7": "black_pawn",
        
        "a2": "white_pawn", "b2": "white_pawn", "c2": "white_pawn", "d2": "white_pawn",
        "e2": "white_pawn", "f2": "white_pawn", "g2": "white_pawn", "h2": "white_pawn",
        "a1": "white_rook", "b1": "white_knight", "c1": "white_bishop", "d1": "white_queen",
        "e1": "white_king", "f1": "white_bishop", "g1": "white_knight", "h1": "white_rook"
    }

    # Check for missing or misplaced pieces
    for square, expected_piece in expected_pieces.items():
        actual_piece = chessboard.get(square)
        if actual_piece != expected_piece:
            return False, f"Error at {square}: Expected {expected_piece}, Found {actual_piece or 'empty'}"

    # Check for unexpected pieces on empty squares
    for square, piece in chessboard.items():
        if square not in expected_pieces and piece != "empty":
            return False, f"Unexpected piece at {square}: Found {piece}"

    return True, "Board is correctly initialized."



