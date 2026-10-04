import math
import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective


class AICore2(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

        self.time = 0.0
        self.rotation = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0

        self.activity = 0.0
        self.target_activity = 0.0

        self.particles = []
        self.flow_particles = []
        self.orbit_particles = []

        self.create_particles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    # ============================================================
    # PARTICLES
    # ============================================================

    def create_particles(self):
        self.particles.clear()
        self.flow_particles.clear()
        self.orbit_particles.clear()

        # --------------------------------------------------------
        # Główna sfera
        # Fibonacci sphere
        # --------------------------------------------------------

        particle_count = 1800

        golden_angle = math.pi * (3.0 - math.sqrt(5.0))

        for i in range(particle_count):
            y = 1.0 - (i / float(particle_count - 1)) * 2.0

            radius = math.sqrt(max(0.0, 1.0 - y * y))

            theta = golden_angle * i

            x = math.cos(theta) * radius
            z = math.sin(theta) * radius

            # Delikatna nieregularność powierzchni
            noise = random.uniform(-0.045, 0.045)

            particle_radius = 3.0 + noise

            x *= particle_radius
            y *= particle_radius
            z *= particle_radius

            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "z": z,
                    "base_x": x,
                    "base_y": y,
                    "base_z": z,
                    "phase": random.uniform(0.0, math.pi * 2.0),
                    "speed": random.uniform(0.4, 1.2),
                    "size": random.choice([1.0, 1.0, 1.2, 1.4, 1.7, 2.0]),
                    "brightness": random.uniform(0.35, 1.0),
                }
            )

        # --------------------------------------------------------
        # Cząsteczki przepływające po powierzchni
        # --------------------------------------------------------

        for _ in range(550):
            latitude = random.uniform(-math.pi * 0.48, math.pi * 0.48)

            longitude = random.uniform(0.0, math.pi * 2.0)

            self.flow_particles.append(
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "speed": random.uniform(0.25, 0.8),
                    "phase": random.uniform(0.0, math.pi * 2.0),
                    "size": random.choice([1.0, 1.2, 1.5, 2.0, 2.5]),
                    "brightness": random.uniform(0.5, 1.0),
                }
            )

        # --------------------------------------------------------
        # Zewnętrzna orbita
        # --------------------------------------------------------

        for _ in range(180):
            angle = random.uniform(0.0, math.pi * 2.0)

            radius = random.uniform(3.25, 4.2)

            self.orbit_particles.append(
                {
                    "angle": angle,
                    "radius": radius,
                    "height": random.uniform(-0.35, 0.35),
                    "speed": random.uniform(0.08, 0.22),
                    "phase": random.uniform(0.0, math.pi * 2.0),
                    "size": random.choice([1.0, 1.2, 1.5, 2.0]),
                }
            )

    # ============================================================
    # OPENGL
    # ============================================================

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)

        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

    def resizeGL(self, width, height):
        if height <= 0:
            height = 1

        glViewport(0, 0, width, height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        gluPerspective(42.0, width / float(height), 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)

    # ============================================================
    # ANIMATION
    # ============================================================

    def animate(self):
        self.time += 0.016

        # Płynny obrót całej sfery
        self.rotation += 0.22
        self.rotation_y += 0.11
        self.rotation_z += 0.04

        # Delikatne przejście activity
        self.activity += (self.target_activity - self.activity) * 0.035

        # --------------------------------------------------------
        # Główne cząsteczki
        # --------------------------------------------------------

        for particle in self.particles:
            particle["phase"] += 0.012 * particle["speed"]

        # --------------------------------------------------------
        # Cząsteczki przepływu
        # --------------------------------------------------------

        for particle in self.flow_particles:
            particle["longitude"] += (
                0.006 * particle["speed"] * (1.0 + self.activity * 2.0)
            )

        # --------------------------------------------------------
        # Orbita
        # --------------------------------------------------------

        for particle in self.orbit_particles:
            particle["angle"] += 0.002 * particle["speed"] * (1.0 + self.activity * 2.0)

        self.update()

    # ============================================================
    # PAINT
    # ============================================================

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Kamera
        glTranslatef(0.0, 0.0, -9.0)

        # Powolny ruch całej struktury
        glRotatef(math.sin(self.time * 0.20) * 4.0, 1.0, 0.0, 0.0)

        glRotatef(self.rotation, 0.0, 1.0, 0.0)

        glRotatef(math.sin(self.time * 0.15) * 3.0, 0.0, 0.0, 1.0)

        # Kolejność ma znaczenie
        self.draw_outer_glow()
        self.draw_orbit_particles()
        self.draw_sphere_particles()
        self.draw_flow_particles()
        self.draw_energy_streams()
        self.draw_core_glow()

    # ============================================================
    # OUTER GLOW
    # ============================================================

    def draw_outer_glow(self):
        pulse = (math.sin(self.time * 1.8) + 1.0) * 0.5

        pulse += self.activity * 0.5

        layers = [
            (3.65, 0.018),
            (3.50, 0.014),
            (3.35, 0.010),
        ]

        for radius, alpha in layers:
            glPointSize(radius * 10.0)

            glBegin(GL_POINTS)

            glColor4f(0.05, 0.55, 1.0, alpha + pulse * 0.008)

            glVertex3f(0.0, 0.0, 0.0)

            glEnd()

    # ============================================================
    # SPHERE PARTICLES
    # ============================================================

    def draw_sphere_particles(self):
        groups = {1.0: [], 1.2: [], 1.4: [], 1.7: [], 2.0: []}

        for particle in self.particles:
            x = particle["base_x"]
            y = particle["base_y"]
            z = particle["base_z"]

            phase = particle["phase"]

            # Delikatne oddychanie sfery
            wave = math.sin(self.time * 0.9 + phase) * 0.025

            scale = 1.0 + wave

            x *= scale
            y *= scale
            z *= scale

            # Subtelne przesuwanie powierzchni
            x += math.sin(self.time * 0.5 + phase) * 0.025

            y += math.cos(self.time * 0.4 + phase) * 0.025

            z += math.sin(self.time * 0.7 + phase) * 0.025

            groups[particle["size"]].append((x, y, z, phase, particle["brightness"]))

        for size, points in groups.items():
            glPointSize(size)

            glBegin(GL_POINTS)

            for x, y, z, phase, brightness in points:
                shimmer = (math.sin(self.time * 2.5 + phase) + 1.0) * 0.5

                alpha = 0.12 + brightness * 0.30 + shimmer * 0.18

                alpha += self.activity * 0.12

                glColor4f(0.08, 0.55 + shimmer * 0.20, 1.0, min(alpha, 0.95))

                glVertex3f(x, y, z)

            glEnd()

    # ============================================================
    # FLOW PARTICLES
    # ============================================================

    def draw_flow_particles(self):
        groups = {1.0: [], 1.2: [], 1.5: [], 2.0: [], 2.5: []}

        for particle in self.flow_particles:
            latitude = particle["latitude"]
            longitude = particle["longitude"]

            radius = 3.04

            cos_lat = math.cos(latitude)

            x = math.cos(longitude) * cos_lat * radius

            y = math.sin(latitude) * radius

            z = math.sin(longitude) * cos_lat * radius

            # Falowanie powierzchni
            wave = math.sin(longitude * 4.0 + self.time * 1.8 + particle["phase"])

            offset = wave * 0.06

            length = math.sqrt(x * x + y * y + z * z)

            if length > 0:
                x += x / length * offset
                y += y / length * offset
                z += z / length * offset

            groups[particle["size"]].append(
                (x, y, z, particle["phase"], particle["brightness"])
            )

        for size, points in groups.items():
            glPointSize(size)

            glBegin(GL_POINTS)

            for x, y, z, phase, brightness in points:
                pulse = (math.sin(self.time * 4.0 + phase) + 1.0) * 0.5

                alpha = 0.25 + brightness * 0.40 + pulse * 0.30

                glColor4f(0.15, 0.70, 1.0, min(alpha, 1.0))

                glVertex3f(x, y, z)

            glEnd()

    # ============================================================
    # ORBIT PARTICLES
    # ============================================================

    def draw_orbit_particles(self):
        groups = {1.0: [], 1.2: [], 1.5: [], 2.0: []}

        for particle in self.orbit_particles:
            angle = particle["angle"]
            radius = particle["radius"]

            x = math.cos(angle) * radius
            z = math.sin(angle) * radius

            y = (
                particle["height"]
                + math.sin(self.time * 0.8 + particle["phase"]) * 0.12
            )

            groups[particle["size"]].append((x, y, z, particle["phase"]))

        for size, points in groups.items():
            glPointSize(size)

            glBegin(GL_POINTS)

            for x, y, z, phase in points:
                pulse = (math.sin(self.time * 2.0 + phase) + 1.0) * 0.5

                glColor4f(0.10, 0.60, 1.0, 0.15 + pulse * 0.35)

                glVertex3f(x, y, z)

            glEnd()

    # ============================================================
    # ENERGY STREAMS
    # ============================================================

    def draw_energy_streams(self):
        stream_count = 12

        for stream in range(stream_count):
            phase = (stream / stream_count) * math.pi * 2.0

            glLineWidth(1.0)

            glBegin(GL_LINE_STRIP)

            segments = 90

            for i in range(segments):
                t = i / float(segments - 1)

                longitude = phase + t * math.pi * 2.0 + self.time * 0.35

                latitude = math.sin(t * math.pi * 2.0 + phase + self.time * 0.7) * 0.55

                radius = (
                    3.08 + math.sin(t * math.pi * 8.0 + self.time * 2.0 + phase) * 0.05
                )

                cos_lat = math.cos(latitude)

                x = math.cos(longitude) * cos_lat * radius

                y = math.sin(latitude) * radius

                z = math.sin(longitude) * cos_lat * radius

                fade = math.sin(t * math.pi)

                movement = (math.sin(self.time * 3.0 + phase) + 1.0) * 0.5

                alpha = 0.025 + fade * 0.10 + movement * 0.05 + self.activity * 0.08

                glColor4f(0.05, 0.55, 1.0, alpha)

                glVertex3f(x, y, z)

            glEnd()

    # ============================================================
    # CENTER GLOW
    # ============================================================

    def draw_core_glow(self):
        pulse = (math.sin(self.time * 2.0) + 1.0) * 0.5

        pulse += self.activity * 0.4

        # Delikatny punkt centralny
        sizes = [(30.0, 0.018), (20.0, 0.025), (12.0, 0.045), (5.0, 0.15)]

        for size, alpha in sizes:
            glPointSize(size)

            glBegin(GL_POINTS)

            glColor4f(0.15, 0.70, 1.0, alpha + pulse * alpha * 0.6)

            glVertex3f(0.0, 0.0, 0.0)

            glEnd()

    # ============================================================
    # PUBLIC STATE
    # ============================================================

    def set_activity(self, value):
        self.target_activity = max(0.0, min(1.0, float(value)))

    # ============================================================
    # CLEANUP
    # ============================================================

    def cleanup(self):
        if self.timer.isActive():
            self.timer.stop()

        self.makeCurrent()
        self.doneCurrent()
