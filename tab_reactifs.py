# tab_reactifs.py
import os
from PySide6.QtCore import QCoreApplication, QSize, QMetaObject, Qt, QThread, Signal
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QApplication, QRadioButton, QDialog, QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QTabWidget,
    QMainWindow, QPushButton, QSpinBox, QVBoxLayout, QWidget, QSizePolicy, QSpacerItem, QMessageBox, QCompleter, QScrollArea
)
from logic_calc import ConsumptionCalculator, VOLUME_UNITS, MASS_UNITS, COUNT_UNITS

# Liste des analyses disponibles
analyse_liste = [
    "FSH", "PRL", "170H", "ACHBS", "ACTH", "AGHBS",
    "ALAT", "ALB", "AMH", "AMYL", "ASAT", "ASLO",
    "ATG", "ATPO", "AU", "BHCG", "BILL", "BL",
    "CA125", "CA153", "CA199", "CAL", "CHOL", "CORT 8",
    "CPK", "CREAT", "CRP", "DE LTA4", "E2", "FER",
    "FERRI", "FIB", "FNS", "FR", "FT3", "FT4",
    "GGT", "GLY", "GPP", "GS", "GSC", "HAV",
    "HBA1C", "HBS", "HCV", "HDLC", "HGPO", "HGPO GSS",
    "HIVD", "IONO", "LDH", "LH", "LIPA", "MAG",
    "malb24", "P24", "PAL", "PHOS", "PRG", "PSA TOTAL",
    "PSAL", "PSATL", "PTH", "RUBG", "RUBM", "SDHEA",
    "TCK", "TESTO", "TOXG", "TOXM", "TP", "TP INR",
    "TPHA", "TRIG", "TROP", "TSH", "UREE", "VDRL",
    "VITB12", "VITB9", "VITD", "VS", "ACR"
]

# Listes des unités
UNITS = [
    "ml", "L", "mg", "g", "kg", "µl", "boîte", "kit", "sachet", "flacon", "tube", "coffret", "test"
]
UNITS_CAL_CONT_CONFIRM = [
    "ml", "L", "mg", "g", "kg", "µl", "test"
]
TIME_UNITS = [
    "Jours", "Semaine", "Mois"
]
VOLUME_UNITS = ["µl", "ml", "l", "pl"]  # Unités de volume compatibles


class PackagingWorker(QThread):
    calculation_finished = Signal(str)

    def __init__(self, nbr_tests: float, qty_per_test: float, total_qty: float, unit: str, time_value: int, time_unit: str, is_container: bool):
        super().__init__()
        self.nbr_tests = nbr_tests
        self.qty_per_test = qty_per_test
        self.total_qty = total_qty
        self.unit = unit
        self.time_value = time_value
        self.time_unit = time_unit
        self.is_container = is_container

    def run(self):
        try:
            if self.is_container:
                if self.qty_per_test > 0 and self.total_qty > 0:
                    nbr_containers = (self.nbr_tests * self.qty_per_test) / self.total_qty
                    result = f"{nbr_containers:.2f} {self.unit}/{self.time_value} {self.time_unit}"
                else:
                    result = "Erreur : La quantité par test et le volume total doivent être supérieurs à zéro."
            else:
                if self.total_qty > 0:
                    nbr_packagings = self.nbr_tests / self.total_qty
                    result = f"{nbr_packagings:.2f} {self.unit}/{self.time_value} {self.time_unit}"
                else:
                    result = "Erreur : Le nombre total de tests par packaging doit être supérieur à zéro."
        except Exception as e:
            result = f"Erreur de calcul : {e}"
        self.calculation_finished.emit(result)


class GestionReactifs(QWidget):
    def __init__(self):
        super().__init__()
        self.calculator = ConsumptionCalculator()
        self.setupUi()
        self.setup_connections()

    def setupUi(self):
        self.setObjectName("Widget")
        self.resize(1194, 1000)

        # Créer un QScrollArea pour permettre le défilement
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # Permet au widget de redimensionner avec le scroll area

        # Créer un widget pour contenir le layout principal
        scroll_widget = QWidget()
        self.layout_main = QVBoxLayout(scroll_widget)  # Utilisez scroll_widget au lieu de self
        self.layout_main.setContentsMargins(8, 8, 8, 8)

        # Ajouter les widgets à l'interface
        self.horizontalLayout = QHBoxLayout()

        self.groupboxFirstRow = self.create_groupbox("Paramètres Consommation")
        self.add_first_row_widgets(self.groupboxFirstRow)
        self.horizontalLayout.addWidget(self.groupboxFirstRow)

        self.groupboxSecundRow = self.create_groupbox("Tests par Conditionnement")
        self.add_second_row_widgets(self.groupboxSecundRow)
        self.horizontalLayout.addWidget(self.groupboxSecundRow)

        self.layout_main.addLayout(self.horizontalLayout)

        self.groupeButtons = self.create_groupbox("Paramètres Calibration")
        self.add_third_row_widgets(self.groupeButtons)
        self.layout_main.addWidget(self.groupeButtons)

        self.groupboxFourthRow = self.create_groupbox("Paramètres Contrôles")
        self.add_fourth_row_widgets(self.groupboxFourthRow)
        self.layout_main.addWidget(self.groupboxFourthRow)

        self.groupboxFiveRow = self.create_groupbox("Paramètres Confirmation")
        self.add_fifth_row_widgets(self.groupboxFiveRow)
        self.layout_main.addWidget(self.groupboxFiveRow)

        self.groupboxSixRow = self.create_groupbox("Résultat")
        self.add_sixth_row_widgets(self.groupboxSixRow)
        self.layout_main.addWidget(self.groupboxSixRow)

        self.buttons_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Annuler", self)
        self.buttons_layout.addWidget(self.cancel_button)

        self.horizontalSpacer = QSpacerItem(310, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.buttons_layout.addItem(self.horizontalSpacer)

        self.print_button_result = QPushButton("Imprimer le résultat", self)
        self.buttons_layout.addWidget(self.print_button_result)

        self.calculate_button = QPushButton("Calculer", self)
        self.buttons_layout.addWidget(self.calculate_button)

        self.layout_main.addLayout(self.buttons_layout)

        # Définir le widget principal du QScrollArea
        scroll_area.setWidget(scroll_widget)

        # Définir le layout principal de la fenêtre pour contenir le QScrollArea
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def create_groupbox(self, title: str):
        groupbox = QGroupBox(title, self)  # Utiliser self au lieu de self.centralwidget
        return groupbox

    def create_groupbox(self, title: str) -> QGroupBox:
        groupbox = QGroupBox(self)
        groupbox.setObjectName(title.replace(" ", ""))
        groupbox.setTitle(title)
        return groupbox

    def add_first_row_widgets(self, groupbox: QGroupBox):
        """
        Ajoute les widgets pour le groupe "Paramètres Consommation".
        Inclut un champ QLineEdit pour saisir la quantité totale par conditionnement et son unité.
        """
        layout = QVBoxLayout(groupbox)
        layout.setSpacing(8)
        layout.setContentsMargins(6, 3, -1, 3)

        # Première ligne : Nombre de tests et période
        h_layout = QHBoxLayout()
        self.lbl_nbrTests_firstRow = QLabel(groupbox)
        self.lbl_nbrTests_firstRow.setText("Nbr Tests")
        h_layout.addWidget(self.lbl_nbrTests_firstRow)

        self.lineEdit_nbrs_test_firstRow = QLineEdit(groupbox)
        h_layout.addWidget(self.lineEdit_nbrs_test_firstRow)

        self.lbl_par_firstRow = QLabel(groupbox)
        self.lbl_par_firstRow.setText("Par")
        h_layout.addWidget(self.lbl_par_firstRow)

        self.number_time_spinBox_firstRow = QSpinBox(groupbox)
        h_layout.addWidget(self.number_time_spinBox_firstRow)

        self.lbl_periode_temps_firstRow = QLabel(groupbox)
        self.lbl_periode_temps_firstRow.setText("Période")
        h_layout.addWidget(self.lbl_periode_temps_firstRow)

        self.comboBox_periode_temps_firstRow = QComboBox(groupbox)
        self.comboBox_periode_temps_firstRow.addItems(TIME_UNITS)
        h_layout.addWidget(self.comboBox_periode_temps_firstRow)

        h_layout.setStretch(1, 4)
        layout.addLayout(h_layout)

        # Deuxième ligne : Quantité par unité et unité physique
        h_layout2 = QHBoxLayout()
        self.lbl_qte_apr_unite_firstRow = QLabel(groupbox)
        self.lbl_qte_apr_unite_firstRow.setText("Qte/Unité")
        h_layout2.addWidget(self.lbl_qte_apr_unite_firstRow)

        self.lineEdit_qte_par_unite_de_test_firstRow = QLineEdit(groupbox)
        h_layout2.addWidget(self.lineEdit_qte_par_unite_de_test_firstRow)


        self.comboBox_unite_physique_firstRow = QComboBox(groupbox)
        self.comboBox_unite_physique_firstRow.addItems(UNITS_CAL_CONT_CONFIRM)
        h_layout2.addWidget(self.comboBox_unite_physique_firstRow)
        
        self.lbl_qte_total_unite_firstRow = QLabel(groupbox)
        self.lbl_qte_total_unite_firstRow.setText("Qte Totale")
        h_layout2.addWidget(self.lbl_qte_total_unite_firstRow)
        self.lineEdit_qte_totale_conditionnement_firstRow = QLineEdit(groupbox)
        self.lineEdit_qte_totale_conditionnement_firstRow.setPlaceholderText("Qte Totale/Conditionnement")
        self.lineEdit_qte_totale_conditionnement_firstRow.setToolTip("Entrez la quantité totale par conditionnement")
        h_layout2.addWidget(self.lineEdit_qte_totale_conditionnement_firstRow)

        self.comboBox_unite_qte_totale_conditionnement_firstRow = QComboBox(groupbox)
        self.comboBox_unite_qte_totale_conditionnement_firstRow.addItems(UNITS_CAL_CONT_CONFIRM)
        h_layout2.addWidget(self.comboBox_unite_qte_totale_conditionnement_firstRow)
        
        layout.addLayout(h_layout2)

        # 3ème ligne : Consommation par unité de temps
        h_layout4 = QHBoxLayout()
        self.lbl_consommation_par_uni_firstRow = QLabel(groupbox)
        self.lbl_consommation_par_uni_firstRow.setText("Consommation U/T")
        h_layout4.addWidget(self.lbl_consommation_par_uni_firstRow)

        self.lineEdit_consommation_par_unite_de_temps_firstRow = QLineEdit(groupbox)
        self.lineEdit_consommation_par_unite_de_temps_firstRow.setReadOnly(True)
        h_layout4.addWidget(self.lineEdit_consommation_par_unite_de_temps_firstRow)

        self.comboBox_unite_consommation_par_unite_de_temps = QComboBox(groupbox)
        self.comboBox_unite_consommation_par_unite_de_temps.addItems(UNITS)
        h_layout4.addWidget(self.comboBox_unite_consommation_par_unite_de_temps)

        layout.addLayout(h_layout4)
        
    def setup_connections(self):
        # Connexions existantes
        self.lineEdit_nbrs_test_firstRow.textChanged.connect(self.update_consumption)
        self.lineEdit_qte_par_unite_de_test_firstRow.textChanged.connect(self.update_consumption)
        self.number_time_spinBox_firstRow.valueChanged.connect(self.update_consumption)
        self.comboBox_periode_temps_firstRow.currentTextChanged.connect(self.update_consumption)

        # Connexions pour les combobox
        self.comboBox_unite_physique_firstRow.currentTextChanged.connect(self.on_physical_unit_changed)
        self.comboBox_unite_consommation_par_unite_de_temps.currentTextChanged.connect(self.on_consumption_unit_changed)
        # Connexion du signal currentTextChanged à une méthode
        self.comboBox_outil_mesure.currentTextChanged.connect(self.calculate_tests_per_container)


        # Connexions des boutons
        self.cancel_button.clicked.connect(self.close)
        self.calculate_button.clicked.connect(self.calculate_all)

        # Connexions pour la deuxième ligne
        self.comboBox_qte_par_unite_secondRow.currentTextChanged.connect(self.on_qty_per_unit_changed)
        self.comboBox_unite_volume_mort_secondRow.currentTextChanged.connect(self.on_dead_volume_unit_changed)
        self.comboBox_unite_qte_totale_par_conditionnement.currentTextChanged.connect(self.on_total_qty_unit_changed)
        self.lineEdit_qte_par_unite_secondRow.textChanged.connect(self.calculate_tests_per_container)
        self.lineEdit_qte_volume_mor_secondRow.textChanged.connect(self.calculate_tests_per_container)
        self.lineEdit_qte_totale_par_conditionnment_secondRow.textChanged.connect(self.calculate_tests_per_container)

        # Connexions pour la calibration
        self.lineEdit_qte_calibration_thirdRow.textChanged.connect(self.update_calibration)
        self.spinBox_frequence_calibration_thirdRow.valueChanged.connect(self.update_calibration)
        self.comboBox_fois_par_periode_temp_thirdRow.currentTextChanged.connect(self.update_calibration)
        self.number_time_spinBox_firstRow.valueChanged.connect(self.update_calibration)  # Ajouté
        self.comboBox_periode_temps_firstRow.currentTextChanged.connect(self.update_calibration)    
        self.comboBox_unite_qte_calibration_thirdRow.currentTextChanged.connect(self.on_calibration_unit_changed)

        # Connexion pour le changement d'unité de calibration totale
        self.comboBox_qte_totale_calibration_unite.currentTextChanged.connect(self.update_calibration)	

        # Connexions pour la confirmation
        self.lineEdit_nbrs_test_firstRow.textChanged.connect(self.update_confirmation)
        self.number_time_spinBox_firstRow.valueChanged.connect(self.update_confirmation)  # Ajouté
        self.comboBox_periode_temps_firstRow.currentTextChanged.connect(self.update_confirmation)
        self.lineEdit_qte_test_refais_confirmation_fiveRow.textChanged.connect(self.update_confirmation)
        self.spinBox_percent_confirmation_test_repete.valueChanged.connect(self.update_confirmation)
        self.comboBox_unite_qte_totale_confirmation_fiveRow.currentTextChanged.connect(self.update_confirmation)

    def update_consumption(self):
        try:
            nbr_tests = float(self.lineEdit_nbrs_test_firstRow.text() or "0")
            time_value = self.number_time_spinBox_firstRow.value()
            time_unit = self.comboBox_periode_temps_firstRow.currentText()
            qty_unit = self.comboBox_unite_physique_firstRow.currentText()

            if qty_unit in ["test", "pcs"]:
                consumption = nbr_tests
                result = f"{consumption:.2f} {qty_unit}/{time_value} {time_unit}"
            elif qty_unit in ["boîte", "kit", "sachet", "flacon", "tube", "coffret"]:
                qty_per_unit_text = self.lineEdit_qte_par_unite_de_test_firstRow.text()
                if qty_per_unit_text.startswith("Nombre de tests"):
                    self.lineEdit_consommation_par_unite_de_temps_firstRow.clear()
                    return
                qty_per_unit = float(qty_per_unit_text or "0")
                consumption = nbr_tests / qty_per_unit
                result = f"{consumption:.2f} {qty_unit}/{time_value} {time_unit}"
            else:
                qty_per_test = float(self.lineEdit_qte_par_unite_de_test_firstRow.text() or "0")
                total_qty = nbr_tests * qty_per_test
                consumption = total_qty 

                target_unit = self.comboBox_unite_consommation_par_unite_de_temps.currentText()
                if target_unit != qty_unit and target_unit in VOLUME_UNITS + MASS_UNITS and qty_unit in VOLUME_UNITS + MASS_UNITS:
                    try:
                        consumption = self.calculator.convert_value(consumption, qty_unit, target_unit)
                        qty_unit = target_unit
                    except ValueError:
                        self.show_error_message("Erreur de conversion")
                        return
                result = f"{consumption:.2f} {qty_unit}/{time_value} {time_unit}"

            self.lineEdit_consommation_par_unite_de_temps_firstRow.setText(result)
        except ValueError:
            self.lineEdit_consommation_par_unite_de_temps_firstRow.clear()

    def on_qty_per_unit_changed(self, new_unit: str):
        old_unit = self.comboBox_qte_par_unite_secondRow.currentText()
        qty_text = self.lineEdit_qte_par_unite_secondRow.text()
        if qty_text and qty_text.replace('.', '').isdigit():
            qty = float(qty_text)
            if old_unit in VOLUME_UNITS + MASS_UNITS and new_unit in VOLUME_UNITS + MASS_UNITS:
                try:
                    converted_qty = self.calculator.convert_value(qty, old_unit, new_unit)
                    self.lineEdit_qte_par_unite_secondRow.setText(f"{converted_qty:.2f}")
                except ValueError:
                    self.show_error_message("Erreur de conversion")
            else:
                self.lineEdit_qte_par_unite_secondRow.setText(qty_text)  # Pas de conversion pour les unités non massiques/volumiques
        else:
            self.lineEdit_qte_par_unite_secondRow.clear()

    def on_dead_volume_unit_changed(self, new_unit: str):
        old_unit = self.comboBox_unite_volume_mort_secondRow.currentText()
        volume_text = self.lineEdit_qte_volume_mor_secondRow.text()
        if volume_text and volume_text.replace('.', '').isdigit():
            volume = float(volume_text)
            if old_unit in VOLUME_UNITS + MASS_UNITS and new_unit in VOLUME_UNITS + MASS_UNITS:
                try:
                    converted_volume = self.calculator.convert_value(volume, old_unit, new_unit)
                    self.lineEdit_qte_volume_mor_secondRow.setText(f"{converted_volume:.2f}")
                except ValueError:
                    self.show_error_message("Erreur de conversion")
            else:
                self.lineEdit_qte_volume_mor_secondRow.setText(volume_text)  # Pas de conversion pour les unités non massiques/volumiques
        else:
            self.lineEdit_qte_volume_mor_secondRow.clear()

    def on_total_qty_unit_changed(self, new_unit: str):
        old_unit = self.comboBox_unite_qte_totale_par_conditionnement.currentText()
        total_qty_text = self.lineEdit_qte_totale_par_conditionnment_secondRow.text()
        if total_qty_text and total_qty_text.replace('.', '').isdigit():
            total_qty = float(total_qty_text)
            if old_unit in VOLUME_UNITS + MASS_UNITS and new_unit in VOLUME_UNITS + MASS_UNITS:
                try:
                    converted_total_qty = self.calculator.convert_value(total_qty, old_unit, new_unit)
                    self.lineEdit_qte_totale_par_conditionnment_secondRow.setText(f"{converted_total_qty:.2f}")
                except ValueError:
                    self.show_error_message("Erreur de conversion")
            else:
                self.lineEdit_qte_totale_par_conditionnment_secondRow.setText(total_qty_text)  # Pas de conversion pour les unités non massiques/volumiques
        else:
            self.lineEdit_qte_totale_par_conditionnment_secondRow.clear()

    def calculate_tests_per_container(self):
        try:
            qty_per_test_text = self.lineEdit_qte_par_unite_secondRow.text()
            total_qty_text = self.lineEdit_qte_totale_par_conditionnment_secondRow.text()
            dead_volume_text = self.lineEdit_qte_volume_mor_secondRow.text()
            measurement_tool = self.comboBox_outil_mesure.currentText()

            if not qty_per_test_text or not total_qty_text or not dead_volume_text:
                self.lineEdit_tests_par_conditionnment_secondRow.clear()
                return

            qty_per_test = float(qty_per_test_text)
            total_qty = float(total_qty_text)
            dead_volume = float(dead_volume_text)

            qty_unit = self.comboBox_qte_par_unite_secondRow.currentText()
            total_qty_unit = self.comboBox_unite_qte_totale_par_conditionnement.currentText()
            dead_volume_unit = self.comboBox_unite_volume_mort_secondRow.currentText()

            # Vérification des unités et conversions comme avant...
            all_units = set(VOLUME_UNITS + MASS_UNITS)
            if qty_unit not in all_units or total_qty_unit not in all_units or dead_volume_unit not in all_units:
                self.lineEdit_tests_par_conditionnment_secondRow.setStyleSheet("color: blue;")
                self.lineEdit_tests_par_conditionnment_secondRow.setText("Erreur : unités non valides")
                return

            # Conversion du volume mort si nécessaire
            if dead_volume_unit != total_qty_unit:
                try:
                    dead_volume = self.calculator.convert_value(dead_volume, dead_volume_unit, total_qty_unit)
                except Exception as e:
                    self.lineEdit_tests_par_conditionnment_secondRow.setText(f"Erreur conversion : {e}")
                    return

            # Conversion de la quantité par test si nécessaire
            if qty_unit != total_qty_unit:
                try:
                    qty_per_test = self.calculator.convert_value(qty_per_test, qty_unit, total_qty_unit)
                except Exception as e:
                    self.lineEdit_tests_par_conditionnment_secondRow.setText(f"Erreur conversion : {e}")
                    return

            if qty_per_test == 0:
                self.lineEdit_tests_par_conditionnment_secondRow.setText("Erreur : division par zéro")
                return

            # Calcul différent selon l'outil de mesure
            if measurement_tool == "Automate":
                # Volume mort global (soustrait une seule fois de la quantité totale)
                usable_qty = total_qty - dead_volume
                if usable_qty < 0:
                    self.lineEdit_tests_par_conditionnment_secondRow.setText("Erreur : volume mort > quantité totale")
                    return
                estimated_tests = usable_qty / qty_per_test
            else:
                # Volume mort par test (ajouté à chaque test)
                estimated_tests = total_qty / (qty_per_test + dead_volume)
                dead_volume_total = estimated_tests * dead_volume
                usable_qty = total_qty - dead_volume_total

            self.lineEdit_tests_par_conditionnment_secondRow.setStyleSheet("color: black;")
            self.lineEdit_tests_par_conditionnment_secondRow.setText(
                f"{int(estimated_tests)} tests / {usable_qty:.2f} {total_qty_unit}"
            )
        except ValueError:
            self.lineEdit_tests_par_conditionnment_secondRow.setText("Erreur de calcul : données invalides")
        except Exception as e:
            self.lineEdit_tests_par_conditionnment_secondRow.setText(f"Erreur inattendue : {e}")


    def validate_input(self, input_text: str, field_name: str) -> float | None:
        try:
            value = float(input_text)
            if value < 0:
                raise ValueError(f"{field_name} must be a positive number.")
            return value
        except ValueError as e:
            self.show_error_message(str(e))
            return None

    def add_second_row_widgets(self, groupbox: QGroupBox):
        layout = QVBoxLayout(groupbox)
        layout.setSpacing(7)

        # Première ligne
        h_layout = QHBoxLayout()
        self.lb_qte_par_unite_secondRow = QLabel(groupbox)
        self.lb_qte_par_unite_secondRow.setText("Qte/Unité")
        h_layout.addWidget(self.lb_qte_par_unite_secondRow)

        self.lineEdit_qte_par_unite_secondRow = QLineEdit(groupbox)
        h_layout.addWidget(self.lineEdit_qte_par_unite_secondRow)

        self.comboBox_qte_par_unite_secondRow = QComboBox(groupbox)
        self.comboBox_qte_par_unite_secondRow.addItems(UNITS)
        h_layout.addWidget(self.comboBox_qte_par_unite_secondRow)

        self.lbl_volume_mortsecondRow = QLabel(groupbox)
        self.lbl_volume_mortsecondRow.setText("Volume mort")
        h_layout.addWidget(self.lbl_volume_mortsecondRow)

        self.lineEdit_qte_volume_mor_secondRow = QLineEdit(groupbox)
        h_layout.addWidget(self.lineEdit_qte_volume_mor_secondRow)

        self.comboBox_unite_volume_mort_secondRow = QComboBox(groupbox)
        self.comboBox_unite_volume_mort_secondRow.addItems(UNITS)
        h_layout.addWidget(self.comboBox_unite_volume_mort_secondRow)

        layout.addLayout(h_layout)

        # Ajouter une ligne pour l'outil de mesure
        h_layout_measure_tool = QHBoxLayout()
        
        self.lbl_measure_tool = QLabel(groupbox)
        self.lbl_measure_tool.setText("Outil de Mesure")
        h_layout_measure_tool.addWidget(self.lbl_measure_tool)
        
        self.comboBox_outil_mesure = QComboBox(groupbox)
        self.comboBox_outil_mesure.addItems(["Automate", "Manual"])
        h_layout_measure_tool.addWidget(self.comboBox_outil_mesure)


        layout.addLayout(h_layout_measure_tool)

        # Deuxième ligne
        h_layout2 = QHBoxLayout()
        self.lineEdit_qte_totale_par_conditionnment_secondRow = QLineEdit(groupbox)
        self.lineEdit_qte_totale_par_conditionnment_secondRow.setPlaceholderText("Qte Total/Conditionnment")
        h_layout2.addWidget(self.lineEdit_qte_totale_par_conditionnment_secondRow)

        self.comboBox_unite_qte_totale_par_conditionnement = QComboBox(groupbox)
        self.comboBox_unite_qte_totale_par_conditionnement.addItems(UNITS)
        h_layout2.addWidget(self.comboBox_unite_qte_totale_par_conditionnement)

        self.lineEdit_tests_par_conditionnment_secondRow = QLineEdit(groupbox)
        self.lineEdit_tests_par_conditionnment_secondRow.setPlaceholderText("Tests/Conditionnment")	
        h_layout2.addWidget(self.lineEdit_tests_par_conditionnment_secondRow)

        layout.addLayout(h_layout2)
    def add_third_row_widgets(self, groupbox: QGroupBox):
        layout = QVBoxLayout(groupbox)

        # Première ligne : Quantité de calibration, unité, fréquence, et période
        h_layout = QHBoxLayout()
        self.lbl_qte_calibration_thirdRow = QLabel(groupbox)
        self.lbl_qte_calibration_thirdRow.setText("Qte Calibration")
        h_layout.addWidget(self.lbl_qte_calibration_thirdRow)

        self.lineEdit_qte_calibration_thirdRow = QLineEdit(groupbox)
        h_layout.addWidget(self.lineEdit_qte_calibration_thirdRow)

        self.comboBox_unite_qte_calibration_thirdRow = QComboBox(groupbox)
        self.comboBox_unite_qte_calibration_thirdRow.addItems(UNITS_CAL_CONT_CONFIRM)
        h_layout.addWidget(self.comboBox_unite_qte_calibration_thirdRow)

        self.lbl_frequence_calibration = QLabel(groupbox)
        self.lbl_frequence_calibration.setText("Fréquence")
        h_layout.addWidget(self.lbl_frequence_calibration)

        self.spinBox_frequence_calibration_thirdRow = QSpinBox(groupbox)
        h_layout.addWidget(self.spinBox_frequence_calibration_thirdRow)

        self.lbl_fois_par_thirdRow = QLabel(groupbox)
        self.lbl_fois_par_thirdRow.setText("Fois par")
        h_layout.addWidget(self.lbl_fois_par_thirdRow)

        self.comboBox_fois_par_periode_temp_thirdRow = QComboBox(groupbox)
        self.comboBox_fois_par_periode_temp_thirdRow.addItems(TIME_UNITS)
        h_layout.addWidget(self.comboBox_fois_par_periode_temp_thirdRow)

        h_layout.setStretch(0, 1)
        h_layout.setStretch(1, 3)
        h_layout.setStretch(2, 1)
        layout.addLayout(h_layout)

        # Deuxième ligne : Affichage du nombre de calibrations et du volume total
        h_layout2 = QHBoxLayout()
        self.lbl_total_calibrations = QLabel(groupbox)
        self.lbl_total_calibrations.setText("Nombre de calibrations")
        h_layout2.addWidget(self.lbl_total_calibrations)

        self.lineEdit_total_calibrations = QLineEdit(groupbox)
        self.lineEdit_total_calibrations.setReadOnly(True)  # Champ en lecture seule
        h_layout2.addWidget(self.lineEdit_total_calibrations)

        self.lbl_total_calibration_volume = QLabel(groupbox)
        self.lbl_total_calibration_volume.setText("Volume total de calibration")
        h_layout2.addWidget(self.lbl_total_calibration_volume)

        self.lineEdit_total_calibration_volume = QLineEdit(groupbox)
        self.lineEdit_total_calibration_volume.setReadOnly(True)  # Champ en lecture seule
        h_layout2.addWidget(self.lineEdit_total_calibration_volume)

        self.comboBox_qte_totale_calibration_unite = QComboBox(groupbox)
        self.comboBox_qte_totale_calibration_unite.addItems(UNITS_CAL_CONT_CONFIRM)
        h_layout2.addWidget(self.comboBox_qte_totale_calibration_unite)

        h_layout2.setStretch(1, 2)
        h_layout2.setStretch(3, 2)
        h_layout2.setStretch(4, 1)	
        layout.addLayout(h_layout2)

    def add_fourth_row_widgets(self, groupbox: QGroupBox):
        """
        Ajoute les widgets pour le groupe "Facteurs de Pertes Critiques".
        Organise les widgets en trois lignes :
        - Ligne 1 : Quantité totale par conditionnement.
        - Ligne 2 : Facteurs critiques de pertes.
        - Ligne 3 : Quantité perdue.
        """
        layout = QVBoxLayout(groupbox)

        # Titre du groupe
        groupbox.setTitle("Facteurs de Pertes Critiques")

        # Première ligne : Quantité totale par conditionnement
        h_layout_total_qty = QHBoxLayout()
        self.lbl_total_qty = QLabel("Qte Totale/Conditionnement", groupbox)
        h_layout_total_qty.addWidget(self.lbl_total_qty)

        self.lineEdit_total_qty = QLineEdit(groupbox)
        h_layout_total_qty.addWidget(self.lineEdit_total_qty)

        self.comboBox_total_qty_unit = QComboBox(groupbox)
        self.comboBox_total_qty_unit.addItems(["ml", "mg", "tests"])
        h_layout_total_qty.addWidget(self.comboBox_total_qty_unit)

        layout.addLayout(h_layout_total_qty)

        # Deuxième ligne : Facteurs critiques de pertes
        h_layout_factors = QHBoxLayout()

        # Mauvaise manipulation
        self.lbl_manipulation_loss = QLabel("Pertes par mauvaise manipulation (%)", groupbox)
        h_layout_factors.addWidget(self.lbl_manipulation_loss)

        self.spinBox_manipulation_loss = QSpinBox(groupbox)
        self.spinBox_manipulation_loss.setRange(0, 100)
        h_layout_factors.addWidget(self.spinBox_manipulation_loss)

        # Contamination
        self.lbl_contamination_loss = QLabel("Pertes par contamination (%)", groupbox)
        h_layout_factors.addWidget(self.lbl_contamination_loss)

        self.spinBox_contamination_loss = QSpinBox(groupbox)
        self.spinBox_contamination_loss.setRange(0, 100)
        h_layout_factors.addWidget(self.spinBox_contamination_loss)

        # Dégradation
        self.lbl_degradation_loss = QLabel("Pertes par dégradation (%)", groupbox)
        h_layout_factors.addWidget(self.lbl_degradation_loss)

        self.spinBox_degradation_loss = QSpinBox(groupbox)
        self.spinBox_degradation_loss.setRange(0, 100)
        h_layout_factors.addWidget(self.spinBox_degradation_loss)

        layout.addLayout(h_layout_factors)

        # Troisième ligne : Quantité perdue
        h_layout_loss = QHBoxLayout()
        self.lbl_total_loss = QLabel("Quantité perdue", groupbox)
        h_layout_loss.addWidget(self.lbl_total_loss)

        self.lineEdit_total_loss = QLineEdit(groupbox)
        self.lineEdit_total_loss.setReadOnly(True)
        h_layout_loss.addWidget(self.lineEdit_total_loss)

        self.comboBox_loss_unit = QComboBox(groupbox)
        self.comboBox_loss_unit.addItems(["ml", "mg", "tests"])
        h_layout_loss.addWidget(self.comboBox_loss_unit)

        layout.addLayout(h_layout_loss)

        # Connexions pour recalculer la quantité perdue
        self.lineEdit_total_qty.textChanged.connect(self.calculate_total_loss)
        self.spinBox_manipulation_loss.valueChanged.connect(self.calculate_total_loss)
        self.spinBox_contamination_loss.valueChanged.connect(self.calculate_total_loss)
        self.spinBox_degradation_loss.valueChanged.connect(self.calculate_total_loss)
        self.comboBox_total_qty_unit.currentTextChanged.connect(self.calculate_total_loss)
        self.comboBox_loss_unit.currentTextChanged.connect(self.calculate_total_loss)


    def add_fifth_row_widgets(self, groupbox: QGroupBox):
        layout = QVBoxLayout(groupbox)

        # Première ligne : Quantité perdue et pourcentage
        h_layout = QHBoxLayout()
        self.lbl_qte_confirmation_fiveRow = QLabel(groupbox)
        self.lbl_qte_confirmation_fiveRow.setText("Qte Perdue")
        h_layout.addWidget(self.lbl_qte_confirmation_fiveRow)

        self.lineEdit_qte_test_refais_confirmation_fiveRow = QLineEdit(groupbox)
        h_layout.addWidget(self.lineEdit_qte_test_refais_confirmation_fiveRow)

        self.comboBox_unite_qte_test_refais_confirmation_fiveRow = QComboBox(groupbox)
        self.comboBox_unite_qte_test_refais_confirmation_fiveRow.addItems(["ml", "L", "mg", "g", "kg", "µl", "test"])
        h_layout.addWidget(self.comboBox_unite_qte_test_refais_confirmation_fiveRow)

        self.lbl_percent_tests_repete_fiveRow = QLabel(groupbox)
        self.lbl_percent_tests_repete_fiveRow.setText("Pourcentage")
        h_layout.addWidget(self.lbl_percent_tests_repete_fiveRow)

        self.spinBox_percent_confirmation_test_repete = QSpinBox(groupbox)
        self.spinBox_percent_confirmation_test_repete.setMaximum(100)
        h_layout.addWidget(self.spinBox_percent_confirmation_test_repete)

        h_layout.setStretch(0, 1)
        h_layout.setStretch(1, 3)
        h_layout.setStretch(2, 1)
        layout.addLayout(h_layout)

        # Deuxième ligne : Quantité totale perdue
        h_layout2 = QHBoxLayout()
        self.lbl_qte_total_confirmation_fiveRow = QLabel(groupbox)
        self.lbl_qte_total_confirmation_fiveRow.setText("Qte Totale Perdue")
        h_layout2.addWidget(self.lbl_qte_total_confirmation_fiveRow)

        self.lineEdit_qte_total_confirmation_fiveRow = QLineEdit(groupbox)
        self.lineEdit_qte_total_confirmation_fiveRow.setReadOnly(True)  # Lecture seule
        h_layout2.addWidget(self.lineEdit_qte_total_confirmation_fiveRow)

        self.comboBox_unite_qte_totale_confirmation_fiveRow = QComboBox(groupbox)
        self.comboBox_unite_qte_totale_confirmation_fiveRow.addItems(["ml", "L", "mg", "g", "kg", "µl", "test"])
        h_layout2.addWidget(self.comboBox_unite_qte_totale_confirmation_fiveRow)

        h_layout2.setStretch(0, 0)
        h_layout2.setStretch(1, 2)
        h_layout2.setStretch(2, 1)
        layout.addLayout(h_layout2)

        # Suppression de la ligne de dilution ici

    def show_error_message(self, message):
        """Affiche un message d'erreur dans une boîte de dialogue."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Erreur")
        msg.setInformativeText(message)
        msg.setWindowTitle("Erreur")
        msg.exec_()

    def add_sixth_row_widgets(self, groupbox):
        layout = QVBoxLayout(groupbox)
        
        # Première ligne
        h_layout = QHBoxLayout()
        self.lbl_jours_analyse_sixRow = QLabel(groupbox)
        self.lbl_jours_analyse_sixRow.setText("Analyse")
        h_layout.addWidget(self.lbl_jours_analyse_sixRow)
        
        # Création et configuration de la QComboBox
        self.comboBox_analyse_sixRow = QComboBox(groupbox)
        self.comboBox_analyse_sixRow.addItems(analyse_liste)
        self.comboBox_analyse_sixRow.setEditable(True)  # Correction : rendre la QComboBox éditable
        
        # Ajouter un QCompleter pour le filtrage dynamique
        completer = QCompleter(analyse_liste, self.comboBox_analyse_sixRow)
        completer.setCaseSensitivity(Qt.CaseInsensitive)  # Ignorer la casse
        completer.setFilterMode(Qt.MatchContains)  # Filtrer en fonction du texte saisi
        self.comboBox_analyse_sixRow.setCompleter(completer)
        
        h_layout.addWidget(self.comboBox_analyse_sixRow)
        
        self.lbl_jours_livraison_sixRow = QLabel(groupbox)
        self.lbl_jours_livraison_sixRow.setText("D.Livraison")
        h_layout.addWidget(self.lbl_jours_livraison_sixRow)
        self.lineEdit_jours_livraison_sixRow = QLineEdit(groupbox)
        h_layout.addWidget(self.lineEdit_jours_livraison_sixRow)
        self.comboBox_unite_date_livraison_sixRow = QComboBox(groupbox)
        self.comboBox_unite_date_livraison_sixRow.addItems(TIME_UNITS)
        h_layout.addWidget(self.comboBox_unite_date_livraison_sixRow)
        
        self.lbl_stock_actuel_sixRow = QLabel(groupbox)
        self.lbl_stock_actuel_sixRow.setText("Stock Actuel")
        h_layout.addWidget(self.lbl_stock_actuel_sixRow)
        self.lineEdit_nbr_test_stock_actuel_sixRow = QLineEdit(groupbox)
        h_layout.addWidget(self.lineEdit_nbr_test_stock_actuel_sixRow)
        self.comboBox_unite_stoc_test_sixRow = QComboBox(groupbox)
        self.comboBox_unite_stoc_test_sixRow.addItems(UNITS)
        h_layout.addWidget(self.comboBox_unite_stoc_test_sixRow)
        
        h_layout.setStretch(1, 2)
        layout.addLayout(h_layout)
        
        # Deuxième ligne
        h_layout2 = QHBoxLayout()
        self.lbl_cm_ajustee_sixRow = QLabel(groupbox)
        self.lbl_cm_ajustee_sixRow.setText("CM ajustée")
        h_layout2.addWidget(self.lbl_cm_ajustee_sixRow)
        self.lineEdit_qte_cm_ajustee_sixRow = QLineEdit(groupbox)
        h_layout2.addWidget(self.lineEdit_qte_cm_ajustee_sixRow)
        self.comboBo_unite_cm_ajustee_sixRow = QComboBox(groupbox)
        self.comboBo_unite_cm_ajustee_sixRow.addItems(UNITS)
        h_layout2.addWidget(self.comboBo_unite_cm_ajustee_sixRow)
        
        self.horizontalSpacer_3 = QSpacerItem(34, 21, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        h_layout2.addItem(self.horizontalSpacer_3)
        
        self.lbl_qte_a_commander_sixRow = QLabel(groupbox)
        self.lbl_qte_a_commander_sixRow.setText("Q.A.C")
        h_layout2.addWidget(self.lbl_qte_a_commander_sixRow)
        self.lineEdit_qte_a_commander_sixRow = QLineEdit(groupbox)
        h_layout2.addWidget(self.lineEdit_qte_a_commander_sixRow)
        self.comboBox_unite_qt_a_commander_sixRow = QComboBox(groupbox)
        self.comboBox_unite_qt_a_commander_sixRow.addItems(UNITS)
        h_layout2.addWidget(self.comboBox_unite_qt_a_commander_sixRow)
        
        layout.addLayout(h_layout2)


    # def load_stylesheet(self, MainWindow):
    #     try:
    #         style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
    #         with open(style_path, "r", encoding="utf-8") as f:
    #             MainWindow.setStyleSheet(f.read())
    #     except FileNotFoundError:
    #         self.show_error_message("Erreur : fichier 'style.qss' introuvable.")

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.cancel_button.setText(QCoreApplication.translate("MainWindow", "Annuler", None))
        self.calculate_button.setText(QCoreApplication.translate("MainWindow", "Calculer", None))

    def calculate_total_loss(self):
        """
        Calcule la quantité perdue en fonction des pourcentages des facteurs critiques.
        Affiche la quantité perdue dans l'unité choisie.
        """
        try:
            # Récupérer la quantité totale par conditionnement
            total_qty_text = self.lineEdit_total_qty.text()
            if not total_qty_text:
                self.lineEdit_total_loss.clear()
                return

            total_qty = float(total_qty_text)
            total_qty_unit = self.comboBox_total_qty_unit.currentText()

            # Récupérer les pourcentages des facteurs critiques
            manipulation_loss_percent = self.spinBox_manipulation_loss.value() / 100
            contamination_loss_percent = self.spinBox_contamination_loss.value() / 100
            degradation_loss_percent = self.spinBox_degradation_loss.value() / 100

            # Calculer la quantité totale perdue
            total_loss_percent = manipulation_loss_percent + contamination_loss_percent + degradation_loss_percent
            total_loss_value = total_qty * total_loss_percent

            # Convertir dans l'unité choisie
            target_unit = self.comboBox_loss_unit.currentText()
            if total_qty_unit != target_unit:
                try:
                    total_loss_value = self.calculator.convert_value(total_loss_value, total_qty_unit, target_unit)
                except ValueError:
                    self.show_error_message(f"Conversion impossible entre {total_qty_unit} et {target_unit}")
                    return

            # Afficher la quantité totale perdue
            self.lineEdit_total_loss.setText(f"{total_loss_value:.2f} {target_unit}")

        except ValueError as e:
            self.show_error_message(f"Erreur de calcul : {e}")
            self.lineEdit_total_loss.clear()

    def on_physical_unit_changed(self, unit):
        """Gère le changement d'unité dans le combobox des unités physiques"""
        old_unit = self.comboBox_unite_physique_firstRow.currentText()
        # Récupérer la valeur actuelle avant la conversion
        current_value_text = self.lineEdit_qte_par_unite_de_test_firstRow.text()
        if unit in ["test", "pcs"]:
            # Pour test/pcs, qty_per_test = 1 et lecture seule
            self.lineEdit_qte_par_unite_de_test_firstRow.setText("1")
            self.lineEdit_qte_par_unite_de_test_firstRow.setReadOnly(True)
        elif unit in ["boîte", "kit", "sachet", "flacon", "tube", "coffret"]:
            # Pour les unités conditionnées, demander le nombre de tests par unité
            placeholder = f"Nombre de tests par {unit}"
            self.lineEdit_qte_par_unite_de_test_firstRow.setPlaceholderText(placeholder)
            self.lineEdit_qte_par_unite_de_test_firstRow.clear()
            self.lineEdit_qte_par_unite_de_test_firstRow.setReadOnly(False)
            # Synchroniser les deux combobox
            self.comboBox_unite_consommation_par_unite_de_temps.setCurrentText(unit)
        else:
            # Pour les unités massiques/volumiques
            if current_value_text and current_value_text.replace('.', '').isdigit():
                try:
                    current_value = float(current_value_text)
                    # Convertir la valeur si l'ancienne unité était aussi massique/volumique
                    if old_unit in VOLUME_UNITS + MASS_UNITS:
                        try:
                            converted_value = self.calculator.convert_value(current_value, old_unit, unit)
                            self.lineEdit_qte_par_unite_de_test_firstRow.setText(f"{converted_value:.2f}")
                        except ValueError:
                            self.lineEdit_qte_par_unite_de_test_firstRow.clear()
                except ValueError:
                    self.lineEdit_qte_par_unite_de_test_firstRow.clear()
            self.lineEdit_qte_par_unite_de_test_firstRow.setPlaceholderText("")
            self.lineEdit_qte_par_unite_de_test_firstRow.setReadOnly(False)
            # Mettre à jour la consommation avec les nouvelles unités
            self.update_consumption()

    def on_consumption_unit_changed(self, new_unit):
        """
        Gère le changement d'unité dans le combobox de consommation.
        Met à jour les champs en fonction du type d'unité sélectionné.
        """
        # Vérifier si l'unité sélectionnée est un contenant (tube, flacon)
        if new_unit in ["tube", "flacon"]:
            # Ouvrir un dialogue pour saisir les paramètres spécifiques aux contenants
            dialog_result = self.open_container_dialog(new_unit)
            if dialog_result:
                qty_per_test, total_qty, unit = dialog_result

                # Mettre à jour les champs correspondants
                self.comboBox_unite_qte_totale_conditionnement_firstRow.setCurrentText(unit)  # Unité totale
                self.lineEdit_qte_totale_conditionnement_firstRow.setText(str(total_qty))  # Quantité totale
                self.lineEdit_qte_par_unite_de_test_firstRow.setText(str(qty_per_test))  # Quantité par test
                self.comboBox_unite_physique_firstRow.setCurrentText(unit)  # Unité physique
                self.comboBox_unite_consommation_par_unite_de_temps.setCurrentText(unit)  # Unité de consommation

                # Recalculer la consommation
                self.update_consumption()

        # Vérifier si l'unité sélectionnée est un conditionnement (boîte, coffret, sachet, kit)
        elif new_unit in ["boîte", "coffret", "sachet", "kit"]:
            # Ouvrir un dialogue pour saisir le nombre total de tests
            dialog_result = self.open_packaging_dialog(new_unit)
            if dialog_result:
                total_tests = dialog_result

                # Mettre à jour les champs correspondants
                self.comboBox_unite_consommation_par_unite_de_temps.setCurrentText("test")  # Unité de consommation
                self.comboBox_unite_qte_totale_conditionnement_firstRow.setCurrentText("test")  # Unité totale
                self.lineEdit_qte_par_unite_de_test_firstRow.setText("1")  # Quantité par test
                self.comboBox_unite_physique_firstRow.setCurrentText("test")  # Unité physique
                self.lineEdit_qte_totale_conditionnement_firstRow.setText(str(total_tests))  # Nombre total de tests

                # Recalculer la consommation
                self.update_consumption()
                
    def open_container_dialog(self, unit):
        """
        Ouvre un dialogue pour saisir les paramètres spécifiques aux contenants.
        Retourne une tuple (qty_per_test, total_qty, unit).
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Paramètres pour {unit}")
        layout = QVBoxLayout(dialog)

        # Créer les champs pour la quantité par test et le volume total
        qty_per_test_layout = QHBoxLayout()
        lbl_qty_per_test = QLabel("Quantité par test:")
        self.lineEdit_qty_per_test = QLineEdit()
        self.comboBox_qty_per_test_unit = QComboBox()
        self.comboBox_qty_per_test_unit.addItems(["ml", "L", "µl", "mg", "g", "kg"])
        qty_per_test_layout.addWidget(lbl_qty_per_test)
        qty_per_test_layout.addWidget(self.lineEdit_qty_per_test)
        qty_per_test_layout.addWidget(self.comboBox_qty_per_test_unit)
        layout.addLayout(qty_per_test_layout)

        total_qty_layout = QHBoxLayout()
        lbl_total_qty = QLabel(f"Volume ou masse totale du {unit}:")
        self.lineEdit_total_qty = QLineEdit()
        self.comboBox_total_qty_unit = QComboBox()
        self.comboBox_total_qty_unit.addItems(["ml", "L", "µl", "mg", "g", "kg"])
        total_qty_layout.addWidget(lbl_total_qty)
        total_qty_layout.addWidget(self.lineEdit_total_qty)
        total_qty_layout.addWidget(self.comboBox_total_qty_unit)
        layout.addLayout(total_qty_layout)

        # Bouton Valider
        btn_validate = QPushButton("Valider")
        btn_validate.clicked.connect(dialog.accept)
        layout.addWidget(btn_validate)

        # Afficher le dialogue
        if dialog.exec_() == QDialog.Accepted:
            try:
                qty_per_test = float(self.lineEdit_qty_per_test.text())
                total_qty = float(self.lineEdit_total_qty.text())
                unit = self.comboBox_total_qty_unit.currentText()
                return qty_per_test, total_qty, unit
            except ValueError:
                self.show_error_message("Veuillez saisir des valeurs numériques valides.")
        return None
    
    def open_packaging_dialog(self, unit):
        """
        Ouvre un dialogue pour saisir le nombre total de tests pour les conditionnements.
        Retourne le nombre total de tests.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Paramètres pour {unit}")
        layout = QVBoxLayout(dialog)

        # Champ pour le nombre total de tests
        lbl_total_tests = QLabel(f"Nombre total de tests par {unit}:")
        self.lineEdit_total_tests = QLineEdit()
        layout.addWidget(lbl_total_tests)
        layout.addWidget(self.lineEdit_total_tests)

        # Bouton Valider
        btn_validate = QPushButton("Valider")
        btn_validate.clicked.connect(dialog.accept)
        layout.addWidget(btn_validate)

        # Afficher le dialogue
        if dialog.exec_() == QDialog.Accepted:
            try:
                total_tests = int(self.lineEdit_total_tests.text())
                return total_tests
            except ValueError:
                self.show_error_message("Veuillez saisir un nombre entier valide.")
        return None
    
    def update_consumption(self):
        """
        Met à jour le champ lineEdit_consommation_par_unite_de_temps_firstRow avec le résultat du calcul.
        Affiche la consommation au format spécifié (ex: 2 flacons/20 jours ou 3.5 tubes/20 jours).
        """
        try:
            # Récupérer les paramètres nécessaires
            nbr_tests = float(self.lineEdit_nbrs_test_firstRow.text() or "0")
            time_value = self.number_time_spinBox_firstRow.value()
            time_unit = self.comboBox_periode_temps_firstRow.currentText()
            qty_per_test = float(self.lineEdit_qte_par_unite_de_test_firstRow.text() or "0")
            total_qty = float(self.lineEdit_qte_totale_conditionnement_firstRow.text() or "0")
            consumption_unit = self.comboBox_unite_consommation_par_unite_de_temps.currentText()

            # Calculer la consommation
            if consumption_unit in ["tube", "flacon"]:
                # Pour les contenants
                if qty_per_test > 0 and total_qty > 0:
                    nbr_containers = (nbr_tests * qty_per_test) / total_qty
                    result = f"{nbr_containers:.2f} {consumption_unit}/{time_value} {time_unit}"
                else:
                    result = "Erreur : Quantité par test et volume total doivent être supérieurs à zéro."
            elif consumption_unit in ["boîte", "coffret", "sachet", "kit"]:
                # Pour les conditionnements
                if total_qty > 0:
                    nbr_packagings = nbr_tests / total_qty
                    result = f"{nbr_packagings:.2f} {consumption_unit}/{time_value} {time_unit}"
                else:
                    result = "Erreur : Le nombre total de tests doit être supérieur à zéro."
            else:
                # Pour les autres unités
                consumption = nbr_tests * qty_per_test
                target_unit = self.comboBox_unite_consommation_par_unite_de_temps.currentText()
                if target_unit != consumption_unit and target_unit in VOLUME_UNITS + MASS_UNITS:
                    try:
                        consumption = self.calculator.convert_value(consumption, consumption_unit, target_unit)
                    except ValueError:
                        self.show_error_message("Erreur de conversion")
                        return
                result = f"{consumption:.2f} {target_unit}/{time_value} {time_unit}"

            # Afficher le résultat
            self.lineEdit_consommation_par_unite_de_temps_firstRow.setText(result)
        except ValueError:
            self.lineEdit_consommation_par_unite_de_temps_firstRow.clear()    
    def update_packaging_fields(self, unit, dialog, is_container=False):
        """
        Met à jour les champs après la saisie dans le QDialog.
        Lance un thread pour effectuer les calculs de manière asynchrone.
        """
        try:
            # Récupérer les valeurs saisies
            if is_container:
                qty_per_test = float(self.lineEdit_qty_per_test.text())
            else:
                qty_per_test = 1  # Par défaut, 1 test par unité pour les unités conditionnées
            total_qty = float(self.lineEdit_total_qty.text())

            # Récupérer le nombre de tests et la période de temps
            nbr_tests = float(self.lineEdit_nbrs_test_firstRow.text() or "0")
            time_value = self.number_time_spinBox_firstRow.value()
            time_unit = self.comboBox_periode_temps_firstRow.currentText()

            # Créer et lancer le thread
            self.worker = PackagingWorker(nbr_tests, qty_per_test, total_qty, unit, time_value, time_unit, is_container)
            self.worker.calculation_finished.connect(self.update_consumption_field)
            self.worker.start()

            # Fermer le QDialog
            dialog.close()

        except ValueError:
            self.show_error_message("Veuillez saisir des valeurs numériques valides.")

    def update_consumption_field(self, result):
        """
        Met à jour le champ lineEdit_consommation_par_unite_de_temps_firstRow avec le résultat du calcul.
        """
        self.lineEdit_consommation_par_unite_de_temps_firstRow.setText(result)

    def open_unified_dialog(self, unit):
        """
        Ouvre un QDialog unifié pour saisir les paramètres nécessaires.
        Affiche ou masque les widgets en fonction du type d'unité.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Paramètres pour {unit}")
        dialog.resize(600, 300)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # GroupBox pour les paramètres
        groupbox = QGroupBox(f"Paramètres pour {unit}", dialog)
        groupbox_layout = QVBoxLayout(groupbox)

        # Champ pour la quantité par test (uniquement pour les contenants)
        self.lineEdit_qty_per_test = QLineEdit(groupbox)
        self.lineEdit_qty_per_test.setPlaceholderText("Ex: 10")
        self.comboBox_qty_per_test_unit = QComboBox(groupbox)
        self.comboBox_qty_per_test_unit.addItems(["ml", "L", "µl", "mg", "g", "kg"])

        # Champ pour le volume ou la masse totale (uniquement pour les contenants)
        self.lineEdit_total_qty = QLineEdit(groupbox)
        self.lineEdit_total_qty.setPlaceholderText("Ex: 100")
        self.comboBox_total_qty_unit = QComboBox(groupbox)
        self.comboBox_total_qty_unit.addItems(["ml", "L", "µl", "mg", "g", "kg"])

        # Champ pour le nombre total de tests (uniquement pour les unités conditionnées)
        self.lineEdit_total_tests = QLineEdit(groupbox)
        self.lineEdit_total_tests.setPlaceholderText("Ex: 100")

        # Masquer ou afficher les widgets en fonction du type d'unité
        if unit in ["flacon", "tube", "bouteille"]:
            # Afficher les champs pour les contenants
            h_layout_qty_per_test = QHBoxLayout()
            lbl_qty_per_test = QLabel("Quantité par test:", groupbox)
            h_layout_qty_per_test.addWidget(lbl_qty_per_test)
            h_layout_qty_per_test.addWidget(self.lineEdit_qty_per_test)
            h_layout_qty_per_test.addWidget(self.comboBox_qty_per_test_unit)
            groupbox_layout.addLayout(h_layout_qty_per_test)

            h_layout_total_qty = QHBoxLayout()
            lbl_total_qty = QLabel(f"Volume ou masse totale du {unit}:", groupbox)
            h_layout_total_qty.addWidget(lbl_total_qty)
            h_layout_total_qty.addWidget(self.lineEdit_total_qty)
            h_layout_total_qty.addWidget(self.comboBox_total_qty_unit)
            groupbox_layout.addLayout(h_layout_total_qty)

            # Masquer le champ pour les unités conditionnées
            self.lineEdit_total_tests.setVisible(False)
        else:
            # Afficher le champ pour les unités conditionnées
            h_layout_total_tests = QHBoxLayout()
            lbl_total_tests = QLabel(f"Nombre total de tests par {unit}:", groupbox)
            h_layout_total_tests.addWidget(lbl_total_tests)
            h_layout_total_tests.addWidget(self.lineEdit_total_tests)
            groupbox_layout.addLayout(h_layout_total_tests)

            # Masquer les champs pour les contenants
            self.lineEdit_qty_per_test.setVisible(False)
            self.comboBox_qty_per_test_unit.setVisible(False)
            self.lineEdit_total_qty.setVisible(False)
            self.comboBox_total_qty_unit.setVisible(False)

        # Ajouter le GroupBox au layout principal
        layout.addWidget(groupbox)

        # Bouton pour valider
        btn_validate = QPushButton("Valider", dialog)
        btn_validate.clicked.connect(lambda: self.update_unified_fields(unit, dialog))
        layout.addWidget(btn_validate)

        dialog.exec_()

    def update_unified_fields(self, unit, dialog):
        """
        Met à jour les champs après la saisie dans le QDialog unifié.
        Effectue les calculs nécessaires et met à jour les champs en conséquence.
        """
        try:
            if unit in ["flacon", "tube", "bouteille"]:
                # Récupérer les valeurs saisies pour les contenants
                qty_per_test = float(self.lineEdit_qty_per_test.text())
                qty_per_test_unit = self.comboBox_qty_per_test_unit.currentText()
                total_qty = float(self.lineEdit_total_qty.text())
                total_qty_unit = self.comboBox_total_qty_unit.currentText()

                # Vérifier que les valeurs sont valides
                if qty_per_test <= 0 or total_qty <= 0:
                    self.show_error_message("Les valeurs saisies doivent être supérieures à zéro.")
                    return

                # Mettre à jour les champs lineEdit_qte_par_unite_de_test_firstRow et comboBox_unite_physique_firstRow
                self.lineEdit_qte_par_unite_de_test_firstRow.setText(str(qty_per_test))
                self.comboBox_unite_physique_firstRow.setCurrentText(qty_per_test_unit)
                self.lineEdit_qte_totale_conditionnement_firstRow.setText(str(total_qty))
                self.comboBox_unite_qte_totale_conditionnement_firstRow.setCurrentText(total_qty_unit)
                self.comboBox_unite_consommation_par_unite_de_temps.setCurrentText(total_qty_unit)

                # Récupérer le nombre de tests et la période de temps
                nbr_tests = float(self.lineEdit_nbrs_test_firstRow.text() or "0")
                time_value = self.number_time_spinBox_firstRow.value()
                time_unit = self.comboBox_periode_temps_firstRow.currentText()

                # Convertir la quantité par test et le volume total dans la même unité
                if qty_per_test_unit != total_qty_unit:
                    if not self.calculator.are_units_compatible(qty_per_test_unit, total_qty_unit):
                        self.show_error_message(f"Conversion impossible entre {qty_per_test_unit} et {total_qty_unit}.")
                        return

                    try:
                        qty_per_test = self.calculator.convert_value(qty_per_test, qty_per_test_unit, total_qty_unit)
                    except ValueError as e:
                        self.show_error_message(f"Erreur de conversion : {e}")
                        return

                # Calculer le nombre de contenants nécessaires
                if total_qty > 0:
                    nbr_containers = (nbr_tests * qty_per_test) / total_qty
                    result = f"{nbr_containers:.2f} {unit}/{time_value} {time_unit}"
                else:
                    self.show_error_message("Le volume ou la masse totale doit être supérieur à zéro.")
                    return

            else:
                # Récupérer les valeurs saisies pour les unités conditionnées
                total_tests = float(self.lineEdit_total_tests.text())

                # Vérifier que la valeur est valide
                if total_tests <= 0:
                    self.show_error_message("Le nombre total de tests par packaging doit être supérieur à zéro.")
                    return

                # Mettre à jour les champs
                self.lineEdit_qte_par_unite_de_test_firstRow.setText("1")  # 1 test par unité
                self.comboBox_unite_physique_firstRow.setCurrentText("test")
                self.lineEdit_qte_totale_conditionnement_firstRow.setText(str(total_tests))
                self.comboBox_unite_consommation_par_unite_de_temps.setCurrentText("test")

                # Récupérer le nombre de tests et la période de temps
                nbr_tests = float(self.lineEdit_nbrs_test_firstRow.text() or "0")
                time_value = self.number_time_spinBox_firstRow.value()
                time_unit = self.comboBox_periode_temps_firstRow.currentText()

                # Calculer le nombre de packagings nécessaires
                if total_tests > 0:
                    nbr_packagings = nbr_tests / total_tests
                    result = f"{nbr_packagings:.2f} {unit}/{time_value} {time_unit}"
                else:
                    self.show_error_message("Le nombre total de tests par packaging doit être supérieur à zéro.")
                    return

            # Mettre à jour le champ lineEdit_consommation_par_unite_de_temps_firstRow
            self.lineEdit_consommation_par_unite_de_temps_firstRow.setText(result)

            # Fermer le QDialog
            dialog.close()

        except ValueError:
            self.show_error_message("Veuillez saisir des valeurs numériques valides.")
        except ZeroDivisionError:
            self.show_error_message("Erreur : division par zéro.")
        except Exception as e:
            self.show_error_message(f"Une erreur inattendue s'est produite : {e}")

    def update_calibration(self):
        """Calcule et met à jour le nombre de calibrations et le volume total de calibration"""
        try:
            # Récupérer les paramètres de calibration
            calibration_frequency = self.spinBox_frequence_calibration_thirdRow.value()
            calibration_period = self.comboBox_fois_par_periode_temp_thirdRow.currentText()
            calibration_volume_text = self.lineEdit_qte_calibration_thirdRow.text()
            calibration_unit = self.comboBox_unite_qte_calibration_thirdRow.currentText()

            if not calibration_volume_text:
                return

            calibration_volume = float(calibration_volume_text)

            # Récupérer les paramètres de temps
            time_value = self.number_time_spinBox_firstRow.value()
            time_unit = self.comboBox_periode_temps_firstRow.currentText()

            # Convertir la période de temps en jours
            time_factors = {
                'Jours': 1,
                'Semaine': 7,
                'Mois': 30
            }
            total_days = time_value * time_factors.get(time_unit, 1)
            calibration_days_per_period = time_factors.get(calibration_period, 1)

            # Calculer le nombre total de calibrations
            if calibration_period == 'Jours':
                total_calibrations = (total_days // calibration_frequency) if calibration_frequency > 0 else 0
            else:
                periods = total_days / calibration_days_per_period
                total_calibrations = periods * calibration_frequency

            # Calculer le volume total de calibration dans l'unité originale
            total_volume = total_calibrations * calibration_volume

            # Convertir dans l'unité d'affichage si nécessaire
            display_unit = self.comboBox_qte_totale_calibration_unite.currentText()
            if calibration_unit != display_unit:
                try:
                    total_volume = self.calculator.convert_value(total_volume, calibration_unit, display_unit)
                except ValueError:
                    self.show_error_message(f"Erreur de conversion de {calibration_unit} vers {display_unit}")
                    return

            # Afficher les résultats
            self.lineEdit_total_calibrations.setText(f"{int(total_calibrations)}")
            self.lineEdit_total_calibration_volume.setText(f"{total_volume:.2f} {display_unit}")

        except ValueError as e:
            self.show_error_message(f"Erreur de calcul : {e}")
            self.lineEdit_total_calibrations.clear()
            self.lineEdit_total_calibration_volume.clear()

    def on_calibration_unit_changed(self, new_unit):
        """Gère le changement d'unité dans le combobox de calibration"""
        # Récupérer la valeur initiale et son unité
        initial_text = self.lineEdit_total_calibration_volume.text()
        # Si le champ est vide, rien à faire
        if not initial_text:
            return

        try:
            # Extraire la valeur et l'unité initiale
            initial_value = float(initial_text.split()[0])
            initial_unit = initial_text.split()[1]

            # Si les unités sont compatibles, faire la conversion
            if initial_unit in VOLUME_UNITS + MASS_UNITS and new_unit in VOLUME_UNITS + MASS_UNITS:
                # Convertir la valeur
                converted_value = self.calculator.convert_value(initial_value, initial_unit, new_unit)
                # Mettre à jour l'affichage
                self.lineEdit_total_calibration_volume.setText(f"{converted_value:.2f} {new_unit}")

        except (ValueError, IndexError):
            self.show_error_message("Erreur lors de la conversion")

    def on_total_calibration_unit_changed(self, new_unit):
        """Gère le changement d'unité dans le combobox de l'unité de calibration totale"""
        # Récupérer l'ancienne unité
        old_unit = self.comboBox_qte_totale_calibration_unite.currentText()

        # Récupérer la valeur actuelle du volume total de calibration
        total_calibration_volume_text = self.lineEdit_total_calibration_volume.text()

        if total_calibration_volume_text:
            try:
                # Extraire la valeur numérique du volume total
                total_calibration_volume = float(total_calibration_volume_text.split()[0])

                # Convertir la valeur dans la nouvelle unité si nécessaire
                if old_unit in VOLUME_UNITS + MASS_UNITS and new_unit in VOLUME_UNITS + MASS_UNITS:
                    try:
                        # Convertir la valeur en utilisant la méthode du calculateur
                        converted_volume = self.calculator.convert_value(total_calibration_volume, old_unit, new_unit)
                        # Mettre à jour l'affichage avec la nouvelle valeur et unité
                        self.lineEdit_total_calibration_volume.setText(f"{converted_volume:.2f} {new_unit}")
                    except ValueError as e:
                        self.show_error_message(f"Erreur de conversion : {e}")
                        # En cas d'erreur, conserver l'ancienne unité et la valeur actuelle
                        self.comboBox_qte_totale_calibration_unite.setCurrentText(old_unit)
                        self.lineEdit_total_calibration_volume.setText(f"{total_calibration_volume:.2f} {old_unit}")
                else:
                    # Si les unités ne sont pas compatibles, conserver l'ancienne unité et la valeur actuelle
                    self.show_error_message("Conversion impossible entre ces unités")
                    self.comboBox_qte_totale_calibration_unite.setCurrentText(old_unit)
                    self.lineEdit_total_calibration_volume.setText(f"{total_calibration_volume:.2f} {old_unit}")

            except ValueError:
                # En cas d'erreur de format, conserver l'ancienne unité et la valeur actuelle
                self.show_error_message("Erreur de format lors de l'extraction de la valeur")
                self.comboBox_qte_totale_calibration_unite.setCurrentText(old_unit)
                self.lineEdit_total_calibration_volume.setText(total_calibration_volume_text)


    def update_confirmation(self):
        """Calcule et met à jour la quantité totale de tests perdus lors de la confirmation"""
        try:
            # Récupérer les paramètres de la confirmation
            nbr_tests_text = self.lineEdit_nbrs_test_firstRow.text()
            time_value = self.number_time_spinBox_firstRow.value()
            time_unit = self.comboBox_periode_temps_firstRow.currentText()
            confirmation_percentage = self.spinBox_percent_confirmation_test_repete.value()
            qty_per_test_text = self.lineEdit_qte_test_refais_confirmation_fiveRow.text()
            qty_unit = self.comboBox_unite_qte_test_refais_confirmation_fiveRow.currentText()
            display_unit = self.comboBox_unite_qte_totale_confirmation_fiveRow.currentText()

            # Vérifier si les champs sont vides
            if not nbr_tests_text or not qty_per_test_text:
                self.lineEdit_qte_total_confirmation_fiveRow.clear()
                return

            # Convertir les valeurs en float
            nbr_tests = float(nbr_tests_text)
            qty_per_test = float(qty_per_test_text)

            # Calculer la quantité totale de tests perdus
            total_lost_volume = self.calculator.calculate_confirmation_loss(
                nbr_tests, time_value, time_unit, confirmation_percentage, qty_per_test, qty_unit, display_unit
            )

            if total_lost_volume is not None:
                # Afficher le résultat
                self.lineEdit_qte_total_confirmation_fiveRow.setText(f"{total_lost_volume:.2f} {display_unit}")
            else:
                self.lineEdit_qte_total_confirmation_fiveRow.clear()

        except ValueError as e:
            self.show_error_message(f"Erreur de calcul : {e}")
            self.lineEdit_qte_total_confirmation_fiveRow.clear()

    def calculate_all(self):
        """Méthode pour le bouton Calculer"""
        try:
            # Récupérer l'unité choisie dans comboBox_unite_qt_a_commander_sixRow
            target_unit = self.comboBox_unite_qt_a_commander_sixRow.currentText()

            # Extraction de la consommation par unité de temps
            consommation_text = self.lineEdit_consommation_par_unite_de_temps_firstRow.text()
            if not consommation_text:
                self.show_error_message("Veuillez calculer la consommation d'abord.")
                return

            # Extraire la valeur numérique (10.00) et l'unité (ml) en ignorant la partie temporelle
            consommation_value = float(consommation_text.split()[0])  # Extraire la valeur numérique
            consommation_unit = consommation_text.split()[1].split('/')[0]  # Extraire "ml" de "ml/10 jours"

            # Extraction du volume total de calibration
            calibration_volume_text = self.lineEdit_total_calibration_volume.text()
            if not calibration_volume_text:
                self.show_error_message("Veuillez calculer le volume total de calibration d'abord.")
                return
            calibration_volume_value = float(calibration_volume_text.split()[0])
            calibration_unit = calibration_volume_text.split()[1]

            # Extraction du volume total utilisé pour les contrôles
            controle_volume_text = self.lineEdit_qte_total_controle_fourthRow.text()
            if not controle_volume_text:
                self.show_error_message("Veuillez calculer le volume total utilisé pour les contrôles d'abord.")
                return
            controle_volume_value = float(controle_volume_text.split()[0])
            controle_unit = controle_volume_text.split()[1]

            # Extraction du volume total perdu lors de la confirmation
            confirmation_volume_text = self.lineEdit_qte_total_confirmation_fiveRow.text()
            if not confirmation_volume_text:
                self.show_error_message("Veuillez calculer le volume total perdu lors de la confirmation d'abord.")
                return
            confirmation_volume_value = float(confirmation_volume_text.split()[0])
            confirmation_unit = confirmation_volume_text.split()[1]

            # Récupérer la valeur de dilution
            dilution_volume_text = self.lineEdit_qte_perdue_dilution.text()
            dilution_volume_value = float(dilution_volume_text.split()[0]) if dilution_volume_text else 0.0
            dilution_unit = "µL"  # Unité par défaut de la dilution (à adapter si nécessaire)

            # Convertir toutes les valeurs dans l'unité choisie (target_unit)
            if consommation_unit != target_unit:
                if self.calculator.are_units_compatible(consommation_unit, target_unit):
                    consommation_value = self.calculator.convert_value(consommation_value, consommation_unit, target_unit)
                else:
                    self.show_error_message(f"Conversion impossible entre {consommation_unit} et {target_unit}")
                    return

            if calibration_unit != target_unit:
                if self.calculator.are_units_compatible(calibration_unit, target_unit):
                    calibration_volume_value = self.calculator.convert_value(calibration_volume_value, calibration_unit, target_unit)
                else:
                    self.show_error_message(f"Conversion impossible entre {calibration_unit} et {target_unit}")
                    return

            if controle_unit != target_unit:
                if self.calculator.are_units_compatible(controle_unit, target_unit):
                    controle_volume_value = self.calculator.convert_value(controle_volume_value, controle_unit, target_unit)
                else:
                    self.show_error_message(f"Conversion impossible entre {controle_unit} et {target_unit}")
                    return

            if confirmation_unit != target_unit:
                if self.are_units_compatible(confirmation_unit, target_unit):
                    confirmation_volume_value = self.calculator.convert_value(confirmation_volume_value, confirmation_unit, target_unit)
                else:
                    self.show_error_message(f"Conversion impossible entre {confirmation_unit} et {target_unit}")
                    return

            if dilution_unit != target_unit:
                if self.calculator.are_units_compatible(dilution_unit, target_unit):
                    dilution_volume_value = self.calculator.convert_value(dilution_volume_value, dilution_unit, target_unit)
                else:
                    self.show_error_message(f"Conversion impossible entre {dilution_unit} et {target_unit}")
                    return

            # Calculer la quantité ajustée (incluant la dilution)
            qte_cm_ajustee = (
                consommation_value
                + calibration_volume_value
                + controle_volume_value
                + confirmation_volume_value
                + dilution_volume_value  # Ajouter la valeur de dilution
            )
            self.lineEdit_qte_cm_ajustee_sixRow.setText(f"{qte_cm_ajustee:.2f} {target_unit}")

            # Calcul de la consommation moyenne journalière
            periode_temps = float(consommation_text.split('/')[1].split()[0])  # Extraire "10" de "ml/10 jours"
            if periode_temps == 0:
                self.show_error_message("La période de temps ne peut pas être zéro.")
                return
            consommation_moyenne_journaliere = consommation_value / periode_temps  # Exemple : 10.00 / 10 = 1.00 ml/jour

            # Extraction des paramètres supplémentaires pour le calcul de la quantité à commander
            jours_livraison_text = self.lineEdit_jours_livraison_sixRow.text()
            stock_actuel_text = self.lineEdit_nbr_test_stock_actuel_sixRow.text()

            if not jours_livraison_text or not stock_actuel_text:
                self.show_error_message("Veuillez entrer les jours de livraison et le stock actuel.")
                return

            jours_livraison = float(jours_livraison_text)
            stock_actuel = float(stock_actuel_text)

            # Calcul de lineEdit_qte_a_commander_sixRow
            qte_a_commander = qte_cm_ajustee + (consommation_moyenne_journaliere * jours_livraison) - stock_actuel

            # Vérifier si la quantité à commander est négative ou nulle
            if qte_a_commander <= 0:
                self.lineEdit_qte_a_commander_sixRow.setText("Couverture suffisante")
            else:
                self.lineEdit_qte_a_commander_sixRow.setText(f"{qte_a_commander:.2f} {target_unit}")

        except ValueError as e:
            self.show_error_message(f"Erreur de calcul : {e}")
        except ZeroDivisionError:
            self.show_error_message("Erreur : division par zéro.")
        except Exception as e:
            self.show_error_message(f"Une erreur inattendue s'est produite : {e}")