import sqlite3
from datetime import datetime
from PySide6.QtCore import QThread, Signal


class ReactifsDatabase:
    """
    Classe pour gérer la base de données des réactifs.
    Elle s'occupe de la création des tables, de l'ajout, la modification,
    la suppression et la récupération des données.
    """
    def __init__(self, db_name="reactifs_database.db"):
        """
        Initialisation de la base de données.
        :param db_name: Nom du fichier de la base de données (par défaut 'reactifs_database.db').
        """
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """
        Crée les tables 'Analytes', 'Lots' et 'Tests' dans la base de données si elles n'existent pas.
        """
        # Table Analytes : pour stocker les types d'analyses (ex: Glucose, Cholestérol)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Analytes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                unit TEXT NOT NULL
            );
        """)

        # Table Lots : pour stocker les lots de réactifs
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analyte_id INTEGER NOT NULL,
                lot_number TEXT NOT NULL UNIQUE,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                total_volume REAL NOT NULL CHECK(total_volume >= 0),
                remaining_volume REAL NOT NULL CHECK(remaining_volume >= 0),
                tests_performed INTEGER DEFAULT 0 CHECK(tests_performed >= 0),
                loss_percentage REAL DEFAULT 0.0 CHECK(loss_percentage >= 0),
                operator TEXT,
                FOREIGN KEY (analyte_id) REFERENCES Analytes(id) ON DELETE CASCADE
            );
        """)

        # Table Tests : pour enregistrer les informations sur les tests
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analyte_id INTEGER NOT NULL,
                lot_number TEXT NOT NULL,
                estimated_tests INTEGER DEFAULT 0 CHECK(estimated_tests >= 0),
                performed_tests INTEGER DEFAULT 0 CHECK(performed_tests >= 0),
                usage_factor REAL DEFAULT 0.0 CHECK(usage_factor >= 0),
                loss_percentage REAL DEFAULT 0.0 CHECK(loss_percentage >= 0),
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                operator TEXT,
                UNIQUE (lot_number),
                FOREIGN KEY (analyte_id) REFERENCES Analytes(id) ON DELETE CASCADE
            );
        """)

        # Index pour améliorer la performance des requêtes
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyte_id ON Lots(analyte_id);")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyte_id_tests ON Tests(analyte_id);")

        self.conn.commit()

    def add_test(self, analyte_id: int, lot_number: str, estimated_tests: int, performed_tests: int = 0,
                 usage_factor: float = 0.0, loss_percentage: float = 0.0,
                 start_date: str = None, end_date: str = None, operator: str = None) -> int | None:
        """
        Ajoute un nouveau test dans la table Tests.
        """
        try:
            with self.conn:
                self.cursor.execute("""
                    INSERT INTO Tests (analyte_id, lot_number, estimated_tests, performed_tests, usage_factor, loss_percentage, start_date, end_date, operator)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (analyte_id, lot_number, estimated_tests, performed_tests, usage_factor, loss_percentage, start_date, end_date, operator))
                return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Erreur : le test existe déjà pour le lot {lot_number}.")
            return None
        except Exception as e:
            print(f"Erreur lors de l'ajout du test : {e}")
            return None

    def update_test(self, test_id: int, analyte_id: int, lot_number: str, estimated_tests: int, performed_tests: int = 0,
                    usage_factor: float = 0.0, loss_percentage: float = 0.0,
                    start_date: str = None, end_date: str = None, operator: str = None) -> bool:
        """
        Met à jour un test existant dans la table Tests.
        """
        try:
            with self.conn:
                self.cursor.execute("""
                    UPDATE Tests
                    SET analyte_id = ?, lot_number = ?, estimated_tests = ?, performed_tests = ?, usage_factor = ?,
                        loss_percentage = ?, start_date = ?, end_date = ?, operator = ?
                    WHERE id = ?
                """, (analyte_id, lot_number, estimated_tests, performed_tests, usage_factor, loss_percentage, start_date, end_date, operator, test_id))
                return True
        except Exception as e:
            print(f"Erreur lors de la mise à jour du test : {e}")
            return False

    def delete_test(self, test_id: int) -> bool:
        """
        Supprime un test de la table Tests par son ID.
        """
        try:
            with self.conn:
                self.cursor.execute("DELETE FROM Tests WHERE id = ?", (test_id,))
                return True
        except Exception as e:
            print(f"Erreur lors de la suppression du test : {e}")
            return False

    def get_all_tests(self):
        """
        Récupère tous les tests avec les informations de l'analyte associé.
        """
        self.cursor.execute("""
            SELECT Tests.id, Analytes.name, Analytes.unit, Tests.lot_number, Tests.start_date, Tests.end_date,
                   Tests.estimated_tests, Tests.performed_tests, Tests.usage_factor, Tests.loss_percentage, Tests.operator
            FROM Tests
            JOIN Analytes ON Tests.analyte_id = Analytes.id
        """)
        return self.cursor.fetchall()

    def add_lot(self, analyte_id: int, lot_number: str, start_date: str, end_date: str,
               total_volume: float, remaining_volume: float, tests_performed: int = 0,
               loss_percentage: float = 0.0, operator: str = None) -> int | None:
        """
        Ajoute un nouveau lot dans la table Lots.
        """
        try:
            with self.conn:
                self.cursor.execute("""
                    INSERT INTO Lots (analyte_id, lot_number, start_date, end_date, total_volume, remaining_volume, tests_performed, loss_percentage, operator)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (analyte_id, lot_number, start_date, end_date, total_volume, remaining_volume, tests_performed, loss_percentage, operator))
                return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Erreur : le lot '{lot_number}' existe déjà.")
            return None
        except Exception as e:
            print(f"Erreur lors de l'ajout du lot : {e}")
            return None
        
    def get_lot_number_by_id(self, lot_id: int) -> str | None:
        """
        Récupère le numéro de lot à partir de l'ID du lot.
        
        :param lot_id: ID du lot
        :return: Numéro de lot ou None si non trouvé
        """
        try:
            self.cursor.execute("SELECT lot_number FROM Lots WHERE id = ?", (lot_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Erreur lors de la récupération du numéro de lot par ID : {e}")
            return None
                
    def get_lots_by_analyte(self, analyte_name):
        """
        Récupère tous les lots associés à un analyte spécifique.
        
        :param analyte_name: Nom de l'analyte
        :return: Liste des lots sous forme de dictionnaires
        """
        query = """
            SELECT 
                Lots.id, Analytes.name, Analytes.unit, Lots.lot_number, 
                Lots.start_date, Lots.end_date, Lots.total_volume, 
                Lots.remaining_volume, Lots.tests_performed, 
                Lots.loss_percentage, Lots.operator
            FROM Lots
            JOIN Analytes ON Lots.analyte_id = Analytes.id
            WHERE Analytes.name = ?
        """
        try:
            self.cursor.execute(query, (analyte_name,))
            rows = self.cursor.fetchall()
            # Convertir les résultats en une liste de dictionnaires
            lots = []
            for row in rows:
                lot = {
                    'id': row[0],
                    'nom_analyte': row[1],
                    'unite': row[2],
                    'lot': row[3],
                    'start_date': row[4],
                    'end_date': row[5],
                    'total_volume': row[6],
                    'remaining_volume': row[7],
                    'tests_performed': row[8],
                    'loss_percentage': row[9],
                    'operator': row[10]
                }
                lots.append(lot)
            return lots
        except Exception as e:
            print(f"Erreur lors de la récupération des lots par analyte : {e}")
            return []
    def update_lot_by_id(self, lot_id: int, analyte_id: int, lot_number: str, start_date: str, end_date: str,
                         total_volume: float, remaining_volume: float, tests_performed: int = 0,
                         loss_percentage: float = 0.0, operator: str = None) -> bool:
        """
        Met à jour un lot existant dans la table Lots.
        """
        try:
            with self.conn:
                self.cursor.execute("""
                    UPDATE Lots
                    SET analyte_id = ?, lot_number = ?, start_date = ?, end_date = ?,
                        total_volume = ?, remaining_volume = ?, tests_performed = ?, loss_percentage = ?, operator = ?
                    WHERE id = ?
                """, (analyte_id, lot_number, start_date, end_date, total_volume, remaining_volume, tests_performed, loss_percentage, operator, lot_id))
                return True
        except Exception as e:
            print(f"Erreur mise à jour lot: {e}")
            return False

    def delete_lot(self, lot_number: str) -> bool:
        """
        Supprime un lot de la table Lots par son numéro de lot.
        """
        try:
            with self.conn:
                self.cursor.execute("DELETE FROM Lots WHERE lot_number = ?", (lot_number,))
                return True
        except Exception as e:
            print(f"Erreur lors de la suppression du lot : {e}")
            return False

    def get_all_lots(self):
        """
        Récupère tous les lots avec les informations de l'analyte associé.
        """
        self.cursor.execute("""
            SELECT Lots.id, Analytes.name, Analytes.unit, Lots.lot_number, Lots.start_date, Lots.end_date,
                   Lots.total_volume, Lots.remaining_volume, Lots.tests_performed, Lots.loss_percentage, Lots.operator
            FROM Lots
            JOIN Analytes ON Lots.analyte_id = Analytes.id
        """)
        return self.cursor.fetchall()

    def get_all_analytes(self) -> list:
        """
        Récupère tous les noms d'analytes depuis la table Analytes.
        """
        self.cursor.execute("SELECT name FROM Analytes")
        return [row[0] for row in self.cursor.fetchall()]

    def get_analyte_id(self, name: str) -> int | None:
        """
        Récupère l'ID d'un analyte à partir de son nom.
        """
        self.cursor.execute("SELECT id FROM Analytes WHERE name = ?", (name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_analyte(self, name: str, unit: str) -> int | None:
        """
        Ajoute un nouvel analyte à la table Analytes.
        """
        try:
            self.cursor.execute("INSERT INTO Analytes (name, unit) VALUES (?, ?)", (name, unit))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Erreur lors de l'ajout de l'analyte '{name}': {e}")
            self.conn.rollback()
            return None

    def calculate_average_tests(self, analyte_name: str) -> dict:
        """
        Calcule les moyennes des tests pour un analyte donné.
        """
        try:
            self.cursor.execute("""
                SELECT AVG(estimated_tests), AVG(performed_tests), AVG(usage_factor), AVG(loss_percentage)
                FROM Tests
                JOIN Analytes ON Tests.analyte_id = Analytes.id
                WHERE Analytes.name = ?
            """, (analyte_name,))
            avg_results = self.cursor.fetchone()
            if not avg_results or any(result is None for result in avg_results):
                return {}
            return {
                "avg_estimated_tests": avg_results[0],
                "avg_performed_tests": avg_results[1],
                "avg_usage_factor": avg_results[2],
                "avg_loss_percentage": avg_results[3]
            }
        except Exception as e:
            print(f"Erreur lors du calcul des moyennes des tests : {e}")
            return {}

    def calculate_average_lots(self, analyte_name: str) -> dict:
        """
        Calcule les moyennes des lots pour un analyte donné.
        """
        try:
            self.cursor.execute("""
                SELECT AVG(total_volume), AVG(remaining_volume), AVG(tests_performed), AVG(loss_percentage),
                       AVG((total_volume - remaining_volume) / tests_performed), AVG(julianday(end_date) - julianday(start_date))
                FROM Lots
                JOIN Analytes ON Lots.analyte_id = Analytes.id
                WHERE Analytes.name = ?
            """, (analyte_name,))
            avg_results = self.cursor.fetchone()
            if not avg_results or any(result is None for result in avg_results):
                return {}
            return {
                "avg_total_volume": avg_results[0],
                "avg_remaining_volume": avg_results[1],
                "avg_tests_performed": avg_results[2],
                "avg_loss_percentage": avg_results[3],
                "avg_volume_per_test": avg_results[4],
                "avg_duration_days": avg_results[5]
            }
        except Exception as e:
            print(f"Erreur lors du calcul des moyennes des lots : {e}")
            return {}

    def close(self):
        """
        Ferme la connexion à la base de données.
        """
        self.conn.close()



    def calculate_averages(self, analyte_name: str, table_name: str) -> dict:
        """
        Calcule les moyennes pour un analyte donné dans la table spécifiée.
        :param analyte_name: Nom de l'analyte
        :param table_name: 'Tests' ou 'Lots'
        :return: Dictionnaire des moyennes calculées
        """
        try:
            if table_name not in ['Tests', 'Lots']:
                raise ValueError("Table invalide. Doit être 'Tests' ou 'Lots'.")

            query = f"""
                SELECT AVG(estimated_tests), AVG(performed_tests), AVG(usage_factor), AVG(loss_percentage)
                FROM {table_name}
                JOIN Analytes ON {table_name}.analyte_id = Analytes.id
                WHERE Analytes.name = ?
            """
            self.cursor.execute(query, (analyte_name,))
            avg_results = self.cursor.fetchone()

            if not avg_results or any(result is None for result in avg_results):
                return {}

            return {
                "avg_estimated_tests": avg_results[0],
                "avg_performed_tests": avg_results[1],
                "avg_usage_factor": avg_results[2],
                "avg_loss_percentage": avg_results[3]
            }
        except Exception as e:
            print(f"Erreur lors du calcul des moyennes : {e}")
            return {}

    def calculate_averages(self, analyte_name: str, table_name: str) -> dict:
        """
        Calcule les moyennes pour un analyte donné dans la table spécifiée.
        :param analyte_name: Nom de l'analyte
        :param table_name: 'Tests' ou 'Lots'
        :return: Dictionnaire des moyennes calculées
        """
        try:
            if table_name not in ['Tests', 'Lots']:
                raise ValueError("Table invalide. Doit être 'Tests' ou 'Lots'.")

            query = f"""
                SELECT AVG(estimated_tests), AVG(performed_tests), AVG(usage_factor), AVG(loss_percentage)
                FROM {table_name}
                JOIN Analytes ON {table_name}.analyte_id = Analytes.id
                WHERE Analytes.name = ?
            """
            self.cursor.execute(query, (analyte_name,))
            avg_results = self.cursor.fetchone()

            if not avg_results or any(result is None for result in avg_results):
                return {}

            return {
                "avg_estimated_tests": avg_results[0],
                "avg_performed_tests": avg_results[1],
                "avg_usage_factor": avg_results[2],
                "avg_loss_percentage": avg_results[3]
            }
        except Exception as e:
            print(f"Erreur lors du calcul des moyennes : {e}")
            return {}

    def close(self):
        """
        Ferme la connexion à la base de données.
        """
        self.conn.close()


class DatabaseWorkerThread(QThread):
    """
    Thread générique pour exécuter des requêtes SQL en arrière-plan.
    """
    finished = Signal(bool, object)

    def __init__(self, query: str | list, params: tuple | list = None, fetch: bool = False,
                 transaction: bool = False, db_path: str = "reactifs_database.db"):
        super().__init__()
        self.query = query
        self.params = params if params else ()
        self.fetch = fetch
        self.transaction = transaction
        self.db_path = db_path

    def run(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if self.transaction:
                cursor.execute("BEGIN TRANSACTION;")

            if isinstance(self.query, list):
                results = []
                for q, p in zip(self.query, self.params or [()]):
                    cursor.execute(q, p)
                    if self.fetch:
                        results.append(cursor.fetchall())
                result = results
            else:
                cursor.execute(self.query, self.params)
                if self.fetch:
                    result = cursor.fetchall()
                else:
                    result = None

            if self.transaction:
                conn.commit()

            self.finished.emit(True, result)
        except sqlite3.IntegrityError as ie:
            if conn and self.transaction:
                conn.rollback()
            self.finished.emit(False, f"Integrity Error: {ie}")
        except sqlite3.Error as e:
            if conn and self.transaction:
                conn.rollback()
            self.finished.emit(False, f"SQLite Error: {e}")
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            if conn:
                conn.close()