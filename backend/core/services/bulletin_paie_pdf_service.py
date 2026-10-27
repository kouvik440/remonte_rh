from io import BytesIO
import unicodedata

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework.exceptions import ValidationError


class BulletinPaiePdfService:
    """Renders a payslip from the immutable payroll calculation snapshot."""

    NAVY = colors.HexColor("#17324D")
    BLUE = colors.HexColor("#245C84")
    PALE_BLUE = colors.HexColor("#EAF1F6")
    PALE_GRAY = colors.HexColor("#F4F6F8")
    TEXT = colors.HexColor("#263746")
    MUTED = colors.HexColor("#647482")
    BORDER = colors.HexColor("#D7E0E7")

    def __init__(self):
        self.regular_font, self.bold_font = "Helvetica", "Helvetica-Bold"

    def render(self, paie) -> bytes:
        detail = paie.detail_calcul or {}
        totals = detail.get("totaux") or {}
        contributions = detail.get("cotisations") or {}
        if not totals or not paie.date_calcul:
            raise ValidationError({"bulletin": "La paie doit être calculée avant de produire le bulletin."})

        output = BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=17 * mm,
            bottomMargin=17 * mm,
            title=f"Bulletin de paie {paie.periode}",
            author="Remonte RH",
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="SlipTitle", parent=styles["Title"], fontName=self.bold_font,
            fontSize=19, leading=23, textColor=self.NAVY, alignment=TA_RIGHT,
            spaceAfter=2,
        ))
        styles.add(ParagraphStyle(
            name="SlipSubtitle", parent=styles["Normal"], fontSize=9,
            leading=12, textColor=self.MUTED, alignment=TA_RIGHT,
        ))
        styles.add(ParagraphStyle(
            name="SectionHeading", parent=styles["Heading2"], fontName=self.bold_font,
            fontSize=10, leading=13, textColor=self.NAVY, spaceBefore=9, spaceAfter=5,
        ))
        styles.add(ParagraphStyle(
            name="SmallMuted", parent=styles["Normal"], fontSize=8,
            leading=10, textColor=self.MUTED,
        ))
        styles.add(ParagraphStyle(
            name="NetLabel", parent=styles["Normal"], fontName=self.bold_font,
            fontSize=11, leading=14, textColor=colors.white,
        ))
        styles.add(ParagraphStyle(
            name="NetAmount", parent=styles["Normal"], fontName=self.bold_font,
            fontSize=16, leading=19, textColor=colors.white, alignment=TA_RIGHT,
        ))

        employee = paie.employe
        clean = self._safe_text
        story = []
        header = Table([
            [
                Paragraph("REMONTE RH", ParagraphStyle(
                    "Brand", parent=styles["Heading1"], fontName=self.bold_font,
                    fontSize=15, leading=18, textColor=self.BLUE,
                )),
                [
                    Paragraph(clean("BULLETIN DE PAIE"), styles["SlipTitle"]),
                    Paragraph(f"Periode : {self._escape(clean(paie.periode))}", styles["SlipSubtitle"]),
                ],
            ]
        ], colWidths=[78 * mm, 96 * mm])
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINEBELOW", (0, 0), (-1, -1), 1.2, self.BLUE),
        ]))
        story.extend([header, Spacer(1, 8 * mm)])

        story.append(Paragraph(clean("INFORMATIONS DU SALARIÉ"), styles["SectionHeading"]))
        employee_rows = [
            [clean("Nom et prénom"), clean(f"{employee.prenom} {employee.nom}"), "Matricule", clean(employee.matricule)],
            ["Emploi", clean(paie.libelle), "Devise", paie.devise],
        ]
        employee_table = Table(employee_rows, colWidths=[28 * mm, 62 * mm, 24 * mm, 60 * mm])
        employee_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), self.PALE_BLUE),
            ("BACKGROUND", (2, 0), (2, -1), self.PALE_BLUE),
            ("TEXTCOLOR", (0, 0), (0, -1), self.NAVY),
            ("TEXTCOLOR", (2, 0), (2, -1), self.NAVY),
            ("FONTNAME", (0, 0), (0, -1), self.bold_font),
            ("FONTNAME", (2, 0), (2, -1), self.bold_font),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("TEXTCOLOR", (1, 0), (1, -1), self.TEXT),
            ("TEXTCOLOR", (3, 0), (3, -1), self.TEXT),
            ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(employee_table)

        story.append(Paragraph(clean("RÉMUNÉRATION"), styles["SectionHeading"]))
        pay_rows = [[clean("Éléments de rémunération"), "Montant (XOF)"]]
        pay_rows.append([clean("Salaire de base calculé"), self._money(totals.get("salaire_base"))])
        for line in detail.get("elements", []):
            if line.get("nature") in ("PRIME", "HEURE_SUP", "AVANTAGE"):
                pay_rows.append([clean(line.get("libelle", "Élément variable")), self._money(line.get("montant"))])
        pay_rows.append(["Salaire brut", self._money(totals.get("salaire_brut"))])
        pay_table = Table(pay_rows, colWidths=[130 * mm, 44 * mm], repeatRows=1)
        pay_table.setStyle(self._table_style(styles, total_row=len(pay_rows) - 1))
        story.append(pay_table)

        story.append(Paragraph("RETENUES SALARIALES", styles["SectionHeading"]))
        deductions = [["Retenue", "Montant (XOF)"]]
        deductions.extend([
            ["CNSS salariale", self._money(contributions.get("cnss_salariale"))],
            ["IUTS", self._money((detail.get("iuts") or {}).get("net"))],
        ])
        for line in detail.get("elements", []):
            if line.get("nature") == "RETENUE":
                deductions.append([clean(line.get("libelle", "Retenue")), self._money(line.get("montant"))])
        if self._decimal(totals.get("avantages_non_verses")):
            deductions.append([clean("Avantages non versés en espèces"), self._money(totals.get("avantages_non_verses"))])
        deductions.append(["Total des retenues diverses", self._money(totals.get("retenues_salariales_diverses"))])
        deduction_table = Table(deductions, colWidths=[130 * mm, 44 * mm], repeatRows=1)
        deduction_table.setStyle(self._table_style(styles, total_row=len(deductions) - 1))
        story.append(deduction_table)

        story.append(Spacer(1, 8 * mm))
        net_table = Table([[
            Paragraph(clean("NET À PAYER"), styles["NetLabel"]),
            Paragraph(f"{self._money(totals.get('salaire_net'))} {self._escape(paie.devise)}", styles["NetAmount"]),
        ]], colWidths=[108 * mm, 66 * mm])
        net_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.NAVY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(net_table)

        story.append(Paragraph("CHARGES EMPLOYEUR (INFORMATIF)", styles["SectionHeading"]))
        employer_rows = [
            ["CNSS patronale", self._money(contributions.get("cnss_patronale"))],
            ["TPA patronale", self._money(contributions.get("tpa_patronale"))],
            ["Autres charges patronales", self._money(contributions.get("autres_charges_patronales"))],
            [clean("Coût total employeur"), self._money(totals.get("cout_charge"))],
        ]
        employer_table = Table(employer_rows, colWidths=[130 * mm, 44 * mm])
        employer_table.setStyle(self._table_style(styles, total_row=len(employer_rows) - 1, header=False))
        story.append(employer_table)
        story.extend([
            Spacer(1, 10 * mm),
            Paragraph(
                clean("Document généré à partir du détail de calcul enregistré dans Remonte RH. "
                "Les paramètres appliqués sont consultables dans le dossier de paie."),
                styles["SmallMuted"],
            ),
        ])

        document.build(story, onFirstPage=self._draw_footer, onLaterPages=self._draw_footer)
        return output.getvalue()

    def _table_style(self, styles, total_row=None, header=True):
        commands = [
            ("GRID", (0, 0), (-1, -1), 0.45, self.BORDER),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), self.TEXT),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
        if header:
            commands.extend([
                ("BACKGROUND", (0, 0), (-1, 0), self.PALE_BLUE),
                ("FONTNAME", (0, 0), (-1, 0), self.bold_font),
                ("TEXTCOLOR", (0, 0), (-1, 0), self.NAVY),
            ])
        if total_row is not None:
            commands.extend([
                ("BACKGROUND", (0, total_row), (-1, total_row), self.PALE_GRAY),
                ("FONTNAME", (0, total_row), (-1, total_row), self.bold_font),
            ])
        return TableStyle(commands)

    def _draw_footer(self, canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(self.BORDER)
        canvas.line(18 * mm, 13 * mm, A4[0] - 18 * mm, 13 * mm)
        canvas.setFont(self.regular_font, 7.5)
        canvas.setFillColor(self.MUTED)
        canvas.drawString(18 * mm, 8.5 * mm, "Remonte RH - Bulletin de paie confidentiel")
        canvas.drawRightString(A4[0] - 18 * mm, 8.5 * mm, f"Page {document.page}")
        canvas.restoreState()

    @staticmethod
    def _decimal(value):
        from decimal import Decimal, InvalidOperation

        try:
            return Decimal(str(value or "0"))
        except (TypeError, InvalidOperation):
            return Decimal("0")

    @classmethod
    def _money(cls, value):
        return f"{cls._decimal(value):,.0f}".replace(",", " ")

    @staticmethod
    def _escape(value):
        return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _safe_text(value):
        return unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")

