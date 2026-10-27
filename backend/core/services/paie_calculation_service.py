from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core.services.payroll_period import payroll_period_bounds

from core.repositories.paie_repository import PaieRepository
from core.services.contrat_service import contrat_service
from core.services.demande_absence_service import demande_absence_service
from core.services.element_variable_paie_service import (
    element_variable_paie_service,
)
from core.services.regle_paie_service import regle_paie_service

from core.models.enums import NatureElementPaie, StatutAbsence, StatutPaie


ZERO = Decimal("0")


class PaieCalculationService:
    def __init__(
        self,
        paie_repository,
        contrat_service,
        demande_absence_service,
        element_variable_service,
        regle_paie_service,
    ):
        self.paie_repository = paie_repository
        self.contrat_service = contrat_service
        self.demande_absence_service = demande_absence_service
        self.element_variable_service = element_variable_service
        self.regle_paie_service = regle_paie_service

    @transaction.atomic
    def calculate(
        self,
        paie_id: int,
        regle_id: int = None,
        charges_familiales: int = 0,
    ):
        paie = self.paie_repository.get(paie_id)
        if paie.statut != StatutPaie.BROUILLON:
            raise ValidationError(
                {"statut": "Seule une paie en brouillon peut être calculée."}
            )
        if paie.ordre_virement_id is not None:
            raise ValidationError(
                {"ordre_virement": "Le calcul doit précéder la création du virement."}
            )
        if not 0 <= charges_familiales <= 4:
            raise ValidationError(
                {"charges_familiales": "La valeur doit être comprise entre 0 et 4."}
            )

        date_debut, date_fin = payroll_period_bounds(paie.periode)
        regle = self._get_rule(regle_id, date_debut, date_fin)
        self._validate_rule(regle)

        contrats = list(
            self.contrat_service.get_for_employee_period(
                paie.employe_id,
                date_debut,
                date_fin,
            )
        )
        if not contrats:
            raise ValidationError(
                {"employe": "Aucun contrat ne couvre la période de paie."}
            )
        if len(contrats) > 1:
            raise ValidationError(
                {"employe": "Plusieurs contrats couvrent la période ; le calcul est ambigu."}
            )
        contrat = contrats[0]
        classification_snapshot = self.paie_repository.get_classification_snapshot(
            paie.employe_id,
            contrat.pk,
        )

        debut_emploi = max(date_debut, contrat.date_debut)
        fin_emploi = min(date_fin, contrat.date_fin or date_fin)
        jours_mois = self._working_days(date_debut, date_fin)
        jours_emploi = self._working_days(debut_emploi, fin_emploi)
        jours_absence_non_payee, jours_absence_payee = self._absence_day_counts(
            paie.employe_id,
            debut_emploi,
            fin_emploi,
        )
        if jours_absence_non_payee > jours_emploi:
            raise ValidationError(
                {"absences": "Les jours d'absence non payée dépassent les jours d'emploi."}
            )

        base_mensuelle = contrat.salaire_base
        jours_payes = jours_emploi - jours_absence_non_payee
        salaire_base = base_mensuelle * Decimal(jours_payes) / Decimal(jours_mois)
        elements = list(
            self.element_variable_service.for_employee_period(
                paie.employe_id,
                paie.periode,
            )
        )
        lignes = [
            self._element_line(element, contrat.salaire_base, regle.heures_mensuelles)
            for element in elements
        ]

        gains = [
            line
            for line in lignes
            if line["nature"]
            in (NatureElementPaie.PRIME, NatureElementPaie.HEURE_SUP, NatureElementPaie.AVANTAGE)
        ]
        retenues = [line for line in lignes if line["nature"] == NatureElementPaie.RETENUE]
        charges_patronales = [
            line for line in lignes if line["nature"] == NatureElementPaie.CHARGE_PATRONALE
        ]
        total_gains = sum((line["montant"] for line in gains), ZERO)
        salaire_brut = self._round(salaire_base + total_gains, regle.decimales_montant)
        avantages_non_verses = sum(
            (line["montant"] for line in gains if not line["verse_en_especes"]),
            ZERO,
        )
        assiette_cnss_brute = salaire_base + sum(
            (line["montant"] for line in gains if line["soumis_cnss"]),
            ZERO,
        )
        assiette_cnss = min(assiette_cnss_brute, regle.plafond_cnss)
        cnss_salariale = self._round(
            assiette_cnss * regle.taux_cnss_salarial,
            regle.decimales_montant,
        )
        cnss_patronale = self._round(
            assiette_cnss * regle.taux_cnss_patronal,
            regle.decimales_montant,
        )
        tpa_patronale = self._round(
            salaire_brut * regle.taux_tpa_patronal,
            regle.decimales_montant,
        )

        assiette_iuts_brute = salaire_base + sum(
            (line["montant"] for line in gains if line["soumis_iuts"]),
            ZERO,
        )
        deduction_retraite = min(
            cnss_salariale,
            salaire_base * regle.plafond_deduction_retraite,
        )
        abattement_professionnel = salaire_base * regle.abattement_professionnel
        assiette_iuts = max(
            ZERO,
            assiette_iuts_brute - deduction_retraite - abattement_professionnel,
        )
        iuts_brut, detail_tranches = self._calculate_iuts(assiette_iuts, regle.tranches_iuts)
        taux_reduction_familiale = self._family_reduction(
            charges_familiales,
            regle.reductions_iuts_charges,
        )
        reduction_iuts = iuts_brut * taux_reduction_familiale
        iuts = self._round(max(ZERO, iuts_brut - reduction_iuts), regle.decimales_montant)
        total_retenues = sum((line["montant"] for line in retenues), ZERO)
        total_charges_variables = sum(
            (line["montant"] for line in charges_patronales),
            ZERO,
        )
        salaire_net = self._round(
            salaire_brut
            - cnss_salariale
            - iuts
            - total_retenues
            - avantages_non_verses,
            regle.decimales_montant,
        )
        if salaire_net < ZERO:
            raise ValidationError(
                {"salaire_net": "Les retenues dépassent le montant net disponible."}
            )

        cotisations = self._round(
            cnss_salariale + cnss_patronale + tpa_patronale,
            regle.decimales_montant,
        )
        cout_charge = self._round(
            salaire_brut + cnss_patronale + tpa_patronale + total_charges_variables,
            regle.decimales_montant,
        )
        detail = {
            "version_schema": 2,
            "devise": regle.devise,
            "classification": classification_snapshot,
            "regle": {
                "id": regle.pk,
                "code": regle.code,
                "date_debut": regle.date_debut.isoformat(),
                "date_fin": regle.date_fin.isoformat() if regle.date_fin else None,
                "source_reference": regle.source_reference,
                "valide": regle.valide,
                "heures_mensuelles": self._format_money(regle.heures_mensuelles),
                "plafond_cnss": self._format_money(regle.plafond_cnss),
                "taux_cnss_salarial": self._format_rate(regle.taux_cnss_salarial),
                "taux_cnss_patronal": self._format_rate(regle.taux_cnss_patronal),
                "taux_tpa_patronal": self._format_rate(regle.taux_tpa_patronal),
                "abattement_professionnel": self._format_rate(regle.abattement_professionnel),
                "plafond_deduction_retraite": self._format_rate(
                    regle.plafond_deduction_retraite
                ),
                "tranches_iuts": regle.tranches_iuts,
                "reductions_iuts_charges": regle.reductions_iuts_charges,
                "decimales_montant": regle.decimales_montant,
            },
            "hypotheses": [
                "Prorata et absence calculés sur les jours du lundi au vendredi, hors jours fériés.",
                "La déduction d'absence utilise les jours ouvrés réels du mois.",
                "Les assiettes et taux sont ceux du profil de règles sélectionné.",
            ],
            "contrat": {
                "id": contrat.pk,
                "salaire_mensuel": self._format_money(base_mensuelle),
                "jours_ouvres_mois": jours_mois,
                "jours_emploi": jours_emploi,
                "jours_absence_payee": jours_absence_payee,
                "jours_absence_non_payee": jours_absence_non_payee,
                "jours_payes": jours_payes,
                "salaire_base_calcule": self._format_money(salaire_base),
            },
            "elements": [self._serialize_line(line, regle.decimales_montant) for line in lignes],
            "assiettes": {
                "cnss_brute": self._format_money(assiette_cnss_brute),
                "cnss_plafonnee": self._format_money(assiette_cnss),
                "iuts_brute": self._format_money(assiette_iuts_brute),
                "deduction_retraite": self._format_money(deduction_retraite),
                "abattement_professionnel": self._format_money(abattement_professionnel),
                "iuts_imposable": self._format_money(assiette_iuts),
            },
            "iuts": {
                "tranches": detail_tranches,
                "brut": self._format_money(iuts_brut),
                "charges_familiales": charges_familiales,
                "taux_reduction_familiale": self._format_rate(taux_reduction_familiale),
                "reduction": self._format_money(reduction_iuts),
                "net": self._format_money(iuts),
            },
            "cotisations": {
                "cnss_salariale": self._format_money(cnss_salariale),
                "cnss_patronale": self._format_money(cnss_patronale),
                "tpa_patronale": self._format_money(tpa_patronale),
                "autres_charges_patronales": self._format_money(total_charges_variables),
                "total": self._format_money(cotisations),
            },
            "totaux": {
                "salaire_brut": self._format_money(salaire_brut),
                "retenues_salariales_diverses": self._format_money(total_retenues),
                "avantages_non_verses": self._format_money(avantages_non_verses),
                "salaire_net": self._format_money(salaire_net),
                "cout_charge": self._format_money(cout_charge),
            },
        }

        paie.salaire_base = self._round(salaire_base, regle.decimales_montant)
        paie.salaire_brut = salaire_brut
        paie.salaire_net = salaire_net
        paie.cotisations = cotisations
        paie.cout_charge = cout_charge
        paie.devise = regle.devise
        paie.detail_calcul = detail
        paie.statut = StatutPaie.CALCULE
        paie.date_calcul = timezone.now()
        return self.paie_repository.update(
            paie,
            {
                "salaire_base": paie.salaire_base,
                "salaire_brut": paie.salaire_brut,
                "salaire_net": paie.salaire_net,
                "cotisations": paie.cotisations,
                "cout_charge": paie.cout_charge,
                "devise": paie.devise,
                "detail_calcul": paie.detail_calcul,
                "statut": paie.statut,
                "date_calcul": paie.date_calcul,
            },
        )

    def _get_rule(self, regle_id, date_debut, date_fin):
        if regle_id is not None:
            regle = self.regle_paie_service.get(regle_id)
            if not regle.actif:
                raise ValidationError({"regle_paie": "Ce profil est désactivé."})
            if regle.date_debut > date_debut or (
                regle.date_fin is not None and regle.date_fin < date_fin
            ):
                raise ValidationError(
                    {"regle_paie": "Le profil ne couvre pas toute la période."}
                )
            return regle

        regles = list(self.regle_paie_service.for_period(date_debut, date_fin))
        if not regles:
            raise ValidationError(
                {"regle_paie": "Aucun profil actif ne couvre cette période."}
            )
        if len(regles) > 1:
            raise ValidationError(
                {"regle_paie": "Plusieurs profils couvrent cette période ; choisissez-en un."}
            )
        return regles[0]

    @staticmethod
    def _validate_rule(regle):
        if not regle.valide or not regle.source_reference.strip():
            raise ValidationError(
                {"regle_paie": "Le profil doit être référencé et validé avant calcul."}
            )
        if regle.devise != "XOF":
            raise ValidationError(
                {"devise": "Ce calcul de paie est configuré uniquement pour le FCFA (XOF)."}
            )
        if regle.heures_mensuelles <= ZERO:
            raise ValidationError({"heures_mensuelles": "La valeur doit être positive."})
        if regle.plafond_cnss <= ZERO:
            raise ValidationError({"plafond_cnss": "Le plafond CNSS doit être positif."})
        if regle.jours_ouvres_semaine != 5:
            raise ValidationError(
                {"jours_ouvres_semaine": "Le moteur actuel suppose une semaine du lundi au vendredi."}
            )
        rates = (
            regle.taux_cnss_salarial,
            regle.taux_cnss_patronal,
            regle.taux_tpa_patronal,
            regle.abattement_professionnel,
            regle.plafond_deduction_retraite,
        )
        if any(rate < ZERO or rate > Decimal("1") for rate in rates):
            raise ValidationError({"regle_paie": "Tous les taux doivent être compris entre 0 et 1."})
        brackets = PaieCalculationService._parse_brackets(regle.tranches_iuts)
        if not brackets:
            raise ValidationError({"tranches_iuts": "Le profil doit définir les tranches IUTS."})

    def _absence_day_counts(
        self,
        employee_id: int,
        date_debut: date,
        date_fin: date,
    ) -> tuple:
        demandes = self.demande_absence_service.calendar(
            date_debut,
            date_fin,
            employee_id=employee_id,
        )
        jours_non_payes = set()
        jours_payes = set()
        for demande in demandes:
            if demande.statut != StatutAbsence.VALIDEE:
                continue
            jours_absence = jours_payes if demande.type_conge.est_payant else jours_non_payes
            current_date = max(date_debut, demande.date_debut)
            last_date = min(date_fin, demande.date_fin)
            while current_date <= last_date:
                if current_date.weekday() < 5:
                    jours_absence.add(current_date)
                current_date = date.fromordinal(current_date.toordinal() + 1)
        jours_en_double = jours_non_payes & jours_payes
        if jours_en_double:
            dates = ", ".join(sorted(jour.isoformat() for jour in jours_en_double))
            raise ValidationError(
                {"absences": f"Des absences payées et non payées se chevauchent le(s) jour(s) : {dates}."}
            )
        return len(jours_non_payes), len(jours_payes)

    @staticmethod
    def _working_days(date_debut: date, date_fin: date) -> int:
        if date_fin < date_debut:
            return 0
        return sum(
            1
            for ordinal in range(date_debut.toordinal(), date_fin.toordinal() + 1)
            if date.fromordinal(ordinal).weekday() < 5
        )

    @staticmethod
    def _element_line(element, salaire_mensuel: Decimal, heures_mensuelles: Decimal):
        if element.nature == NatureElementPaie.HEURE_SUP:
            if element.quantite is None or element.coefficient is None:
                raise ValidationError(
                    {"elements": f"{element.libelle} doit préciser quantité et coefficient."}
                )
            if element.quantite < ZERO or element.coefficient <= ZERO:
                raise ValidationError(
                    {"elements": f"{element.libelle} contient une quantité ou un coefficient invalide."}
                )
            montant = salaire_mensuel / heures_mensuelles * element.quantite * element.coefficient
        else:
            if element.montant is None or element.montant < ZERO:
                raise ValidationError(
                    {"elements": f"{element.libelle} doit avoir un montant positif ou nul."}
                )
            montant = element.montant

        if element.nature in (NatureElementPaie.RETENUE, NatureElementPaie.CHARGE_PATRONALE):
            if element.soumis_iuts or element.soumis_cnss:
                raise ValidationError(
                    {"elements": f"Les assiettes ne s'appliquent pas à {element.libelle}."}
                )
        return {
            "id": element.pk,
            "nature": element.nature,
            "libelle": element.libelle,
            "montant": montant,
            "quantite": element.quantite,
            "coefficient": element.coefficient,
            "soumis_iuts": element.soumis_iuts,
            "soumis_cnss": element.soumis_cnss,
            "verse_en_especes": element.verse_en_especes,
        }

    @staticmethod
    def _parse_brackets(raw_brackets):
        if not isinstance(raw_brackets, list):
            raise ValidationError({"tranches_iuts": "Les tranches doivent être une liste."})
        brackets = []
        for raw in raw_brackets:
            try:
                minimum = Decimal(str(raw["minimum"]))
                maximum = Decimal(str(raw["maximum"])) if raw.get("maximum") is not None else None
                rate = Decimal(str(raw["taux"]))
            except (KeyError, TypeError, InvalidOperation):
                raise ValidationError(
                    {"tranches_iuts": "Chaque tranche exige minimum, maximum et taux numérique."}
                )
            if minimum < ZERO or rate < ZERO or rate > Decimal("1"):
                raise ValidationError({"tranches_iuts": "Bornes ou taux IUTS invalides."})
            if maximum is not None and maximum <= minimum:
                raise ValidationError({"tranches_iuts": "La borne maximale doit dépasser le minimum."})
            brackets.append({"minimum": minimum, "maximum": maximum, "taux": rate})
        brackets.sort(key=lambda bracket: bracket["minimum"])
        if brackets and brackets[0]["minimum"] != ZERO:
            raise ValidationError({"tranches_iuts": "La première tranche doit commencer à zéro."})
        for index, bracket in enumerate(brackets):
            if index < len(brackets) - 1:
                if bracket["maximum"] != brackets[index + 1]["minimum"]:
                    raise ValidationError(
                        {"tranches_iuts": "Les tranches doivent être contiguës, sans chevauchement."}
                    )
            elif bracket["maximum"] is not None:
                raise ValidationError({"tranches_iuts": "La dernière tranche doit être sans plafond."})
        return brackets

    @classmethod
    def _calculate_iuts(cls, taxable_income: Decimal, raw_brackets: list):
        brackets = cls._parse_brackets(raw_brackets)
        total = ZERO
        detail = []
        for bracket in brackets:
            minimum = bracket["minimum"]
            maximum = bracket["maximum"]
            if taxable_income <= minimum:
                continue
            taxable_in_band = (
                taxable_income - minimum
                if maximum is None
                else min(taxable_income, maximum) - minimum
            )
            if taxable_in_band <= ZERO:
                continue
            tax = taxable_in_band * bracket["taux"]
            total += tax
            detail.append(
                {
                    "minimum": str(minimum),
                    "maximum": str(maximum) if maximum is not None else None,
                    "taux": str(bracket["taux"]),
                    "base": str(taxable_in_band),
                    "impot": str(tax),
                }
            )
        return total, detail

    @staticmethod
    def _family_reduction(charges_familiales: int, raw_reductions: list) -> Decimal:
        if not isinstance(raw_reductions, list):
            raise ValidationError(
                {"reductions_iuts_charges": "Les réductions familiales doivent être une liste."}
            )
        for item in raw_reductions:
            try:
                if int(item["charges"]) == charges_familiales:
                    rate = Decimal(str(item["taux"]))
                    if ZERO <= rate <= Decimal("1"):
                        return rate
                    break
            except (KeyError, TypeError, ValueError, InvalidOperation):
                break
        if charges_familiales == 0:
            return ZERO
        raise ValidationError(
            {"charges_familiales": "Aucune réduction configurée pour ce nombre de charges."}
        )

    @classmethod
    def _round(cls, amount: Decimal, decimal_places: int) -> Decimal:
        quantum = Decimal("1").scaleb(-decimal_places)
        return amount.quantize(quantum, rounding=ROUND_HALF_UP)

    @staticmethod
    def _format_money(amount: Decimal) -> str:
        return format(amount, "f")

    @staticmethod
    def _format_rate(rate: Decimal) -> str:
        return format(rate, "f")

    @classmethod
    def _serialize_line(cls, line, decimal_places: int):
        serialized = dict(line)
        serialized["montant"] = cls._format_money(
            cls._round(line["montant"], decimal_places)
        )
        if line["quantite"] is not None:
            serialized["quantite"] = cls._format_money(line["quantite"])
        if line["coefficient"] is not None:
            serialized["coefficient"] = cls._format_rate(line["coefficient"])
        return serialized


paie_calculation_service = PaieCalculationService(
    PaieRepository(),
    contrat_service,
    demande_absence_service,
    element_variable_paie_service,
    regle_paie_service,
)
