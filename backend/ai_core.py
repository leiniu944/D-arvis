import math
import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective


class AICore(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

        self.rotation = 0.0
        self.rotation_2 = 0.0
        self.pulse = 0.0
        self.time = 0.0

        self.outer_particles = []
        self.energy_particles = []

        self.create_particles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def create_particles(self):
        self.outer_particles.clear()
        self.energy_particles.clear()

        # Delikatne cząsteczki otaczające czarną dziurę
        for _ in range(520):
            angle = random.uniform(0.0, math.pi * 2.0)
            radius = random.uniform(3.0, 6.5)
            height = random.uniform(-2.5, 2.5)

            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            z = height

            size = random.choice([1.0, 1.4, 1.8, 2.4])

            self.outer_particles.append({
                "x": x,
                "y": y,
                "z": z,
                "angle": angle,
                "radius": radius,
                "height": height,
                "speed": random.uniform(0.0005, 0.002),
                "size": size,
                "phase": random.uniform(0.0, math.pi * 2.0)
            })

        # Cząsteczki wirujące wokół horyzontu
        for _ in range(240):
            angle = random.uniform(0.0, math.pi * 2.0)
            radius = random.uniform(1.65, 3.4)

            self.energy_particles.append({
                "angle": angle,
                "radius": radius,
                "z": random.uniform(-0.22, 0.22),
                "speed": random.uniform(0.004, 0.012),
                "size": random.choice([1.0, 1.5, 2.0, 2.8]),
                "phase": random.uniform(0.0, math.pi * 2.0)
            })

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
        if height == 0:
            height = 1

        glViewport(0, 0, width, height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        gluPerspective(
            45.0,
            width / float(height),
            0.1,
            100.0
        )

        glMatrixMode(GL_MODELVIEW)

    def animate(self):
        self.time += 0.016

        self.rotation += 0.35
        self.rotation_2 += 0.17

        self.pulse += 0.045

        if self.pulse > math.pi * 2:
            self.pulse -= math.pi * 2

        # Obrót cząsteczek
        for particle in self.outer_particles:
            particle["angle"] += particle["speed"]

        for particle in self.energy_particles:
            particle["angle"] += particle["speed"]

        self.update()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Odsunięcie kamery
        glTranslatef(0.0, 0.0, -8.5)

        # Lekka perspektywiczna rotacja całego obiektu
        glRotatef(math.sin(self.time * 0.25) * 4.0, 1.0, 0.0, 0.0)
        glRotatef(math.cos(self.time * 0.20) * 5.0, 0.0, 1.0, 0.0)

        self.draw_outer_particles()
        self.draw_accretion_disk()
        self.draw_energy_particles()
        self.draw_black_hole()
        self.draw_inner_ring()

    def draw_outer_particles(self):
        groups = {
            1.0: [],
            1.4: [],
            1.8: [],
            2.4: []
        }

        for p in self.outer_particles:
            x = p["x"]
            y = p["y"]
            z = p["z"]

            angle = p["angle"]

            radius = p["radius"]

            # Powolny obrót przestrzeni
            ca = math.cos(angle)
            sa = math.sin(angle)

            px = ca * radius
            py = sa * radius
            pz = z + math.sin(self.time * 0.6 + p["phase"]) * 0.08

            groups[p["size"]].append((px, py, pz, p["phase"]))

        for size, points in groups.items():
            glPointSize(size)

            glBegin(GL_POINTS)

            for x, y, z, phase in points:
                brightness = 0.18 + (
                    0.18 * (math.sin(self.time * 2.0 + phase) + 1.0)
                )

                glColor4f(
                    0.15,
                    0.65,
                    1.0,
                    brightness
                )

                glVertex3f(x, y, z)

            glEnd()

    def draw_accretion_disk(self):
        # Główna świecąca warstwa dysku
        layers = [
            (2.05, 0.055, 0.65),
            (2.25, 0.045, 0.48),
            (2.50, 0.035, 0.32),
            (2.80, 0.025, 0.20),
            (3.15, 0.018, 0.10)
        ]

        for radius, thickness, alpha in layers:
            glLineWidth(2.0)

            glBegin(GL_LINE_LOOP)

            segments = 180

            for i in range(segments):
                angle = (i / segments) * math.pi * 2.0

                # Delikatne deformacje dysku
                wave = math.sin(
                    angle * 5.0 +
                    self.time * 1.5
                ) * thickness

                r = radius + wave

                x = math.cos(angle) * r
                y = math.sin(angle) * r

                z = math.sin(angle * 3.0 + self.time) * 0.035

                intensity = 0.55 + (
                    0.45 * math.sin(
                        angle * 2.0 -
                        self.time * 2.0
                    )
                )

                intensity = max(0.1, intensity)

                glColor4f(
                    0.12,
                    0.65 + intensity * 0.25,
                    1.0,
                    alpha
                )

                glVertex3f(x, y, z)

            glEnd()

        # Grubszy, bardzo jasny pierścień
        glLineWidth(3.0)

        glBegin(GL_LINE_LOOP)

        for i in range(240):
            angle = (i / 240.0) * math.pi * 2.0

            radius = 1.88

            deformation = math.sin(
                angle * 8.0 +
                self.time * 3.0
            ) * 0.025

            radius += deformation

            x = math.cos(angle) * radius
            y = math.sin(angle) * radius

            pulse = (
                math.sin(self.time * 3.0) + 1.0
            ) * 0.5

            alpha = 0.55 + pulse * 0.35

            glColor4f(
                0.25,
                0.82,
                1.0,
                alpha
            )

            glVertex3f(x, y, 0.0)

        glEnd()

    def draw_energy_particles(self):
        groups = {
            1.0: [],
            1.5: [],
            2.0: [],
            2.8: []
        }

        for p in self.energy_particles:
            angle = p["angle"]
            radius = p["radius"]

            # Spiralny ruch w kierunku czarnej dziury
            spiral_radius = radius

            x = math.cos(angle) * spiral_radius
            y = math.sin(angle) * spiral_radius

            # Delikatna wysokość dysku
            z = (
                p["z"] +
                math.sin(
                    angle * 3.0 +
                    self.time * 2.0 +
                    p["phase"]
                ) * 0.06
            )

            groups[p["size"]].append(
                (x, y, z, p["phase"])
            )

        for size, points in groups.items():
            glPointSize(size)

            glBegin(GL_POINTS)

            for x, y, z, phase in points:
                pulse = (
                    math.sin(
                        self.time * 5.0 +
                        phase
                    ) + 1.0
                ) * 0.5

                alpha = 0.30 + pulse * 0.55

                glColor4f(
                    0.25,
                    0.75,
                    1.0,
                    alpha
                )

                glVertex3f(x, y, z)

            glEnd()

    def draw_black_hole(self):
        # Zewnętrzna poświata
        glow_layers = [
            (1.75, 0.04),
            (1.55, 0.055),
            (1.35, 0.07),
            (1.18, 0.09)
        ]

        for radius, alpha in glow_layers:
            glColor4f(
                0.08,
                0.55,
                1.0,
                alpha
            )

            self.draw_filled_circle(
                radius,
                96
            )

        # Sama czarna dziura
        glColor4f(
            0.002,
            0.004,
            0.008,
            1.0
        )

        self.draw_filled_circle(
            1.08,
            128
        )

        # Delikatny niebieski horyzont
        glLineWidth(2.0)

        glBegin(GL_LINE_LOOP)

        for i in range(180):
            angle = (i / 180.0) * math.pi * 2.0

            radius = 1.08

            x = math.cos(angle) * radius
            y = math.sin(angle) * radius

            glColor4f(
                0.15,
                0.70,
                1.0,
                0.40
            )

            glVertex3f(
                x,
                y,
                0.015
            )

        glEnd()

    def draw_inner_ring(self):
        # Jasny pierścień znajdujący się "przed" czarną dziurą
        pulse = (
            math.sin(self.time * 3.0) + 1.0
        ) * 0.5

        glLineWidth(2.5)

        glBegin(GL_LINE_LOOP)

        for i in range(240):
            angle = (i / 240.0) * math.pi * 2.0

            radius = 1.30 + (
                math.sin(
                    angle * 6.0 +
                    self.time * 2.0
                ) * 0.018
            )

            x = math.cos(angle) * radius
            y = math.sin(angle) * radius

            alpha = 0.45 + pulse * 0.35

            glColor4f(
                0.20,
                0.75,
                1.0,
                alpha
            )

            glVertex3f(
                x,
                y,
                0.04
            )

        glEnd()

    def draw_filled_circle(self, radius, segments):
        glBegin(GL_TRIANGLE_FAN)

        glVertex3f(
            0.0,
            0.0,
            0.0
        )

        for i in range(segments + 1):
            angle = (
                i / segments
            ) * math.pi * 2.0

            x = math.cos(angle) * radius
            y = math.sin(angle) * radius

            glVertex3f(
                x,
                y,
                0.0
            )

        glEnd()

    def cleanup(self):
        self.makeCurrent()
        self.doneCurrent()
