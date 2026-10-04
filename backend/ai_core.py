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

        self.time = 0.0
        self.rotation = 0.0
        self.rotation_y = 0.0
        self.activity = 0.0
        self.pulse = 0.0
        self.pulse_strength = 0.0
        self.particles = []
        self.flow_particles = []
        self.orbit_particles = []
        self.create_particles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def create_particles(self):
        self.particles.clear()
        self.flow_particles.clear()
        self.orbit_particles.clear()

        golden_angle = math.pi * (3.0 - math.sqrt(5.0))

        # Gęsta, organiczna sfera
        for i in range(2400):
            y = 1.0 - (i / 2399.0) * 2.0
            r = math.sqrt(max(0.0, 1.0 - y * y))
            theta = golden_angle * i

            radius = 3.0 + random.uniform(-0.035, 0.035)
            x = math.cos(theta) * r * radius
            y *= radius
            z = math.sin(theta) * r * radius

            self.particles.append({
                "x": x,
                "y": y,
                "z": z,
                "phase": random.uniform(0.0, math.tau),
                "speed": random.uniform(0.35, 1.25),
                "size": random.choice([0.7, 0.9, 1.1, 1.3, 1.6, 2.0]),
                "brightness": random.uniform(0.25, 1.0)
            })

        # Strumienie przemieszczające się po powierzchni
        for _ in range(900):
            self.flow_particles.append({
                "lat": random.uniform(-1.25, 1.25),
                "lon": random.uniform(0.0, math.tau),
                "speed": random.uniform(0.25, 1.0),
                "phase": random.uniform(0.0, math.tau),
                "size": random.choice([0.8, 1.0, 1.2, 1.5, 2.0, 2.6]),
                "brightness": random.uniform(0.5, 1.0)
            })

        # Luźne cząsteczki poza sferą
        for _ in range(260):
            self.orbit_particles.append({
                "angle": random.uniform(0.0, math.tau),
                "radius": random.uniform(3.15, 4.25),
                "height": random.uniform(-0.7, 0.7),
                "speed": random.uniform(0.05, 0.20),
                "phase": random.uniform(0.0, math.tau),
                "size": random.choice([0.8, 1.0, 1.3, 1.7, 2.2])
            })

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    def resizeGL(self, width, height):
        height = max(1, height)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(43.0, width / float(height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def animate(self):
        self.time += 0.016
        self.rotation += 0.16
        self.rotation_y += 0.07

        # Autonomiczna aktywność - Core nigdy nie jest całkowicie statyczny.
        self.activity = (
            0.22
            + 0.12 * math.sin(self.time * 0.37)
            + 0.07 * math.sin(self.time * 0.91)
        )

        # Okresowe, naturalne impulsy energii.
        pulse_cycle = self.time % 9.0
        if pulse_cycle < 0.55:
            self.pulse_strength = math.sin(
                (pulse_cycle / 0.55) * math.pi
            )
        else:
            self.pulse_strength *= 0.91

        for p in self.flow_particles:
            p["lon"] += 0.0045 * p["speed"] * (1.0 + self.activity * 1.8)

        for p in self.orbit_particles:
            p["angle"] += 0.0015 * p["speed"] * (1.0 + self.activity)

        self.update()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -9.0)

        # Bardzo wolne "oddychanie" całej sfery.
        glRotatef(math.sin(self.time * 0.18) * 5.0, 1.0, 0.0, 0.0)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)
        glRotatef(math.sin(self.time * 0.11) * 3.0, 0.0, 0.0, 1.0)

        self.draw_aura()
        self.draw_orbit_particles()
        self.draw_sphere()
        self.draw_flow()
        self.draw_ribbons()
        self.draw_energy_pulse()
        self.draw_center()

    def draw_aura(self):
        # Miękka poświata budowana z punktów, dzięki czemu nie ma ostrej krawędzi.
        for size, alpha in [
            (170.0, 0.012),
            (125.0, 0.016),
            (85.0, 0.020),
            (50.0, 0.028),
        ]:
            glPointSize(size)
            glBegin(GL_POINTS)
            glColor4f(0.03, 0.42, 1.0, alpha)
            glVertex3f(0.0, 0.0, 0.0)
            glEnd()

    def draw_sphere(self):
        groups = {0.7: [], 0.9: [], 1.1: [], 1.3: [], 1.6: [], 2.0: []}

        for p in self.particles:
            phase = p["phase"]
            wave = math.sin(self.time * 0.9 * p["speed"] + phase)
            scale = 1.0 + wave * 0.018 + self.pulse_strength * 0.025

            x = p["x"] * scale
            y = p["y"] * scale
            z = p["z"] * scale

            # Subtelne lokalne przesuwanie cząsteczek.
            x += math.sin(self.time * 0.45 + phase) * 0.018
            y += math.cos(self.time * 0.52 + phase) * 0.018
            z += math.sin(self.time * 0.62 + phase) * 0.018

            groups[p["size"]].append(
                (x, y, z, phase, p["brightness"])
            )

        for size, points in groups.items():
            glPointSize(size)
            glBegin(GL_POINTS)

            for x, y, z, phase, brightness in points:
                shimmer = (
                    math.sin(self.time * 2.8 + phase) + 1.0
                ) * 0.5
                alpha = 0.08 + brightness * 0.25 + shimmer * 0.20
                alpha += self.pulse_strength * 0.12

                glColor4f(
                    0.04,
                    0.45 + shimmer * 0.25,
                    1.0,
                    min(alpha, 0.82)
                )
                glVertex3f(x, y, z)

            glEnd()

    def draw_flow(self):
        groups = {0.8: [], 1.0: [], 1.2: [], 1.5: [], 2.0: [], 2.6: []}

        for p in self.flow_particles:
            lat = p["lat"]
            lon = p["lon"]

            # Ruch o zmiennej prędkości tworzy wrażenie "rzek" energii.
            lat += math.sin(
                lon * 2.5 + self.time * 0.7 + p["phase"]
            ) * 0.035

            radius = 3.035 + math.sin(
                lon * 5.0 - self.time * 1.8 + p["phase"]
            ) * 0.075

            cos_lat = math.cos(lat)
            x = math.cos(lon) * cos_lat * radius
            y = math.sin(lat) * radius
            z = math.sin(lon) * cos_lat * radius

            groups[p["size"]].append(
                (x, y, z, p["phase"], p["brightness"])
            )

        for size, points in groups.items():
            glPointSize(size)
            glBegin(GL_POINTS)

            for x, y, z, phase, brightness in points:
                pulse = (
                    math.sin(self.time * 4.5 + phase) + 1.0
                ) * 0.5

                alpha = 0.14 + brightness * 0.34 + pulse * 0.34
                alpha += self.pulse_strength * 0.20

                glColor4f(
                    0.08,
                    0.58 + pulse * 0.18,
                    1.0,
                    min(alpha, 1.0)
                )
                glVertex3f(x, y, z)

            glEnd()

    def draw_orbit_particles(self):
        groups = {0.8: [], 1.0: [], 1.3: [], 1.7: [], 2.2: []}

        for p in self.orbit_particles:
            angle = p["angle"]
            radius = p["radius"]

            x = math.cos(angle) * radius
            z = math.sin(angle) * radius
            y = p["height"] + math.sin(
                self.time * 0.8 + p["phase"]
            ) * 0.12

            groups[p["size"]].append(
                (x, y, z, p["phase"])
            )

        for size, points in groups.items():
            glPointSize(size)
            glBegin(GL_POINTS)

            for x, y, z, phase in points:
                brightness = (
                    math.sin(self.time * 2.0 + phase) + 1.0
                ) * 0.5

                glColor4f(
                    0.05,
                    0.45 + brightness * 0.20,
                    1.0,
                    0.10 + brightness * 0.30
                )
                glVertex3f(x, y, z)

            glEnd()

    def draw_ribbons(self):
        # Długie, prawie niewidoczne strumienie oplatające kulę.
        for stream in range(18):
            phase = stream / 18.0 * math.tau
            glLineWidth(1.0)
            glBegin(GL_LINE_STRIP)

            for i in range(120):
                t = i / 119.0
                lon = (
                    phase
                    + t * math.tau
                    + self.time * (0.20 + stream * 0.002)
                )

                lat = math.sin(
                    t * math.tau * 1.35
                    + phase
                    + self.time * 0.45
                ) * 0.72

                radius = 3.045 + math.sin(
                    t * math.tau * 7.0
                    + self.time * 2.0
                    + phase
                ) * 0.045

                cos_lat = math.cos(lat)
                x = math.cos(lon) * cos_lat * radius
                y = math.sin(lat) * radius
                z = math.sin(lon) * cos_lat * radius

                edge = math.sin(t * math.pi)
                flow = (
                    math.sin(
                        t * math.tau * 3.0
                        - self.time * 3.0
                        + phase
                    ) + 1.0
                ) * 0.5

                alpha = 0.012 + edge * 0.075 + flow * 0.035
                alpha += self.pulse_strength * 0.055

                glColor4f(
                    0.03,
                    0.50,
                    1.0,
                    alpha
                )
                glVertex3f(x, y, z)

            glEnd()

    def draw_energy_pulse(self):
        if self.pulse_strength <= 0.01:
            return

        radius = 3.0 + self.pulse_strength * 0.9
        glPointSize(2.0 + self.pulse_strength * 3.0)
        glBegin(GL_POINTS)

        for i in range(180):
            angle = i / 180.0 * math.tau
            lat = math.sin(angle * 3.0 + self.time) * 0.55
            cos_lat = math.cos(lat)

            x = math.cos(angle) * cos_lat * radius
            y = math.sin(lat) * radius
            z = math.sin(angle) * cos_lat * radius

            glColor4f(
                0.10,
                0.70,
                1.0,
                self.pulse_strength * 0.22
            )
            glVertex3f(x, y, z)

        glEnd()

    def draw_center(self):
        # Bardzo subtelne źródło światła wewnątrz sfery.
        intensity = (
            0.035
            + self.pulse_strength * 0.10
            + self.activity * 0.025
        )

        for size, multiplier in [
            (45.0, 0.25),
            (24.0, 0.45),
            (10.0, 1.0),
        ]:
            glPointSize(size)
            glBegin(GL_POINTS)
            glColor4f(
                0.05,
                0.55,
                1.0,
                intensity * multiplier
            )
            glVertex3f(0.0, 0.0, 0.0)
            glEnd()

    def set_activity(self, value):
        self.activity = max(0.0, min(1.0, float(value)))

    def cleanup(self):
        if self.timer.isActive():
            self.timer.stop()

        self.makeCurrent()
        self.doneCurrent()
