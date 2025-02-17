import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PySide6.QtGui import QIcon  # Importez QIcon pour gérer les icônes
from tab_reactifs import GestionReactifs  # Classe correcte pour le premier onglet
from tab_volume_par_test import TabVolumeParTest  # Deuxième onglet
from tab_tests_estimes import TabTests  # Troisième onglet
from database import ReactifsDatabase  # Importer la classe ReactifsDatabase


def load_stylesheet(app):
    """
    Charge le fichier de style CSS et l'applique à l'application.
    """
    style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())  # Appliquer le style à l'application
    else:
        print("⚠️ Avertissement : fichier 'style.qss' introuvable.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion Réactifs et Calcul Volume Test")
        self.resize(1200, 800)

        # Définir l'icône globale de l'application
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "app_icon.png")  # Chemin vers l'icône
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))  # Appliquer l'icône
        else:
            print("⚠️ Avertissement : icône de l'application introuvable.")

        # Initialiser la base de données
        self.database = ReactifsDatabase()  # Crée la base de données si elle n'existe pas

        # Création du layout principal avec des marges professionnelles
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 20, 15, 15)  # Marges autour du contenu principal

        # Création des onglets
        self.tabs = QTabWidget()

        # Ajout des onglets avec leurs icônes respectives
        tab1 = GestionReactifs()
        tab2 = TabVolumeParTest()
        tab3 = TabTests()

        # Définir les icônes pour chaque onglet
        tab1_icon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "reactifs.png"))
        tab2_icon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "volume.png"))
        tab3_icon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "tests.png"))

        self.tabs.addTab(tab1, tab1_icon, "Gestion Réactifs")
        self.tabs.addTab(tab2, tab2_icon, "Calcul Volume Test")
        self.tabs.addTab(tab3, tab3_icon, "Calcul Test")

        # Ajouter les styles personnalisés aux onglets (si non inclus dans style.qss)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #FFFFFF;
            }
            QTabBar::tab {
                background: #F7F7F7; /* Gris très clair */
                color: #2E2E2E; /* Texte sombre */
                padding: 10px 20px;
                font: 12pt "Segoe UI Semibold";
                border: 1px solid #D0D0D0;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #178E3B; /* Vert moyen pour la sélection */
                border: 1px solid #D0D0D0;
                border-bottom: 3px solid #178E3B; /* Ligne de sélection verte */
            }
            QTabBar::tab:hover {
                background: #E9F2FA; /* Bleu très clair au survol */
                color: #178E3B; /* Vert moyen au survol */
            }
        """)

        # Ajouter le widget des onglets au layout principal
        main_layout.addWidget(self.tabs)

        # Encapsuler le layout dans un widget central
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Charger le style global depuis style.qss
    load_stylesheet(app)

    # Charger l'icône globale de l'application
    global_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "app_icon.png")
    if os.path.exists(global_icon_path):
        app.setWindowIcon(QIcon(global_icon_path))  # Appliquer l'icône globale à l'application
    else:
        print("⚠️ Avertissement : icône globale introuvable.")

    # Lancer la fenêtre principale
    window = MainWindow()
    window.show()
    sys.exit(app.exec())