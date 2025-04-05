import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
from digitalio import Direction, Pull
import time
import os
import json
import shutil

class ChessSetupChecker:
    def __init__(self, i2c):
        # Initialize MCP23017 instances
        self.mcp_0x25 = MCP23017(i2c, address=0x25)
        self.mcp_0x27 = MCP23017(i2c, address=0x27)
        self.mcp_0x26 = MCP23017(i2c, address=0x26)
        self.mcp_0x23 = MCP23017(i2c, address=0x23)

        # Map pins to chessboard positions
        self.all_pins = self.map_pins()
        
        # Define expected initial positions
        self.initial_positions = {
            "a1": "R{W}", "b1": "N{W}", "c1": "B{W}", "d1": "Q{W}", "e1": "K{W}",
            "f1": "B{W}", "g1": "N{W}", "h1": "R{W}",
            "a2": "P{W}", "b2": "P{W}", "c2": "P{W}", "d2": "P{W}", "e2": "P{W}",
            "f2": "P{W}", "g2": "P{W}", "h2": "P{W}",
            "a7": "P{B}", "b7": "P{B}", "c7": "P{B}", "d7": "P{B}", "e7": "P{B}",
            "f7": "P{B}", "g7": "P{B}", "h7": "P{B}",
            "a8": "R{B}", "b8": "N{B}", "c8": "B{B}", "d8": "K{B}", "e8": "Q{B}",
            "f8": "B{B}", "g8": "N{B}", "h8": "R{B}"
        }

        # Initialize empty positions for rows 3 to 6
        for row in range(3, 7):
            for col in "abcdefgh":
                self.initial_positions[f"{col}{row}"] = "empty"

    def map_pins(self):
        """Map MCP23017 pins to chessboard positions with correct wiring."""
        pins = {}

        def map_row(mcp, port, start_square, reverse=True):
            col_order = "hgfedcba" if reverse else "abcdefgh"
            row = start_square[1]
            for i, col in enumerate(col_order):
                pin = mcp.get_pin(i if port == 'a' else i + 8)
                pin.direction = Direction.INPUT
                pin.pull = Pull.UP
                pins[f"{col}{row}"] = pin

        # 0x27 - Rows 1 (port B) and 2 (port A)
        map_row(self.mcp_0x27, 'b', 'h1')  # h1 to a1
        map_row(self.mcp_0x27, 'a', 'h2')  # h2 to a2

        # 0x23 - Rows 3 (port A) and 4 (port B)
        map_row(self.mcp_0x23, 'a', 'h3')  # h3 to a3
        map_row(self.mcp_0x23, 'b', 'h4')  # h4 to a4

        # 0x26 - Rows 5 (port B) and 6 (port A)
        map_row(self.mcp_0x26, 'b', 'h5')  # h5 to a5
        map_row(self.mcp_0x26, 'a', 'h6')  # h6 to a6

        # 0x25 - Rows 7 (port B) and 8 (port A)
        map_row(self.mcp_0x25, 'b', 'h7')  # h7 to a7
        map_row(self.mcp_0x25, 'a', 'h8')  # h8 to a8

        return pins

    def generate_initial_chess_setup(self):
        """Continuously check the entire chessboard setup until valid."""
        while True:
            time.sleep(0.1)
            os.system('clear' if os.name == 'posix' else 'cls')
            errors = []
            for position, pin in self.all_pins.items():
                piece_present = not pin.value  # Low means piece present
                expected_piece = self.initial_positions.get(position, "empty")

                if expected_piece == "empty" and piece_present:
                    errors.append(f"Unexpected piece on {position}")
                elif expected_piece != "empty" and not piece_present:
                    errors.append(f"{expected_piece} is not on {position} as expected")

            if errors:
                print("\nInitial setup errors detected:")
                for error in errors:
                    print(f"- {error}")
                print("\nRechecking continuously...")
                time.sleep(0.1)
            else:
                print("\nNo errors detected. Validating stability...")
                time.sleep(2)
                # Double-check to ensure stability
                os.system('clear' if os.name == 'posix' else 'cls')
                recheck_errors = []
                for position, pin in self.all_pins.items():
                    piece_present = not pin.value
                    expected_piece = self.initial_positions.get(position, "empty")

                    if expected_piece == "empty" and piece_present:
                        recheck_errors.append(f"Unexpected piece on {position}")
                    elif expected_piece != "empty" and not piece_present:
                        recheck_errors.append(f"{expected_piece} is not on {position} as expected")

                if not recheck_errors:
                    print("\nInitial setup is valid and stable.")
                    self.save_chess_board_state()
                    return True
                else:
                    print("\nErrors detected on recheck. Continuing...")

    def save_chess_board_state(self):
        """Save the current board state to a JSON file."""
        board_state = {}
        for position, pin in self.all_pins.items():
            piece_present = not pin.value  # Low means piece present
            expected_piece = self.initial_positions.get(position, "empty")

            if piece_present:
                piece_name = self.translate_piece(expected_piece)
            else:
                piece_name = "empty"

            board_state[position] = piece_name

        with open("chess_board.json", "w") as json_file:
            json.dump(board_state, json_file, indent=4)

        print("\nChess board state saved to chess_board.json.")

    def translate_piece(self, piece_code):
        """Translate piece codes to descriptive names."""
        piece_map = {
            "R{W}": "white_rook", "N{W}": "white_knight", "B{W}": "white_bishop", 
            "Q{W}": "white_queen", "K{W}": "white_king", "P{W}": "white_pawn",
            "R{B}": "black_rook", "N{B}": "black_knight", "B{B}": "black_bishop", 
            "Q{B}": "black_queen", "K{B}": "black_king", "P{B}": "black_pawn",
            "empty": "empty"
        }
        return piece_map.get(piece_code, "unknown_piece")

    def track_progress_chessboard(self):
        """Track and update the progress of the chessboard continuously."""
        #print("\nTracking progress and saving to progress_chess_board.json...")
    
        with open("progress_chess_board.json", "r") as progress_file:
            progress_board = json.load(progress_file)

        with open("chess_board_incomplete.json", "r") as incomplete_file:
            incomplete_board = json.load(incomplete_file)

        updated_board = progress_board.copy()
        for position, pin in self.all_pins.items():
            piece_present = not pin.value  # Low means piece present
            incomplete_piece = incomplete_board[position]
            progress_piece = progress_board[position]

            if not piece_present and incomplete_piece != "empty":
                updated_board[position] = "empty"
                #print("empty detected")
            elif piece_present and incomplete_piece == "empty" and progress_piece != "unknown":
                updated_board[position] = "unknown"
                #print("unknown detected")

        with open("progress_chess_board.json", "w") as progress_file:
            json.dump(updated_board, progress_file, indent=4)

        time.sleep(0.5)  # Delay for validation

    
