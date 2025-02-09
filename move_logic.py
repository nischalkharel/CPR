def detect_move(old_chessboard, new_chessboard):
    changes = []

    for square in old_chessboard:
        if old_chessboard[square] != new_chessboard[square]:
            changes.append(square)

    # Case 1: No moves detected
    if len(changes) == 0:
        return None

    # Case 2: More than two squares changed (indicating multiple moves)
    if len(changes) > 2:
        return changes  # Handle as an error in handle_human_turn

    # Case 3: Single move detected
    moved_from = next((sq for sq in changes if old_chessboard[sq] != "empty" and new_chessboard[sq] == "empty"), None)
    moved_to = next((sq for sq in changes if old_chessboard[sq] == "empty" and new_chessboard[sq] != "empty"), None)

    if moved_from and moved_to:
        return {
            "from": moved_from,
            "to": moved_to,
            "piece": old_chessboard[moved_from],
            "captured": old_chessboard[moved_to] if old_chessboard[moved_to] != "empty" else None
        }

    return None


def validate_move(old_chessboard, move):
    
    piece = move["piece"]
    from_square = move["from"]
    to_square = move["to"]
    captured = move.get("captured")

    if from_square == to_square: # THIS SHOULD NOT REALLY HAPPEN BUT JUST IN CASE
        return False, "Piece did not move."

    # Piece-specific validation
    if "pawn" in piece:
        return validate_pawn_move(old_chessboard, move)
    elif "rook" in piece:
        return validate_rook_move(old_chessboard, move)
    elif "knight" in piece:
        return validate_knight_move(old_chessboard, move)
    elif "bishop" in piece:
        return validate_bishop_move(old_chessboard, move)
    elif "queen" in piece:
        return validate_queen_move(old_chessboard, move)
    elif "king" in piece:
        return validate_king_move(old_chessboard, move)

    return False, "Unknown piece type."

############## SPECIFIC PIECE MOVE VALIDATION FUNCTIONS ##############

def validate_pawn_move(old_chessboard, move):
    from_file, from_rank = move["from"][0], int(move["from"][1])
    to_file, to_rank = move["to"][0], int(move["to"][1])
    direction = 1 if "white" in move["piece"] else -1
    start_rank = 2 if "white" in move["piece"] else 7

    # Forward move
    if from_file == to_file:
        if to_rank - from_rank == direction and old_chessboard[move["to"]] == "empty":
            return True, "Valid pawn move."
        # Double move from starting position
        if from_rank == start_rank and to_rank - from_rank == 2 * direction:
            intermediate_square = f"{from_file}{from_rank + direction}"
            if old_chessboard[intermediate_square] == "empty" and old_chessboard[move["to"]] == "empty":
                return True, "Valid double pawn move."

    # Capturing move
    if abs(ord(to_file) - ord(from_file)) == 1 and to_rank - from_rank == direction:
        if old_chessboard[move["to"]] != "empty":
            return True, "Valid pawn capture."

    return False, "Invalid pawn move."

def validate_rook_move(old_chessboard, move):
    if move["from"][0] == move["to"][0]:  # Moving vertically
        return validate_straight_path(old_chessboard, move, axis="vertical")
    if move["from"][1] == move["to"][1]:  # Moving horizontally
        return validate_straight_path(old_chessboard, move, axis="horizontal")
    return False, "Invalid rook move."

def validate_knight_move(old_chessboard, move):
    dx = abs(ord(move["to"][0]) - ord(move["from"][0]))
    dy = abs(int(move["to"][1]) - int(move["from"][1]))
    #L move
    if (dx, dy) in [(1, 2), (2, 1)]:
        return True, "Valid knight move."
    return False, "Invalid knight move."

def validate_bishop_move(old_chessboard, move):
    dx = abs(ord(move["to"][0]) - ord(move["from"][0]))
    dy = abs(int(move["to"][1]) - int(move["from"][1]))
    if dx == dy:
        return validate_diagonal_path(old_chessboard, move)
    return False, "Invalid bishop move."

def validate_queen_move(old_chessboard, move):
    # Queen combines rook and bishop moves
    rook_valid, _ = validate_rook_move(old_chessboard, move)
    bishop_valid, _ = validate_bishop_move(old_chessboard, move)
    if rook_valid or bishop_valid:
        return True, "Valid queen move."
    return False, "Invalid queen move."

def validate_king_move(old_chessboard, move):
    dx = abs(ord(move["to"][0]) - ord(move["from"][0]))
    dy = abs(int(move["to"][1]) - int(move["from"][1]))
    if max(dx, dy) == 1:
        return True, "Valid king move."
    # TODO: Placeholder for castling (to be implemented)
    return False, "Invalid king move."


########## PATH VALIDATION FUNCTIONS ##########

# Path validation helpers
def validate_straight_path(old_chessboard, move, axis):
    from_square, to_square = move["from"], move["to"]
    step = 1 if axis == "vertical" else ord(to_square[0]) - ord(from_square[0])

    if axis == "vertical":
        col = from_square[0]
        for row in range(min(int(from_square[1]), int(to_square[1])) + 1, max(int(from_square[1]), int(to_square[1]))):
            if old_chessboard[f"{col}{row}"] != "empty":
                return False, "Path is blocked."
    else:  # Horizontal
        row = from_square[1]
        for col in range(min(ord(from_square[0]), ord(to_square[0])) + 1, max(ord(from_square[0]), ord(to_square[0]))):
            if old_chessboard[f"{chr(col)}{row}"] != "empty":
                return False, "Path is blocked."

    return True, "Path is clear."

def validate_diagonal_path(old_chessboard, move):
    from_file, from_rank = ord(move["from"][0]), int(move["from"][1])
    to_file, to_rank = ord(move["to"][0]), int(move["to"][1])

    file_step = 1 if to_file > from_file else -1
    rank_step = 1 if to_rank > from_rank else -1

    current_file = from_file + file_step
    current_rank = from_rank + rank_step

    while current_file != to_file and current_rank != to_rank:
        if old_chessboard[f"{chr(current_file)}{current_rank}"] != "empty":
            return False, "Path is blocked."
        current_file += file_step
        current_rank += rank_step

    return True, "Path is clear."


# special moves like castling not implemented yet