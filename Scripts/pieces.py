import pygame
import numpy as np
import os, sys

class Piece:
	MOVE_UP = np.array([0, -1])
	MOVE_DOWN = np.array([0, 1])
	MOVE_LEFT= np.array([-1, 0])
	MOVE_RIGHT = np.array([1, 0])

	ASSETS_PATH = "Assets/Default/"
	
	def __init__(self, pos, moves, image_names, is_player=True):
		self.pos = pos
		self.moves = moves
		self.is_player = is_player

		self.images = []
		self.scaled_images = []

		for name in image_names:
			try:
				if getattr(sys, 'frozen', False):
					wd = sys._MEIPASS
				else:
					wd = ''    
				image = pygame.image.load(os.path.join(wd, self.ASSETS_PATH, name)).convert_alpha()
			except FileNotFoundError:
				image = pygame.Surface((1, 1))
				image.fill("magenta")
			
			self.images.append(image)
			self.scaled_images.append(image)
		
		self.forward = np.array([0, -1])
		if not is_player:
			moves *= -1 # mirroring moves
			self.forward *= -1
	
	def __getattribute__(self, item):
		if item == "image":
			return self.scaled_images[self.is_player]
		elif item == "value":
			return np.sum(np.abs(self.moves))
		return object.__getattribute__(self, item)
	
	def __repr__(self):
		return self.__class__.__name__ + f" p={self.pos} v={self.value}"

	def update_image_size(self, size):
		self.scaled_images = []
		for image in self.images:
			scaled_image = pygame.transform.smoothscale(image, (int(size[0]), int(size[1])))
			self.scaled_images.append(scaled_image)

	def get_value_after_eating(self, piece):
		return self.value
	
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

	def get_value_after_eating(self, piece):
		return piece.value


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
			self.MOVE_UP * 2 + self.MOVE_LEFT,
			self.MOVE_UP * 2 + self.MOVE_RIGHT,
			self.MOVE_DOWN * 2 + self.MOVE_LEFT,
			self.MOVE_DOWN * 2 + self.MOVE_RIGHT,
			self.MOVE_LEFT * 2 + self.MOVE_UP,
			self.MOVE_LEFT * 2 + self.MOVE_DOWN,
			self.MOVE_RIGHT * 2 + self.MOVE_UP,
			self.MOVE_RIGHT * 2 + self.MOVE_DOWN,
		])
		image_names = ("BlackViolet.png", "WhiteViolet.png")
		super().__init__(pos, moves, image_names, is_player)

if __name__ == "__main__":
	pass
