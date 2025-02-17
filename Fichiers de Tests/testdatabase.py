import sqlite3
import random
import sys
sys.stdout.reconfigure(encoding='utf-8')

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

# Unités possibles
unit_choices = ["ml", "test", "mg"]

# Connexion à la base de données
conn = sqlite3.connect("reactifs_database.db")
cursor = conn.cursor()

# Création de la table si elle n'existe pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS Analytes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    unit TEXT NOT NULL
);
""")

# Insérer les analyses avec des unités aléatoires
try:
    cursor.execute("BEGIN TRANSACTION;")  # Début transaction
    for analyte in analyse_liste:
        unit = random.choice(unit_choices)
        cursor.execute("INSERT OR IGNORE INTO Analytes (name, unit) VALUES (?, ?)", (analyte, unit))
    
    conn.commit()  # Valider la transaction
    print("✅ Insertion réussie !")
except Exception as e:
    conn.rollback()  # Annuler si erreur
    print(f"❌ Erreur : {e}")

# Fermer la connexion
conn.close()
