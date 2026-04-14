import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from constants import BODIES_DATA
from body import CelestialBody
from physics import update_physics

WIDTH  = 1200
HEIGHT = 800
FPS    = 60
TITLE  = "Solar System Simulator 3D — Gravitational Field"

camera_distance = 40.0
camera_rot_x    = 20.0
camera_rot_y    = 0.0
mouse_last      = None
mouse_dragging  = False

GRID_SIZE   = 80
GRID_EXTENT = 18.0
GRID_DEPTH  = 10.0

SUN_MASS = 1.989e30
BH_MASS  = 1.989e30

black_hole_active  = False
bh_position        = np.array([-35.0, 0.0, 0.0])
bh_accretion_angle = 0.0
bh_radius          = 0.3

ORBIT_RADIUS     = 4.0
ORBIT_SPEED      = 0.004
orbit_angle      = 0.0

BH_APPROACH_SPEED = 0.08
SUN_MOVE_SPEED    = 0.012
ORBIT_START_DIST  = 5.0


def update_binary_orbit(sun_pos, dt=1.0):
    global orbit_angle, ORBIT_RADIUS
    orbit_angle  += 0.003 * dt
    # Raza rămâne FIXĂ la 4.0 — Soarele și BH nu se suprapun niciodată
    ORBIT_RADIUS = 4.0
    new_sun = np.array([
        np.cos(orbit_angle) * ORBIT_RADIUS, 0.0,
        np.sin(orbit_angle) * ORBIT_RADIUS])
    new_bh = np.array([
        np.cos(orbit_angle + np.pi) * ORBIT_RADIUS, 0.0,
        np.sin(orbit_angle + np.pi) * ORBIT_RADIUS])
    bary = (SUN_MASS * new_sun + BH_MASS * new_bh) / (SUN_MASS + BH_MASS)
    return new_sun, new_bh, bary


def init_bodies():
    bodies = []
    for data in BODIES_DATA:
        body = CelestialBody(
            name=data["name"], mass=data["mass"],
            position=data["position"], velocity=data["velocity"],
            color=data["color"], radius=data["radius"],
            is_star=data.get("is_star", False))
        body.absorbed = False
        if not data.get("is_star", False):
            v = np.array(data["velocity"], dtype=float)
            v_norm = np.linalg.norm(v)
            if v_norm > 0:
                body.velocity = (v / v_norm) * 0.3
        bodies.append(body)
    return bodies


def update_planets_chaotic(bodies, sun_pos, dt=0.02):
    G = 2.5
    for body in bodies:
        if body.is_star or body.absorbed:
            continue
        pos = body.position.copy()

        # Direcția spre BH
        to_bh = bh_position - pos
        d_bh  = max(np.linalg.norm(to_bh), 0.3)
        direction_to_bh = to_bh / d_bh

        # Forță constantă spre BH
        a_bh = direction_to_bh * G / (d_bh ** 1.0)

        # Deviație laterală FOARTE puternică și vizibilă
        perp = np.array([-direction_to_bh[2], 0.0, direction_to_bh[0]])
        # Alternăm direcția la fiecare frame pentru efect haotic vizibil
        sign = 1.0 if np.random.random() > 0.5 else -1.0
        lateral = perp * sign * np.random.uniform(0.8, 2.0)

        # Adăugăm ambele componente la viteză
        body.velocity += a_bh * dt          # merge spre BH
        body.velocity += lateral * dt       # deviază stânga-dreapta

        # Normalizăm viteza păstrând direcția generală spre BH
        # Componenta spre BH trebuie să fie dominantă
        v_toward_bh = np.dot(body.velocity, direction_to_bh)
        if v_toward_bh < 0.5:
            # Dacă planeta nu merge spre BH, o corectăm
            body.velocity += direction_to_bh * 1.0

        speed = np.linalg.norm(body.velocity)
        if speed > 5.0:
            body.velocity = (body.velocity / speed) * 5.0

        body.position += body.velocity * dt

        if d_bh < 4.0:
            if not hasattr(body, 'shrinking'):
                body.shrinking  = 0.0
                body.spiral_angle = 0.0

            # Spirală vizibilă — planeta se rotește în jurul BH
            # în timp ce e trasă spre interior
            body.spiral_angle += 0.15  # viteza de rotație a spiralei

            # Direcție spre BH
            to_bh_dir = (bh_position - body.position)
            d = max(np.linalg.norm(to_bh_dir), 0.1)
            to_bh_dir = to_bh_dir / d

            # Componentă perpendiculară — rotație vizibilă
            perp = np.array([-to_bh_dir[2], 0.0, to_bh_dir[0]])

            # Cu cât e mai aproape, cu atât spirala e mai strânsă și mai rapidă
            pull_strength  = 0.25 * (4.0 - d) / 4.0 + 0.05
            spin_strength  = 0.3  * (4.0 - d) / 4.0

            body.position += to_bh_dir * pull_strength
            body.position += perp      * spin_strength * np.sin(body.spiral_angle)

            # Micșorare vizibilă
            shrink_rate   = 0.008 * (4.0 - d) / 4.0
            body.radius   = max(0.0, body.radius - shrink_rate)

            if body.radius <= 0.01:
                body.absorbed = True
                body.position = np.array([9999.0, 9999.0, 9999.0])

def compute_grid_deformation(bodies, sun_pos):
    step = (2 * GRID_EXTENT) / GRID_SIZE
    grid_points = []
    for i in range(GRID_SIZE + 1):
        row = []
        for j in range(GRID_SIZE + 1):
            x = -GRID_EXTENT + i * step
            z = -GRID_EXTENT + j * step
            deform_y = 0.0
            dist = max(np.sqrt((x-sun_pos[0])**2 + (z-sun_pos[2])**2), 0.5)
            deform_y -= 5.0 / (dist**1.5 + 0.5)
            for body in bodies:
                if body.is_star or body.absorbed:
                    continue
                dist = max(np.sqrt((x-body.position[0])**2 +
                                   (z-body.position[2])**2), 0.5)
                if body.name == "Jupiter":
                    deform_y -= 3.0 / (dist**1.5 + 0.5)
                elif body.name == "Earth":
                    deform_y -= 1.5 / (dist**1.5 + 0.5)
                elif body.name == "Mars":
                    deform_y -= 0.9 / (dist**1.5 + 0.5)
            if black_hole_active:
                dist_bh = max(np.sqrt((x-bh_position[0])**2 +
                                      (z-bh_position[2])**2), 0.5)
                deform_y -= 5.0 / (dist_bh**1.5 + 0.5)
            deform_y = max(deform_y, -GRID_DEPTH)
            row.append((x, deform_y, z))
        grid_points.append(row)
    return grid_points


def draw_gravity_grid(grid_points):
    glLineWidth(1.0)
    glDisable(GL_LIGHTING)

    def grid_color(y):
        t = min(abs(y) / GRID_DEPTH, 1.0)
        if black_hole_active:
            return (min(0.2+t*0.8, 1.0), min(0.1+t*0.2, 1.0),
                    min(0.6+t*0.2, 1.0))
        return (min(t*0.9, 1.0), min(0.3+t*0.5, 1.0), 0.8)

    for i in range(GRID_SIZE + 1):
        glBegin(GL_LINE_STRIP)
        for j in range(GRID_SIZE + 1):
            x, y, z = grid_points[i][j]
            glColor3f(*grid_color(y))
            glVertex3f(x, y, z)
        glEnd()
    for j in range(GRID_SIZE + 1):
        glBegin(GL_LINE_STRIP)
        for i in range(GRID_SIZE + 1):
            x, y, z = grid_points[i][j]
            glColor3f(*grid_color(y))
            glVertex3f(x, y, z)
        glEnd()
    glEnable(GL_LIGHTING)


def draw_barycenter(bary_pos, pulse_t):
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    pulse  = 0.25 + 0.2 * np.sin(pulse_t * 0.06)
    pulse2 = 0.25 + 0.2 * np.sin(pulse_t * 0.06 + np.pi)
    for ring in range(7):
        r     = (pulse if ring % 2 == 0 else pulse2) + ring * 0.28
        alpha = max(0.0, 1.0 - ring * 0.13)
        heat  = max(0.0, 1.0 - ring * 0.1)
        glColor4f(1.0, heat*0.85+0.1, heat*0.1, alpha)
        glBegin(GL_LINE_LOOP)
        for angle in range(0, 360, 3):
            rad = np.radians(angle)
            glVertex3f(bary_pos[0]+np.cos(rad)*r, bary_pos[1],
                       bary_pos[2]+np.sin(rad)*r)
        glEnd()
    cross_angle = pulse_t * 1.5
    cross_size  = 0.6 + 0.2 * np.sin(pulse_t * 0.05)
    glLineWidth(1.5)
    glColor4f(1.0, 1.0, 0.5, 0.9)
    glBegin(GL_LINES)
    for arm in range(4):
        rad = np.radians(cross_angle + arm * 90)
        glVertex3f(*bary_pos)
        glVertex3f(bary_pos[0]+np.cos(rad)*cross_size, bary_pos[1],
                   bary_pos[2]+np.sin(rad)*cross_size)
    glEnd()
    glLineWidth(1.0)
    glPointSize(14.0)
    glBegin(GL_POINTS)
    glColor4f(1.0, 1.0, 0.6, 1.0)
    glVertex3f(*bary_pos)
    glEnd()
    for g in range(4):
        gr = 0.15 + g * 0.12
        ga = max(0.0, 0.6 - g * 0.14)
        glColor4f(1.0, 0.9, 0.3, ga)
        glBegin(GL_LINE_LOOP)
        for angle in range(0, 360, 6):
            rad = np.radians(angle)
            glVertex3f(bary_pos[0]+np.cos(rad)*gr, bary_pos[1],
                       bary_pos[2]+np.sin(rad)*gr)
        glEnd()
    glColor4f(1.0, 1.0, 0.3, 0.2)
    glBegin(GL_LINES)
    glVertex3f(*bary_pos)
    glVertex3f(*bh_position)
    glEnd()
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LIGHTING)


def draw_black_hole():
    global bh_accretion_angle
    bh_accretion_angle += 1.5
    glPushMatrix()
    glTranslatef(*bh_position)
    glDisable(GL_LIGHTING)
    glColor3f(0.0, 0.0, 0.0)
    quad = gluNewQuadric()
    gluSphere(quad, bh_radius, 32, 32)
    gluDeleteQuadric(quad)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glRotatef(bh_accretion_angle, 0, 1, 0)
    glRotatef(20, 1, 0, 0)
    for ring in range(8):
        r_inner = bh_radius + ring * 0.12
        r_outer = r_inner + 0.10
        alpha   = max(0.0, 0.9 - ring * 0.10)
        heat    = max(0.0, 1.0 - ring * 0.1)
        glColor4f(1.0, heat*0.7+0.3, heat*0.1, alpha)
        glBegin(GL_QUAD_STRIP)
        for angle in range(361):
            rad = np.radians(angle)
            glVertex3f(np.cos(rad)*r_inner, np.sin(rad)*r_inner, 0.0)
            glVertex3f(np.cos(rad)*r_outer, np.sin(rad)*r_outer, 0.0)
        glEnd()
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LIGHTING)
    glPopMatrix()


def draw_sphere(radius, color, slices=24, stacks=24):
    glColor3f(*color)
    quad = gluNewQuadric()
    gluSphere(quad, radius, slices, stacks)
    gluDeleteQuadric(quad)


def draw_glow(position, color, radius):
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    for layer in range(5):
        alpha = 0.15 - layer * 0.025
        scale = radius + layer * 0.12
        glColor4f(color[0], color[1]*0.8, 0.1, alpha)
        glPushMatrix()
        glTranslatef(*position)
        quad = gluNewQuadric()
        gluSphere(quad, scale, 16, 16)
        gluDeleteQuadric(quad)
        glPopMatrix()
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LIGHTING)


def draw_trail(trail, color):
    if len(trail) < 2:
        return
    glDisable(GL_LIGHTING)
    glLineWidth(2.0)
    glBegin(GL_LINE_STRIP)
    for i, pos in enumerate(trail):
        alpha = i / len(trail)
        glColor3f(color[0]*alpha, color[1]*alpha, color[2]*alpha)
        glVertex3f(*pos)
    glEnd()
    glLineWidth(1.0)
    glEnable(GL_LIGHTING)


def draw_stars_background():
    glDisable(GL_LIGHTING)
    glPointSize(1.5)
    glBegin(GL_POINTS)
    rng = np.random.default_rng(42)
    positions    = rng.uniform(-200, 200, (1000, 3))
    brightnesses = rng.uniform(0.5, 1.0, 1000)
    for pos, b in zip(positions, brightnesses):
        glColor3f(b, b, b)
        glVertex3f(*pos)
    glEnd()
    glEnable(GL_LIGHTING)


def setup_opengl():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.0, 0.0, 0.04, 1.0)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 2.0, 0.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 0.95, 0.8, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.05, 0.05, 0.1, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 0.8, 1.0])


def set_camera():
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -camera_distance)
    glRotatef(camera_rot_x, 1, 0, 0)
    glRotatef(camera_rot_y, 0, 1, 0)


def draw_hud(surface, font, font_large, bodies, paused, sim_day,
             time_speed, barycenter, sun_pos, bh_phase):
    global bh_position
    panel = pygame.Surface((285, 390), pygame.SRCALPHA)
    panel.fill((3, 5, 18, 200))
    pygame.draw.rect(panel, (40, 80, 160, 200), panel.get_rect(), 1)
    surface.blit(panel, (10, 10))
    surface.blit(font_large.render(
        "Gravity Field Simulator", True, (255, 220, 50)), (20, 18))
    pygame.draw.line(surface, (40, 80, 160), (15, 40), (283, 40), 1)
    years = sim_day // 365
    days  = sim_day % 365
    for i, (txt, col) in enumerate([
        (f"Year: {years}   Day: {days}", (160, 210, 255)),
        (f"Speed: {time_speed} days/frame", (160, 210, 255)),
        ("PAUSED" if paused else "RUNNING",
         (255, 80, 80) if paused else (80, 255, 120)),
    ]):
        surface.blit(font.render(txt, True, col), (20, 50 + i * 22))
    pygame.draw.line(surface, (40, 80, 160), (15, 120), (283, 120), 1)
    surface.blit(font.render(
        "CELESTIAL BODIES", True, (120, 160, 220)), (20, 128))
    for i, body in enumerate(bodies):
        absorbed = getattr(body, 'absorbed', False)
        c   = (80, 80, 80) if absorbed else tuple(
              int(x * 255) for x in body.color)
        txt = f"{body.name} (absorbed)" if absorbed else body.name
        pygame.draw.circle(surface, c, (28, 150 + i * 20), 5)
        surface.blit(font.render(txt, True, c), (42, 143 + i * 20))
    pygame.draw.line(surface, (40, 80, 160), (15, 242), (283, 242), 1)
    bh_col  = (255, 100, 50) if black_hole_active else (150, 150, 150)
    bh_text = "BLACK HOLE: ACTIVE" if black_hole_active else "BLACK HOLE: OFF"
    surface.blit(font.render(bh_text, True, bh_col), (20, 250))
    surface.blit(font.render(
        "Press B to toggle", True, (120, 120, 140)), (20, 268))
    if black_hole_active:
        pygame.draw.line(surface, (40, 80, 160), (15, 287), (283, 287), 1)
        dist = np.linalg.norm(sun_pos - bh_position)
        if bh_phase == "approaching":
            surface.blit(font.render(
                f"BH approaching... dist: {dist:.1f}",
                True, (255, 180, 80)), (20, 295))
            surface.blit(font.render(
                "Planets destabilizing...",
                True, (200, 150, 100)), (20, 313))
        elif bh_phase == "orbiting":
            surface.blit(font.render(
                f"Barycenter: ({barycenter[0]:.1f}, {barycenter[2]:.1f})",
                True, (255, 255, 150)), (20, 295))
            surface.blit(font.render(
                "★ BINARY ORBIT ACTIVE", True, (255, 200, 50)), (20, 313))
            surface.blit(font.render(
                "Press R to reset", True, (180, 180, 180)), (20, 331))
    legend = pygame.Surface((285, 55), pygame.SRCALPHA)
    legend.fill((3, 5, 18, 200))
    pygame.draw.rect(legend, (40, 80, 160, 200), legend.get_rect(), 1)
    surface.blit(legend, (10, 410))
    surface.blit(font.render(
        "Grid = 3D gravitational field", True, (140, 180, 255)), (20, 418))
    surface.blit(font.render(
        "Curvature = gravity intensity", True, (140, 180, 255)), (20, 436))
    ctrl = pygame.Surface((540, 55), pygame.SRCALPHA)
    ctrl.fill((3, 5, 18, 200))
    pygame.draw.rect(ctrl, (40, 80, 160, 200), ctrl.get_rect(), 1)
    surface.blit(ctrl, (10, HEIGHT - 65))
    surface.blit(font.render(
        "Drag: rotate  Scroll: zoom  SPACE: pause  B: black hole",
        True, (140, 160, 200)), (20, HEIGHT - 58))
    surface.blit(font.render(
        "Up/Down: speed   R: reset   ESC: exit",
        True, (140, 160, 200)), (20, HEIGHT - 38))


def draw_labels(surface, font_label, bodies, sun_pos):
    try:
        mv  = glGetDoublev(GL_MODELVIEW_MATRIX)
        prj = glGetDoublev(GL_PROJECTION_MATRIX)
        vp  = glGetIntegerv(GL_VIEWPORT)

        def project(pos):
            sx, sy, _ = gluProject(pos[0], pos[1], pos[2], mv, prj, vp)
            return int(sx), HEIGHT - int(sy)

        sx, sy = project(sun_pos)
        if 0 < sx < WIDTH and 0 < sy < HEIGHT:
            lbl = font_label.render("Sun", True, (255, 220, 50))
            surface.blit(lbl, (sx - lbl.get_width()//2, sy - 28))
        for body in bodies:
            if getattr(body, 'absorbed', False) or body.is_star:
                continue
            sx, sy = project(body.position)
            if 0 < sx < WIDTH and 0 < sy < HEIGHT:
                c   = tuple(int(v*255) for v in body.color)
                lbl = font_label.render(body.name, True, c)
                surface.blit(lbl, (sx - lbl.get_width()//2, sy - 28))
        if black_hole_active:
            sx, sy = project(bh_position)
            if 0 < sx < WIDTH and 0 < sy < HEIGHT:
                lbl = font_label.render("BLACK HOLE", True, (255, 100, 50))
                surface.blit(lbl, (sx - lbl.get_width()//2, sy - 35))
    except:
        pass


def main():
    global camera_distance, camera_rot_x, camera_rot_y
    global mouse_last, mouse_dragging
    global black_hole_active, bh_position, bh_accretion_angle
    global orbit_angle, ORBIT_RADIUS, WIDTH, HEIGHT

    pygame.init()
    info   = pygame.display.Info()
    WIDTH  = info.current_w
    HEIGHT = info.current_h
    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT), DOUBLEBUF | OPENGL | FULLSCREEN)
    pygame.event.pump()
    pygame.display.flip()
    pygame.display.set_caption(TITLE)
    clock      = pygame.time.Clock()
    font       = pygame.font.SysFont("Arial", 13)
    font_large = pygame.font.SysFont("Arial", 13, bold=True)
    font_label = pygame.font.SysFont("Arial", 12, bold=True)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, WIDTH / HEIGHT, 0.1, 1000.0)
    setup_opengl()

    bodies             = init_bodies()
    hud_tex            = glGenTextures(1)
    paused             = True
    sim_day            = 0
    time_speed         = 3
    pulse_t            = 0
    sun_pos            = np.array([0.0, 0.0, 0.0])
    barycenter         = np.array([0.0, 0.0, 0.0])
    black_hole_active  = False
    bh_position        = np.array([-35.0, 0.0, 0.0])
    bh_accretion_angle = 0.0
    orbit_angle        = 0.0
    ORBIT_RADIUS       = 4.0
    bh_phase           = "inactive"

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    paused = not paused
                elif event.key == K_UP:
                    time_speed = min(time_speed + 1, 50)
                elif event.key == K_DOWN:
                    time_speed = max(time_speed - 1, 1)
                elif event.key == K_r:
                    bodies             = init_bodies()
                    sim_day            = 0
                    sun_pos            = np.array([0.0, 0.0, 0.0])
                    barycenter         = np.array([0.0, 0.0, 0.0])
                    black_hole_active  = False
                    bh_position        = np.array([-35.0, 0.0, 0.0])
                    bh_accretion_angle = 0.0
                    orbit_angle        = 0.0
                    ORBIT_RADIUS       = 4.0
                    bh_phase           = "inactive"
                    paused             = True
                elif event.key == K_b:
                    black_hole_active = not black_hole_active
                    if black_hole_active:
                        bh_position  = np.array([-35.0, 0.0, 0.0])
                        bh_phase     = "approaching"
                        orbit_angle  = 0.0
                        ORBIT_RADIUS = 4.0
                    else:
                        bh_phase          = "inactive"
                        sun_pos           = np.array([0.0, 0.0, 0.0])
                        bh_position       = np.array([-35.0, 0.0, 0.0])
                        bodies            = init_bodies()
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                mouse_dragging = True
                mouse_last = event.pos
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                mouse_dragging = False
            elif event.type == MOUSEMOTION and mouse_dragging:
                dx = event.pos[0] - mouse_last[0]
                dy = event.pos[1] - mouse_last[1]
                camera_rot_y += dx * 0.4
                camera_rot_x += dy * 0.4
                mouse_last = event.pos
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 4:
                    camera_distance = max(5, camera_distance - 2)
                elif event.button == 5:
                    camera_distance = min(200, camera_distance + 2)

        if not paused:
            sim_day += time_speed
            pulse_t += 1

            if black_hole_active:

                if bh_phase == "approaching":
                    # BH se mișcă spre Soare
                    direction = sun_pos - bh_position
                    dist = np.linalg.norm(direction)
                    if dist > 0.1:
                        bh_position = bh_position + (
                            direction / dist) * BH_APPROACH_SPEED

                    # Soarele se mișcă LENT și VIZIBIL spre BH
                    to_bh = bh_position - sun_pos
                    d_sb  = np.linalg.norm(to_bh)
                    if d_sb > 0.1:
                        sun_pos = sun_pos + (to_bh / d_sb) * SUN_MOVE_SPEED
                    for body in bodies:
                        if body.is_star:
                            body.position = sun_pos.copy()

                    # Planetele — traiectorie haotică
                    update_planets_chaotic(bodies, sun_pos)

                    # Tranziție lină la orbită
                    if dist <= ORBIT_START_DIST:
                        bh_phase = "orbiting"
                        orbit_angle  = np.arctan2(
                            bh_position[2] - sun_pos[2],
                            bh_position[0] - sun_pos[0])
                        ORBIT_RADIUS = max(dist / 2.0, 4.0)

                elif bh_phase == "orbiting":
                    # Soarele și BH orbitează baricentrul
                    sun_pos, bh_position, barycenter = update_binary_orbit(
                        sun_pos, dt=time_speed)
                    for body in bodies:
                        if body.is_star:
                            body.position = sun_pos.copy()

                    # Planetele rămase continuă să fie înghițite cu spirală
                    update_planets_chaotic(bodies, sun_pos)

                barycenter = (SUN_MASS * sun_pos + BH_MASS * bh_position) / (
                    SUN_MASS + BH_MASS)

            else:
                update_physics(bodies, steps=time_speed)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        set_camera()
        draw_stars_background()
        grid = compute_grid_deformation(bodies, sun_pos)
        draw_gravity_grid(grid)

        for body in bodies:
            if not body.is_star and not getattr(body, 'absorbed', False):
                draw_trail(body.trail, body.color)

        glEnable(GL_LIGHTING)
        for body in bodies:
            if getattr(body, 'absorbed', False):
                continue
            glPushMatrix()
            glTranslatef(*body.position)
            draw_sphere(body.radius, body.color)
            glPopMatrix()
            if body.is_star:
                draw_glow(body.position, body.color, body.radius)

        if black_hole_active:
            draw_black_hole()
            # Barycenter vizibil când BH e aproape SAU în orbită
            dist_now = np.linalg.norm(sun_pos - bh_position)
            if bh_phase == "orbiting" or (
                    bh_phase == "approaching" and dist_now < 15.0):
                draw_barycenter(barycenter, pulse_t)

        hud = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        hud.fill((0, 0, 0, 0))
        draw_hud(hud, font, font_large, bodies, paused,
                 sim_day, time_speed, barycenter, sun_pos, bh_phase)
        draw_labels(hud, font_label, bodies, sun_pos)

        hud_data = pygame.image.tostring(hud, "RGBA", True)
        glBindTexture(GL_TEXTURE_2D, hud_tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WIDTH, HEIGHT, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, hud_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, hud_tex)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(1, 0)
        glTexCoord2f(1, 1); glVertex2f(1, 1)
        glTexCoord2f(0, 1); glVertex2f(0, 1)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()