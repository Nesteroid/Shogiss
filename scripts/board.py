from main import pyinstaller_image_load
from scripts import ai, pieces
from scripts.layout import Layout
from numba import njit
import numpy as np
import pygame


@njit(cache=True, fastmath=True)
def arrays_are_equal(a: np.array, b: np.array):
	return (np.equal(a, b)).all()


class BoardUI(Layout):
	def __init__(self, board, size: tuple, AI_enabled: bool, difficulty: float):
		self.board = board

		self.player_image_names = dict()
		self.enemy_image_names = dict()
		self.piece_image_names = dict()

		self.setup_image_names()

		self.assets_path = "assets\\default\\"
		self.piece_images = {"player": dict(), "enemy": dict()}
		self.scaled_piece_images = {"player": dict(), "enemy": dict()}

		super().__init__(size)

		self.selected_piece = None
		self.selected_piece_moves = None
		self.selected_piece_valid_moves = None
		self.highlighted_squares = list()

		self.check_pattern_surf = None

		self.AI = ai.SimpleAI(self.board, difficulty)
		self.AI_enabled = AI_enabled

		self.is_player_move = True

	def setup_image_names(self):
		from scripts.pieces import Diamond, Triangle, Square, Circle, Pentagon, Octagon, Ring
		self.player_image_names = {
			Diamond: "WhiteYellowishOrange.png",
			Triangle: "WhiteLime.png",
			Square: "WhitePink.png",
			Circle: "WhitePurple.png",
			Pentagon: "WhiteBlueLagoon.png",
			Octagon: "WhiteViolet.png",
			Ring: "White.png",
		}
		self.enemy_image_names = {
			Diamond: "BlackYellowishOrange.png",
			Triangle: "BlackLime.png",
			Square: "BlackPink.png",
			Circle: "BlackPurple.png",
			Pentagon: "BlackBlueLagoon.png",
			Octagon: "BlackViolet.png",
			Ring: "Black.png",
		}

		self.piece_image_names = {
			"player": self.player_image_names,
			"enemy": self.enemy_image_names
		}

	def _on_resize(self):
		self.square_size = self.min_ / self.board.squares
		self.board_size = self.square_size * self.board.squares
		self.square_border_radius = round(self.square_size * 0.2)
		self.offset = (self.size - self.board_size) // 2

		self.pieces_surf = pygame.Surface([self.board_size] * 2)
		self.pieces_surf_size = np.array([self.board_size] * 2)
		self.pieces_surf.set_colorkey("black")

		self.update_check_image()
		self.update_piece_images()

	def update_piece_images(self):
		for side, dict_image_names in self.piece_image_names.items():
			for piece_class, image_name in dict_image_names.items():
				image = pyinstaller_image_load(self.assets_path, image_name).convert_alpha()
				image = pygame.transform.smoothscale(image, [int(self.square_size)]*2)
				self.piece_images[side][piece_class] = image

	def update_check_image(self):
		self.check_pattern_surf = pygame.Surface([self.board_size] * 2)
		self.check_pattern_surf.set_colorkey("black")

		for i in range(self.board.squares):
			for j in range(self.board.squares):
				piece_surf_position = (self.square_size * i, self.square_size * j)

				color = "gray20" if (i + j) % 2 else "gray60"
				pygame.draw.rect(self.check_pattern_surf, color,
				                 (*piece_surf_position, self.square_size, self.square_size),
				                 border_radius=self.square_border_radius)

	def restart(self):
		self.is_player_move = True
		self.board.reset()
		self._on_resize()

	def on_mouse_click(self):
		if self.board.winner is not None:
			return

		pieces_surf_mouse_pos = np.array(pygame.mouse.get_pos()) - self.offset
		mouse_clicked_on_board = ((0 <= pieces_surf_mouse_pos) & (pieces_surf_mouse_pos <= self.pieces_surf_size)).all()

		if not mouse_clicked_on_board:
			return

		on_board_position = pieces_surf_mouse_pos // self.square_size

		piece = self.board.try_get_piece_by_pos(on_board_position)  # SLOW

		is_reachable = self.selected_piece and (np.equal(on_board_position, self.highlighted_squares)).all(axis=1).any()

		if is_reachable:
			chosen_piece_is_allied = piece and self.selected_piece.is_player == piece.is_player
			if chosen_piece_is_allied:
				self.selected_piece = piece
				self.highlighted_squares = self.board.get_piece_legal_moves(piece)
			elif self.selected_piece.is_player != self.is_player_move:
				self.selected_piece = None
			elif self.board.try_to_make_move(self.selected_piece.pos, on_board_position):
				self.is_player_move = not self.is_player_move
				self.selected_piece = None
		elif piece:
			if piece != self.selected_piece:
				self.selected_piece = piece
				self.highlighted_squares = self.board.get_piece_legal_moves(piece)
			else:
				self.selected_piece = None

	def draw(self, window):
		pieces_surf_mouse_pos = np.array(pygame.mouse.get_pos()) - self.offset
		self.pieces_surf.blit(self.check_pattern_surf, (0, 0))

		for i in range(self.board.squares):
			for j in range(self.board.squares):
				on_board_position = np.array([i, j])
				piece_surf_position = on_board_position * self.square_size

				piece = self.board.try_get_piece_by_pos(on_board_position)  # SLOW

				is_howered = (piece_surf_position < pieces_surf_mouse_pos).all() and (
						pieces_surf_mouse_pos < piece_surf_position + self.square_size).all()
				is_reachable = self.selected_piece and (np.equal(on_board_position, self.highlighted_squares)).all(
					axis=1).any()

				if self.board.winner is None:
					if is_reachable:
						if self.selected_piece.is_player == self.is_player_move:
							self.highlight_square((72, 194, 68, 150), piece_surf_position)
						else:
							self.highlight_square((194, 89, 68, 150), piece_surf_position)
					if is_howered:
						self.highlight_square((185, 194, 68, 150), piece_surf_position)

				if piece:
					piece_image = self.piece_images[("enemy", "player")[piece.is_player]][piece.__class__]
					self.pieces_surf.blit(piece_image, piece_surf_position)

		window.blit(self.pieces_surf, self.offset)

		if not self.is_player_move and self.AI_enabled:
			self.AI.make_move()
			self.is_player_move = True

	def highlight_square(self, color, position):
		transparent_square = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
		pygame.draw.rect(transparent_square, color, (0, 0, self.square_size, self.square_size),
		                 border_radius=self.square_border_radius)
		self.pieces_surf.blit(transparent_square, position)


class Board:
	def __init__(self, squares: int):
		self.squares = squares
		self.winner = None
		self.pieces = list()
		self.reset()

	def reset(self):
		self.winner = None
		self.reset_pieces()

	def get_piece_legal_moves(self, piece, from_pos=None):
		if from_pos is not None:
			piece_moves = piece.moves + from_pos
		else:
			piece_moves = piece.moves + piece.pos

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
		return np.array(list(filter(lambda piece: is_player == piece.is_player, self.pieces)))

	def get_player_pieces(self):
		return self._get_pieces(True)

	def get_enemy_pieces(self):
		return self._get_pieces(False)

	def reset_pieces(self):
		self.pieces = list()

		for column in range(self.squares):
			self.add_mirrored_pieces(pieces.Diamond, np.array([column, self.squares - 2]))

			if column in (0, self.squares - 1):
				self.add_mirrored_pieces(pieces.Triangle, np.array([column, self.squares - 1]))
			elif column in (1, self.squares - 2):
				self.add_mirrored_pieces(pieces.Square, np.array([column, self.squares - 1]))
			elif column in (2, self.squares - 3):
				self.add_mirrored_pieces(pieces.Pentagon, np.array([column, self.squares - 1]))
			elif self.squares >= 9 and column == (self.squares - 1) / 2:
				self.add_mirrored_pieces(pieces.Ring, np.array([column, self.squares - 1]))
			elif self.squares // 2 <= column <= self.squares - 4:
				self.add_mirrored_pieces(pieces.Octagon, np.array([column, self.squares - 1]))
			else:
				self.add_mirrored_pieces(pieces.Circle, np.array([column, self.squares - 1]))

	def add_mirrored_pieces(self, piece_class, pos):
		player_piece = piece_class(pos, is_player=True)
		enemy_piece = piece_class(np.array([self.squares - 1] * 2) - pos, is_player=False)
		self.pieces.extend([player_piece, enemy_piece])

	def try_get_piece_by_pos(self, pos):
		for piece in self.pieces:
			if arrays_are_equal(piece.pos, pos):
				return piece
		else:
			return None

	def try_to_make_move(self, start_pos, end_pos):
		if self.is_move_valid_check(start_pos, end_pos):
			self.process_move(start_pos, end_pos)
			return True
		return False

	def get_last_rank(self, piece):
		return (self.squares - 1, 0)[piece.is_player]

	def process_move(self, start_pos, end_pos):
		selected_piece = self.try_get_piece_by_pos(start_pos)
		target_piece = self.try_get_piece_by_pos(end_pos)

		selected_piece.pos = end_pos

		reached_last_rank = end_pos[1] == self.get_last_rank(selected_piece)

		if target_piece:
			self.pieces.remove(target_piece)

		if reached_last_rank:
			if isinstance(selected_piece, pieces.Diamond):
				self.pieces.remove(selected_piece)
				self.pieces.append(pieces.Ring(selected_piece.pos, selected_piece.is_player))
			elif isinstance(selected_piece, pieces.Triangle):
				self.pieces.remove(selected_piece)
				self.pieces.append(pieces.Octagon(selected_piece.pos, selected_piece.is_player))
			elif isinstance(selected_piece, pieces.Square):
				self.pieces.remove(selected_piece)
				self.pieces.append(pieces.Circle(selected_piece.pos, selected_piece.is_player))
		elif target_piece and target_piece.value >= selected_piece.value:
			self.pieces.remove(selected_piece)
			self.pieces.append(target_piece.__class__(selected_piece.pos, selected_piece.is_player))

		if len(self.get_enemy_pieces()) == 0:
			self.winner = "player"
		elif len(self.get_player_pieces()) == 0:
			self.winner = "enemy"

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
