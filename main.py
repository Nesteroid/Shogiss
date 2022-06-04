import pygame
import numpy as np
# from loguru import logger
from numba import njit
from scripts import board
import os
import sys


def pyinstaller_image_load(path, name):
	if getattr(sys, 'frozen', False):
		wd = sys._MEIPASS
	else:
		wd = ''
	return pygame.image.load(os.path.join(wd, path, name))


@njit(cache=True, fastmath=True)
def arrays_are_equal(a: np.array, b: np.array):
	return (np.equal(a, b)).all()


class Game:
	# TODO: ЗАМЕНИТЬ ХРАНЕНИЕ ФИГУР НА ARRAY

	MATCH_GOING = 1
	MATCH_ENDED = 2

	def __init__(self, two_players: bool = False, board_size: int = 8, difficulty: float = 1.0,
				 caption: str = "Board Game"):

		self.window = None
		self.caption = caption
		self.icon_name = "shogiss.ico"
		self.state = None
		self.running = False

		self.clock = None
		self.board = None

		self.color_lerp_perc = 0
		self.two_players = two_players
		self.board_size = board_size
		self.difficulty = difficulty

	def run(self):
		self.running = True

		enemy_won_bg = pygame.Color("gray20")
		default_bg = pygame.Color("gray40")
		player_won_bg = pygame.Color("gray60")

		pygame.font.init()
		pygame.init()

		self.window = pygame.display.set_mode((600, 600), pygame.RESIZABLE)
		self.clock = pygame.time.Clock()

		try:
			icon = pyinstaller_image_load("", self.icon_name).convert_alpha()
			icon.set_colorkey((0, 0, 0))
			pygame.display.set_icon(icon)
		except FileNotFoundError:
			pass
			# logger.warning(f"Icon {self.icon_name} not found in working dir.")

		self.board = board.Board(self.board_size)
		self.boardUI = board.BoardUI(
			self.board, self.window.get_size(),
			not self.two_players, 1)

		self.restart()

		while self.running:
			self.handle_events()

			if not self.running:
				break

			if self.board.winner == "enemy":
				self.window.fill(default_bg.lerp(enemy_won_bg, self.color_lerp_perc))
			elif self.board.winner == "player":
				self.window.fill(default_bg.lerp(player_won_bg, self.color_lerp_perc))
			else:
				self.window.fill(default_bg)

			self.boardUI.draw(self.window)
			if self.board.winner is not None:
				self.color_lerp_perc += 0.015
				self.color_lerp_perc = min(1, self.color_lerp_perc)
				if self.state == self.MATCH_GOING:
					pygame.display.set_caption("PRESS ENTER TO RESTART")
					self.state = self.MATCH_ENDED

			pygame.display.update()
			self.clock.tick(60)

			# DEBUG
			pygame.display.set_caption(f"{int(self.clock.get_fps())}")

	def restart(self):
		pygame.display.set_caption(self.caption)
		self.boardUI.restart()
		self.state = self.MATCH_GOING
		self.color_lerp_perc = 0

	def handle_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				self.running = False
			elif event.type == pygame.VIDEORESIZE:
				self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
				self.boardUI.resize(self.window.get_size())
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_ESCAPE:
					pygame.quit()
					self.running = False
				elif event.key == pygame.K_RETURN:
					if self.state == self.MATCH_ENDED and self.color_lerp_perc == 1:
						self.restart()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				self.boardUI.on_mouse_click()
				if self.state == self.MATCH_ENDED and self.color_lerp_perc == 1:
					self.restart()


# logger.add("error_log.txt", rotation="10 KB", backtrace=True, diagnose=True)


# [0 - 0.25] easy
# (0.25 - 0.75] normal
# (0.75 - 1] celeste farewell d-side

# @logger.catch
def main():
	game = Game(
		two_players=False,
		board_size=8,
		difficulty=0.75,
	)
	game.run()


if __name__ == "__main__":
	main()
