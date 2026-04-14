G = 6.674e-11
SCALE = 1e9
TIME_STEP = 3600 * 24

BODIES_DATA = [
    {
        "name": "Sun",
        "mass": 1.989e30,
        "position": [0.0, 0.0, 0.0],
        "velocity": [0.0, 0.0, 0.0],
        "color": (1.0, 0.9, 0.2),
        "radius": 0.3,
        "is_star": True
    },
    {
        "name": "Earth",
        "mass": 5.972e24,
        "position": [5.0, 0.0, 0.0],
        "velocity": [0.0, 29780.0, 0.0],
        "color": (0.2, 0.6, 1.0),
        "radius": 0.15,
        "is_star": False
    },
    {
        "name": "Mars",
        "mass": 6.390e23,
        "position": [8.0, 0.0, 0.0],
        "velocity": [0.0, 24077.0, 0.0],
        "color": (0.9, 0.3, 0.1),
        "radius": 0.12,
        "is_star": False
    },
    {
        "name": "Jupiter",
        "mass": 1.898e27,
        "position": [13.0, 0.0, 0.0],
        "velocity": [0.0, 13070.0, 0.0],
        "color": (0.85, 0.65, 0.4),
        "radius": 0.25,
        "is_star": False
    },
]