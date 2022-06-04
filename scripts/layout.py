import numpy as np


class Layout:
	def __init__(self, size):
		self.resize(size)

	def resize(self, size: list):
		self.size = np.array(size)
		self.width, self.height = self.size
		self.center = self.size / 2
		self.min_ = self.size.min()
		self.max_ = self.size.max()
		self._on_resize()

	def _on_resize(self):
		pass
