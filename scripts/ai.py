import random
import numpy as np


class SimpleAI:
	def __init__(self, board, difficulty):
		self.board = board
		self.difficulty = difficulty
		self.algorithm = [
			self.try_safe_eat_player,
			self.try_run_from_player,
			self.try_trade,
			self.try_safe_defended_attack_move,
			self.try_make_safe_forward_move,
			self.try_safe_defend_move,
			self.try_make_safe_move,
			self.try_defended_attack_move,
			self.try_trade_attack_move,
			self.try_defend_move,
		]

	def is_smart_enough_to_move(self):
		return random.random() <= self.difficulty

	def get_move(self):
		my_pieces = self.board.get_enemy_pieces()
		enemy_pieces = self.board.get_player_pieces()
		
		# under same conditions, the moves can be different
		random.shuffle(my_pieces)
		random.shuffle(enemy_pieces)

		for action in self.algorithm:
			if self.is_smart_enough_to_move():
				if move := action(my_pieces, enemy_pieces):
					return move
		
		# couldn't make smart moves
		return self.get_random_move(my_pieces, enemy_pieces)

	def is_trade_cost_it_check(self, piece, target_piece, move, enemy_pieces):
		if target_piece.value >= piece.get_value_after_eating(target_piece):
			max_killer_value = 0
			for enemy_piece in enemy_pieces:
				if ((piece.pos + move) == self.board.get_piece_legal_moves(enemy_piece)).all(1).any():
					max_killer_value = max(max_killer_value, enemy_piece.get_value_after_eating(piece))
			if (max_killer_value <= piece.get_value_after_eating(target_piece)):
				return True

	def try_make_safe_forward_move(self, my_pieces: list, _):
		for piece in my_pieces:
			safe_moves = self.board.get_safe_moves(piece)	
			np.random.shuffle(safe_moves)
			for move in safe_moves:
				is_moving_forward = (piece.forward[1] > 0 and (move[1] - piece.pos[1]) > 0) or (piece.forward[1] < 0 and (move[1] - piece.pos[1]) < 0)
				if is_moving_forward:
					return piece.pos, move
		return False
	
	def try_trade(self, my_pieces: list, enemy_pieces: list):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				target_piece = self.board.try_get_piece_by_pos(move)
				if target_piece and self.is_trade_cost_it_check(piece, target_piece, move, enemy_pieces):
					return piece.pos, move
		return False
	
	def try_defended_attack_move(self, my_pieces: list, enemy_pieces: list):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				for enemy_piece in enemy_pieces:
					if (enemy_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						other_pieces = list(filter(lambda other_piece: other_piece != piece, my_pieces))
						random.shuffle(other_pieces)
						for other_piece in other_pieces:
							if ((piece.pos + move) == self.board.get_piece_legal_moves(other_piece)).all(1).any():
								return piece.pos, move
		return False
	
	def try_safe_defended_attack_move(self, my_pieces: list, enemy_pieces: list):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				for enemy_piece in enemy_pieces:
					if (enemy_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						other_pieces = list(filter(lambda other_piece: other_piece != piece, my_pieces))
						random.shuffle(other_pieces)
						for other_piece in other_pieces:
							if ((piece.pos + move) == self.board.get_piece_legal_moves(other_piece)).all(1).any():
								if self.board.is_move_safe_check(piece, move):
									return piece.pos, move
		return False
	
	def try_trade_attack_move(self, my_pieces: list, enemy_pieces: list):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				for target_piece in enemy_pieces:
					if (target_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						if target_piece and self.is_trade_cost_it_check(piece, target_piece, move, enemy_pieces):
							return piece.pos, move
		return False

	# defend most valuable (endangered) (with safe defend)
	def try_defend_move(self, my_pieces: list, _):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				other_pieces = list(filter(lambda other_piece: other_piece != piece, my_pieces))
				random.shuffle(other_pieces)
				for other_piece in other_pieces:
					if (other_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						return piece.pos, move
		return False
	
	def try_safe_defend_move(self, my_pieces: list, _):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				other_pieces = list(filter(lambda other_piece: other_piece != piece, my_pieces))
				random.shuffle(other_pieces)
				for other_piece in other_pieces:
					if (other_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						if self.board.is_move_safe_check(piece, move):
							return piece.pos, move
		return False

	def try_run_from_player(self, my_pieces: list, enemy_pieces: list):
		pieces_under_threat = dict()
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			for move in piece_legal_moves:
				for enemy_piece in enemy_pieces:
					enemy_piece_legal_moves = self.board.get_piece_legal_moves(enemy_piece)
					if (piece.pos == enemy_piece_legal_moves).all(axis=1).any():
						if self.board.is_move_safe_check(piece, move):
							pieces_under_threat[piece] = (piece.pos, move)
		if len(pieces_under_threat) > 0:
			most_valuable = max(pieces_under_threat, key=lambda p: p.value)
			return pieces_under_threat[most_valuable]
		return False

	def try_safe_eat_player(self, my_pieces: list, _):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			
			for move in piece_legal_moves:
				target_piece = self.board.try_get_piece_by_pos(move)
				if target_piece and self.board.is_move_safe_check(piece, move):
					return piece.pos, move
		return False

	def try_make_safe_move(self, my_pieces: list, _):
		for piece in my_pieces:
			safe_moves = self.board.get_safe_moves(piece)
			np.random.shuffle(safe_moves)
			if len(safe_moves) > 0:
				return piece.pos, safe_moves[0]
		return False

	def get_random_move(self, my_pieces: list, _):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			if len(piece_legal_moves) > 0:
				return piece.pos, piece_legal_moves[0]
