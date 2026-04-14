import numpy as np
from constants import G, TIME_STEP

def compute_gravity(body_a, body_b):
    delta = (body_b.position - body_a.position) * 1e9
    distance = np.linalg.norm(delta)
    if distance < 1e6:
        return np.zeros(3)
    force_magnitude = G * body_a.mass * body_b.mass / (distance ** 2)
    direction = delta / distance
    return force_magnitude * direction

def update_physics(bodies, steps=1):
    dt = TIME_STEP * steps
    for body in bodies:
        body.reset_force()
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            force = compute_gravity(bodies[i], bodies[j])
            bodies[i].apply_force(force)
            bodies[j].apply_force(-force)
    for body in bodies:
        body.update(dt)