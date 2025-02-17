import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedWidget, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
import bcrypt
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import re
from flask import Flask, session, request, jsonify

# Flask pour gérer les sessions
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # NE PAS utiliser en prod, générer une clé aléatoire

Base = declarative_base()
engine = create_engine('sqlite:///users.db', echo=False)  # SQLite pour l'exemple, pas d'echo pour moins de logs

# Définir la classe User
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Fonctions utilitaires
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

class LoginWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        layout.addWidget(self.email)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Mot de passe")
        layout.addWidget(self.password)

        login_btn = QPushButton("Connexion")
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)

        register = QLabel("<a href='#'>S'inscrire</a>")
        register.setOpenExternalLinks(False)
        register.linkActivated.connect(self.show_register)
        layout.addWidget(register)

        self.setLayout(layout)

    def login(self):
        email = self.email.text()
        password = self.password.text()

        if not is_valid_email(email):
            QMessageBox.warning(self, "Échec", "L'email n'est pas valide.")
            return

        session = Session()
        user = session.query(User).filter_by(email=email).first()
        if user and check_password(password, user.password):
            session['logged_in'] = True
            session['user_id'] = user.id
            QMessageBox.information(self, "Succès", "Connexion réussie!")
        else:
            QMessageBox.warning(self, "Échec", "Email ou mot de passe incorrect.")
        session.close()

    def show_register(self):
        self.parent().setCurrentIndex(1)

class RegisterWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.name = QLineEdit()
        self.name.setPlaceholderText("Nom")
        layout.addWidget(self.name)

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        layout.addWidget(self.email)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Mot de passe")
        layout.addWidget(self.password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setPlaceholderText("Confirmer le mot de passe")
        layout.addWidget(self.confirm_password)

        register_btn = QPushButton("S'inscrire")
        register_btn.clicked.connect(self.register)
        layout.addWidget(register_btn)

        back = QLabel("<a href='#'>Retour à la connexion</a>")
        back.setOpenExternalLinks(False)
        back.linkActivated.connect(self.show_login)
        layout.addWidget(back)

        self.setLayout(layout)

    def register(self):
        name = self.name.text()
        email = self.email.text()
        password = self.password.text()
        confirm_password = self.confirm_password.text()

        if not all([name, email, password, confirm_password]):
            QMessageBox.warning(self, "Échec", "Tous les champs doivent être remplis.")
            return

        if not is_valid_email(email):
            QMessageBox.warning(self, "Échec", "L'email n'est pas valide.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Échec", "Les mots de passe ne correspondent pas.")
            return

        if len(password) < 8:
            QMessageBox.warning(self, "Échec", "Le mot de passe doit contenir au moins 8 caractères.")
            return

        session = Session()
        if session.query(User).filter_by(email=email).first():
            QMessageBox.warning(self, "Échec", "Cet email est déjà utilisé.")
            session.close()
            return

        hashed_password = hash_password(password)
        new_user = User(name=name, email=email, password=hashed_password)
        session.add(new_user)
        session.commit()
        session.close()

        QMessageBox.information(self, "Succès", "Inscription réussie!")
        self.show_login()

    def show_login(self):
        self.parent().setCurrentIndex(0)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.stack = QStackedWidget()  # Change to QStackedWidget

        self.login_widget = LoginWidget()
        self.register_widget = RegisterWidget()

        self.stack.addWidget(self.login_widget)
        self.stack.addWidget(self.register_widget)

        layout.addWidget(self.stack)
        self.setLayout(layout)
        self.setCurrentIndex(0)

    def setCurrentIndex(self, index):
        self.stack.setCurrentIndex(index)  # Correct usage with QStackedWidget

if __name__ == "__main__":
    # Lancer le serveur Flask en mode thread pour ne pas bloquer l'UI
    import threading
    flask_thread = threading.Thread(target=app.run, kwargs={'host': '127.0.0.1', 'port': 5000, 'threaded': True})
    flask_thread.start()

    # Lancer l'application Qt
    app_qt = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app_qt.exec())