from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QVBoxLayout, QPushButton, QWidget,
    QMessageBox, QHeaderView, QComboBox, QDialog,
    QDialogButtonBox, QDateEdit, QSpacerItem, QSizePolicy, QMenu,QFileDialog
)
from PySide6.QtCore import QDate, Qt, QThread, Signal
from PySide6.QtGui import QIntValidator, QDoubleValidator, QIcon, QAction

from database import ReactifsDatabase, DatabaseWorkerThread
from export import export_data

class SearchThread(QThread):
    results_ready = Signal(list)

    def __init__(self, data_model, search_text):
        super().__init__()
        self.data_model = data_model
        self.search_text = search_text.lower()

    def run(self):
        filtered_results = [data for data in self.data_model if self.search_text in data['nom_analyte'].lower()]
        self.results_ready.emit(filtered_results)

class DatabaseUpdateThread(QThread):
    finished = Signal(bool, str)

    def __init__(self, db_name, updated_data):
        super().__init__()
        self.db_name = "reactifs_database.db"
        self.updated_data = updated_data

    def run(self):
        try:
            database = ReactifsDatabase(self.db_name)
            success = database.update_analyte_and_lot(
                analyte_name=self.updated_data['nom_analyte'],
                unit=self.updated_data['unite'],
                lot_number=self.updated_data['lot'],
                start_date=self.updated_data['debut'],
                end_date=self.updated_data['fin'],
                total_volume=float(self.updated_data['volume_total']),
                remaining_volume=float(self.updated_data['volume_restant']),
                tests_performed=int(self.updated_data['tests']),
                loss_percentage=float(self.updated_data['perte']),
                operator=self.updated_data['operator']
            )
            if not success:
                raise Exception("Impossible de mettre à jour les données dans la base de données.")
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            if 'database' in locals():
                database.close()

class DatabaseDeleteThread(QThread):
    finished = Signal(bool, str)  # Signal émis à la fin (succès, erreur)

    def __init__(self, db_name, lot_id):
        super().__init__()
        self.db_name = "reactifs_database.db"
        self.lot_id = lot_id
        self.success = False
        self.error_message = ""

    def run(self):
        try:
            db = ReactifsDatabase(self.db_name) # Connexion à la base de données DANS le thread
            lot_number = db.get_lot_number_by_id(self.lot_id) # Récupérer lot_number par ID
            if lot_number:
                if db.delete_lot(lot_number): # Supprimer le lot par lot_number
                    self.success = True
                else:
                    self.success = False
                    self.error_message = "Erreur lors de la suppression du lot de la base de données."
            else:
                self.success = False
                self.error_message = f"Lot non trouvé avec l'ID : {self.lot_id}."
        except Exception as e:
            self.success = False
            self.error_message = f"Erreur inattendue lors de la suppression : {e}"
        finally:
            self.finished.emit(self.success, self.error_message) # Émettre le signal à la fin


class AddEditDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvel Analyte" if not data else "Modifier Analyte")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        self.database = ReactifsDatabase()
        self.fields = {}
        self.create_form(layout, data)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.validate)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def create_form(self, layout, data):
        group_box = QGroupBox("Informations du Lot")
        form_layout = QVBoxLayout()

        # Champ "Nom analyte"
        nom_analyte_combo = QComboBox()
        nom_analyte_combo.setEditable(True)
        self.add_form_row(form_layout, "Nom analyte :", nom_analyte_combo, "nom_analyte", data, add_to_layout=True,
                        items=self.fetch_analytes_from_database())

        # Champ "Unité"
        hbox = QHBoxLayout()
        unite_combo = QComboBox()
        self.add_form_row(hbox, "Unité :", unite_combo, "unite", data, add_to_layout=True,
                        items=["ml", "l", "µl", "mg", "g", "kg", "test"])
        form_layout.addLayout(hbox)

        # Champ "Numéro lot"
        self.add_form_row(form_layout, "Numéro lot :", QLineEdit(), "lot", data, add_to_layout=True)

        # Champs "Date début" et "Date fin"
        hbox_dates = QHBoxLayout()
        debut_date_edit = QDateEdit(calendarPopup=True)
        debut_date_edit.setDate(QDate.currentDate())
        fin_date_edit = QDateEdit(calendarPopup=True)
        fin_date_edit.setDate(QDate.currentDate())
        self.add_form_row(hbox_dates, "Date début :", debut_date_edit, "debut", data, add_to_layout=True)
        self.add_form_row(hbox_dates, "Date fin :", fin_date_edit, "fin", data, add_to_layout=True)
        form_layout.addLayout(hbox_dates)

        # Champs "Volume Total" et "Volume Restant"
        hbox_vol = QHBoxLayout()
        volume_total_line_edit = QLineEdit()
        self.add_form_row(hbox_vol, "Volume Total (ml) :", volume_total_line_edit, "volume_total", data, add_to_layout=True)
        volume_restant_line_edit = QLineEdit()
        self.add_form_row(hbox_vol, "Volume Restant (ml) :", volume_restant_line_edit, "volume_restant", data, add_to_layout=True)

        # Connecter le signal textChanged pour recalculer la perte
        volume_restant_line_edit.textChanged.connect(self.calculate_loss)
        volume_total_line_edit.textChanged.connect(self.calculate_loss)
        form_layout.addLayout(hbox_vol)

        # Champ "Tests réalisés"
        hbox_tests = QHBoxLayout()
        tests_line_edit = QLineEdit()
        self.add_form_row(hbox_tests, "Tests réalisés :", tests_line_edit, "tests", data, add_to_layout=True)

        # Connecter le signal textChanged pour recalculer le volume par test
        tests_line_edit.textChanged.connect(self.calculate_volume_per_test)
        form_layout.addLayout(hbox_tests)

        # Champ "Perte (%)"
        hbox_perte = QHBoxLayout()
        perte_line_edit = QLineEdit()
        self.add_form_row(hbox_perte, "Perte (%) :", perte_line_edit, "perte", data, add_to_layout=True)
        form_layout.addLayout(hbox_perte)

        # Champ "Opérateur"
        hbox_operator = QHBoxLayout()
        self.add_form_row(hbox_operator, "Opérateur :", QLineEdit(), "operator", data, add_to_layout=True)
        form_layout.addLayout(hbox_operator)

        # Initialiser les champs si aucune donnée n'est fournie
        if not data:
            self.fields['volume_restant'].setText("0.00")
            self.fields['tests'].setText("0")
            self.calculate_loss()  # Calculer la perte automatiquement

        group_box.setLayout(form_layout)
        layout.addWidget(group_box)

    def calculate_loss(self):
        try:
            total_volume = float(self.fields['volume_total'].text())
            remaining_volume = float(self.fields['volume_restant'].text())
            
            # Calcul du volume utilisé
            used_volume = total_volume - remaining_volume
            
            # Perte est égale au volume restant
            loss_volume = remaining_volume
            
            # Pourcentage de perte
            loss_percentage = (loss_volume / total_volume) * 100 if total_volume > 0 else 0
            
            # Mettre à jour les champs correspondants
            self.fields['perte'].setText(f"{loss_percentage:.2f}")
        except ValueError:
            pass

    def validate(self):
        try:
            total_volume = float(self.fields['volume_total'].text())
            remaining_volume = float(self.fields['volume_restant'].text())
            tests = int(self.fields['tests'].text())
            
            # Calcul du volume utilisé
            used_volume = total_volume - remaining_volume
            
            # Perte est égale au volume restant
            loss_volume = remaining_volume
            
            # Pourcentage de perte
            loss_percentage = (loss_volume / total_volume) * 100 if total_volume > 0 else 0
            
            # Mettre à jour le champ "perte"
            self.fields['perte'].setText(f"{loss_percentage:.2f}")
            
            # Vérifier les types des données saisies
            float(self.fields['volume_total'].text())
            float(self.fields['volume_restant'].text())
            int(self.fields['tests'].text())
            float(self.fields['perte'].text())
            
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Veuillez vérifier les valeurs saisies.")
            
    def calculate_volume_per_test(self):
        try:
            total_volume = float(self.fields['volume_total'].text())
            remaining_volume = float(self.fields['volume_restant'].text())
            tests = int(self.fields['tests'].text())

            # Calcul du volume utilisé
            used_volume = total_volume - remaining_volume

            # Calcul du volume par test
            vol_per_test = used_volume / tests if tests > 0 else 0

            # Mettre à jour le champ "Volume/Test (ml)"
            self.fields['volume_per_test'].setText(f"{vol_per_test:.2f}")
        except ValueError:
            pass  # Ignorer les erreurs si les champs ne contiennent pas des nombres valides
        
    def fetch_analytes_from_database(self):
        try:
            analytes = self.database.get_all_analytes()
            return analytes
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les analytes : {e}")
            return []

    def add_form_row(self, layout, label, widget, field_name, data, add_to_layout=False, items=None):
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(label))
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if isinstance(widget, QDateEdit):
            if not widget.date().isValid():
                widget.setDate(QDate.currentDate())

        if isinstance(widget, QComboBox) and items:
            widget.addItems(items)

        if data and field_name in data:
            if isinstance(widget, QLineEdit):
                widget.setText(str(data[field_name]))
            elif isinstance(widget, QDateEdit):
                widget.setDate(QDate.fromString(data[field_name], "yyyy-MM-dd"))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(data[field_name])

        self.fields[field_name] = widget
        hbox.addWidget(widget)

        if add_to_layout:
            layout.addLayout(hbox)
        else:
            return hbox

    def get_data(self):
        return {
            'nom_analyte': self.fields['nom_analyte'].currentText(),
            'unite': self.fields['unite'].currentText(),
            'lot': self.fields['lot'].text(),
            'debut': self.fields['debut'].date().toString("yyyy-MM-dd"),
            'fin': self.fields['fin'].date().toString("yyyy-MM-dd"),
            'volume_total': self.fields['volume_total'].text(),
            'volume_restant': self.fields['volume_restant'].text(),
            'tests': self.fields['tests'].text(),
            'perte': self.fields['perte'].text(),
            'operator': self.fields['operator'].text()
        }
class TabVolumeParTest(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.database = ReactifsDatabase()
        self.current_row = -1
        self.data_model = []
        self.export_thread = None  # Ajout d'un attribut pour stocker le thread
        self.thread = None
        self.setup_ui()
        self.load_data_from_database()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # === GroupBox pour l'analyse des données ===
        analysis_box = QGroupBox("Analyse des Données")
        analysis_main_layout = QVBoxLayout()

        # Zone de recherche et bouton Rétablir
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Rechercher un analyte...")
        self.txt_search.textChanged.connect(self.dynamic_search)
        self.btn_reset = QPushButton("Rétablir")
        self.btn_reset.clicked.connect(self.load_data_from_database)

        self.cmb_analytes = QComboBox()
        self.cmb_analytes.setEditable(True)
        self.populate_analytes_combo()
        self.cmb_analytes.currentTextChanged.connect(self.update_analyte_stats)

        search_layout.addWidget(self.txt_search)
        search_layout.addWidget(self.btn_reset)
        search_layout.addWidget(self.cmb_analytes)
        analysis_main_layout.addLayout(search_layout)

        # Layout des analyses
        analysis_layout = QHBoxLayout()

        # Initialisation des champs manquants
        self.txt_selected_analyte = QLineEdit(); self.txt_selected_analyte.setReadOnly(True)
        self.txt_tests = QLineEdit(); self.txt_tests.setReadOnly(True)  # <--- Ajout ici
        self.txt_days = QLineEdit(); self.txt_days.setReadOnly(True)
        self.txt_total_vol = QLineEdit(); self.txt_total_vol.setReadOnly(True)
        self.txt_consumed_vol = QLineEdit(); self.txt_consumed_vol.setReadOnly(True)
        self.txt_lost_vol = QLineEdit(); self.txt_lost_vol.setReadOnly(True)
        self.txt_vol_per_test = QLineEdit(); self.txt_vol_per_test.setReadOnly(True)

        analysis_layout.addWidget(QLabel("Analyte Sélectionné :"))
        analysis_layout.addWidget(self.txt_selected_analyte)
        analysis_layout.addWidget(QLabel("Tests :"))
        analysis_layout.addWidget(self.txt_tests)  # <--- Utilisé ici
        analysis_layout.addWidget(QLabel("Jours :"))
        analysis_layout.addWidget(self.txt_days)
        analysis_layout.addWidget(QLabel("Vol. Total :"))
        analysis_layout.addWidget(self.txt_total_vol)
        analysis_layout.addWidget(QLabel("Vol. Cons. :"))
        analysis_layout.addWidget(self.txt_consumed_vol)
        analysis_layout.addWidget(QLabel("Perte :"))
        analysis_layout.addWidget(self.txt_lost_vol)
        analysis_layout.addWidget(QLabel("Vol./Test :"))
        analysis_layout.addWidget(self.txt_vol_per_test)

        analysis_main_layout.addLayout(analysis_layout)
        analysis_box.setLayout(analysis_main_layout)
        layout.addWidget(analysis_box)

        # Table pour afficher les données
        self.table = self.create_table()
        layout.addWidget(self.table)

        # Boutons d'action avec spacer
        btn_layout = QHBoxLayout()
        actions = [
            ("Explication", self.show_explanation),
            ("Enregistrer tout", self.save_all),
            ("Export PDF", self.export_pdf),
            ("Export Excel", self.export_excel),
            ("Ajouter", self.add)
        ]

        add_button = QPushButton("Explication")
        add_button.clicked.connect(self.show_explanation)
        btn_layout.addWidget(add_button, stretch=1)

        spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_layout.addSpacerItem(spacer)
        btn_layout.addStretch(2)

        for btn_text, slot in actions[1:]:
            btn = QPushButton(btn_text)
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn, stretch=1)

        layout.addLayout(btn_layout)

        # Activation du menu contextuel pour la table
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def populate_analytes_combo(self):
        try:
            analytes = self.database.get_all_analytes()
            self.cmb_analytes.clear()
            self.cmb_analytes.addItems([analyte for analyte in analytes])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les analytes : {e}")

    def show_context_menu(self, position):
        menu = QMenu(self.table)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 3px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #d0d0d0;
                margin: 4px 0px;
            }
        """)

        edit_action = QAction("Modifier", menu)
        edit_action.setIcon(QIcon(":/icons/edit.png"))
        menu.addAction(edit_action)

        menu.addSeparator()

        delete_action = QAction("Supprimer", menu)
        delete_action.setIcon(QIcon(":/icons/delete.png"))
        menu.addAction(delete_action)

        row = self.table.currentRow()
        if row == -1:
            return

        edit_action.triggered.connect(lambda: self.edit(row))
        delete_action.triggered.connect(lambda: self.delete(row))

        menu.exec_(self.table.viewport().mapToGlobal(position))

    def load_data_from_database(self):
        query_lots = """
            SELECT Lots.id, Analytes.name, Analytes.unit, Lots.lot_number, Lots.start_date, Lots.end_date, Lots.total_volume, Lots.remaining_volume, Lots.tests_performed, Lots.loss_percentage, Lots.operator
            FROM Lots
            JOIN Analytes ON Lots.analyte_id = Analytes.id
        """
        self.thread = DatabaseWorkerThread(query=query_lots, db_path="reactifs_database.db", fetch=True)
        self.thread.finished.connect(self.on_load_data_finished)
        self.thread.start()

    def on_load_data_finished(self, success, lots):
        if not success:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données : {lots[0]}")
            return

        try:
            self.table.clearContents()
            self.table.setRowCount(0)
            self.data_model = []

            for lot in lots:
                data = {
                    'id': lot[0],
                    'nom_analyte': lot[1],
                    'unite': lot[2],
                    'lot': lot[3],
                    'debut': lot[4],
                    'fin': lot[5],
                    'volume_total': str(lot[6]),
                    'volume_restant': str(lot[7]),
                    'tests': str(lot[8]),
                    'perte': str(lot[9]),
                    'operator': lot[10] if len(lot) > 10 else ''
                }
                self.add_to_table(data)
                self.data_model.append(data)

            self.table.setUpdatesEnabled(True)
            QMessageBox.information(self, "Succès", "Les données ont été chargées avec succès.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données : {lots if isinstance(lots, str) else 'Erreur inconnue'}")

    def create_table(self):
        table = QTableWidget()
        headers = [
            "ID", "Nom analyte", "Unité", "Numéro lot", "Début", "Fin", "Durée",
            "Volume Total (ml)", "Volume Restant (ml)", "Tests Réalisés", "Volume/Test (ml)", "Perte %", "Opérateur"
        ]

        table.setColumnCount(len(headers))
        header = table.horizontalHeader()
        header.setFixedHeight(50)
        table.verticalHeader().setDefaultSectionSize(45)
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.selectionModel().currentRowChanged.connect(self.on_row_selected)

        return table

    def add_to_table(self, data):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.data_model.append(data)

        headers = [
            "ID", "Nom analyte", "Unité", "Numéro lot", "Début", "Fin", "Durée",
            "Volume Total (ml)", "Volume Restant (ml)", "Tests Réalisés", "Volume/Test (ml)", "Perte %", "Opérateur"
        ]

        for col, header in enumerate(headers):
            value = ""
            if header == "ID":
                value = str(data.get('id', ""))
            elif header == "Nom analyte":
                value = data.get('nom_analyte', "")
            elif header == "Unité":
                value = data.get('unite', "")
            elif header == "Numéro lot":
                value = data.get('lot', "")
            elif header == "Début":
                value = data.get('debut', "")
            elif header == "Fin":
                value = data.get('fin', "")
            elif header == "Durée":
                value = self.calculate_duration(data.get('debut', ""), data.get('fin', ""))
            elif header == "Volume Total (ml)":
                value = data.get('volume_total', "")
            elif header == "Volume Restant (ml)":
                value = data.get('volume_restant', "")
            elif header == "Tests Réalisés":
                value = data.get('tests', "")
            elif header == "Volume/Test (ml)":
                value = self.calculate_volume_per_test(data)
            elif header == "Perte %":
                value = data.get('perte', "")
            elif header == "Opérateur":
                value = data.get('operator', "")

            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_count, col, item)

    def calculate_duration(self, start_date, end_date):
        try:
            start = QDate.fromString(start_date, "yyyy-MM-dd")
            end = QDate.fromString(end_date, "yyyy-MM-dd")
            return str(abs(start.daysTo(end))) + " jours"
        except Exception:
            return ""

    def calculate_volume_per_test(self, data):
        try:
            total = float(data.get('volume_total', 0))
            restant = float(data.get('volume_restant', 0))
            tests = int(data.get('tests', 0))
            consumed = total - restant
            return f"{consumed / tests:.2f}" if tests > 0 else ""
        except Exception:
            return ""

    def add(self):
        dialog = AddEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                analyte_id = self.database.get_analyte_id(data['nom_analyte'])
                if not analyte_id:
                    self.database.add_analyte(data['nom_analyte'], data['unite'])
                    analyte_id = self.database.get_analyte_id(data['nom_analyte'])

                lot_id = self.database.add_lot(
                    analyte_id=analyte_id,
                    lot_number=data['lot'],
                    start_date=data['debut'],
                    end_date=data['fin'],
                    total_volume=float(data['volume_total']),
                    remaining_volume=float(data['volume_restant']),
                    tests_performed=int(data['tests']),
                    loss_percentage=float(data['perte']),
                    operator=data['operator']
                )

                if lot_id is not None:
                    data['id'] = lot_id
                    self.add_to_table(data)
                    self.update_analysis()
                    QMessageBox.information(self, "Succès", "Le lot a été ajouté avec succès.")
                else:
                    QMessageBox.critical(self, "Erreur", "Impossible d'ajouter le lot.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter le lot : {e}")

    def on_add_finished(self, success, result, data):
        if success:
            lot_id = result
            if lot_id is not None:
                data['id'] = lot_id
            else:
                QMessageBox.warning(self, "Avertissement", "L'ID du lot n'a pas pu être récupéré.")

            self.add_to_table(data)
            self.update_analysis()
            QMessageBox.information(self, "Succès", "Le lot a été ajouté avec succès.")
        else:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter le lot : {result}")

    def update_table(self, lot_id, data):
        try:
            row = self.table.rowCount()
            self.table.insertRow(row)

            duration = self.calculate_duration(data['debut'], data['fin'])
            volume_per_test = self.calculate_volume_per_test(data)

            items = [
                (0, str(lot_id)),
                (1, data['nom_analyte']),
                (2, data['unite']),
                (3, data['lot']),
                (4, data['debut']),
                (5, data['fin']),
                (6, str(duration)),
                (7, str(data['volume_total'])),
                (8, str(data['volume_restant'])),
                (9, str(data['tests'])),
                (10, str(volume_per_test)),
                (11, str(data['perte'])),
                (12, str(data['operator']))
            ]

            for col, value in items:
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            self.update_analysis()
            QMessageBox.information(self, "Succès", "Ajout réussi")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur d'affichage : {e}")

    def calculate_loss_volume(self, total_volume, loss_percentage):
        return (total_volume * loss_percentage) / 100

    def edit(self, row=None):
            if row is None:
                row = self.table.currentRow()
            if row == -1:
                QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une ligne à modifier.")
                return

            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            data = {
                header: self.table.item(row, col).text() if self.table.item(row, col) else ""
                for col, header in enumerate(headers)
            }
            mapped_data = {
                'nom_analyte': data.get("Nom analyte", ""),
                'unite': data.get("Unité", ""),
                'lot': data.get("Numéro lot", ""),
                'debut': data.get("Début", ""),
                'fin': data.get("Fin", ""),
                'volume_total': data.get("Volume Total (ml)", ""),
                'volume_restant': data.get("Volume Restant (ml)", ""),
                'tests': data.get("Tests Réalisés", ""),
                'perte': data.get("Perte %", ""),
                'operator': data.get("Opérateur", "")
            }

            dialog = AddEditDialog(self, mapped_data)
            if dialog.exec_() != QDialog.Accepted:
                return

            updated_data = dialog.get_data()
            try:
                lot_id = int(self.table.item(row, 0).text())
                self.update_test_in_database(lot_id, updated_data) # On appelle toujours update_test_in_database mais on va le modifier
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour : {e}")

    def update_test_in_database(self, lot_id, data):
        try:
            # Récupérer l'analyte_id original
            analyte_id = self.database.get_analyte_id(data['nom_analyte'])
            
            if analyte_id is None:
                QMessageBox.critical(self, "Erreur", "Analyte introuvable dans la base de données.")
                return

            success = self.database.update_lot_by_id(
                lot_id=lot_id,
                analyte_id=analyte_id,
                lot_number=data['lot'],
                start_date=data['debut'],
                end_date=data['fin'],
                total_volume=float(data['volume_total']),
                remaining_volume=float(data['volume_restant']),
                tests_performed=int(data['tests']),
                loss_percentage=float(data['perte']),
                operator=data['operator']
            )
            
            if success:
                self.update_table_row(lot_id, data)
            else:
                QMessageBox.critical(self, "Erreur", "Échec de la mise à jour du lot.")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur DB: {str(e)}")


    def update_table_row(self, lot_id, data):
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == str(lot_id):
                headers = [
                    "ID", "Nom analyte", "Unité", "Numéro lot", "Début", "Fin", "Durée",
                    "Volume Total (ml)", "Volume Restant (ml)", "Tests Réalisés", "Volume/Test (ml)", "Perte %", "Opérateur"
                ]

                for col, header in enumerate(headers):
                    value = ""
                    if header == "ID":
                        value = str(lot_id)
                    elif header == "Nom analyte":
                        value = data.get('nom_analyte', "")
                    elif header == "Unité":
                        value = data.get('unite', "")
                    elif header == "Numéro lot":
                        value = data.get('lot', "")
                    elif header == "Début":
                        value = data.get('debut', "")
                    elif header == "Fin":
                        value = data.get('fin', "")
                    elif header == "Durée":
                        value = self.calculate_duration(data.get('debut', ""), data.get('fin', ""))
                    elif header == "Volume Total (ml)":
                        value = data.get('volume_total', "")
                    elif header == "Volume Restant (ml)":
                        value = data.get('volume_restant', "")
                    elif header == "Tests Réalisés":
                        value = data.get('tests', "")
                    elif header == "Volume/Test (ml)":
                        value = self.calculate_volume_per_test(data)
                    elif header == "Perte %":
                        value = data.get('perte', "")
                    elif header == "Opérateur":
                        value = data.get('operator', "")

                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)
                break

    def delete(self, row=None):
        if row is None:
            row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une ligne à supprimer.")
            return

        reply = QMessageBox.question(
            self, "Confirmation",
            "Êtes-vous sûr de vouloir supprimer ce lot ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            # Récupérer l'ID du lot depuis la première colonne
            lot_id = int(self.table.item(row, 0).text())

            # Démarrer le thread pour exécuter la suppression
            self.thread = DatabaseDeleteThread(db_name="reactifs_database.db", lot_id=lot_id)
            self.thread.finished.connect(lambda success, error: self.on_delete_finished(success, error, row))
            self.thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de préparer la suppression : {e}")

    def on_delete_finished(self, success, error, row):
        if success:
            self.table.removeRow(row)  # Supprimer la ligne de la table UI
            del self.data_model[row]  # Supprimer la donnée du modèle interne
            # self.update_analysis()  # Retirer cet appel pour ne pas mettre à jour l'analyse
            QMessageBox.information(self, "Succès", "Le lot a été supprimé avec succès.")
        else:
            QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le lot : {error}")
            
    def update_analysis(self):
        if not self.data_model:
            return

        last_data = self.data_model[-1]
        try:
            total = self.safe_convert_to_float(last_data.get('volume_total', 0), 0)
            restant = self.safe_convert_to_float(last_data.get('volume_restant', 0), 0)
            tests = self.safe_convert_to_float(last_data.get('tests', 0), 0)
            
            # Calcul du volume utilisé
            used_volume = total - restant
            
            # Perte est égale au volume restant
            loss_volume = restant
            
            # Pourcentage de perte
            loss_percentage = (loss_volume / total) * 100 if total > 0 else 0
            
            # Calcul du volume par test
            vol_per_test = used_volume / tests if tests > 0 else 0

            # Mettre à jour les champs texte de l'interface
            self.txt_tests.setText(f"{tests:.2f}")
            self.txt_total_vol.setText(f"{total:.2f} ml")
            self.txt_consumed_vol.setText(f"{used_volume:.2f} ml")
            self.txt_lost_vol.setText(f"{loss_volume:.2f} ml ({loss_percentage:.1f}%)")
            self.txt_vol_per_test.setText(f"{vol_per_test:.2f} ml/test")

            start = QDate.fromString(last_data.get('debut', ""), "yyyy-MM-dd")
            end = QDate.fromString(last_data.get('fin', ""), "yyyy-MM-dd")
            days = start.daysTo(end)
            self.txt_days.setText(f"{abs(days)} jours")

            # Aligner les données existantes dans la table au centre
            self.align_table_data()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def align_table_data(self):
        """
        Aligne les données de la table au centre.
        """
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
        self.table.blockSignals(False)

    def safe_convert_to_float(self, value, default_value):
        """ Convert value to float safely, return default if fails"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default_value


    def save_all(self):
        try:
            queries = []
            params_list = []

            for row in range(self.table.rowCount()):
                data = self.get_row_data(row)

                analyte_id = self.database.get_analyte_id(data['Nom analyte'])
                if not analyte_id:
                    self.database.add_analyte(data['Nom analyte'], data['Unité'])
                    analyte_id = self.database.get_analyte_id(data['Nom analyte'])

                lot_id = int(self.table.item(row, 0).text())

                query = """
                    UPDATE Lots
                    SET analyte_id = ?, lot_number = ?, start_date = ?, end_date = ?,
                        total_volume = ?, remaining_volume = ?, tests_performed = ?, loss_percentage = ?, operator = ?
                    WHERE id = ?;
                    """
                params = (
                    analyte_id,
                    data['Numéro lot'],
                    data['Début'],
                    data['Fin'],
                    float(data['Volume Total (ml)']),
                    float(data['Volume Restant (ml)']),
                    int(data['Tests Réalisés']),
                    float(data['Perte %']),
                    data['Opérateur'],
                    lot_id
                )

                queries.append(query)
                params_list.append(params)

            self.thread = DatabaseWorkerThread(query=queries, params=params_list, transaction=True)
            self.thread.finished.connect(self.on_save_all_finished)
            self.thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {e}")

    def on_save_all_finished(self, success, result):
        if success:
            QMessageBox.information(self, "Succès", "Toutes les données ont été enregistrées avec succès.")
        else:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {result}")


    def export_pdf(self):
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        data = [[self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(self.table.columnCount())] for row in range(self.table.rowCount())]
        export_data(self, "pdf", headers, data)

    def export_excel(self):
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        data = []

        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                value = item.text() if item else ""
                row_data.append(value)
            data.append(row_data)

        export_data(self, "excel", headers, data)

    def on_export_finished(self, success, message):
        if success:
            QMessageBox.information(self, "Exportation réussie", message)
        else:
            QMessageBox.critical(self, "Erreur", message)
        self.export_thread = None



    def show_explanation(self):
        explanation = (
            "Analyse des volumes et consommation :\n"
            "1. Volume Total : Quantité initiale de réactif\n"
            "2. Volume Restant : Quantité disponible actuellement\n"
            "3. Volume Consommé = Volume Total - Volume Restant\n"
            "4. Volume/Test = (Volume Consommé) / Nombre de tests\n"
            "5. Perte % = (Perte / Volume Total) * 100, où Perte = valeur saisie\n"
        )
        QMessageBox.information(self, "Explication", explanation)

    def get_row_data(self, row):
        data = {}
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        for col, header in enumerate(headers):
            item = self.table.item(row, col)
            data[header] = item.text() if item else ""
        return data

    def update_row(self, row, data):
        try:
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            for col, header in enumerate(headers):
                if col == 0:
                    continue
                value = ""
                if header == "Nom analyte":
                    value = data.get('nom_analyte', "")
                elif header == "Unité":
                    value = data.get('unite', "")
                elif header == "Numéro lot":
                    value = data.get('lot', "")
                elif header == "Début":
                    value = data.get('debut', "")
                elif header == "Fin":
                    value = data.get('fin', "")
                elif header == "Durée":
                    value = self.calculate_duration(data.get('debut', ""), data.get('fin', ""))
                elif header == "Volume Total (ml)":
                    value = data.get('volume_total', "")
                elif header == "Volume Restant (ml)":
                    value = data.get('volume_restant', "")
                elif header == "Tests Réalisés":
                    value = data.get('tests', "")
                elif header == "Volume/Test (ml)":
                    value = self.calculate_volume_per_test(data)
                elif header == "Perte %":
                    value = data.get('perte', "")
                elif header == "Opérateur":
                    value = data.get('operator', "")
                self.table.setItem(row, col, QTableWidgetItem(value))
            QMessageBox.information(self, "Succès", "Les données ont été mises à jour avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour : {e}")

    def on_row_selected(self, current, previous):
        row = current.row()
        if row >= 0:
            try:
                tests = self.table.item(row, 9).text() if self.table.item(row, 9) else "0"
                total = self.table.item(row, 7).text() if self.table.item(row, 7) else "0"
                restant = self.table.item(row, 8).text() if self.table.item(row, 8) else "0"
                total_float = self.safe_convert_to_float(total.replace(" ml", "").strip(), 0)
                restant_float = self.safe_convert_to_float(restant.replace(" ml", "").strip(), 0)
                volume_consomme = total_float - restant_float
                perte_ml = restant_float
                perte_pct = (perte_ml / total_float) * 100 if total_float > 0 else 0
                date_debut_str = self.table.item(row, 4).text() if self.table.item(row, 4) else ""
                date_fin_str = self.table.item(row, 5).text() if self.table.item(row, 5) else ""
                date_debut = QDate.fromString(date_debut_str, "yyyy-MM-dd")
                date_fin = QDate.fromString(date_fin_str, "yyyy-MM-dd")
                days = date_debut.daysTo(date_fin) if date_debut.isValid() and date_fin.isValid() else 0
                self.txt_tests.setText(f"{tests}")
                self.txt_total_vol.setText(f"{total_float:.2f} ml")
                self.txt_consumed_vol.setText(f"{volume_consomme:.2f} ml")
                self.txt_lost_vol.setText(f"{perte_ml:.2f} ml ({perte_pct:.1f}%)")
                self.txt_days.setText(f"{abs(days)} jours")
                vol_test = self.table.item(row, 10).text() if self.table.item(row, 10) else "0"
                self.txt_vol_per_test.setText(vol_test)
                analyte = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                self.txt_selected_analyte.setText(analyte)
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Une erreur s'est produite lors de la conversion des données : {e}")

    def safe_convert_to_float(self, value, default=0.0):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def on_search(self):
        search_text = self.txt_search.text().strip().lower()
        for row in range(self.table.rowCount()):
            match_found = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            self.table.setRowHidden(row, not match_found)

    def dynamic_search(self):
        search_text = self.txt_search.text().strip().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            self.table.setRowHidden(row, search_text not in item.text().lower() if item else True)

    def update_search_results(self, results):
        self.table.clearContents()
        self.table.setRowCount(0)
        for data in results:
            self.add_to_table(data)

    def update_analyte_stats(self):
        analyte_name = self.cmb_analytes.currentText().strip()
        if not analyte_name:
            self.clear_stat_fields()
            return

        try:
            lots = self.database.get_lots_by_analyte(analyte_name)
            if not lots:
                self.clear_stat_fields()
                return

            total_tests = sum(lot['tests_performed'] for lot in lots) / len(lots) if lots else 0
            total_days = sum(self.calculate_duration_days(lot['start_date'], lot['end_date']) for lot in lots) / len(lots) if lots else 0
            total_vol = sum(lot['total_volume'] for lot in lots) / len(lots) if lots else 0
            consumed_vol = sum(lot['total_volume'] - lot['remaining_volume'] for lot in lots) / len(lots) if lots else 0
            loss_percentage = sum(lot['loss_percentage'] for lot in lots) / len(lots) if lots else 0
            vol_per_test = (
                sum((lot['total_volume'] - lot['remaining_volume']) / lot['tests_performed']
                for lot in lots if lot['tests_performed'] > 0) /
                len([lot for lot in lots if lot['tests_performed'] > 0])
            ) if any(lot['tests_performed'] > 0 for lot in lots) else 0

            self.txt_tests.setText(f"{total_tests:.2f}")
            self.txt_days.setText(f"{total_days:.2f}")
            self.txt_total_vol.setText(f"{total_vol:.2f} ml")
            self.txt_consumed_vol.setText(f"{consumed_vol:.2f} ml")
            self.txt_lost_vol.setText(f"{loss_percentage:.2f}%")
            self.txt_vol_per_test.setText(f"{vol_per_test:.2f} ml/test")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les statistiques : {e}")
            self.clear_stat_fields()

    def calculate_duration_days(self, start_date: str, end_date: str) -> int:
        try:
            if not start_date or not end_date:
                return 0
            start = QDate.fromString(start_date, "yyyy-MM-dd")
            end = QDate.fromString(end_date, "yyyy-MM-dd")
            return abs(start.daysTo(end))
        except Exception:
            return 0

    def update_average_stats(self, success, results):
        if not success or not results:
            self.clear_stat_fields()
            return

        try:
            avg_total_volume, avg_remaining_volume, avg_tests, avg_loss_percentage, avg_vol_per_test, avg_duration = results[0]

            avg_consumed_volume = avg_total_volume - avg_remaining_volume if avg_total_volume else 0

            self.txt_total_vol.setText(f"{avg_total_volume:.2f} ml" if avg_total_volume else "")
            self.txt_consumed_vol.setText(f"{avg_consumed_volume:.2f} ml" if avg_consumed_volume else "")
            self.txt_tests.setText(f"{avg_tests:.2f}" if avg_tests else "")
            self.txt_lost_vol.setText(f"{avg_loss_percentage:.2f}%" if avg_loss_percentage else "")
            self.txt_vol_per_test.setText(f"{avg_vol_per_test:.2f} ml/test" if avg_vol_per_test else "")
            self.txt_days.setText(f"{avg_duration:.2f} jours" if avg_duration else "")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de calculer les statistiques : {e}")
            self.clear_stat_fields()

    def clear_stat_fields(self):
        self.txt_tests.setText("")
        self.txt_days.setText("")
        self.txt_total_vol.setText("")
        self.txt_consumed_vol.setText("")
        self.txt_lost_vol.setText("")
        self.txt_vol_per_test.setText("")