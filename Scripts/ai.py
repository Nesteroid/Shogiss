import random
import numpy as np


class SimpleAI:
	'''safe endagered piece!'''
	def __init__(self, board):
		self.board = board

	def make_move(self):
		my_pieces = self.board.get_pieces(is_player=False)
		random.shuffle(my_pieces)

		if self.try_safe_eat_player(my_pieces): return

		if self.try_run_from_player(my_pieces): return
			
		if self.try_trade(my_pieces): return
		
		if (random.random() <= self.board.difficulty) and self.try_safe_defended_attack_move(my_pieces): return
		
		if self.try_make_safe_forward_move(my_pieces): return
		
		if self.try_safe_defend_move(my_pieces): return

		if self.try_make_safe_move(my_pieces): return
		
		# if self.try_eat_player(my_pieces): return
		
		if (random.random() <= self.board.difficulty) and self.try_defended_attack_move(my_pieces): return

		if self.try_trade_attack_move(my_pieces): return
		
		if self.try_defend_move(my_pieces): return
		
		self.make_random_move(my_pieces)

	def try_make_safe_forward_move(self, my_pieces):
		for piece in my_pieces:
			safe_moves = self.board.get_safe_moves(piece)	
			np.random.shuffle(safe_moves)
			for move in safe_moves:
				is_moving_forward = (piece.forward[1] > 0 and (move[1] - piece.pos[1]) > 0) or (piece.forward[1] < 0 and (move[1] - piece.pos[1]) < 0)
				if is_moving_forward and self.board.try_to_make_move(piece.pos, move):
					# print(piece.forward, move)
					# print("try_make_safe_forward_move")
					return True
		return False
	
	def try_trade(self, my_pieces):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				target_piece = self.board.try_get_piece_by_pos(move)
				if target_piece and self.is_trade_cost_it_check(piece, target_piece, move):
					if self.board.try_to_make_move(piece.pos, move):
						# print("try_trade")
						return True
		return False

	def is_trade_cost_it_check(self, piece, target_piece, move):
		if target_piece.value >= piece.get_value_after_eating(target_piece):
			max_killer_value = 0
			for player_piece in self.board.get_pieces():
				player_piece_legal_moves = self.board.get_piece_legal_moves(player_piece)
				if ((piece.pos + move) == self.board.get_piece_legal_moves(player_piece)).all(1).any():
					max_killer_value = max(max_killer_value, player_piece.get_value_after_eating(piece))
			if (max_killer_value <= piece.get_value_after_eating(target_piece)):
				return True
	
	def try_defended_attack_move(self, my_pieces):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				for player_piece in self.board.get_pieces():
					if (player_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						other_pieces = list(filter(lambda other_piece: other_piece != piece, my_pieces))
						random.shuffle(other_pieces)
						for other_piece in other_pieces:
							if ((piece.pos + move) == self.board.get_piece_legal_moves(other_piece)).all(1).any():
								
								# # print(piece, piece.pos + move, other_piece, self.board.get_piece_legal_moves(other_piece)) ##########
								
								if self.board.try_to_make_move(piece.pos, move):
									# print("try_defended_attack_move")
									return True
	
	def try_safe_defended_attack_move(self, my_pieces):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				for player_piece in self.board.get_pieces():
					if (player_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						other_pieces = list(filter(lambda other_piece: other_piece != piece, my_pieces))
						random.shuffle(other_pieces)
						for other_piece in other_pieces:
							if ((piece.pos + move) == self.board.get_piece_legal_moves(other_piece)).all(1).any():
								if self.board.is_move_safe_check(piece, move) and self.board.try_to_make_move(piece.pos, move):
									# print("try_safe_defended_attack_move")
									return True
	
	def try_trade_attack_move(self, my_pieces):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				for target_piece in self.board.get_pieces():
					if (target_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						if target_piece and self.is_trade_cost_it_check(piece, target_piece, move):
							if self.board.try_to_make_move(piece.pos, move):
								# print("try_trade_attack_move")
								return True
	
	def try_defend_move(self, my_pieces):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				other_pieces = list(filter(lambda other_piece: other_piece != piece, my_pieces))
				random.shuffle(other_pieces)
				for other_piece in other_pieces:
					if (other_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						if self.board.try_to_make_move(piece.pos, move):
							# print("try_defend_move")
							return True
		return False
	
	def try_safe_defend_move(self, my_pieces):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				other_pieces = list(filter(lambda other_piece: other_piece != piece, my_pieces))
				random.shuffle(other_pieces)
				for other_piece in other_pieces:
					if (other_piece.pos == self.board.get_piece_legal_moves(piece, move)).all(1).any():
						if self.board.is_move_safe_check(piece, move) and self.board.try_to_make_move(piece.pos, move):
							# print("try_safe_defend_move")
							return True
		return False

	def make_random_move(self, my_pieces):
		# print("make_random_move")

		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				if self.board.try_to_make_move(piece.pos, move):
					return

	def try_run_from_player(self, my_pieces):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			for move in piece_legal_moves:
				for player_piece in self.board.get_pieces():
					player_piece_legal_moves = self.board.get_piece_legal_moves(player_piece)
					if (piece.pos == player_piece_legal_moves).all(axis=1).any():
						if self.board.is_move_safe_check(piece, move) and self.board.try_to_make_move(piece.pos, move):
							# print("try_run_from_player")
							return True
		return False

	def try_eat_player(self, my_pieces):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			
			for move in piece_legal_moves:
				target_piece = self.board.try_get_piece_by_pos(move)
				if target_piece and self.board.try_to_make_move(piece.pos, move):
					# print("try_eat_player")
					return True
		return False

	def try_safe_eat_player(self, my_pieces):
		for piece in my_pieces:
			piece_legal_moves = self.board.get_piece_legal_moves(piece)
			np.random.shuffle(piece_legal_moves)
			
			for move in piece_legal_moves:
				target_piece = self.board.try_get_piece_by_pos(move)
				if target_piece and self.board.is_move_safe_check(piece, move) and self.board.try_to_make_move(piece.pos, move):
					# print("try_safe_eat_player")
					return True
		return False

	def try_make_safe_move(self, my_pieces):
		for piece in my_pieces:
			safe_moves = self.board.get_safe_moves(piece)
			np.random.shuffle(safe_moves)
			for move in safe_moves:
				if self.board.try_to_make_move(piece.pos, move):
					# print("try_make_safe_move")
					return True
		return False
