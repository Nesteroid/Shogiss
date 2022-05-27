import pygame
import random
import numpy as np
from copy import deepcopy
from loguru import logger
from numba import njit


@njit(cache=True, fastmath=True)
def arrays_are_equal(a: np.array, b: np.array):
	return (np.equal(a, b)).all()


class WindowInfo:
	def __init__(self, window):
		self.window = window
		self.update()

	def update(self):
		self.size = np.array(self.window.get_size())
		self.width, self.height = self.size
		self.center = self.size / 2
		self.min_ = self.size.min()
		self.max_ = self.size.max()


class Piece:
	MOVE_UP = np.array([0, -1])
	MOVE_DOWN = np.array([0, 1])
	MOVE_LEFT= np.array([-1, 0])
	MOVE_RIGHT = np.array([1, 0])

	ASSETS_PATH = "Assets\\Default\\"
	
	def __init__(self, pos, moves, image_names, is_player=True):
		self.pos = pos
		self.moves = moves
		self.is_player = is_player

		self.images = []
		self.scaled_images = []

		for name in image_names:
			image = pygame.image.load(self.ASSETS_PATH + name)
			self.images.append(image)
			self.scaled_images.append(image)
		
		if not is_player: moves *= -1 # mirroring moves
	
	def __getattribute__(self, item):
		if item == "image":
			return self.scaled_images[self.is_player]
		return object.__getattribute__(self, item)

	def update_image_size(self, size):
		self.scaled_images = []
		for image in self.images:
			scaled_image = pygame.transform.smoothscale(image, (int(size[0]), int(size[1])))
			self.scaled_images.append(scaled_image)
	
	def switch_side(self):
		self.is_player = not is_player
		self.moves *= -1


class Triangle(Piece):
	def __init__(self, pos, is_player=True):
		moves = np.array([
			self.MOVE_UP,
			# self.MOVE_UP + self.MOVE_LEFT,
			# self.MOVE_UP + self.MOVE_RIGHT,
		])
		image_names = ("BlackLime.png", "WhiteLime.png")
		super().__init__(pos, moves, image_names, is_player)


class Diamond(Piece):
	def __init__(self, pos, is_player=True):
		moves = np.array([
			self.MOVE_UP,
			self.MOVE_LEFT,
			self.MOVE_RIGHT,
			self.MOVE_DOWN,
		])
		image_names = ("BlackYellowishOrange.png", "WhiteYellowishOrange.png")
		super().__init__(pos, moves, image_names, is_player)


class Square(Piece):
	def __init__(self, pos, is_player=True):
		moves = np.array([
			self.MOVE_UP + self.MOVE_LEFT,
			self.MOVE_UP + self.MOVE_RIGHT,
			self.MOVE_DOWN + self.MOVE_LEFT,
			self.MOVE_DOWN + self.MOVE_RIGHT,
		])
		image_names = ("BlackPink.png", "WhitePink.png")
		super().__init__(pos, moves, image_names, is_player)


class Circle(Piece):
	def __init__(self, pos, is_player=True):
		moves = np.array([
			self.MOVE_UP,
			self.MOVE_LEFT,
			self.MOVE_RIGHT,
			self.MOVE_DOWN,
			self.MOVE_UP + self.MOVE_LEFT,
			self.MOVE_UP + self.MOVE_RIGHT,
			self.MOVE_DOWN + self.MOVE_LEFT,
			self.MOVE_DOWN + self.MOVE_RIGHT,
		])
		image_names = ("BlackPurple.png", "WhitePurple.png")
		super().__init__(pos, moves, image_names, is_player)


class Octagon(Piece):
	def __init__(self, pos, is_player=True):
		moves = np.array([
			self.MOVE_UP * 2,
			self.MOVE_DOWN * 2,
			self.MOVE_LEFT * 2,
			self.MOVE_RIGHT * 2,
			self.MOVE_UP + self.MOVE_LEFT,
			self.MOVE_UP + self.MOVE_RIGHT,
			self.MOVE_DOWN + self.MOVE_LEFT,
			self.MOVE_DOWN + self.MOVE_RIGHT,
		])
		image_names = ("BlackViolet.png", "WhiteViolet.png")
		super().__init__(pos, moves, image_names, is_player)


class Board:
	def __init__(self, win_info, squares):
		self.win_info = win_info
		self.squares = squares

		self.selected_piece = None
		self.selected_piece_moves = None
		self.selected_piece_valid_moves = None
		self.highlighted_squares = None

		self.mouse_clicked = False

		self.is_player_move = True
		self.AI_enabled = True

		self.reset()

	def reset(self):
		self.reset_pieces()
		self.on_window_resize()

	def on_window_resize(self):
		self.square_size = self.win_info.min_ / self.squares
		self.size = self.square_size*self.squares
		self.square_border_radius = round(self.square_size*0.2)
		self.offset = (self.win_info.size - self.size) // 2

		self.pieces_surf = pygame.Surface([self.size]*2)
		self.pieces_surf.set_colorkey("black")

		self.update_image()

		for piece in self.pieces:
			piece.update_image_size((self.square_size, self.square_size))

	def update_image(self):
		self.check_pattern_surf = pygame.Surface([self.size]*2)
		self.check_pattern_surf.set_colorkey("black")

		for i in range(self.squares):
			for j in range(self.squares):
				pieces_surf_position = (self.square_size*i, self.square_size*j)

				color = "gray20" if (i + j) % 2 else "gray60"
				pygame.draw.rect(self.check_pattern_surf, color, (*pieces_surf_position, self.square_size, self.square_size), border_radius=self.square_border_radius)

	def AI_make_move(self):
		my_pieces = self.get_pieces(is_player=False)
		random.shuffle(my_pieces)

		for piece in my_pieces:
			piece_moves = piece.moves + piece.pos
			piece_legal_moves_filter = np.array(list(map(self.check_pos_is_valid, piece_moves)))
			piece_legal_moves = piece_moves[piece_legal_moves_filter]
			np.random.shuffle(piece_legal_moves)
			for move in piece_legal_moves:
				if self.try_to_make_move(piece.pos, move):
					self.is_player_move = True
					return

		self.is_player_move = True

	def get_pieces(self, is_player=True):
		return list(filter(lambda piece: is_player == piece.is_player, self.pieces))

	def update(self, window):
		if self.AI_enabled and not self.is_player_move:
			self.AI_make_move()
			if len(self.get_pieces(is_player=True)) == 0:
				self.reset()
				return

		pieces_surf_mouse_pos = np.array(pygame.mouse.get_pos()) - self.offset

		self.pieces_surf.blit(self.check_pattern_surf, (0, 0))

		for i in range(self.squares):
			for j in range(self.squares):
				pieces_surf_position = (self.square_size*i, self.square_size*j)
				on_board_position = np.array([i, j])

				is_reachable = self.selected_piece and (np.equal(on_board_position, self.highlighted_squares)).all(axis=1).any()
				if is_reachable:
					highlighted_square = pygame.Surface((self.square_size, self.square_size))
					highlighted_square.set_colorkey("black")
					highlighted_square.set_alpha(50)
					pygame.draw.rect(highlighted_square, "yellow", (0, 0, self.square_size, self.square_size), border_radius=self.square_border_radius)
					self.pieces_surf.blit(highlighted_square, pieces_surf_position)

				is_howered = (pieces_surf_position <= pieces_surf_mouse_pos).all() and (pieces_surf_mouse_pos <= pieces_surf_position + self.square_size).all()
				if is_howered:
					blackout_square = pygame.Surface((self.square_size, self.square_size))
					blackout_square.set_colorkey("black")
					blackout_square.set_alpha(60)
					pygame.draw.rect(blackout_square, "green", (0, 0, self.square_size, self.square_size), border_radius=self.square_border_radius)
					self.pieces_surf.blit(blackout_square, pieces_surf_position)
				
				if self.selected_piece and is_howered and self.mouse_clicked and is_reachable:
					if self.try_to_make_move(self.selected_piece.pos, on_board_position):
						if len(self.get_pieces(is_player=False)) == 0:
							self.reset()
							return
						self.is_player_move = not self.is_player_move
					self.selected_piece = None
					self.mouse_clicked = False
				
				if piece := self.try_get_piece_by_pos(on_board_position):
					self.pieces_surf.blit(piece.image, pieces_surf_position)

					if is_howered and self.mouse_clicked and (self.is_player_move == piece.is_player):
						self.selected_piece = piece
						self.selected_piece_moves = self.selected_piece.moves + self.selected_piece.pos
						self.selected_piece_valid_moves = np.array(list(map(self.check_pos_is_valid, self.selected_piece_moves)))
						self.highlighted_squares = self.selected_piece_moves[self.selected_piece_valid_moves]

		window.blit(self.pieces_surf, self.offset)
		
		self.mouse_clicked = False

	def on_mouse_click(self):
		self.mouse_clicked = True
	
	def reset_pieces(self):
		self.pieces = list()
		
		for column in range(self.squares):
			self.add_mirrored_pieces(Triangle, np.array([column, self.squares-2]))
			
			if column in (0, self.squares-1):
				self.add_mirrored_pieces(Diamond, np.array([column, self.squares-1]))
			elif column in (1, self.squares-2):
				self.add_mirrored_pieces(Square, np.array([column, self.squares-1]))
			elif column in (2, self.squares-3):
				self.add_mirrored_pieces(Circle, np.array([column, self.squares-1]))
			else:
				self.add_mirrored_pieces(Octagon, np.array([column, self.squares-1]))

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

	def process_move(self, start_pos, end_pos):
		selected_piece = self.try_get_piece_by_pos(start_pos)
		target_piece = self.try_get_piece_by_pos(end_pos)
		
		selected_piece.pos = end_pos

		reached_last_rank = ((end_pos[1] == self.squares-1), (end_pos[1] == 0))[selected_piece.is_player]

		if target_piece: self.pieces.remove(target_piece)

		if reached_last_rank:
			if isinstance(selected_piece, Triangle):
				self.pieces.remove(selected_piece)
				self.pieces.append(Octagon(selected_piece.pos, selected_piece.is_player))
				self.pieces[-1].update_image_size([self.square_size]*2)
			elif isinstance(selected_piece, Diamond) or isinstance(selected_piece, Square):
				self.pieces.remove(selected_piece)
				self.pieces.append(Circle(selected_piece.pos, selected_piece.is_player))
				self.pieces[-1].update_image_size([self.square_size]*2)
		elif isinstance(selected_piece, Triangle) and target_piece:
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
		
		if not isinstance(selected_piece, Piece):
			return False

		if (target_piece is not None) and (selected_piece.is_player == target_piece.is_player):
			return False

		return True


class Game:
	def __init__(self, caption="Board Game"):
		pygame.font.init()
		pygame.init()

		self.window = pygame.display.set_mode((600, 600), pygame.RESIZABLE)
		# window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
		
		pygame.display.set_caption(caption)
		
		self.clock = pygame.time.Clock()
		self.win_info = WindowInfo(self.window)

		self.board = Board(self.win_info, 7)

	def run(self):
		self.run = True
		
		while self.run:
			self.handle_events()
			if not self.run: break

			self.window.fill("gray40")
			self.board.update(self.window)

			pygame.display.update()
			self.clock.tick(60)

			pygame.display.set_caption(f"{int(self.clock.get_fps())}")

	def handle_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				self.run = False
			elif event.type == pygame.VIDEORESIZE:
				self.win_info.update()
				self.board.on_window_resize()
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_ESCAPE:
					pygame.quit()
					self.run = False
			elif event.type == pygame.MOUSEBUTTONUP:
				self.board.on_mouse_click()



@logger.catch
def main():
	game = Game()
	game.run()


if __name__ == "__main__":
	main()
