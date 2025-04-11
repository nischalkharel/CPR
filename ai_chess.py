import chess
import chess.engine

class AIChess:
    def __init__(self, engine_path=r"/usr/games/stockfish"):
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.board = None

    def set_position(self, fen):
        self.board = chess.Board(fen)

    def get_next_move(self, depth=None, time_limit=None):
        if depth:
            result = self.engine.play(self.board, chess.engine.Limit(depth=depth))
        elif time_limit:
            result = self.engine.play(self.board, chess.engine.Limit(time=time_limit))
        else:
            result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        return result.move

    def is_checkmate(self):
        """Check if the current board state is a checkmate."""
        return self.board.is_checkmate()

    def is_stalemate(self):
        """Check if the current board state is a stalemate."""
        return self.board.is_stalemate()

    def close_engine(self):
        self.engine.quit()
        
    def get_ai_move(self,difficulty = "medium"):
        TIME_LIMIT = .5
        if difficulty == "easy":
            TIME_LIMIT = .5
        elif difficulty == "medium":
            TIME_LIMIT = 1
        else:
            TIME_LIMIT = 3

        result = self.engine.play(self.board, chess.engine.Limit(time=TIME_LIMIT))  # Adjust time for difficulty
        move = result.move.uci() 
        return [move[:2], move[2:4]]
