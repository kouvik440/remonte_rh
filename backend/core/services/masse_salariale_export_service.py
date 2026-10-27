import csv
from io import BytesIO, StringIO
from decimal import Decimal, InvalidOperation
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.services.masse_salariale_service import masse_salariale_service


class MasseSalarialeExportService:
    CONTENT_TYPES = {
        "csv": "text/csv; charset=utf-8",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
    }

    HEADERS = [
        "Paies validees", "Paies payees", "Brut valide (XOF)", "Net valide (XOF)",
        "Cotisations validees (XOF)", "Cout employeur valide (XOF)",
        "Brut paye (XOF)", "Net paye (XOF)", "Cotisations payees (XOF)",
        "Cout employeur paye (XOF)",
    ]
    TOTAL_KEYS = [
        "paies_validees", "paies_payees", "brut_valide", "net_valide",
        "cotisations_validees", "cout_employeur_valide", "brut_paye", "net_paye",
        "cotisations_payees", "cout_employeur_paye",
    ]

    def __init__(self, reporting_service):
        self.reporting_service = reporting_service

    def export(self, start_period: str, end_period: str, export_format: str, department_id=None, *, granularity="mensuelle"):
        if export_format not in self.CONTENT_TYPES:
            raise ValueError("Format d'export non pris en charge.")
        if granularity not in ("mensuelle", "annuelle"):
            raise ValueError("Granularité d'export non prise en charge.")
        report = self.reporting_service.summarize(
            start_period,
            end_period,
            department_id=department_id,
        )
        report["granularite"] = granularity
        if export_format == "csv":
            body = self._csv(report)
        elif export_format == "xlsx":
            body = self._xlsx(report)
        else:
            body = self._pdf(report)
        filename = f"masse-salariale-{start_period}-{end_period}-{granularity}.{export_format}"
        return body, self.CONTENT_TYPES[export_format], filename


    @classmethod
    def _sections(cls, report):
        total = report["totaux"]
        yield "Synthese", ["Indicateur", *cls.HEADERS], [
            ["Total de la periode", *[total[key] for key in cls.TOTAL_KEYS]]
        ]
        granularity = report.get("granularite", "mensuelle")
        period_key = "annee" if granularity == "annuelle" else "periode"
        yield f"Evolution {granularity}", ["Annee" if granularity == "annuelle" else "Periode", "Employes", *cls.HEADERS], [
            [row[period_key], row["employes"], *[row[key] for key in cls.TOTAL_KEYS]]
            for row in report[f"evolution_{granularity}"]
        ]
        yield "Departements", ["Departement ID", "Departement", *cls.HEADERS], [
            [row["departement_id"], row["departement"], *[row[key] for key in cls.TOTAL_KEYS]]
            for row in report["par_departement"]
        ]
        yield "Types contrat", ["Type contrat ID", "Type de contrat", *cls.HEADERS], [
            [row["type_contrat_id"], row["type_contrat"], *[row[key] for key in cls.TOTAL_KEYS]]
            for row in report["par_type_contrat"]
        ]

    @classmethod
    def _csv(cls, report):
        output = StringIO(newline="")
        writer = csv.writer(output, delimiter=";")
        writer.writerow(["Analyse de la masse salariale", report["periode_debut"], report["periode_fin"]])
        for name, headers, rows in cls._sections(report):
            writer.writerow([])
            writer.writerow([name])
            writer.writerow(headers)
            writer.writerows(rows)
        return ("\ufeff" + output.getvalue()).encode("utf-8")

    @classmethod
    def _xlsx(cls, report):
        sheets = list(cls._sections(report))
        output = BytesIO()
        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", cls._content_types(len(sheets)))
            archive.writestr("_rels/.rels", cls._root_relationships())
            archive.writestr("xl/workbook.xml", cls._workbook_xml(sheets))
            archive.writestr("xl/_rels/workbook.xml.rels", cls._workbook_relationships(len(sheets)))
            archive.writestr("xl/styles.xml", cls._styles_xml())
            for index, (_, headers, rows) in enumerate(sheets, start=1):
                archive.writestr(f"xl/worksheets/sheet{index}.xml", cls._worksheet_xml(headers, rows))
        return output.getvalue()

    @staticmethod
    def _column_name(number):
        result = ""
        while number:
            number, remainder = divmod(number - 1, 26)
            result = chr(65 + remainder) + result
        return result

    @classmethod
    def _worksheet_xml(cls, headers, rows):
        xml_rows = []
        for row_number, values in enumerate([headers, *rows], start=1):
            cells = []
            for column_number, value in enumerate(values, start=1):
                reference = f"{cls._column_name(column_number)}{row_number}"
                numeric_value = cls._numeric_cell_value(value)
                if numeric_value is not None:
                    cells.append(f'<c r="{reference}"><v>{numeric_value}</v></c>')
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    cells.append(f'<c r="{reference}"><v>{value}</v></c>')
                else:
                    cells.append(
                        f'<c r="{reference}" t="inlineStr"><is><t xml:space="preserve">'
                        f'{escape(str(value if value is not None else ""))}</t></is></c>'
                    )
            xml_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
        )

    @staticmethod
    def _numeric_cell_value(value):
        if not isinstance(value, str):
            return None
        try:
            number = Decimal(value)
        except InvalidOperation:
            return None
        return format(number, "f") if number.is_finite() else None

    @staticmethod
    def _content_types(sheet_count):
        overrides = ''.join(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(1, sheet_count + 1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            f'{overrides}</Types>'
        )

    @staticmethod
    def _root_relationships():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        )

    @staticmethod
    def _workbook_xml(sheets):
        names = ''.join(
            f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
            for i, (name, _, _) in enumerate(sheets, start=1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets>{names}</sheets></workbook>'
        )

    @staticmethod
    def _workbook_relationships(sheet_count):
        sheets = ''.join(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, sheet_count + 1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'{sheets}<Relationship Id="rId{sheet_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>'
        )

    @staticmethod
    def _styles_xml():
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
            '</styleSheet>'
        )

    @classmethod
    def _pdf(cls, report):
        output = BytesIO()
        document = SimpleDocTemplate(
            output, pagesize=landscape(A4), rightMargin=12 * mm, leftMargin=12 * mm,
            topMargin=12 * mm, bottomMargin=12 * mm, title="Analyse de la masse salariale",
        )
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            "ExportHeaderCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=8,
            textColor=colors.white,
        )
        story = [
            Paragraph("Analyse de la masse salariale", styles["Title"]),
            Paragraph(f"Periode : {report['periode_debut']} a {report['periode_fin']} | Devise : XOF", styles["Normal"]),
            Spacer(1, 5 * mm),
        ]
        for section_index, (name, headers, rows) in enumerate(cls._sections(report)):
            story.append(Paragraph(name, styles["Heading2"]))
            pdf_headers = [Paragraph(escape(str(value)), header_style) for value in headers]
            table_data = [pdf_headers, *[[str(value) for value in row] for row in rows]]
            table = Table(table_data, colWidths=cls._pdf_column_widths(name, len(headers)), repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E0E7")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(table)
            story.append(Spacer(1, 4 * mm))
            if section_index == 1:
                story.append(PageBreak())
        document.build(story)
        return output.getvalue()

    @staticmethod
    def _pdf_column_widths(section, count):
        if section == "Synthese":
            first, second = 150, 59
            return [first] + [second] * (count - 1)
        if section.startswith("Evolution "):
            widths = [50, 48] + [64] * 10
            return widths[:count]
        widths = [85, 130] + [55] * 10
        return widths[:count]


masse_salariale_export_service = MasseSalarialeExportService(masse_salariale_service)
