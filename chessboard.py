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
        self.piece_positions = {
            "a1": "R{B}", "b1": "N{B}", "c1": "B{B}", "d1": "Q{B}", "e1": "K{B}",
            "f1": "B{B}", "g1": "N{B}", "h1": "R{B}",
            "a2": "P{B}", "b2": "P{B}", "c2": "P{B}", "d2": "P{B}", "e2": "P{B}",
            "f2": "P{B}", "g2": "P{B}", "h2": "P{B}",
            "a7": "P{W}", "b7": "P{W}", "c7": "P{W}", "d7": "P{W}", "e7": "P{W}",
            "f7": "P{W}", "g7": "P{W}", "h7": "P{W}",
            "a8": "R{W}", "b8": "N{W}", "c8": "B{W}", "d8": "K{W}", "e8": "Q{W}",
            "f8": "B{W}", "g8": "N{W}", "h8": "R{W}"
        }

        # Initialize empty positions for rows 3 to 6
        for row in range(3, 7):
            for col in "abcdefgh":
                self.piece_positions[f"{col}{row}"] = "empty"

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
                expected_piece = self.piece_positions.get(position, "empty")

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
                time.sleep(3)
                # Double-check to ensure stability
                os.system('clear' if os.name == 'posix' else 'cls')
                recheck_errors = []
                for position, pin in self.all_pins.items():
                    piece_present = not pin.value
                    expected_piece = self.piece_positions.get(position, "empty")

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
            expected_piece = self.piece_positions.get(position, "empty")

            if piece_present:
                piece_name = self.translate_piece(expected_piece)
            else:
                piece_name = "empty"

            board_state[position] = piece_name

        with open("chessboard.json", "w") as json_file:
            json.dump(board_state, json_file, indent=4)

        print("\nChess board state saved to chessboard.json.")

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
        
    def currentVSprevious_board_states(self):
        """Compare current GPIO state with previous board state stored in pre_turn_board.json."""
        changed_squares = {}

        with open("pre_turn_board.json", "r") as file:
            previous_board = json.load(file)

        for position, pin in self.all_pins.items():
            current_state = "empty" if pin.value else "piece"
            previous_state = previous_board.get(position)

            if (current_state == "piece" and previous_state == "empty") or (current_state == "empty" and previous_state != "empty"):
                changed_squares[position] = current_state

        return changed_squares

    
