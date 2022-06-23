import pygame


class ParticleSystem:
	def __init__(self):
		self.particles = list()

	def add_particle(self, **data):
		data["x"] = data.get("x", 0)
		data["y"] = data.get("y", 0)
		data["color"] = data.get("color", [255, 255, 255])
		self.particles.append(data)

	def emit(self, surface, living_area: list = None, delta_time: float = 1.0, update=True):
		if not self.particles:
			return
		for particle in self.particles:
			pygame.draw.circle(surface, particle["color"], (particle["x"], particle["y"]), particle["r"])
			if update:
				self.update_particle(particle, delta_time)
				self.remove_dead_particle(particle, living_area)

	@staticmethod
	def update_particle(particle, deltatime):
		if "dx" in particle:
			particle["x"] += particle["dx"] * deltatime
		if "dy" in particle:
			particle["y"] += particle["dy"] * deltatime
		if "dr" in particle:
			particle["r"] += particle["dr"] * deltatime
		if "dcolor" in particle:
			if len(particle["color"]) > len(particle["dcolor"]):
				raise AttributeError(f"Length of color ({len(particle['color'])}) greater then length of dcolor ({len(particle['dcolor'])})")
			for i in range(len(particle["color"])):
				particle["color"][i] = max(0, min(255, particle["color"][i] + particle["dcolor"][i] * deltatime))

	def remove_dead_particle(self, particle, living_area):
		if living_area is not None:
			if (0 < particle["x"] < living_area[0]) and (0 < particle["y"] < living_area[1]):
				pass  # we are in living area, so do nothing
			else:
				self.particles.remove(particle)
		if particle["r"] <= 0 and particle in self.particles:
			self.particles.remove(particle)
