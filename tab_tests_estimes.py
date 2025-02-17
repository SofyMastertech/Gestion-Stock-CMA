from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QVBoxLayout, QPushButton, QWidget,
    QMessageBox, QHeaderView, QComboBox, QDialog,
    QDialogButtonBox, QDateEdit, QSpacerItem, QSizePolicy, QMenu,QFileDialog
)
from PySide6.QtCore import QDate, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QAction
from database import ReactifsDatabase, DatabaseWorkerThread
from export import export_data


class AddEditTestDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau Test" if not data else "Modifier Test")
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
        group_box = QGroupBox("Informations du Test")
        form_layout = QVBoxLayout()

        # Nom analyte
        analyte_combo = QComboBox()
        analyte_combo.setEditable(True)  # Rendre le QComboBox éditable
        self.add_form_row(form_layout, "Nom analyte :", analyte_combo, "nom_analyte", data, add_to_layout=True,
                        items=self.fetch_analytes_from_database())

        # Numéro de lot
        self.add_form_row(form_layout, "Numéro de lot :", QLineEdit(), "lot_number", data, add_to_layout=True)

        # Dates
        hbox_dates = QHBoxLayout()
        debut_date_edit = QDateEdit(calendarPopup=True)
        fin_date_edit = QDateEdit(calendarPopup=True)
        debut_date_edit.setDate(QDate.currentDate())
        fin_date_edit.setDate(QDate.currentDate())
        self.add_form_row(hbox_dates, "Date Ouverture :", debut_date_edit, "start_date", data, add_to_layout=True)
        self.add_form_row(hbox_dates, "Date Fin :", fin_date_edit, "end_date", data, add_to_layout=True)
        form_layout.addLayout(hbox_dates)

        # Tests estimés et réalisés
        hbox_tests = QHBoxLayout()
        self.add_form_row(hbox_tests, "Tests Estimés :", QLineEdit(), "estimated_tests", data, add_to_layout=True)
        self.add_form_row(hbox_tests, "Tests Réalisés :", QLineEdit(), "performed_tests", data, add_to_layout=True)
        form_layout.addLayout(hbox_tests)

        # Connecteurs pour recalculer automatiquement les champs
        self.fields["estimated_tests"].textChanged.connect(self.calculate_fields)
        self.fields["performed_tests"].textChanged.connect(self.calculate_fields)

        # Facteur utilisation
        self.add_form_row(form_layout, "Facteur Utilisation :", QLineEdit(), "usage_factor", data, add_to_layout=True)
        self.fields["usage_factor"].setReadOnly(True)

        # Perte (%)
        self.add_form_row(form_layout, "Perte (%) :", QLineEdit(), "loss_percentage", data, add_to_layout=True)
        self.fields["loss_percentage"].setReadOnly(True)

        # Perte (Tests)
        self.add_form_row(form_layout, "Perte (Tests) :", QLineEdit(), "loss_tests", data, add_to_layout=True)
        self.fields["loss_tests"].setReadOnly(True)

        # Opérateur
        hbox_operator = QHBoxLayout()
        self.add_form_row(hbox_operator, "Opérateur :", QLineEdit(), "operator", data, add_to_layout=True)
        form_layout.addLayout(hbox_operator)

        group_box.setLayout(form_layout)
        layout.addWidget(group_box)

    def calculate_fields(self):
        try:
            estimated_tests = int(self.fields["estimated_tests"].text() or 0)
            performed_tests = int(self.fields["performed_tests"].text() or 0)

            if performed_tests == 0:
                self.fields["usage_factor"].setText("0")
                self.fields["loss_percentage"].setText("0")
                self.fields["loss_tests"].setText(str(estimated_tests))
                return

            usage_factor = performed_tests / estimated_tests if estimated_tests > 0 else 0
            loss_tests = estimated_tests - performed_tests
            loss_percentage = (loss_tests / estimated_tests) * 100 if estimated_tests > 0 else 0

            self.fields["usage_factor"].setText(f"{usage_factor:.2f}")
            self.fields["loss_tests"].setText(str(loss_tests))
            self.fields["loss_percentage"].setText(f"{loss_percentage:.2f}")
        except ZeroDivisionError:
            self.fields["usage_factor"].setText("0")
            self.fields["loss_percentage"].setText("0")
            self.fields["loss_tests"].setText("")
        except ValueError:
            self.fields["usage_factor"].setText("")
            self.fields["loss_percentage"].setText("")
            self.fields["loss_tests"].setText("")

    def fetch_analytes_from_database(self):
        try:
            analytes = self.database.get_all_analytes()
            return analytes
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les analytes : {e}")
            return []

    def validate(self):
        try:
            int(self.fields['estimated_tests'].text())
            int(self.fields['performed_tests'].text())
            float(self.fields['usage_factor'].text())
            float(self.fields['loss_percentage'].text())
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Veuillez vérifier les valeurs saisies.")

    def add_form_row(self, layout, label, widget, field_name, data, add_to_layout=False, items=None):
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(label))
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Ajouter des éléments à un QComboBox si nécessaire
        if isinstance(widget, QComboBox) and items:
            widget.addItems(items)

        # Initialiser le widget avec les données transmises
        if data and field_name in data:
            if isinstance(widget, QLineEdit):
                widget.setText(str(data[field_name]))
            elif isinstance(widget, QDateEdit):
                widget.setDate(QDate.fromString(data[field_name], "yyyy-MM-dd"))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(data[field_name])

        # Enregistrer le widget dans le dictionnaire des champs
        self.fields[field_name] = widget
        hbox.addWidget(widget)

        # Ajouter la ligne au layout si spécifié
        if add_to_layout:
            layout.addLayout(hbox)
        else:
            return hbox

    def get_data(self):
        return {
            'nom_analyte': self.fields['nom_analyte'].currentText(),
            'lot_number': self.fields['lot_number'].text(),
            'start_date': self.fields['start_date'].date().toString("yyyy-MM-dd"),
            'end_date': self.fields['end_date'].date().toString("yyyy-MM-dd"),
            'estimated_tests': self.fields['estimated_tests'].text(),
            'performed_tests': self.fields['performed_tests'].text(),
            'usage_factor': self.fields['usage_factor'].text(),
            'loss_percentage': self.fields['loss_percentage'].text(),
            'loss_tests': self.fields['loss_tests'].text(),
            'operator': self.fields['operator'].text()
        }


class TabTests(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.database = ReactifsDatabase()
        self.current_row = -1
        self.data_model = []
        self.export_thread = None  # Stocker le thread ici
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
        self.txt_search.setPlaceholderText("Rechercher un test...")
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
        self.txt_estimated_tests = QLineEdit(); self.txt_estimated_tests.setReadOnly(True)
        self.txt_performed_tests = QLineEdit(); self.txt_performed_tests.setReadOnly(True)
        self.txt_loss_tests = QLineEdit(); self.txt_loss_tests.setReadOnly(True)
        self.txt_usage_factor = QLineEdit(); self.txt_usage_factor.setReadOnly(True)
        self.txt_loss_percentage = QLineEdit(); self.txt_loss_percentage.setReadOnly(True)

        analysis_layout.addWidget(QLabel("Tests Estimés :"))
        analysis_layout.addWidget(self.txt_estimated_tests)
        analysis_layout.addWidget(QLabel("Tests Réalisés :"))
        analysis_layout.addWidget(self.txt_performed_tests)
        analysis_layout.addWidget(QLabel("Perte (Tests) :"))
        analysis_layout.addWidget(self.txt_loss_tests)
        analysis_layout.addWidget(QLabel("Facteur Utilisation :"))
        analysis_layout.addWidget(self.txt_usage_factor)
        analysis_layout.addWidget(QLabel("Perte (%) :"))
        analysis_layout.addWidget(self.txt_loss_percentage)

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

        # Ajout du bouton "Explication" avec un facteur d'étirement de 1
        add_button = QPushButton("Explication")
        add_button.clicked.connect(self.show_explanation)
        btn_layout.addWidget(add_button, stretch=1)  # Facteur d'étirement de 1

        # Ajout d'un spacer avec un facteur d'étirement de 2 pour occuper plus d'espace
        spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_layout.addSpacerItem(spacer)
        btn_layout.addStretch(2)  # Facteur d'étirement de 2 pour le spacer

        # Ajout des autres boutons avec des facteurs d'étirement différents
        for btn_text, slot in actions[1:]:
            btn = QPushButton(btn_text)
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn, stretch=1)  # Facteur d'étirement de 1 pour chaque bouton

        # Ajout du layout des boutons au layout principal
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

    def update_analyte_stats(self):
        """
        Met à jour les statistiques moyennes pour l'analyte sélectionné dans la combobox.
        """
        analyte_name = self.cmb_analytes.currentText().strip()
        if not analyte_name:
            self.clear_stat_fields()
            return

        # Annuler le thread précédent s'il est encore en cours
        if self.thread and self.thread.isRunning():
            self.thread.requestInterruption()
            self.thread.wait()  # Attendre que le thread se termine

        # Démarrer un nouveau thread pour charger les tests associés à l'analyte
        self.thread = DatabaseWorkerThread(
            query="""
            SELECT AVG(estimated_tests), AVG(performed_tests), AVG(usage_factor), AVG(loss_percentage)
            FROM Tests
            JOIN Analytes ON Tests.analyte_id = Analytes.id
            WHERE Analytes.name = ?
            """,
            params=(analyte_name,),
            fetch=True,
            db_path="reactifs_database.db"
        )
        self.thread.finished.connect(lambda success, results: self.update_average_stats(success, results))
        self.thread.start()

    def update_average_stats(self, success, results):
        """
        Met à jour les statistiques moyennes pour l'analyte sélectionné.
        """
        if not success or not results:
            self.clear_stat_fields()
            return

        try:
            avg_estimated_tests, avg_performed_tests, avg_usage_factor, avg_loss_percentage = results[0]
            
            # Calculer la perte en tests
            avg_loss_tests = avg_estimated_tests - avg_performed_tests if avg_estimated_tests and avg_performed_tests else 0
            
            # Mettre à jour les champs de statistiques
            self.txt_estimated_tests.setText(f"{avg_estimated_tests:.2f}" if avg_estimated_tests else "")
            self.txt_performed_tests.setText(f"{avg_performed_tests:.2f}" if avg_performed_tests else "")
            self.txt_loss_tests.setText(f"{avg_loss_tests:.2f}" if avg_loss_tests else "")
            self.txt_usage_factor.setText(f"{avg_usage_factor:.2f}" if avg_usage_factor else "")
            self.txt_loss_percentage.setText(f"{avg_loss_percentage:.2f}%" if avg_loss_percentage else "")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de calculer les statistiques : {e}")
            self.clear_stat_fields()

    def clear_stat_fields(self):
        """
        Vide tous les champs de statistiques.
        """
        self.txt_estimated_tests.setText("")
        self.txt_performed_tests.setText("")
        self.txt_loss_tests.setText("")
        self.txt_usage_factor.setText("")
        self.txt_loss_percentage.setText("")


    def load_data_from_database(self):
        self.thread = DatabaseWorkerThread(
            query="""
            SELECT Tests.id, Analytes.name, Tests.lot_number, Tests.start_date, Tests.end_date,
                   Tests.estimated_tests, Tests.performed_tests, Tests.usage_factor, Tests.loss_percentage, Tests.operator
            FROM Tests
            JOIN Analytes ON Tests.analyte_id = Analytes.id
            """,
            db_path="reactifs_database.db",
            fetch=True
        )
        self.thread.finished.connect(self.on_load_data_finished)
        self.thread.start()

    def on_load_data_finished(self, success, tests):
        if not success:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données : {tests[0]}")
            return

        try:
            self.table.clearContents()
            self.table.setRowCount(0)
            self.data_model = []
            for test in tests:
                data = {
                    'id': test[0],
                    'nom_analyte': test[1],
                    'lot_number': test[2],
                    'start_date': test[3],
                    'end_date': test[4],
                    'estimated_tests': str(test[5]),
                    'performed_tests': str(test[6]),
                    'usage_factor': str(test[7]),
                    'loss_percentage': str(test[8]),
                    'operator': test[9] if len(test) > 9 else ''
                }
                self.add_to_table(data)
                self.data_model.append(data)
            QMessageBox.information(self, "Succès", "Les données ont été chargées avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données : {e}")

    def create_table(self):
        table = QTableWidget()
        headers = [
            "ID", "Nom analyte", "Numéro de lot", "Date Ouverture", "Date Fin", "Durée",
            "Tests Estimés", "Tests Réalisés", "Perte (Tests)", "Facteur Utilisation", "Perte (%)", "Opérateur"
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
        headers = [
            "ID", "Nom analyte", "Numéro de lot", "Date Ouverture", "Date Fin", "Durée",
            "Tests Estimés", "Tests Réalisés", "Perte (Tests)", "Facteur Utilisation", "Perte (%)", "Opérateur"
        ]
        for col, header in enumerate(headers):
            value = ""
            if header == "ID":
                value = str(data.get('id', ""))
            elif header == "Nom analyte":
                value = data.get('nom_analyte', "")
            elif header == "Numéro de lot":
                value = data.get('lot_number', "")
            elif header == "Date Ouverture":
                value = data.get('start_date', "")
            elif header == "Date Fin":
                value = data.get('end_date', "")
            elif header == "Durée":
                value = self.calculate_duration(data.get('start_date', ""), data.get('end_date', ""))
            elif header == "Tests Estimés":
                value = data.get('estimated_tests', "")
            elif header == "Tests Réalisés":
                value = data.get('performed_tests', "")
            elif header == "Perte (Tests)":
                value = str(int(data.get('estimated_tests', 0)) - int(data.get('performed_tests', 0)))
            elif header == "Facteur Utilisation":
                value = data.get('usage_factor', "")
            elif header == "Perte (%)":
                value = data.get('loss_percentage', "")
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

    def add(self):
        dialog = AddEditTestDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                analyte_id = self.database.get_analyte_id(data['nom_analyte'])
                if not analyte_id:
                    self.database.add_analyte(data['nom_analyte'], "test")
                    analyte_id = self.database.get_analyte_id(data['nom_analyte'])
                test_id = self.database.add_test(
                    analyte_id=analyte_id,
                    lot_number=data['lot_number'],
                    estimated_tests=int(data['estimated_tests']),
                    performed_tests=int(data['performed_tests']),
                    usage_factor=float(data['usage_factor']),
                    loss_percentage=float(data['loss_percentage']),
                    start_date=data['start_date'],
                    end_date=data['end_date'],
                    operator=data['operator']
                )
                if test_id is not None:
                    data['id'] = test_id
                    self.add_to_table(data)
                    QMessageBox.information(self, "Succès", "Le test a été ajouté avec succès.")
                else:
                    QMessageBox.critical(self, "Erreur", "Impossible d'ajouter le test.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter le test : {e}")

    def show_context_menu(self, position):
        menu = QMenu(self.table)
        menu.setStyleSheet("""
            QMenu {
                background-color: #f9f9f9;
                border: 1px solid #d3d3d3;
                padding: 8px;
                font-size: 14px;
            }
            QMenu::item {
                padding: 6px 24px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #d3d3d3;
                margin: 4px 0;
            }
        """)
        edit_action = QAction("Modifier", menu)
        edit_action.setIcon(QIcon(":/icons/edit.png"))
        edit_action.triggered.connect(lambda: self.edit(self.table.currentRow()))
        delete_action = QAction("Supprimer", menu)
        delete_action.setIcon(QIcon(":/icons/delete.png"))
        delete_action.triggered.connect(lambda: self.delete(self.table.currentRow()))
        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        row = self.table.currentRow()
        if row == -1:
            return
        menu.exec_(self.table.viewport().mapToGlobal(position))

    def edit(self, row=None):
        if row is None:
            row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une ligne à modifier.")
            return

        # Récupérer les en-têtes du tableau
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]

        # Récupérer les données de la ligne sélectionnée
        data = {
            header: self.table.item(row, col).text() if self.table.item(row, col) else ""
            for col, header in enumerate(headers)
        }

        # Mapper les données aux champs attendus par AddEditTestDialog
        mapped_data = {
            'nom_analyte': data.get("Nom analyte", ""),
            'lot_number': data.get("Numéro de lot", ""),
            'start_date': data.get("Date Ouverture", ""),
            'end_date': data.get("Date Fin", ""),
            'estimated_tests': data.get("Tests Estimés", ""),
            'performed_tests': data.get("Tests Réalisés", ""),
            'usage_factor': data.get("Facteur Utilisation", ""),
            'loss_percentage': data.get("Perte (%)", ""),
            'operator': data.get("Opérateur", "")
        }

        # Ouvrir le dialogue avec les données mappées
        dialog = AddEditTestDialog(self, mapped_data)
        if dialog.exec_() != QDialog.Accepted:
            return

        # Récupérer les données modifiées et mettre à jour la base de données
        updated_data = dialog.get_data()
        try:
            test_id = int(self.table.item(row, 0).text())
            self.update_test_in_database(test_id, updated_data)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour : {e}")

    def update_test_in_database(self, test_id, data):
        try:
            analyte_id = self.database.get_analyte_id(data['nom_analyte'])
            if not analyte_id:
                self.database.add_analyte(data['nom_analyte'], "test")
                analyte_id = self.database.get_analyte_id(data['nom_analyte'])
            success = self.database.update_test(
                test_id=test_id,
                analyte_id=analyte_id,
                lot_number=data['lot_number'],
                estimated_tests=int(data['estimated_tests']),
                performed_tests=int(data['performed_tests']),
                usage_factor=float(data['usage_factor']),
                loss_percentage=float(data['loss_percentage']),
                start_date=data['start_date'],
                end_date=data['end_date'],
                operator=data['operator']
            )
            if success:
                QMessageBox.information(self, "Succès", "Le test a été mis à jour avec succès.")
                self.update_table_row(test_id, data)
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de mettre à jour le test.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour : {e}")

    def update_table_row(self, test_id, data):
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == str(test_id):
                headers = [
                    "ID", "Nom analyte", "Numéro de lot", "Date Ouverture", "Date Fin", "Durée",
                    "Tests Estimés", "Tests Réalisés", "Perte (Tests)", "Facteur Utilisation", "Perte (%)", "Opérateur"
                ]
                for col, header in enumerate(headers):
                    value = ""
                    if header == "ID":
                        value = str(test_id)
                    elif header == "Nom analyte":
                        value = data.get('nom_analyte', "")
                    elif header == "Numéro de lot":
                        value = data.get('lot_number', "")
                    elif header == "Date Ouverture":
                        value = data.get('start_date', "")
                    elif header == "Date Fin":
                        value = data.get('end_date', "")
                    elif header == "Durée":
                        value = self.calculate_duration(data.get('start_date', ""), data.get('end_date', ""))
                    elif header == "Tests Estimés":
                        value = data.get('estimated_tests', "")
                    elif header == "Tests Réalisés":
                        value = data.get('performed_tests', "")
                    elif header == "Perte (Tests)":
                        value = str(int(data.get('estimated_tests', 0)) - int(data.get('performed_tests', 0)))
                    elif header == "Facteur Utilisation":
                        value = data.get('usage_factor', "")
                    elif header == "Perte (%)":
                        value = data.get('loss_percentage', "")
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
            "Êtes-vous sûr de vouloir supprimer ce test ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            test_id = int(self.table.item(row, 0).text())
            success = self.database.delete_test(test_id)
            if success:
                self.table.removeRow(row)
                QMessageBox.information(self, "Succès", "Le test a été supprimé avec succès.")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de supprimer le test.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression : {e}")

    def save_all(self):
        try:
            queries = []
            params_list = []
            for row in range(self.table.rowCount()):
                data = self.get_row_data(row)
                analyte_id = self.database.get_analyte_id(data['Nom analyte'])
                if not analyte_id:
                    self.database.add_analyte(data['Nom analyte'], "test")
                    analyte_id = self.database.get_analyte_id(data['Nom analyte'])
                test_id = int(self.table.item(row, 0).text())
                query = """
                    UPDATE Tests
                    SET analyte_id = ?, lot_number = ?, estimated_tests = ?, performed_tests = ?,
                        usage_factor = ?, loss_percentage = ?, start_date = ?, end_date = ?, operator = ?
                    WHERE id = ?;
                """
                params = (
                    analyte_id,
                    data['Numéro de lot'],
                    int(data['Tests Estimés']),
                    int(data['Tests Réalisés']),
                    float(data['Facteur Utilisation']),
                    float(data['Perte (%)']),
                    data['Date Ouverture'],
                    data['Date Fin'],
                    data['Opérateur'],
                    test_id
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
            "Calculs des tests :\n"
            "1. Tests Estimés : Nombre de tests prévus.\n"
            "2. Tests Réalisés : Nombre de tests effectués.\n"
            "3. Perte (Tests) : Nombre de tests non effectués (Estimés - Réalisés).\n"
            "4. Facteur Utilisation : Ratio entre Tests Réalisés et Tests Estimés.\n"
            "5. Perte (%) : Pourcentage de perte associé aux tests."
        )
        QMessageBox.information(self, "Explication", explanation)

    def get_row_data(self, row):
        data = {}
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        for col, header in enumerate(headers):
            item = self.table.item(row, col)
            data[header] = item.text() if item else ""
        return data

    def on_row_selected(self, current, previous):
        row = current.row()
        if row >= 0:
            try:
                estimated_tests = int(self.table.item(row, 6).text() or 0)
                performed_tests = int(self.table.item(row, 7).text() or 0)
                loss_tests = estimated_tests - performed_tests
                usage_factor = performed_tests / estimated_tests if estimated_tests > 0 else 0
                loss_percentage = (loss_tests / estimated_tests) * 100 if estimated_tests > 0 else 0
                self.txt_estimated_tests.setText(str(estimated_tests))
                self.txt_performed_tests.setText(str(performed_tests))
                self.txt_loss_tests.setText(str(loss_tests))
                self.txt_usage_factor.setText(f"{usage_factor:.2f}")
                self.txt_loss_percentage.setText(f"{loss_percentage:.2f}%")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Une erreur s'est produite lors de la conversion des données : {e}")

    def dynamic_search(self):
        search_text = self.txt_search.text().strip().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)  # Colonne du nom d'analyte
            self.table.setRowHidden(row, search_text not in item.text().lower() if item else True)