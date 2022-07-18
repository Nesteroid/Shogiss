import main
import pygame
import random
import math
from scripts.ai import SimpleAI
from scripts.layout import Layout
from scripts.particles import ParticleSystem
import numpy as np


def invert_img(img):
	img.lock()
	for x in range(img.get_width()):
		for y in range(img.get_height()):
			RGBA = img.get_at((x, y))
			for i in range(3):
				# Invert RGB, but not Alpha
				RGBA[i] = 255 - RGBA[i]
			img.set_at((x, y), RGBA)
	img.unlock()


def illuminate_img(img, strength):
	img.lock()
	for x in range(img.get_width()):
		for y in range(img.get_height()):
			RGBA = img.get_at((x, y))
			for i in range(3):
				# illuminate RGB, but not Alpha
				RGBA[i] = min(255, round(RGBA[i] + (RGBA[i]/255 * strength)*255))
			img.set_at((x, y), RGBA)
	img.unlock()


def get_random_color_from_img(img):
	img.lock()
	x = random.randint(0, img.get_width()-1)
	y = random.randint(0, img.get_height()-1)
	RGBA = img.get_at((x, y))
	img.unlock()
	return RGBA


def interpolate(start: float, end: float, percantage: float):
	return start + (end - start)*percantage


class BoardUI(Layout):
	def __init__(self, game, board, size: tuple, AI_enabled: bool, difficulty: float):
		self.game = game
		self.board = board

		self.tile_type = "square"

		self.player_image_names = dict()
		self.enemy_image_names = dict()
		self.piece_image_names = dict()

		self.setup_image_names()

		self.assets_path = "assets/fancy/"
		self.default_assets_path = "assets/default/"
		self.piece_images = {"player": dict(), "enemy": dict()}
		self.tile_images = {"square": list(), "hex": list()}

		self.updated_surfs = []
		self.prev_updated_surfs = []

		super().__init__(size)

		self.selected_piece = None
		self.selected_piece_moves = None
		self.selected_piece_valid_moves = None
		self.highlighted_squares = set()

		self.animation_percentage = 0
		self.animation_speed = 5
		self.animation_piece = None
		self.move_in_process = None

		self.slide_sound = main.pyinstaller_sound_load('audio', 'piece-slide.mp3')
		self.shattering_sound = main.pyinstaller_sound_load('audio', 'shattering.mp3')
		self.shattering_sound.set_volume(0.25)
		self.chess_placed = main.pyinstaller_sound_load('audio', 'chess_placed.wav')

		self.board_surf = None

		self.AI = SimpleAI(self.board, difficulty)
		self.AI_enabled = AI_enabled

		self.is_player_move = True

		self.start()

	def setup_image_names(self):
		from scripts.pieces import Diamond, Triangle, Square, Circle, Cross, Octagon, Ring
		self.player_image_names = {
			Diamond: "WhiteYellowishOrange.png",
			Triangle: "WhiteLime.png",
			Square: "WhitePink.png",
			Circle: "WhitePurple.png",
			Cross: "WhiteBlueLagoon.png",
			Octagon: "WhiteViolet.png",
			Ring: "White.png",
		}
		self.enemy_image_names = {
			Diamond: "BlackYellowishOrange.png",
			Triangle: "BlackLime.png",
			Square: "BlackPink.png",
			Circle: "BlackPurple.png",
			Cross: "BlackBlueLagoon.png",
			Octagon: "BlackViolet.png",
			Ring: "Black.png",
		}
		self.piece_image_names = {
			"player": self.player_image_names,
			"enemy": self.enemy_image_names
		}

		self.square_tile_names = ("hex tile 1.png", "hex tile 2.png")
		self.hex_tile_names = ("hex tile 1.png", "hex tile 2.png", "hex tile 3.png")

		self.tile_images_names = {
			"square": self.square_tile_names,
			"hex": self.hex_tile_names
		}

	def _on_resize(self):
		self.tile_width = self.min_ / self.board.squares
		if self.tile_type == "square":
			self.tile_height = self.tile_width
		elif self.tile_type == "hex":
			self.tile_height = self.tile_width / 2 * 3 ** 0.5
		self.board_size = self.tile_width * self.board.squares
		self.square_border_radius = round(self.tile_width * 0.3)
		self.offset = (self.size - self.board_size) // 2

		self.render_surf = pygame.Surface([self.board_size]*2, pygame.SRCALPHA)

		self.update_piece_images()
		self.update_tile_images()
		self.update_board_image()

	def update_piece_images(self):
		for side, dict_image_names in self.piece_image_names.items():
			for piece_class, image_name in dict_image_names.items():
				image = main.pyinstaller_image_load(self.assets_path, image_name)
				if not image:
					image = main.pyinstaller_image_load(self.default_assets_path, image_name)
				image.convert_alpha()
				size = image.get_size()[0]
				center = (round(size / 2),) * 2
				color = "black" if "black" in image_name.lower() else "white"
				pygame.draw.circle(image, color, center, size / 2, round(size / 32))
				pygame.draw.circle(image, color, center, size / 6)
				image = pygame.transform.smoothscale(image, [int(self.tile_width)] * 2)
				self.piece_images[side][piece_class] = image

	def update_tile_images(self):
		self.tile_images = {"square": list(), "hex": list()}
		for shape, dict_image_names in self.tile_images_names.items():
			for image_name in dict_image_names:
				image = main.pyinstaller_image_load(self.assets_path, image_name)
				if not image:
					image = main.pyinstaller_image_load(self.default_assets_path, image_name)
				image.convert_alpha()
				image = pygame.transform.smoothscale(image, [int(self.tile_width)] * 2)
				self.tile_images[shape].append(image)

	def update_board_image(self):
		self.board_surf = pygame.Surface([self.board_size] * 2)
		self.board_surf.set_colorkey("black")
		if self.tile_type == "square":
			self.render_square_board_image()
		elif self.tile_type == "hex":
			self.render_hex_board_image()

	def render_square_board_image(self):
		for i in range(self.board.squares):
			for j in range(self.board.squares):
				color = "gray20" if (i + j) % 2 else "gray60"
				self.render_square(self.board_surf, color, (i, j))

	def render_square(self, surface, color, position):
		x, y = position

		if len(color) == 4:
			surf = pygame.Surface((self.tile_width, self.tile_height), pygame.SRCALPHA)
			surf.set_alpha(color[3])
			rect = (0, 0, self.tile_width, self.tile_width)
		else:
			surf = surface
			rect = (self.tile_width * x, self.tile_width * y, self.tile_width, self.tile_width)

		if x == 0 and y == 0:
			pygame.draw.rect(surf, color, rect, border_top_left_radius=self.square_border_radius)
		elif x == self.board.squares - 1 and y == 0:
			pygame.draw.rect(surf, color, rect, border_top_right_radius=self.square_border_radius)
		elif x == 0 and y == self.board.squares - 1:
			pygame.draw.rect(surf, color, rect, border_bottom_left_radius=self.square_border_radius)
		elif x == self.board.squares - 1 and y == self.board.squares - 1:
			pygame.draw.rect(surf, color, rect, border_bottom_right_radius=self.square_border_radius)
		else:
			pygame.draw.rect(surf, color, rect)

		if len(color) == 4:
			upd_rect = surface.blit(surf, (self.tile_width * x, self.tile_width * y))
			self.updated_surfs.append(upd_rect.move(self.offset))

	def render_hex_board_image(self):
		for x in range(self.board.squares):
			for y in range(self.board.squares):
				if x % 2 == 0:
					piece_surf_position = (self.tile_width * 0.75 * x, self.tile_height * y)
				else:
					piece_surf_position = (self.tile_width * 0.75 * x, self.tile_height * y - self.tile_height * 0.5)
				self.board_surf.blit(self.tile_images["hex"][2], piece_surf_position)

	def start(self):
		self.is_player_move = True
		self._on_resize()
		self.particle_system = ParticleSystem()

	def restart(self):
		self.is_player_move = True
		self.board.reset()
		self._on_resize()

	def on_mouse_click(self, event):
		if self.game.menu_opened:
			return

		if event.button not in (1, 3):
			return
		if self.board.winner is not None:
			return
		if self.animation_piece is not None:
			return

		pieces_surf_mouse_pos = np.array(pygame.mouse.get_pos()) - self.offset
		mouse_clicked_on_board = ((0 <= pieces_surf_mouse_pos) & (pieces_surf_mouse_pos <= self.board_size)).all()
		if not mouse_clicked_on_board:
			return

		on_board_position = (pieces_surf_mouse_pos // self.tile_width).astype(int)
		piece = self.board.try_get_piece_by_pos(on_board_position)
		is_reachable = self.selected_piece and (np.equal(on_board_position, self.highlighted_squares)).all(axis=1).any()

		if is_reachable:
			chosen_piece_is_allied = piece and self.selected_piece.is_player == piece.is_player
			if chosen_piece_is_allied:
				self.selected_piece = piece
				self.highlighted_squares = self.board.get_piece_legal_moves(piece)
			elif self.selected_piece.is_player != self.is_player_move:
				self.selected_piece = None
			else:
				self.animate_move((self.selected_piece.pos, on_board_position))
		elif piece:
			if piece != self.selected_piece:
				self.selected_piece = piece
				self.highlighted_squares = self.board.get_piece_legal_moves(piece)
			else:
				self.selected_piece = None

	def get_piece_image(self, piece):
		return self.piece_images[("enemy", "player")[piece.is_player]][piece.__class__]

	def animate_move(self, move):
		self.animation_piece = self.board.try_get_piece_by_pos(move[0])
		self.move_in_process = move
		self.slide_sound.play()

	def apply_move(self):
		target_piece = self.board.try_get_piece_by_pos(self.move_in_process[1])

		self.board.process_move(*self.move_in_process)

		new_piece = self.board.try_get_piece_by_pos(self.move_in_process[1])
		if new_piece != self.animation_piece:
			self.animation_create_promoted_particles(new_piece, 32)
			self.chess_placed.play()
		elif target_piece is not None:
			self.animation_create_eaten_particles(target_piece, 32)
			self.shattering_sound.play()

		self.is_player_move = not self.is_player_move
		self.selected_piece = None

		self.animation_piece = None
		self.move_in_process = None
		self.animation_percentage = 0

		rect = pygame.Rect(*(self.offset + new_piece.pos*self.tile_width), self.tile_width, self.tile_height)
		self.updated_surfs.append(rect)

		if not self.is_player_move and (self.board.winner is None) and self.AI_enabled:
			ai_move = self.AI.get_move()
			self.animate_move(ai_move)

	def update(self, delta_time: float = 1.0):
		self.game.add_debug_text(f"Particles: {len(self.particle_system.particles)}")
		if self.game.menu_opened:
			return
		if self.animation_piece is not None:
			self.animation_percentage = min(1, self.animation_percentage + self.animation_speed*delta_time/1000)
		if self.animation_percentage >= 1:
			self.apply_move()

	def draw(self, surface, centered=True, delta_time: float = 1.0):
		# self.render_surf = pygame.Surface(self.board_surf.get_size(), pygame.SRCALPHA)
		self.render_surf.blit(self.board_surf, (0, 0))

		self.prev_updated_surfs = self.updated_surfs
		self.updated_surfs = []

		if not self.game.menu_opened:
			self.render_highlighted_tiles(self.render_surf)

		rects = self.particle_system.emit(self.render_surf, self.size, delta_time / 1000, not self.game.menu_opened)
		rects = map(lambda rect: rect.move(self.offset), rects)
		self.updated_surfs.extend(rects)

		self.render_pieces(self.render_surf)
		self.render_animated_piece(self.render_surf)

		surface.blit(self.render_surf, self.offset)

		if self.game.menu_opened:
			black_surf = pygame.Surface(self.board_surf.get_size())
			black_surf.set_alpha(128)
			surface.blit(black_surf, self.offset)

			self.game.add_debug_text("ASSIST MODE")
			self.game.add_debug_text(f"Difficulty: {round(self.AI.difficulty * 100)}%")

	def render_highlighted_tiles(self, render_surf):
		if self.animation_piece is not None:
			return

		pieces_surf_mouse_pos = np.array(pygame.mouse.get_pos()) - self.offset

		for i in range(self.board.squares):
			for j in range(self.board.squares):
				on_board_position = np.array([i, j])
				piece_surf_position = on_board_position * self.tile_width

				is_howered = (piece_surf_position < pieces_surf_mouse_pos).all() and (
						pieces_surf_mouse_pos < piece_surf_position + self.tile_width).all()
				is_reachable = self.selected_piece and (np.equal(on_board_position, self.highlighted_squares)).all(
					axis=1).any()

				if self.board.winner is None:
					alpha = 160
					if is_howered:
						self.render_square(render_surf, (204, 214, 62, alpha), (i, j))
					if is_reachable:
						color = (214, 60, 60, alpha)
						if self.selected_piece.is_player == self.is_player_move:
							color = (62, 214, 65, alpha)
						self.render_square(render_surf, color, (i, j))

	def render_pieces(self, render_surf):
		for i in range(self.board.squares):
			for j in range(self.board.squares):
				on_board_position = np.array([i, j])
				piece_surf_position = on_board_position * self.tile_width
				piece = self.board.try_get_piece_by_pos(on_board_position)
				if piece and piece != self.animation_piece:
					piece_image = self.get_piece_image(piece)
					render_surf.blit(piece_image, piece_surf_position)

	def render_animated_piece(self, render_surf):
		if self.animation_piece is not None:
			x = interpolate(self.move_in_process[0][0], self.move_in_process[1][0], self.animation_percentage)
			y = interpolate(self.move_in_process[0][1], self.move_in_process[1][1], self.animation_percentage)
			animation_image = self.get_piece_image(self.animation_piece)
			rect = render_surf.blit(animation_image, (x * self.tile_width, y * self.tile_height))
			self.updated_surfs.append(rect.move(self.offset))
			self.animation_create_particle()

	def animation_create_particle(self):
		speed = random.uniform(20, 70)
		angle = random.uniform(0, 2) * math.pi
		x = interpolate(self.move_in_process[0][0], self.move_in_process[1][0], self.animation_percentage)
		y = interpolate(self.move_in_process[0][1], self.move_in_process[1][1], self.animation_percentage)
		x, y = x * self.tile_width + self.tile_width / 2, y * self.tile_height + self.tile_height / 2
		radius = random.uniform(4, 6)
		delta_radius = random.uniform(-7, -6)
		dx = math.cos(angle) * speed
		dy = math.sin(angle) * speed
		color = get_random_color_from_img(self.get_piece_image(self.animation_piece))
		self.particle_system.add_particle(x=x, y=y, dx=dx, dy=dy, r=radius,
		                                  dr=delta_radius, color=color)

	def animation_create_promoted_particles(self, piece, count: int = 1):
		image = self.get_piece_image(piece)
		for _ in range(count):
			speed = random.uniform(50, 100)
			angle = random.uniform(0, 2) * math.pi
			x = interpolate(self.move_in_process[0][0], self.move_in_process[1][0], self.animation_percentage)
			y = interpolate(self.move_in_process[0][1], self.move_in_process[1][1], self.animation_percentage)
			x, y = x * self.tile_width + self.tile_width / 2, y * self.tile_height + self.tile_height / 2
			radius = random.uniform(7, 10)
			delta_radius = random.uniform(-9, -6)
			dx = math.cos(angle) * speed
			dy = math.sin(angle) * speed
			color = list(get_random_color_from_img(image))
			color.pop()
			self.particle_system.add_particle(x=x, y=y, dx=dx, dy=dy, r=radius,
			                                  dr=delta_radius, color=color, dcolor=(50, 50, 50))

	def animation_create_eaten_particles(self, piece, count: int = 1):
		image = self.get_piece_image(piece)
		for _ in range(count):
			speed = random.uniform(50, 60)
			angle = random.uniform(0, 2) * math.pi
			x = interpolate(self.move_in_process[0][0], self.move_in_process[1][0], self.animation_percentage)
			y = interpolate(self.move_in_process[0][1], self.move_in_process[1][1], self.animation_percentage)
			x, y = x * self.tile_width + self.tile_width / 2, y * self.tile_height + self.tile_height / 2
			radius = random.uniform(12, 16)
			delta_radius = random.uniform(-10, -6)
			dx = math.cos(angle) * speed
			dy = math.sin(angle) * speed
			color = list(get_random_color_from_img(image))
			color.pop()
			self.particle_system.add_particle(x=x, y=y, dx=dx, dy=dy, r=radius,
			                                  dr=delta_radius, color=color, dcolor=(-75, -75, -75))
