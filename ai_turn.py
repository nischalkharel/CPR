import chess
import chess.engine

STOCKFISH_PATH = r"C:\Users\nisch\stockfish\stockfish.exe"  # TODO: Update the path to Stockfish when running on raspberry pi. 


def chessboard_to_fen(chessboard, ai_color):
    rows = []
    for rank in range(8, 0, -1):
        row = ""
        empty_count = 0
        for file in "abcdefgh":
            square = f"{file}{rank}"
            piece = chessboard.get(square, "empty")

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
        "white_pawn": "P", "black_pawn": "p",
        "white_rook": "R", "black_rook": "r",
        "white_knight": "N", "black_knight": "n",
        "white_bishop": "B", "black_bishop": "b",
        "white_queen": "Q", "black_queen": "q",
        "white_king": "K", "black_king": "k"
    }
    return mapping.get(piece, "")


def get_ai_move(chessboard_fen, ai_color, difficulty = "medium"):
    TIME_LIMIT = .5
    if difficulty == "easy":
        TIME_LIMIT = .5
    elif difficulty == "medium":
        TIME_LIMIT = 1
    else:
        TIME_LIMIT = 3
        
    board = chess.Board(chessboard_fen)

    # Use Stockfish to get the best move
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    result = engine.play(board, chess.engine.Limit(time=20))  # Adjust time for difficulty
    move = result.move  
    engine.quit()
    return move.uci()



def check_game_status(board):
    if board.is_checkmate():
        return "checkmate"
    if board.is_stalemate():
        return "stalemate"
    if board.is_insufficient_material():
        return "draw_insufficient_material"
    if board.is_seventyfive_moves():
        return "draw_75_moves"
    if board.is_fivefold_repetition():
        return "draw_5fold_repetition"
    return None
