from main import arrays_are_equal
from scripts import pieces
import numpy as np


class Board:
	KILL_ALL = 0
	KILL_ANY = 1

	def __init__(self, squares: int, victory_condition=None):
		if victory_condition is None:
			victory_condition = self.KILL_ALL

		self.squares = squares
		self.victory_condition = victory_condition

		self.winner = None
		self.init_player_pieces_count = 0
		self.init_enemy_pieces_count = 0

		self.reset()

	def reset(self):
		self.winner = None
		self.reset_pieces()

	def get_piece_legal_moves(self, piece, from_pos=None):
		if from_pos is not None:
			piece_moves = piece.steps + from_pos
		else:
			piece_moves = piece.steps + piece.pos

		def checker(move):
			return self.check_is_move_legal(move, piece)

		piece_legal_moves_filter = np.array(list(map(checker, piece_moves)))
		piece_legal_moves = piece_moves[piece_legal_moves_filter]

		return piece_legal_moves

	def check_is_move_legal(self, move, this_piece):
		if not self.check_pos_is_valid(move):
			return False
		piece = self.try_get_piece_by_pos(move)
		if piece and piece.is_player == this_piece.is_player:
			return False
		return True

	def check_pos_is_valid(self, pos):
		if not (0 <= pos[0] < self.squares):
			return False
		if not (0 <= pos[1] < self.squares):
			return False
		return True

	def is_move_safe_check(self, piece, move):
		is_safe = True
		for possible_killer in self._get_pieces(is_player=not piece.is_player):
			possible_killer_legal_moves = self.get_piece_legal_moves(possible_killer)
			if (np.equal(move, possible_killer_legal_moves)).all(axis=1).any():
				is_safe = False
				break
		return is_safe

	def get_safe_moves(self, piece, from_pos=None):
		legal_moves = self.get_piece_legal_moves(piece, from_pos=from_pos)
		safe_moves = []
		for move in legal_moves:
			if self.is_move_safe_check(piece, move):
				safe_moves.append(move)
		return np.array(safe_moves)

	def _get_pieces(self, is_player):
		filtered_pieces = list()
		for line in self.pieces:
			for piece in line:
				if piece and piece.is_player is is_player:
					filtered_pieces.append(piece)
		return filtered_pieces

	def get_player_pieces(self):
		return self._get_pieces(True)

	def get_enemy_pieces(self):
		return self._get_pieces(False)

	def reset_pieces(self):
		self.pieces = [[None for _ in range(self.squares)] for _ in range(self.squares)]
		self.init_player_pieces_count = 0
		self.init_enemy_pieces_count = 0

		for column in range(self.squares):
			self.add_mirrored_pieces(pieces.Triangle, np.array([column, self.squares - 2]))

			if column in (0, self.squares - 1):
				self.add_mirrored_pieces(pieces.Diamond, np.array([column, self.squares - 1]))
			elif column in (1, self.squares - 2):
				self.add_mirrored_pieces(pieces.Square, np.array([column, self.squares - 1]))
			elif column in (2, self.squares - 3):
				self.add_mirrored_pieces(pieces.Circle, np.array([column, self.squares - 1]))
			elif self.squares >= 9 and column == (self.squares - 1) / 2:
				self.add_mirrored_pieces(pieces.Ring, np.array([column, self.squares - 1]))
			elif self.squares // 2 <= column <= self.squares - 4:
				self.add_mirrored_pieces(pieces.Cross, np.array([column, self.squares - 1]))
			else:
				self.add_mirrored_pieces(pieces.Octagon, np.array([column, self.squares - 1]))

	def add_mirrored_pieces(self, piece_class, pos):
		player_piece_pos = pos
		enemy_piece_pos = np.array([self.squares - 1] * 2) - pos
		player_piece = piece_class(player_piece_pos, is_player=True)
		enemy_piece = piece_class(enemy_piece_pos, is_player=False)
		self.pieces[player_piece_pos[0]][player_piece_pos[1]] = player_piece
		self.pieces[enemy_piece_pos[0]][enemy_piece_pos[1]] = enemy_piece
		self.init_player_pieces_count += 1
		self.init_enemy_pieces_count += 1

	def try_get_piece_by_pos(self, pos):
		return self.pieces[pos[0]][pos[1]]

	def try_to_make_move(self, start_pos, end_pos):
		if self.is_move_valid_check(start_pos, end_pos):
			self.process_move(start_pos, end_pos)
			return True
		return False

	def is_move_valid_check(self, start_pos, end_pos):
		if not (self.check_pos_is_valid(start_pos) and self.check_pos_is_valid(end_pos)):
			return False
		if arrays_are_equal(start_pos, end_pos):
			return False

		selected_piece = self.try_get_piece_by_pos(start_pos)
		target_piece = self.try_get_piece_by_pos(end_pos)

		if not isinstance(selected_piece, pieces.Piece):
			return False
		if (target_piece is not None) and (selected_piece.is_player == target_piece.is_player):
			return False
		return True

	def get_last_rank(self, piece):
		return (self.squares - 1, 0)[piece.is_player]

	def process_move(self, start_pos, end_pos):
		selected_piece = self.try_get_piece_by_pos(start_pos)
		target_piece = self.try_get_piece_by_pos(end_pos)

		selected_piece.pos = end_pos
		self.pieces[end_pos[0]][end_pos[1]] = selected_piece
		self.pieces[start_pos[0]][start_pos[1]] = None

		reached_last_rank = end_pos[1] == self.get_last_rank(selected_piece)

		if reached_last_rank:
			self.promote(selected_piece)
		elif target_piece and target_piece.value > selected_piece.value:
			self.pieces[end_pos[0]][end_pos[1]] = target_piece.__class__(end_pos, selected_piece.is_player)

		self.check_end_of_game()

	def promote(self, piece):
		x, y = piece.pos
		if isinstance(piece, pieces.Triangle):
			self.pieces[x][y] = pieces.Ring(piece.pos, piece.is_player)
		elif type(piece) in (pieces.Square, pieces.Diamond, pieces.Circle, pieces.Octagon):
			self.pieces[x][y] = pieces.Cross(piece.pos, piece.is_player)

	def check_end_of_game(self):
		if self.victory_condition == self.KILL_ALL:
			if len(self.get_enemy_pieces()) == 0:
				self.winner = "player"
			elif len(self.get_player_pieces()) == 0:
				self.winner = "enemy"
		elif self.victory_condition == self.KILL_ANY:
			if len(self.get_enemy_pieces()) < self.init_enemy_pieces_count:
				self.winner = "player"
			elif len(self.get_player_pieces()) < self.init_player_pieces_count:
				self.winner = "enemy"
