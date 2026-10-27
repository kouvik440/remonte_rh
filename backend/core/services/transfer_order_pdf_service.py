from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from num2words import num2words
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.services.bank_rib import rib_components


class TransferOrderPdfService:
    """Prepare a bank instruction for manual signature, without issuing a payment."""

    def render(self, data: dict) -> bytes:
        self.styles = self._styles()
        output = BytesIO()
        document = SimpleDocTemplate(output, pagesize=A4, rightMargin=17 * mm, leftMargin=17 * mm,
                                     topMargin=14 * mm, bottomMargin=15 * mm, title="Ordre de virement", author=data["donneur_nom"])
        amount = Decimal(data["montant"])
        figures = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
        story = [self._paragraph("ORDRE DE VIREMENT", "Title"), self._paragraph("Burkina Faso - Franc CFA (XOF)", "Muted"),
                 self._paragraph(f"Référence : {data['reference']} | Paie : {data['periode']}", "Body"), Spacer(1, 3 * mm),
                 self._paragraph("Veuillez effectuer le virement ci-dessous par le débit de notre compte.", "Body")]
        story += self._party("DONNEUR D’ORDRE", [
            ("Raison sociale / titulaire", data["donneur_nom"]), ("Adresse", data["donneur_adresse"]),
            ("Téléphone", data["donneur_telephone"] or "Non renseigné"), ("Banque / agence", self._join(data["banque"], data["agence"])),
        ], data["compte_debit"])
        story += self._party("BÉNÉFICIAIRE", [
            ("Nom et prénom", data["beneficiaire_nom"]), ("Adresse", data["beneficiaire_adresse"]),
            ("Banque", data["beneficiaire_banque"]),
        ], data["beneficiaire_rib"])
        story += [self._paragraph("MONTANT ET INSTRUCTIONS", "Section"), self._rows([
            ("Montant en chiffres", f"{figures} FCFA"),
            ("Montant en lettres", num2words(amount, lang="fr") + " francs CFA"),
            ("Motif du virement", data["motif"]),
            ("Exécution demandée le", self._date(data["date_execution"])),
            ("Mode demandé", {"BANQUE": "Selon les modalités de la banque", "INTERNE": "Virement interne", "SICA": "SICA", "RTGS": "RTGS"}[data["canal"]]),
        ])]
        story += [Spacer(1, 5 * mm), self._signatures(data)]
        document.build(story, onFirstPage=self._footer, onLaterPages=self._footer)
        return output.getvalue()

    def _styles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=9, leading=12))
        styles.add(ParagraphStyle(name="Muted", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#64748b"), spaceAfter=7))
        styles.add(ParagraphStyle(name="Section", fontName="Helvetica-Bold", fontSize=10, leading=13,
                                  textColor=colors.HexColor("#17324d"), spaceBefore=10, spaceAfter=5))
        return styles

    def _paragraph(self, value, style="Body"):
        return Paragraph(escape(str(value)).replace("\n", "<br/>"), self.styles[style])

    def _rows(self, fields):
        table = Table([[self._paragraph(label), self._paragraph(value)] for label, value in fields], colWidths=[47 * mm, 129 * mm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), .3, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return table

    def _party(self, title, fields, rib):
        bank = Table([[self._paragraph(value) for value in ("Code banque", "Code guichet", "Numéro de compte", "Clé RIB")],
                      [self._paragraph(value) for value in rib_components(rib)]], colWidths=[35 * mm, 35 * mm, 81 * mm, 25 * mm])
        bank.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
            ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return [KeepTogether([self._paragraph(title, "Section"), self._rows(fields), bank])]

    def _signatures(self, data):
        left = [self._paragraph(f"Fait à {data['lieu']}, le {self._date(data['date_emission'])}"),
                self._paragraph(data["signataire"]), self._paragraph(data["fonction_signataire"]),
                Spacer(1, 4 * mm), self._paragraph("Signature et cachet du donneur d’ordre")]
        right = [self._paragraph("Cadre réservé à la banque"), Spacer(1, 10 * mm), self._paragraph("Date, visa et cachet")]
        table = Table([[left, right]], colWidths=[100 * mm, 76 * mm], minRowHeights=[32 * mm])
        table.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#cbd5e1")),
                                   ("INNERGRID", (0, 0), (-1, -1), .5, colors.HexColor("#cbd5e1")),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 7)]))
        return KeepTogether([table, Spacer(1, 3 * mm), self._paragraph("Document à signer et remettre à la banque pour validation et exécution.", "Muted")])

    @staticmethod
    def _join(bank, agency):
        return f"{bank} / {agency}" if agency else bank

    @staticmethod
    def _date(value):
        year, month, day = value.split("-")
        return f"{day}/{month}/{year}"

    @staticmethod
    def _footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(17 * mm, 9 * mm, "Remonte RH - Ordre de virement confidentiel")
        canvas.drawRightString(A4[0] - 17 * mm, 9 * mm, f"Page {document.page}")
        canvas.restoreState()
