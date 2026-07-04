from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["reference", "name", "entity_type"]


class ClientFactSetForm(forms.Form):
    tax_year = forms.CharField(initial="2025/26", help_text="e.g. 2025/26")

    other_income = forms.FloatField(initial=0, min_value=0, required=False)
    salary_from_own_company = forms.FloatField(initial=0, min_value=0, required=False)
    dividends_from_own_company = forms.FloatField(initial=0, min_value=0, required=False)
    spouse_income = forms.FloatField(initial=0, min_value=0, required=False)

    company_profit_before_remuneration = forms.FloatField(initial=0, min_value=0, required=False)
    employment_allowance_available = forms.BooleanField(initial=False, required=False)
    associated_companies = forms.IntegerField(initial=0, min_value=0, required=False)

    sole_trade_annual_profit = forms.FloatField(initial=0, min_value=0, required=False)

    pension_threshold_income = forms.FloatField(initial=0, min_value=0, required=False)
    pension_adjusted_income = forms.FloatField(initial=0, min_value=0, required=False)
    pension_unused_aa_y1 = forms.FloatField(initial=0, min_value=0, required=False)
    pension_unused_aa_y2 = forms.FloatField(initial=0, min_value=0, required=False)
    pension_unused_aa_y3 = forms.FloatField(initial=0, min_value=0, required=False)
    pension_desired_contribution = forms.FloatField(initial=0, min_value=0, required=False)

    estate_gross_value = forms.FloatField(initial=0, min_value=0, required=False)
    estate_liabilities = forms.FloatField(initial=0, min_value=0, required=False)
    estate_home_equity_value = forms.FloatField(initial=0, min_value=0, required=False)
    estate_home_to_direct_descendants = forms.BooleanField(initial=False, required=False)
    estate_amount_to_spouse = forms.FloatField(initial=0, min_value=0, required=False)
    estate_charitable_legacy = forms.FloatField(initial=0, min_value=0, required=False)
    estate_combined_value_second_death = forms.FloatField(
        initial=0, min_value=0, required=False,
        help_text="Projected combined estate on the surviving spouse's death, if married.",
    )
    estate_combined_home_equity_second_death = forms.FloatField(initial=0, min_value=0, required=False)
    estate_planned_lifetime_gift = forms.FloatField(initial=0, min_value=0, required=False)
    estate_prior_year_annual_exemption_unused = forms.BooleanField(initial=False, required=False)

    def to_facts(self) -> dict:
        data = self.cleaned_data
        return {
            "personal": {
                "other_income": data.get("other_income") or 0,
                "salary_from_own_company": data.get("salary_from_own_company") or 0,
                "dividends_from_own_company": data.get("dividends_from_own_company") or 0,
                "spouse_income": data.get("spouse_income") or 0,
            },
            "company": {
                "profit_before_remuneration": data.get("company_profit_before_remuneration") or 0,
                "employment_allowance_available": data.get("employment_allowance_available") or False,
                "associated_companies": data.get("associated_companies") or 0,
            },
            "sole_trade": {"annual_profit": data.get("sole_trade_annual_profit") or 0},
            "pension": {
                "threshold_income": data.get("pension_threshold_income") or 0,
                "adjusted_income": data.get("pension_adjusted_income") or 0,
                "unused_aa_prior_3_years": [
                    data.get("pension_unused_aa_y1") or 0,
                    data.get("pension_unused_aa_y2") or 0,
                    data.get("pension_unused_aa_y3") or 0,
                ],
                "desired_contribution": data.get("pension_desired_contribution") or 0,
            },
            "estate": {
                "gross_value": data.get("estate_gross_value") or 0,
                "liabilities": data.get("estate_liabilities") or 0,
                "home_equity_value": data.get("estate_home_equity_value") or 0,
                "home_passes_to_direct_descendants": data.get("estate_home_to_direct_descendants") or False,
                "amount_to_spouse": data.get("estate_amount_to_spouse") or 0,
                "charitable_legacy": data.get("estate_charitable_legacy") or 0,
                "combined_estate_second_death": data.get("estate_combined_value_second_death") or 0,
                "combined_home_equity_second_death": data.get("estate_combined_home_equity_second_death") or 0,
                "planned_lifetime_gift": data.get("estate_planned_lifetime_gift") or 0,
                "prior_year_annual_exemption_unused": data.get("estate_prior_year_annual_exemption_unused") or False,
            },
        }


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()
