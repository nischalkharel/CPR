from board_manager import read_chessboard, validate_initial_setup

chessboard = read_chessboard("C:/Users/nisch/Desktop/CPR/chessboard.json")

if chessboard:
    is_valid, message = validate_initial_setup(chessboard)
    print(message)
else:
    print("Cannot validate chessboard. Invalid chessboard file.")