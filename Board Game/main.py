import pygame
from numba import njit
import numpy as np
from copy import deepcopy

@njit()
def array_is_equal(a: np.array, b: np.array):
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
	
	def __init__(self, pos, moves, image, is_player=True):
		self.pos = pos
		self.moves = moves
		self.image = image
		self.is_player = is_player


class Triangle(Piece):
	def __init__(self, pos, is_player=True):
		moves = np.array([
			self.MOVE_UP,
			self.MOVE_UP + self.MOVE_LEFT,
			self.MOVE_UP + self.MOVE_RIGHT,
		])
		image = pygame.image.load("Assets\\Meme\\ahegao.png")
		super().__init__(pos, moves, image, is_player)


class Diamond(Piece):
	def __init__(self, pos, is_player=True):
		moves = np.array([
			self.MOVE_UP,
			self.MOVE_LEFT,
			self.MOVE_RIGHT,
			self.MOVE_DOWN,
		])
		image = pygame.image.load("Assets\\Meme\\gachi.jpg")
		super().__init__(pos, moves, image, is_player)


class Square(Piece):
	def __init__(self, pos, is_player=True):
		moves = np.array([
			self.MOVE_UP + self.MOVE_LEFT,
			self.MOVE_UP + self.MOVE_RIGHT,
			self.MOVE_DOWN + self.MOVE_LEFT,
			self.MOVE_DOWN + self.MOVE_RIGHT,
		])
		image = pygame.image.load("Assets\\Meme\\leatherman.jpg")
		super().__init__(pos, moves, image, is_player)


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
		image = pygame.image.load("Assets\\Meme\\slut.jpg")
		super().__init__(pos, moves, image, is_player)


class Hexagon(Piece):
	def __init__(self, pos, is_player=True):
		moves = np.array([
			self.MOVE_UP * 2,
			self.MOVE_DOWN * 2,
			self.MOVE_UP + self.MOVE_LEFT,
			self.MOVE_UP + self.MOVE_RIGHT,
			self.MOVE_DOWN + self.MOVE_LEFT,
			self.MOVE_DOWN + self.MOVE_RIGHT,
		])
		image = pygame.image.load("Assets\\Meme\\rock.jpg")
		super().__init__(pos, moves, image, is_player)


class Board:
	def __init__(self, squares):
		self.squares = squares

		self.selected_piece = None
		self.selected_piece_moves = None
		self.selected_piece_valid_moves = None
		self.highlighted_squares = None

		self.reset_pieces()

	def update(self, window, win_info):
		square_size = win_info.min_ / self.squares
		board_size = square_size*self.squares
		border_radius = round(square_size*0.2)
		offset = (win_info.size - board_size) // 2

		mouse_pos = np.array(pygame.mouse.get_pos())

		for i in range(self.squares):
			for j in range(self.squares):
				position = (square_size*i, square_size*j) + offset

				color = "gray20" if (i + j) % 2 else "gray60"
				pygame.draw.rect(window, color, (*position, square_size, square_size), border_radius=border_radius)

				is_reachable = self.selected_piece and (np.array([i, j]) == self.highlighted_squares).all(axis=1).any()
				if is_reachable:
					highlighted_square = pygame.Surface((square_size, square_size))
					highlighted_square.set_colorkey("black")
					highlighted_square.set_alpha(50)
					pygame.draw.rect(highlighted_square, "yellow", (0, 0, square_size, square_size), border_radius=border_radius)
					window.blit(highlighted_square, position)

				is_howered = (position <= mouse_pos).all() and (mouse_pos <= position + square_size).all()
				if is_howered:
					blackout_square = pygame.Surface((square_size, square_size))
					blackout_square.set_colorkey("black")
					blackout_square.set_alpha(60)
					pygame.draw.rect(blackout_square, "green", (0, 0, square_size, square_size), border_radius=border_radius)
					window.blit(blackout_square, position)

				if piece := self.try_get_piece_by_pos(np.array([i, j])):
					scaled_piece_image = pygame.transform.smoothscale(piece.image, (square_size, square_size))
					window.blit(scaled_piece_image, position)

					if is_howered and pygame.mouse.get_pressed()[0]:
						self.selected_piece = piece
						self.selected_piece_moves = self.selected_piece.moves + self.selected_piece.pos
						self.selected_piece_valid_moves = np.array(list(map(self.check_pos_is_valid, self.selected_piece_moves)))
						self.highlighted_squares = self.selected_piece_moves[self.selected_piece_valid_moves]

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
				self.add_mirrored_pieces(Hexagon, np.array([column, self.squares-1]))

	def add_mirrored_pieces(self, piece_class, pos):
		player_piece = piece_class(pos)
		enemy_piece = piece_class(np.array([self.squares - 1]*2) - pos)
		self.pieces.extend([player_piece, enemy_piece])
	
	def try_get_piece_by_pos(self, pos):
		for piece in self.pieces:
			if array_is_equal(piece.pos, pos):
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

	def process_move(self, start_pos, end_pos):
		selected_piece = self.try_get_piece_by_pos(start_pos)
		target_piece = self.try_get_piece_by_pos(end_pos)
		
		selected_piece.pos = deepcopy(end_pos)
		
		if isinstance(selected_piece, Triangle):
			self.pieces.remove(selected_piece)

			if selected_piece.is_player and (end_pos[1] == 0):
				self.pieces.append(Hexagon(selected_piece, selected_piece.is_player))
			elif (not selected_piece.is_player) and (end_pos[1] == self.squares-1):
				self.pieces.append(Hexagon(selected_piece, selected_piece.is_player))
			elif target_piece:
				target_piece.is_player = not target_piece # switch sides
		
		elif target_piece:
			self.pieces.remove(target_piece)

	def is_move_valid_check(self, start_pos, end_pos):
		if not(self.check_pos_is_valid(start_pos) and self.check_pos_is_valid(end_pos)):
			return False

		if start_pos == end_pos:
			return False
		
		selected_piece = self.try_get_piece_by_pos(start_pos)
		target_piece = self.try_get_piece_by_pos(end_pos)
		
		if not isinstance(selected_piece, piece):
			return False

		if target_piece and (selected_piece.is_player == target_piece.is_player):
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

		self.board = Board(8)

	def run(self):
		self.run = True
		
		while self.run:
			self.handle_events()
			if not self.run: break

			self.window.fill("gray40")
			self.board.update(self.window, self.win_info)

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
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_ESCAPE:
					pygame.quit()
					self.run = False


def main():
	Game().run()

if __name__ == "__main__":
	main()
