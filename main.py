import pygame
import numpy as np
from scripts import board, board_ui
import os
import sys
from matplotlib import pyplot as plt


def pyinstaller_image_load(path, name):
	try:
		if getattr(sys, 'frozen', False):
			wd = sys._MEIPASS
		else:
			wd = ''
		return pygame.image.load(os.path.join(wd, path, name))
	except FileNotFoundError:
		return None


def pyinstaller_sound_load(path, name):
	try:
		if getattr(sys, 'frozen', False):
			wd = sys._MEIPASS
		else:
			wd = ''
		return pygame.mixer.Sound(os.path.join(wd, path, name))
	except FileNotFoundError:
		return None


def pyinstaller_music_load(path, name):
	try:
		if getattr(sys, 'frozen', False):
			wd = sys._MEIPASS
		else:
			wd = ''
		return pygame.mixer.music.load(os.path.join(wd, path, name))
	except FileNotFoundError:
		return None


def arrays_are_equal(a: np.array, b: np.array):
	return a[0] == b[0] and a[1] == b[1]


class Game:

	MATCH_GOING = 1
	MATCH_ENDED = 2

	def __init__(self, two_players: bool = False, board_size: int = 8, difficulty: float = 1.0,
				 caption: str = "Board Game", fps: int = 60):
		pygame.init()
		pygame.font.init()
		pygame.mixer.init()

		self.debug_font = pygame.font.SysFont('Comic Sans MS', 14)

		self.mouse_hold_frames = 0
		self.fps = fps

		self.window = None
		self.caption = caption
		self.icon_name = "shogiss.ico"
		self.state = None
		self.running = False

		self.clock = None
		self.board = None

		self.menu_opened = False

		self.debug = False

		self.delta_time = 0
		self.frames = 0

		self.two_players = two_players
		self.board_size = board_size
		self.difficulty = difficulty

		self.debug_texts = list()
		self.delta_time_history = list()

	def start(self):
		pygame.display.set_caption(self.caption)
		self.state = self.MATCH_GOING
		self.delta_time_history = list()
		self.default_bg = pygame.Color("gray40")

	def restart(self):
		pygame.display.set_caption(self.caption)
		self.boardUI.restart()
		self.state = self.MATCH_GOING
		self.delta_time_history = list()

	def run(self):
		self.running = True

		self.window = pygame.display.set_mode((600, 600), pygame.RESIZABLE)
		self.clock = pygame.time.Clock()

		try:
			icon = pyinstaller_image_load("", self.icon_name).convert_alpha()
			icon.set_colorkey((0, 0, 0))
			pygame.display.set_icon(icon)
		except FileNotFoundError:
			pass

		self.board = board.Board(self.board_size)
		self.boardUI = board_ui.BoardUI(self, self.board, self.window.get_size(), not self.two_players, self.difficulty)

		self.start()
		self.loop()

	def loop(self):
		while self.running:
			self.handle_events()

			if not self.running:
				break

			if self.frames == 0:
				self.window.fill(self.default_bg)

			if self.board.winner is not None:
				if self.state == self.MATCH_GOING:
					if self.board.winner == "player":
						pyinstaller_music_load("audio", "So, How'd We Do-.mp3")
					else:
						pyinstaller_music_load("audio", "It's Okay To Try Again....mp3")
					pygame.mixer.music.play(loops=-1)
					pygame.display.set_caption("PRESS ENTER TO RESTART")
					self.state = self.MATCH_ENDED
					if self.debug:
						self.show_debug_plot()

			self.boardUI.draw(self.window, delta_time=self.delta_time)
			self.boardUI.update(self.delta_time)

			self._draw_debug_texts()

			if self.frames == 0:
				pygame.display.update()

			# pygame.display.update()

			if self.debug:
				for rect in self.boardUI.updated_surfs:
					blink_color = self.frames % 256
					pygame.draw.rect(self.window, (blink_color, 0, blink_color), rect, 1)

			pygame.display.update(self.boardUI.prev_updated_surfs)
			pygame.display.update(self.boardUI.updated_surfs)

			self.delta_time = self.clock.tick(self.fps)

			if self.debug:
				real_fps = self.clock.get_fps()
				pygame.display.set_caption(f"DEBUG {int(real_fps)}")
				self.delta_time_history.append(self.delta_time)

			self.frames += 1

	def handle_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				self.running = False
			elif event.type == pygame.VIDEORESIZE:
				self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
				self.boardUI.resize(self.window.get_size())
				self.window.fill(self.default_bg)
				self.boardUI.updated_surfs.append(self.window.get_rect())
			elif event.type == pygame.VIDEOEXPOSE:
				self.boardUI.updated_surfs.append(self.window.get_rect())
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_ESCAPE:
					if self.boardUI.move_in_process is None:
						self.menu_opened = not self.menu_opened
					# pygame.quit()
					# self.running = False
				elif event.key == pygame.K_RETURN:
					if self.state == self.MATCH_ENDED:
						pygame.mixer.music.unload()
						self.restart()
				elif event.key == pygame.K_r:
					if self.boardUI.move_in_process is None:
						if self.boardUI.board.undo():
							self.boardUI.updated_surfs.append(self.window.get_rect())
			elif event.type == pygame.MOUSEBUTTONDOWN:
				self.boardUI.on_mouse_click(event)
				if not self.menu_opened:
					continue
				if event.button == 4:
					self.boardUI.AI.difficulty += 0.01
					self.boardUI.AI.difficulty = min(self.boardUI.AI.difficulty, 1)
				elif event.button == 5:
					self.boardUI.AI.difficulty -= 0.01
					self.boardUI.AI.difficulty = max(self.boardUI.AI.difficulty, 0)

		# Pressed keys
		keys = pygame.key.get_pressed()
		if keys[pygame.K_UP] and self.menu_opened:
			self.boardUI.AI.difficulty += 0.01
			self.boardUI.AI.difficulty = min(self.boardUI.AI.difficulty, 1)
		elif keys[pygame.K_DOWN] and self.menu_opened:
			self.boardUI.AI.difficulty -= 0.01
			self.boardUI.AI.difficulty = max(self.boardUI.AI.difficulty, 0)

		# Mouse holding
		if pygame.mouse.get_pressed()[0]:
			self.mouse_hold_frames += 1
		elif self.mouse_hold_frames:  # mouse have been released
			if self.mouse_hold_frames / self.fps >= 1.5:  # seconds
				if self.boardUI.board.undo():
					self.boardUI.updated_surfs.append(self.window.get_rect())
			self.mouse_hold_frames = 0

	def add_debug_text(self, text):
		self.debug_texts.append(text)

	def draw_multiple_lines(self, lines, font=None, color=(255, 255, 255), background='gray10', offset=pygame.math.Vector2()):
		line_y_offset = 0
		max_width = 0
		for line in lines:
			font = self.debug_font if font is None else font
			text_surface = font.render(line, True, color)
			text_surface_rect = text_surface.get_rect()
			max_width = max(max_width, text_surface_rect.width)
			pygame.draw.rect(self.window, background, text_surface_rect.move(0, line_y_offset).move(offset))
			self.window.blit(text_surface, pygame.math.Vector2(0, line_y_offset) + offset)
			line_y_offset += text_surface.get_height()
		self.boardUI.updated_surfs.append(pygame.Rect(*offset, max_width, line_y_offset - offset.y))

	def _draw_debug_texts(self, color=(255, 255, 255), background='gray10'):
		if self.debug is False:
			return
		self.draw_multiple_lines(self.debug_texts)
		self.debug_texts.clear()

	def show_debug_plot(self):
		x = [i for i in range(len(self.delta_time_history))]
		y = self.delta_time_history

		# Calculate the simple average of the data
		y_mean = [np.mean(y)] * len(x)

		fig, ax = plt.subplots()

		# Plot the data
		data_line = ax.plot(x, y, label='Data', marker='o')

		# Plot the average line
		mean_line = ax.plot(x, y_mean, label='Mean', linestyle='--')

		plt.xlabel("Frames")
		plt.ylabel(f"Delay in ms (mean = {round(np.mean(y), 4)}, fps = {round(1000/np.mean(y), 2)})")

		# Make a legend
		legend = ax.legend(loc='upper right')

		plt.show()


# [0 - 0.25] easy
# (0.25 - 0.75] normal
# (0.75 - 1] celeste farewell d-side

def main():
	game = Game(
		two_players=False,
		board_size=8,
		difficulty=1,
		fps=60,
	)
	# game.debug = True
	game.run()


if __name__ == "__main__":
	main()
