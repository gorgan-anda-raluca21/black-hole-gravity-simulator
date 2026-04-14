import numpy as np

class CelestialBody:
    MAX_TRAIL_LENGTH = 300

    def __init__(self, name, mass, position, velocity, color, radius, is_star=False):
        self.name = name
        self.mass = mass
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.force = np.zeros(3, dtype=float)
        self.color = color
        self.radius = radius
        self.is_star = is_star
        self.trail = []

    def reset_force(self):
        self.force = np.zeros(3, dtype=float)

    def apply_force(self, f):
        self.force += f

    def update(self, dt):
        if self.is_star:
            return
        acceleration = self.force / self.mass
        self.velocity += acceleration * dt
        self.position += self.velocity * dt / 1e9
        self.trail.append(self.position.copy())
        if len(self.trail) > self.MAX_TRAIL_LENGTH:
            self.trail.pop(0)