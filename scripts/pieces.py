import numpy as np
from weakref import WeakSet


class Piece:
	MOVE_UP = np.array([0, -1])
	MOVE_DOWN = np.array([0, 1])
	MOVE_LEFT = np.array([-1, 0])
	MOVE_RIGHT = np.array([1, 0])

	instances = WeakSet()
	
	def __init__(self, pos: np.ndarray, steps: np.ndarray, is_player: bool = True):
		self.pos = pos
		self.steps = steps
		self.is_player = is_player

		self.forward = np.array([0, -1])
		if not is_player:
			steps *= -1  # mirroring steps
			self.forward *= -1  # direction to last rank

		self.id_ = len(Piece.instances)
		Piece.instances.add(self)

	def __getattribute__(self, item):
		if item == "value":
			return self.steps.shape[0]  # * np.sum(np.abs(self.steps))
		return object.__getattribute__(self, item)
	
	def __repr__(self):
		return self.__class__.__name__ + f" id={self.id_}"

	def get_value_after_eating(self, piece):
		return max(piece.value, self.value)
	
	def switch_side(self):
		self.is_player = not self.is_player
		self.steps *= -1


class Triangle(Piece):
	def __init__(self, pos, is_player=True):
		self.steps = np.array([
			Piece.MOVE_UP,
			Piece.MOVE_LEFT,
			Piece.MOVE_RIGHT,
		])
		super().__init__(pos, self.steps, is_player)


class Diamond(Piece):
	def __init__(self, pos, is_player=True):
		self.steps = np.array([
			Piece.MOVE_UP,
			Piece.MOVE_LEFT,
			Piece.MOVE_RIGHT,
			Piece.MOVE_DOWN,
			Piece.MOVE_UP * 2,
			Piece.MOVE_LEFT * 2,
			Piece.MOVE_RIGHT * 2,
			Piece.MOVE_DOWN * 2,
		])
		super().__init__(pos, self.steps, is_player)


class Square(Piece):
	def __init__(self, pos, is_player=True):
		self.steps = np.array([
			Piece.MOVE_UP + Piece.MOVE_LEFT,
			Piece.MOVE_UP + Piece.MOVE_RIGHT,
			Piece.MOVE_DOWN + Piece.MOVE_LEFT,
			Piece.MOVE_DOWN + Piece.MOVE_RIGHT,
			(Piece.MOVE_UP + Piece.MOVE_LEFT) * 2,
			(Piece.MOVE_UP + Piece.MOVE_RIGHT) * 2,
			(Piece.MOVE_DOWN + Piece.MOVE_LEFT) * 2,
			(Piece.MOVE_DOWN + Piece.MOVE_RIGHT) * 2,
		])
		super().__init__(pos, self.steps, is_player)


class Circle(Piece):
	def __init__(self, pos, is_player=True):
		self.steps = np.array([
			Piece.MOVE_UP + Piece.MOVE_LEFT,
			Piece.MOVE_UP + Piece.MOVE_RIGHT,
			Piece.MOVE_DOWN + Piece.MOVE_LEFT,
			Piece.MOVE_DOWN + Piece.MOVE_RIGHT,
			Piece.MOVE_UP,
			Piece.MOVE_LEFT,
			Piece.MOVE_RIGHT,
			Piece.MOVE_DOWN,
		])
		super().__init__(pos, self.steps, is_player)


class Cross(Piece):
	def __init__(self, pos, is_player=True):
		self.steps = np.array([
			Piece.MOVE_UP * 2 + Piece.MOVE_RIGHT,
			Piece.MOVE_UP * 2 + Piece.MOVE_LEFT,
			Piece.MOVE_DOWN * 2 + Piece.MOVE_RIGHT,
			Piece.MOVE_DOWN * 2 + Piece.MOVE_LEFT,
			Piece.MOVE_RIGHT * 2 + Piece.MOVE_DOWN,
			Piece.MOVE_RIGHT * 2 + Piece.MOVE_UP,
			Piece.MOVE_LEFT * 2 + Piece.MOVE_DOWN,
			Piece.MOVE_LEFT * 2 + Piece.MOVE_UP,
			Piece.MOVE_UP + Piece.MOVE_LEFT,
			Piece.MOVE_UP + Piece.MOVE_RIGHT,
			Piece.MOVE_DOWN + Piece.MOVE_LEFT,
			Piece.MOVE_DOWN + Piece.MOVE_RIGHT,
		])
		super().__init__(pos, self.steps, is_player)


class Octagon(Piece):
	def __init__(self, pos, is_player=True):
		self.steps = np.array([
			Piece.MOVE_UP*2 + Piece.MOVE_LEFT,
			Piece.MOVE_UP*2 + Piece.MOVE_RIGHT,
			Piece.MOVE_DOWN*2 + Piece.MOVE_LEFT,
			Piece.MOVE_DOWN*2 + Piece.MOVE_RIGHT,
			Piece.MOVE_LEFT*2 + Piece.MOVE_UP,
			Piece.MOVE_LEFT*2 + Piece.MOVE_DOWN,
			Piece.MOVE_RIGHT*2 + Piece.MOVE_UP,
			Piece.MOVE_RIGHT*2 + Piece.MOVE_DOWN,
		])
		super().__init__(pos, self.steps, is_player)


class Ring(Piece):
	def __init__(self, pos, is_player=True):
		self.steps = np.array([
			Piece.MOVE_UP + Piece.MOVE_LEFT,
			Piece.MOVE_UP + Piece.MOVE_RIGHT,
			Piece.MOVE_DOWN + Piece.MOVE_LEFT,
			Piece.MOVE_DOWN + Piece.MOVE_RIGHT,
			Piece.MOVE_UP*2 + Piece.MOVE_RIGHT,
			Piece.MOVE_UP*2 + Piece.MOVE_LEFT,
			Piece.MOVE_UP*2,
			Piece.MOVE_DOWN*2 + Piece.MOVE_RIGHT,
			Piece.MOVE_DOWN*2 + Piece.MOVE_LEFT,
			Piece.MOVE_DOWN*2,
			Piece.MOVE_RIGHT*2,
			Piece.MOVE_RIGHT*2 + Piece.MOVE_DOWN,
			Piece.MOVE_RIGHT*2 + Piece.MOVE_UP,
			Piece.MOVE_LEFT*2,
			Piece.MOVE_LEFT*2 + Piece.MOVE_DOWN,
			Piece.MOVE_LEFT*2 + Piece.MOVE_UP,
		])
		super().__init__(pos, self.steps, is_player)
