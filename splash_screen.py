import sys
import random
import math
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                            QGraphicsDropShadowEffect)
from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve,
                         QTimer, QRectF, Property)
from PySide6.QtGui import (QPainter, QColor, QPen, QPainterPath,
                        QLinearGradient, QFont, QRadialGradient)

class StyleConstants:
    # Couleurs
    PRIMARY_COLOR = QColor(56, 189, 248)
    BACKGROUND_COLOR = QColor(15, 23, 42)
    TEXT_COLOR = QColor(255, 255, 255)
    SECONDARY_TEXT_COLOR = QColor(148, 163, 184)
    LIQUID_COLOR = QColor(56, 189, 248)
    BUBBLE_COLOR = QColor(255, 255, 255, 100)
    
    # Dimensions
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    BEAKER_SIZE = 150
    LOADING_BAR_HEIGHT = 8
    LOADING_BAR_WIDTH = 400

class Bubble:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.opacity = 255

class LoadingBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(StyleConstants.LOADING_BAR_WIDTH, 
                         StyleConstants.LOADING_BAR_HEIGHT)
        self._progress = 0
        
    def _set_progress(self, value):
        self._progress = value
        self.update()
        
    def _get_progress(self):
        return self._progress
    
    progress = Property(float, _get_progress, _set_progress)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fond de la barre
        background_path = QPainterPath()
        background_path.addRoundedRect(0, 0, self.width(), self.height(), 
                                     self.height()/2, self.height()/2)
        painter.fillPath(background_path, QColor(30, 41, 59))
        
        # Barre de progression
        progress_width = int(self.width() * self._progress)
        if progress_width > 0:
            progress_path = QPainterPath()
            progress_path.addRoundedRect(0, 0, progress_width, self.height(),
                                       self.height()/2, self.height()/2)
            
            gradient = QLinearGradient(0, 0, progress_width, 0)
            gradient.setColorAt(0, StyleConstants.PRIMARY_COLOR)
            gradient.setColorAt(1, QColor(99, 202, 255))
            
            painter.fillPath(progress_path, gradient)

class LabBeaker(QWidget):
    def __init__(self, size=StyleConstants.BEAKER_SIZE):
        super().__init__()
        self.setFixedSize(150, 150)
        self._animation_value = 0
        self.bubbles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_bubbles)
        self.timer.start(50)
        self.generate_bubbles()

    def _set_animation_value(self, value):
        self._animation_value = value
        self.update()

    def _get_animation_value(self):
        return self._animation_value

    animation_value = Property(float, _get_animation_value, _set_animation_value)

    def generate_bubbles(self):
        for _ in range(10):  # Augmenté à 10 bulles
            x = random.randint(int(self.width() * 0.3), int(self.width() * 0.7))
            y = self.height()
            size = random.randint(3, 8)  # Bulles plus petites
            speed = random.uniform(1, 2)
            self.bubbles.append(Bubble(x, y, size, speed))

    def update_bubbles(self):
        for bubble in self.bubbles[:]:
            bubble.y -= bubble.speed
            bubble.x += math.sin(bubble.y / 20) * 0.5
            
            if bubble.y < self.height() * 0.3:
                bubble.opacity -= 5
                if bubble.opacity <= 0:
                    self.bubbles.remove(bubble)
                    x = random.randint(int(self.width() * 0.3), int(self.width() * 0.7))
                    y = self.height()
                    size = random.randint(3, 8)
                    speed = random.uniform(1, 2)
                    self.bubbles.append(Bubble(x, y, size, speed))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width, height = self.width(), self.height()
        
        # Corps du bécher
        beaker_path = QPainterPath()
        beaker_path.moveTo(width * 0.2, height * 0.1)
        beaker_path.lineTo(width * 0.8, height * 0.1)
        beaker_path.lineTo(width * 0.85, height * 0.9)
        beaker_path.lineTo(width * 0.15, height * 0.9)
        beaker_path.closeSubpath()

        # Bec verseur
        spout_path = QPainterPath()
        spout_path.moveTo(width * 0.2, height * 0.1)
        spout_path.lineTo(width * 0.15, height * 0.05)
        spout_path.lineTo(width * 0.25, height * 0.1)

        # Graduations
        grad_path = QPainterPath()
        for i in range(1, 5):
            y = height * (0.2 + i * 0.15)
            grad_path.moveTo(width * 0.3, y)
            grad_path.lineTo(width * 0.4, y)

        # Dessiner le verre
        glass_pen = QPen(QColor(200, 200, 200))
        glass_pen.setWidth(2)
        painter.setPen(glass_pen)
        painter.drawPath(beaker_path)
        painter.drawPath(spout_path)
        painter.drawPath(grad_path)

        # Dessiner le liquide
        liquid_height = height * 0.6
        liquid_path = QPainterPath()
        liquid_path.moveTo(width * 0.2, liquid_height)
        
        wave_amplitude = 5 * self._animation_value
        for x in range(int(width * 0.2), int(width * 0.8), 5):
            y = liquid_height + math.sin(x / 20 + self._animation_value * 10) * wave_amplitude
            liquid_path.lineTo(float(x), float(y))

        liquid_path.lineTo(width * 0.8, liquid_height)
        liquid_path.lineTo(width * 0.85, height * 0.9)
        liquid_path.lineTo(width * 0.15, height * 0.9)
        liquid_path.closeSubpath()

        gradient = QLinearGradient(0, liquid_height, 0, height)
        gradient.setColorAt(0, StyleConstants.LIQUID_COLOR)
        gradient.setColorAt(1, StyleConstants.LIQUID_COLOR.darker(150))
        painter.fillPath(liquid_path, gradient)

        # Dessiner les bulles
        for bubble in self.bubbles:
            bubble_color = QColor(StyleConstants.BUBBLE_COLOR)
            bubble_color.setAlpha(bubble.opacity)
            painter.setBrush(bubble_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(bubble.x - bubble.size/2, 
                                    bubble.y - bubble.size/2,
                                    bubble.size, bubble.size))

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(StyleConstants.WINDOW_WIDTH, StyleConstants.WINDOW_HEIGHT)
        
        # Appliquer un style spécifique au SplashScreen
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;  /* Couleur de fond */
                color: #FFFFFF;            /* Couleur du texte */
                font-family: "Segoe UI";
            }
            QLabel {
                self.dev_info.setTextFormat(Qt.TextFormat.RichText)
                color: #FFFFFF;
            }
            QLabel#title {
                font-size: 30px;
                font-weight: bold;
            }
            QLabel#subtitle {
                font-size: 20px;
                color: #94A3B8;
            }
            QLabel#version {
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QLabel#loading_text {
                font-size: 14px;
                color: #94A3B8;
            }
            QLabel#dev_info {
                font-size: 16px;
                font-weight: bold;
                color: #94A3B8;
            }
            QLabel#copyright {
                font-size: 14px;
                color: #94A3B8;
            }
        """)
        
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Bécher animé
        self.beaker = LabBeaker()
        layout.addWidget(self.beaker, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Titre principal
        self.title = QLabel("Advanced Laboratory Stock Manager")
        self.title.setObjectName("title")
        layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Sous-titre
        self.subtitle = QLabel("système de gestion de stock")
        self.subtitle.setObjectName("subtitle")
        layout.addWidget(self.subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Version
        self.version = QLabel("Version 1.0")
        self.version.setObjectName("version")
        layout.addWidget(self.version, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Barre de chargement
        self.loading_bar = LoadingBar()
        layout.addWidget(self.loading_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Texte de chargement
        self.loading_text = QLabel("Initialisation du système...")
        self.loading_text.setObjectName("loading_text")
        layout.addWidget(self.loading_text, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Spacer
        layout.addStretch()
        
        # Information développeur
        self.dev_info = QLabel("Développé par D. Sofiane :  <i>Développeur Python Et Biologiste</i>")
        self.dev_info.setObjectName("dev_info")
        layout.addWidget(self.dev_info, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Copyright
        self.copyright = QLabel("© 2025 Laboratoire-Tous droits réservés")
        self.copyright.setObjectName("copyright")
        layout.addWidget(self.copyright, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def setup_animations(self):
        easing_curve = QEasingCurve(QEasingCurve.Type.InOutQuart)
        
        # Animation du bécher
        self.beaker_animation = QPropertyAnimation(self.beaker, b"animation_value")
        self.beaker_animation.setDuration(6000)
        self.beaker_animation.setStartValue(0.0)
        self.beaker_animation.setEndValue(1.0)
        self.beaker_animation.setEasingCurve(easing_curve)
        self.beaker_animation.setLoopCount(-1)
        
        # Animation de la barre de progression
        self.progress_animation = QPropertyAnimation(self.loading_bar, b"progress")
        self.progress_animation.setDuration(6000)
        self.progress_animation.setStartValue(0.0)
        self.progress_animation.setEndValue(1.0)
        self.progress_animation.setEasingCurve(easing_curve)
        
        # Démarrage des animations
        self.beaker_animation.start()
        self.progress_animation.start()
        
        # QTimer.singleShot(6000, self.close_splash)
    
    def close_splash(self):
        self.close()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        background = QPainterPath()
        background.addRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, StyleConstants.BACKGROUND_COLOR)
        gradient.setColorAt(1, QColor(21, 32, 59))
        
        painter.fillPath(background, gradient)

def main():
    app = QApplication(sys.argv)
    splash = SplashScreen()
    
    screen_geometry = app.primaryScreen().geometry()
    x = (screen_geometry.width() - splash.width()) // 2
    y = (screen_geometry.height() - splash.height()) // 2
    splash.move(x, y)
    
    splash.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()