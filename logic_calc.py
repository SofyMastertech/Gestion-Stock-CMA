# logic_calc.py

# Unités de volume
VOLUME_UNITS = ['µl', 'ml', 'l']
VOLUME_CONVERSIONS = {
    'µl': 0.001,  # 1 µL = 0.001 mL
    'ml': 1,      # 1 mL = 1 mL
    'l': 1000     # 1 L = 1000 mL
}

# Unités de masse
MASS_UNITS = ['mg', 'g', 'kg']
MASS_CONVERSIONS = {
    'mg': 0.001,  # 1 mg = 0.001 g
    'g': 1,       # 1 g = 1 g
    'kg': 1000    # 1 kg = 1000 g
}

# Unités de comptage
COUNT_UNITS = ['boîte', 'kit', 'sachet', 'flacon', 'tube', 'coffret', 'test']

class ConsumptionCalculator:
    def __init__(self):
        self.time_factors = {
            'jours': 1,
            'semaine': 7,
            'mois': 30
        }

    def is_unit_valid(self, unit):
        """Vérifie si une unité est valide."""
        unit = unit.lower()
        return (unit in VOLUME_UNITS or
                unit in MASS_UNITS or
                unit in COUNT_UNITS)

    def are_units_compatible(self, from_unit, to_unit):
        """Vérifie si les unités sont compatibles pour la conversion."""
        from_unit, to_unit = from_unit.lower(), to_unit.lower()

        if not self.is_unit_valid(from_unit) or not self.is_unit_valid(to_unit):
            return False

        # Compatibilité au sein du même type
        if (from_unit in VOLUME_UNITS and to_unit in VOLUME_UNITS) or \
           (from_unit in MASS_UNITS and to_unit in MASS_UNITS) or \
           (from_unit in COUNT_UNITS and to_unit in COUNT_UNITS):
            return True

        # Conversion volume ↔ masse nécessite une densité
        return False

    def convert_value(self, value, from_unit, to_unit, density=None):
        """Convertit une valeur entre deux unités compatibles."""
        from_unit, to_unit = from_unit.lower(), to_unit.lower()

        if not self.is_unit_valid(from_unit):
            raise ValueError(f"Unité source invalide : {from_unit}")
        if not self.is_unit_valid(to_unit):
            raise ValueError(f"Unité cible invalide : {to_unit}")

        if not self.are_units_compatible(from_unit, to_unit):
            if density is None:
                raise ValueError(f"Conversion impossible entre {from_unit} et {to_unit} sans densité")
            elif not (from_unit in VOLUME_UNITS and to_unit in MASS_UNITS) and \
                 not (from_unit in MASS_UNITS and to_unit in VOLUME_UNITS):
                raise ValueError(f"Conversion impossible entre {from_unit} et {to_unit}")

        # Conversion entre volumes
        if from_unit in VOLUME_UNITS and to_unit in VOLUME_UNITS:
            value_in_ml = value * VOLUME_CONVERSIONS[from_unit]
            return value_in_ml / VOLUME_CONVERSIONS[to_unit]

        # Conversion entre masses
        if from_unit in MASS_UNITS and to_unit in MASS_UNITS:
            value_in_g = value * MASS_CONVERSIONS[from_unit]
            return value_in_g / MASS_CONVERSIONS[to_unit]

        # Conversion volume ↔ masse (nécessite une densité)
        if from_unit in VOLUME_UNITS and to_unit in MASS_UNITS:
            if density is None:
                raise ValueError("Une densité est requise pour convertir un volume en masse")
            value_in_g = value * VOLUME_CONVERSIONS[from_unit] * density  # ml → g
            return value_in_g / MASS_CONVERSIONS[to_unit]

        if from_unit in MASS_UNITS and to_unit in VOLUME_UNITS:
            if density is None:
                raise ValueError("Une densité est requise pour convertir une masse en volume")
            value_in_ml = value * MASS_CONVERSIONS[from_unit] / density  # g → ml
            return value_in_ml / VOLUME_CONVERSIONS[to_unit]

        raise ValueError(f"Conversion impossible entre {from_unit} et {to_unit}")

    def calculate_control_usage(self, qty_per_control, frequency, period, time_value, time_unit, qty_unit, display_unit):
        """Calcule la quantité totale utilisée par le contrôle."""
        try:
            total_days = time_value * self.time_factors.get(time_unit.lower(), 1)
            period_days = self.time_factors.get(period.lower(), 1)

            total_controls = (total_days // period_days) * frequency
            total_qty = total_controls * qty_per_control

            if qty_unit != display_unit:
                total_qty = self.convert_value(total_qty, qty_unit, display_unit)

            return total_qty
        except Exception as e:
            print(f"Erreur de calcul : {e}")
            raise ValueError("Problème dans le calcul des contrôles")