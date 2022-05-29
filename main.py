import pygame
import random
import numpy as np
from loguru import logger
from numba import njit
from Scripts import ai, pieces
import os, sys
import time


def pyinstaller_image_load(path, name):
	if getattr(sys, 'frozen', False):
		wd = sys._MEIPASS
	else:
		wd = ''    
	return pygame.image.load(os.path.join(wd, path, name))


@njit(cache=True, fastmath=True)
def arrays_are_equal(a: np.array, b: np.array):
	return (np.equal(a, b)).all()


class Layout:
	def __init__(self, window):
		self.window = window
		self.update()

	def update(self):
		self.size = np.array(self.window.get_size())
		self.width, self.height = self.size
		self.center = self.size / 2
		self.min_ = self.size.min()
		self.max_ = self.size.max()


class Board:
	def __init__(self, win_info, squares, difficulty):
		self.win_info = win_info
		self.squares = squares

		self.difficulty = difficulty

		self.selected_piece = None
		self.selected_piece_moves = None
		self.selected_piece_valid_moves = None
		self.highlighted_squares = None

		self.is_player_move = True
		self.game_ended = False
		self.AI_enabled = True
		self.AI = ai.SimpleAI(self)

		self.reset()

	def reset(self):
		self.is_player_move = True
		self.game_ended = False
		self.reset_pieces()
		self.on_window_resize()

	def on_window_resize(self):
		self.square_size = self.win_info.min_ / self.squares
		self.size = self.square_size*self.squares
		self.square_border_radius = round(self.square_size*0.2)
		self.offset = (self.win_info.size - self.size) // 2

		self.pieces_surf = pygame.Surface([self.size]*2)
		self.pieces_surf_size = np.array([self.size]*2)
		self.pieces_surf.set_colorkey("black")

		self.update_image()

		for piece in self.pieces:
			piece.update_image_size((self.square_size, self.square_size))

	def update_image(self):
		self.check_pattern_surf = pygame.Surface([self.size]*2)
		self.check_pattern_surf.set_colorkey("black")

		for i in range(self.squares):
			for j in range(self.squares):
				piece_surf_position = (self.square_size*i, self.square_size*j)

				color = "gray20" if (i + j) % 2 else "gray60"
				pygame.draw.rect(self.check_pattern_surf, color, (*piece_surf_position, self.square_size, self.square_size), border_radius=self.square_border_radius)

	def get_piece_legal_moves(self, piece, from_pos=None):
		if from_pos is not None:
			piece_moves = piece.moves + from_pos
		else:
			piece_moves = piece.moves + piece.pos
		piece_legal_moves_filter = np.array(list(map(self.check_pos_is_valid, piece_moves)))
		piece_legal_moves = piece_moves[piece_legal_moves_filter]
		return piece_legal_moves

	def is_move_safe_check(self, piece, move):
		is_safe = True
		for possible_killer in self.get_pieces(is_player=not piece.is_player):
			possible_killer_legal_moves = self.get_piece_legal_moves(possible_killer)
			if (move == possible_killer_legal_moves).all(axis=1).any():
				is_safe = False
		return is_safe

	def get_safe_moves(self, piece, from_pos=None):
		legal_moves = self.get_piece_legal_moves(piece, from_pos=from_pos)
		safe_moves = []
		for move in legal_moves:
			if self.is_move_safe_check(piece, move):
				safe_moves.append(move)
		return np.array(safe_moves)

	def get_pieces(self, is_player=True):
		return np.array(list(filter(lambda piece: is_player == piece.is_player, self.pieces)))

	def update(self, window):
		if not self.is_player_move and self.AI_enabled:
			start_time = time.process_time()
			self.AI.make_move()
			end_time = time.process_time()

			logger.info(f"AI CPU Execution time: {end_time - start_time} seconds")

			self.is_player_move = True
			if len(self.get_pieces(is_player=True)) == 0:
				self.game_ended = True

		pieces_surf_mouse_pos = np.array(pygame.mouse.get_pos()) - self.offset
		self.pieces_surf.blit(self.check_pattern_surf, (0, 0))

		for i in range(self.squares):
			for j in range(self.squares):
				on_board_position = np.array([i, j])
				piece_surf_position = on_board_position * self.square_size

				piece = self.try_get_piece_by_pos(on_board_position) # SLOW

				is_howered = (piece_surf_position < pieces_surf_mouse_pos).all() and (pieces_surf_mouse_pos < piece_surf_position + self.square_size).all()
				is_reachable = self.selected_piece and (np.equal(on_board_position, self.highlighted_squares)).all(axis=1).any()

				if not self.game_ended:
					if is_reachable:
						if self.selected_piece.is_player:
							self.highlight_square((72, 194, 68, 150), piece_surf_position)
						else:
							self.highlight_square((194, 89, 68, 150), piece_surf_position)
					if is_howered:
						self.highlight_square((185, 194, 68, 150), piece_surf_position)

				if piece:
					self.pieces_surf.blit(piece.image, piece_surf_position)

		window.blit(self.pieces_surf, self.offset)

	def highlight_square(self, color, position):
		transparent_square = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
		pygame.draw.rect(transparent_square, color, (0, 0, self.square_size, self.square_size),
						 border_radius=self.square_border_radius)
		self.pieces_surf.blit(transparent_square, position)

	def on_mouse_click(self):
		if self.game_ended: return

		pieces_surf_mouse_pos = np.array(pygame.mouse.get_pos()) - self.offset
		mouse_clicked_on_board = ((0 <= pieces_surf_mouse_pos)&(pieces_surf_mouse_pos <= self.pieces_surf_size)).all()
		
		if not mouse_clicked_on_board: return

		on_board_position = pieces_surf_mouse_pos // self.square_size
		piece_surf_position = on_board_position * self.square_size
		
		piece = self.try_get_piece_by_pos(on_board_position) # SLOW

		is_reachable = self.selected_piece and (np.equal(on_board_position, self.highlighted_squares)).all(axis=1).any()

		current_piece_is_allied = piece and self.is_player_move == piece.is_player
		no_piece_selected = self.selected_piece is None

		if is_reachable:
			chosen_piece_is_allied = piece and self.selected_piece.is_player == piece.is_player
			if chosen_piece_is_allied:
				self.selected_piece = piece
				self.highlighted_squares = self.get_piece_legal_moves(piece)
			elif not self.selected_piece.is_player:
				self.selected_piece = None
			elif self.try_to_make_move(self.selected_piece.pos, on_board_position):
				if len(self.get_pieces(is_player=False)) == 0:
					self.game_ended = True
				self.is_player_move = not self.is_player_move
				self.selected_piece = None
		elif piece:
			if piece != self.selected_piece:
				self.selected_piece = piece
				self.highlighted_squares = self.get_piece_legal_moves(piece)
			else:
				self.selected_piece = None
		
	def reset_pieces(self):
		self.pieces = list()
		for column in range(self.squares):
			self.add_mirrored_pieces(pieces.Triangle, np.array([column, self.squares-2]))
			
			if column in (0, self.squares-1):
				self.add_mirrored_pieces(pieces.Diamond, np.array([column, self.squares-1]))
			elif column in (1, self.squares-2):
				self.add_mirrored_pieces(pieces.Square, np.array([column, self.squares-1]))
			elif column in (2, self.squares-3):
				self.add_mirrored_pieces(pieces.Circle, np.array([column, self.squares-1]))
			elif self.squares//2 <= column <= self.squares-4:
				self.add_mirrored_pieces(pieces.Hexagon, np.array([column, self.squares-1]))
			else:
				self.add_mirrored_pieces(pieces.Octagon, np.array([column, self.squares-1]))
		
	def add_mirrored_pieces(self, piece_class, pos):
		player_piece = piece_class(pos, is_player=True)
		enemy_piece = piece_class(np.array([self.squares - 1]*2) - pos, is_player=False)
		self.pieces.extend([player_piece, enemy_piece])
	
	def try_get_piece_by_pos(self, pos):
		for piece in self.pieces:
			if arrays_are_equal(piece.pos, pos):
				return piece
		else:
			return None

	def check_pos_is_valid(self, pos):
		if not(0 <= pos[0] < self.squares):
			return False
		if not(0 <= pos[1] < self.squares):
			return False
		return True

	def try_to_make_move(self, start_pos, end_pos):
		if self.is_move_valid_check(start_pos, end_pos):
			self.process_move(start_pos, end_pos)
			return True
		return False

	def get_last_rank(self, piece):
		return (self.squares-1, 0)[piece.is_player]

	def process_move(self, start_pos, end_pos):
		selected_piece = self.try_get_piece_by_pos(start_pos)
		target_piece = self.try_get_piece_by_pos(end_pos)
		
		selected_piece.pos = end_pos

		reached_last_rank = end_pos[1] == self.get_last_rank(selected_piece)

		if target_piece: self.pieces.remove(target_piece)

		if reached_last_rank:
			if isinstance(selected_piece, pieces.Triangle):
				self.pieces.remove(selected_piece)
				self.pieces.append(pieces.Ring(selected_piece.pos, selected_piece.is_player))
				self.pieces[-1].update_image_size([self.square_size]*2)
			elif isinstance(selected_piece, pieces.Diamond) or isinstance(selected_piece, pieces.Square):
				self.pieces.remove(selected_piece)
				self.pieces.append(pieces.Circle(selected_piece.pos, selected_piece.is_player))
				self.pieces[-1].update_image_size([self.square_size]*2)
		elif isinstance(selected_piece, pieces.Triangle) and target_piece:
			self.pieces.remove(selected_piece)
			self.pieces.append(target_piece.__class__(selected_piece.pos, selected_piece.is_player))
			self.pieces[-1].update_image_size([self.square_size]*2)

	def is_move_valid_check(self, start_pos, end_pos):
		if not(self.check_pos_is_valid(start_pos) and self.check_pos_is_valid(end_pos)):
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


class Game: # ЗАМЕНИТЬ ХРАНЕНИЕ ФИГУР НА 8Х8 ARRAY
	
	MATCH_GOING = 1
	MATCH_ENDED = 2

	def __init__(self, two_players=False, board_size=7, difficulty=1, caption="Board Game"):
		pygame.font.init()
		pygame.init()

		self.window = pygame.display.set_mode((600, 600), pygame.RESIZABLE)
		# window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
		
		self.caption = caption
		pygame.display.set_caption(caption)

		self.icon_name = "shogiss.ico"
		self.state = self.MATCH_GOING

		try:
			icon = pyinstaller_image_load("", self.icon_name).convert_alpha()
			icon.set_colorkey((0, 0, 0))
			pygame.display.set_icon(icon)
		except Exception as e:
			logger.warning(f"Icon {self.icon_name} not found in working dir.")
		
		self.clock = pygame.time.Clock()
		self.win_info = Layout(self.window)

		self.board = Board(self.win_info, board_size, difficulty)
		self.board.AI_enabled = not two_players

	def run(self):
		self.run = True
		
		while self.run:
			self.handle_events()
			if not self.run: break

			self.window.fill("gray40")
			
			self.board.update(self.window)
			if self.board.game_ended and self.state == self.MATCH_GOING:
				pygame.display.set_caption("PRESS ENTER TO RESTART")
				self.state = self.MATCH_ENDED

			pygame.display.update()
			self.clock.tick(60)

			# DEBUG
			pygame.display.set_caption(f"{int(self.clock.get_fps())}")

	def handle_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				self.run = False
			elif event.type == pygame.VIDEORESIZE:
				self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
				self.win_info.update()
				self.board.on_window_resize()
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_ESCAPE:
					pygame.quit()
					self.run = False
				elif event.key == pygame.K_RETURN:
					if self.state == self.MATCH_ENDED:
						pygame.display.set_caption(self.caption)
						self.board.reset()
						self.state = self.MATCH_GOING
			elif event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONUP):
				self.board.on_mouse_click()


logger.add("error_log.txt", rotation="10 KB",  backtrace=True, diagnose=True)

# [0 - 0.7] easy
# (0.7 - 0.8] normal
# (0.9 - 1] celeste farewell d-side

@logger.catch
def main():
	game = Game(
		two_players=False,
		board_size=8,
		difficulty=1
	)
	game.run()


if __name__ == "__main__":
	main()