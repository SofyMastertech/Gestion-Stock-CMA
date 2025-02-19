# report_generator.py
"""
Module pour générer un rapport PDF stylisé et détaillé avec des fonctionnalités avancées.

Ce module utilise reportlab pour créer un document PDF professionnel avec des polices Roboto,
une palette de couleurs cohérente (#FFFFFF, #178E3B, #F0F7EE, etc.), des tableaux stylisés
avec alternance de couleurs, des en-têtes décoratifs, des formules mathématiques encadrées,
et une architecture modulaire. Les largeurs sont adaptatives, et les espacements sont homogènes.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Définir la palette de couleurs
WHITE = colors.HexColor('#FFFFFF')  # Fond blanc
GREEN = colors.HexColor('#178E3B')  # Vert pour titres
LIGHT_GREEN = colors.HexColor('#F0F7EE')  # Fond clair pour alternance
GRAY_BORDER = colors.HexColor('#D0D0D0')  # Gris pour bordures
DARK_GRAY = colors.HexColor('#2E2E2E')  # Texte principal
LIGHT_BLUE = colors.HexColor('#E9F2FA')  # Bleu clair optionnel

# Charger les polices Roboto avec gestion des erreurs
try:
    pdfmetrics.registerFont(TTFont('Roboto-Regular', 'Roboto-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Bold', 'Roboto-Bold.ttf'))
    BASE_FONT = 'Roboto-Regular'
    BOLD_FONT = 'Roboto-Bold'
except Exception as e:
    print(f"Polices Roboto non trouvées : {e}. Utilisation de Helvetica par défaut.")
    BASE_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'

# Mapper les polices
addMapping(BASE_FONT, 0, 0, BASE_FONT)  # Normal
addMapping(BOLD_FONT, 1, 0, BOLD_FONT)  # Gras

def generate_explanation_report(data, pdf_filename="rapport_explications.pdf"):
    """
    Génère un rapport PDF stylisé avec sections numérotées, tableaux, et formules.

    Args:
        data (dict): Dictionnaire contenant les données extraites (valeurs, unités, etc.).
        pdf_filename (str): Nom du fichier PDF à générer.

    Returns:
        None: Le PDF est généré et ouvert automatiquement.
    """
    # Initialiser le document PDF avec marges
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=72
    )
    elements = []

    # Définir les styles réutilisables
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontName=BOLD_FONT,
        fontSize=20,
        textColor=GREEN,
        spaceBefore=20,
        spaceAfter=15,
        alignment=1  # Centré
    )
    section_title_style = ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontName=BOLD_FONT,
        fontSize=16,
        textColor=DARK_GRAY,
        spaceBefore=15,
        spaceAfter=10
    )
    normal_style = ParagraphStyle(
        name='NormalStyle',
        parent=styles['Normal'],
        fontName=BASE_FONT,
        fontSize=12,
        textColor=DARK_GRAY,
        spaceAfter=10,
        leading=14  # Espacement entre lignes
    )
    formula_style = ParagraphStyle(
        name='FormulaStyle',
        parent=normal_style,
        fontName=BOLD_FONT,
        textColor=GREEN,
        borderPadding=5,
        borderColor=GRAY_BORDER,
        borderWidth=1,
        borderRadius=3,
        alignment=0  # Gauche
    )
    footer_style = ParagraphStyle(
        name='FooterStyle',
        parent=styles['Normal'],
        fontName=BASE_FONT,
        fontSize=10,
        textColor=GRAY_BORDER,
        alignment=1,  # Centré
        spaceBefore=10
    )

    # Titre principal avec décoration
    elements.append(Paragraph("Explication des Calculs - Guide pour Débutants", title_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=15))
    elements.append(Paragraph(
        "Ce rapport fournit une explication détaillée et professionnelle des calculs effectués par le système.",
        normal_style
    ))
    elements.append(Spacer(1, 0.5*inch))  # Espacement homogène

    # Fonction modulaire pour ajouter une section
    def add_section(section_number, title, explanation, formula, data_table, elements_list):
        """
        Ajoute une section numérotée avec titre, explication, formule, et tableau stylisé.

        Args:
            section_number (int): Numéro de la section.
            title (str): Titre de la section.
            explanation (str): Texte explicatif.
            formula (str): Formule mathématique.
            data_table (list): Données pour le tableau.
            elements_list (list): Liste des éléments PDF à remplir.
        """
        # Titre de section avec soulignement
        elements_list.append(Paragraph(f"{section_number}. {title}", section_title_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=GRAY_BORDER, spaceAfter=10))

        # Explication
        elements_list.append(Paragraph(explanation, normal_style))

        # Formule encadrée
        formula_para = Paragraph(f"<b>Formule :</b> {formula}", formula_style)
        elements_list.append(KeepTogether([Spacer(1, 5), formula_para, Spacer(1, 5)]))

        # Tableau avec largeur adaptative et alternance de couleurs corrigée
        table = Table(data_table, colWidths=[doc.width/3] * 3)  # Trois colonnes égales
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), GREEN),  # En-tête vert
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GREEN),  # Toutes les lignes en vert clair
            ('TEXTCOLOR', (0, 1), (-1, -1), DARK_GRAY),
            ('FONTNAME', (0, 1), (-1, -1), BASE_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, GRAY_BORDER),  # Grille stylisée
            ('BOX', (0, 0), (-1, -1), 2, GRAY_BORDER),  # Bordure extérieure
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GREEN]),  # Alternance corrigée
        ]))
        elements_list.append(table)
        elements_list.append(Spacer(1, 0.3*inch))  # Espacement après tableau

    # Extraire les données
    nbr_tests = data.get('nbr_tests', 0)
    qty_per_test = data.get('qty_per_test', 0)
    time_value = data.get('time_value', 1)
    time_unit = data.get('time_unit', 'Jours')
    unit = data.get('unit', 'ml')
    qty_per_unit = data.get('qty_per_unit', 0)
    total_qty = data.get('total_qty', 0)
    dead_volume = data.get('dead_volume', 0)
    unit_qty = data.get('unit_qty', 'ml')
    unit_total = data.get('unit_total', 'ml')
    unit_dead = data.get('unit_dead', 'ml')
    calibration_volume = data.get('calibration_volume', 0)
    calibration_frequency = data.get('calibration_frequency', 1)
    calibration_period = data.get('calibration_period', 'Jours')
    cal_unit = data.get('cal_unit', 'ml')
    total_qty_loss = data.get('total_qty_loss', 0)
    manipulation_loss = data.get('manipulation_loss', 0) / 100
    contamination_loss = data.get('contamination_loss', 0) / 100
    degradation_loss = data.get('degradation_loss', 0) / 100
    loss_unit = data.get('loss_unit', 'ml')
    confirmation_qty = data.get('confirmation_qty', 0)
    confirmation_percent = data.get('confirmation_percent', 0) / 100
    conf_unit = data.get('conf_unit', 'ml')
    stock_actuel = data.get('stock_actuel', 0)
    livraison = data.get('livraison', 0)
    cond_unit = data.get('cond_unit', 'ml')

    # Ajouter les sections
    add_section(
        1, "Gestion des Paramètres de Consommation",
        "Calcule la consommation totale basée sur le nombre de tests et la quantité par test.",
        "Consommation Totale = Nombre de Tests × Quantité par Test",
        [
            ["Paramètre", "Valeur", "Unité"],
            ["Nombre de Tests", str(nbr_tests), ""],
            ["Quantité par Test", str(qty_per_test), unit],
            ["Période", str(time_value), time_unit],
            ["Consommation Totale", str(nbr_tests * qty_per_test), unit]
        ],
        elements
    )

    add_section(
        2, "Tests selon le Type de Conditionnement",
        "Détermine le nombre de tests par conditionnement en soustrayant le volume mort.",
        "Tests par Conditionnement = (Quantité Totale - Volume Mort) / Quantité par Test",
        [
            ["Paramètre", "Valeur", "Unité"],
            ["Quantité par Unité", str(qty_per_unit), unit_qty],
            ["Quantité Totale", str(total_qty), unit_total],
            ["Volume Mort", str(dead_volume), unit_dead],
            ["Tests", str((total_qty - dead_volume) / qty_per_unit if qty_per_unit > 0 else 0), unit_total]
        ],
        elements
    )

    add_section(
        3, "Paramètres de Calibration",
        "Évalue le volume total nécessaire pour les calibrations.",
        "Volume Total de Calibration = Fréquence × Volume par Calibration",
        [
            ["Paramètre", "Valeur", "Unité"],
            ["Fréquence", str(calibration_frequency), calibration_period],
            ["Volume par Calibration", str(calibration_volume), cal_unit],
            ["Volume Total", str(calibration_frequency * calibration_volume), cal_unit]
        ],
        elements
    )

    add_section(
        4, "Optimisation des Réactifs - Suivi des Pertes",
        "Analyse les pertes dues à la manipulation, contamination et dégradation.",
        "Quantité Perdue = Quantité Totale × (Pertes Manipulation + Pertes Contamination + Pertes Dégradation)",
        [
            ["Paramètre", "Valeur", "Unité"],
            ["Quantité Totale", str(total_qty_loss), loss_unit],
            ["Pertes Manipulation (%)", str(manipulation_loss * 100), "%"],
            ["Pertes Contamination (%)", str(contamination_loss * 100), "%"],
            ["Pertes Dégradation (%)", str(degradation_loss * 100), "%"],
            ["Quantité Perdue", str(total_qty_loss * (manipulation_loss + contamination_loss + degradation_loss)), loss_unit]
        ],
        elements
    )

    add_section(
        5, "Validation et Confirmation",
        "Calcule les pertes liées à la répétition des tests.",
        "Quantité Totale Perdue = Nombre de Tests × Pourcentage de Répetition × Quantité par Test",
        [
            ["Paramètre", "Valeur", "Unité"],
            ["Nombre de Tests", str(nbr_tests), ""],
            ["Pourcentage Répetition", str(confirmation_percent * 100), "%"],
            ["Quantité par Test", str(confirmation_qty), conf_unit],
            ["Quantité Perdue", str(nbr_tests * confirmation_percent * confirmation_qty), conf_unit]
        ],
        elements
    )

    add_section(
        6, "Résultats et Analyse",
        "Détermine la quantité à commander en optimisant les stocks.",
        "QAC = max(0, ceil((Consommation Totale + Stock Sécurité - Stock Actuel) / Conditionnement))",
        [
            ["Paramètre", "Valeur", "Unité"],
            ["Stock Actuel", str(stock_actuel), cond_unit],
            ["Délai de Livraison", str(livraison), "Jours"],
            ["Unité de Conditionnement", "", cond_unit]
        ],
        elements
    )

    # Footer sur chaque page
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(BASE_FONT, 10)
        canvas.setFillColor(GRAY_BORDER)
        footer_text = f"Page {doc.page}"
        canvas.drawString(inch, 0.75*inch, footer_text)
        canvas.restoreState()

    # Construire et générer le PDF
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)

    # Ouvrir le PDF
    if os.name == 'nt':  # Windows
        os.startfile(pdf_filename)
    elif os.name == 'posix':  # Linux/Mac
        os.system(f"xdg-open {pdf_filename}" if os.uname().sysname == 'Linux' else f"open {pdf_filename}")
