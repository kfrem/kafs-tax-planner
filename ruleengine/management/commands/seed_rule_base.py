"""Seeds the rule base with real, published 2024/25 and 2025/26 UK tax
parameters, an authority registry, and a handful of Phase 1 strategies
(architecture doc Section 10: "personal income tax and the corporation tax
strategies that interact with it").

IMPORTANT — governance (architecture doc Section 5.6): this command creates
a DRAFT rule-base release by default. Nothing in this seed data has been
reviewed by a qualified tax professional. A named tax editor and a distinct
second reviewer must check every parameter and citation against the primary
source (legislation.gov.uk, HMRC manuals) and mark the release RELEASED via
Django Admin before any advice is generated from it. Pass --release only
for local development/testing convenience — never in a real deployment.
"""

from __future__ import annotations

import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from psycopg.types.range import Range

from authority.models import Authority
from ruleengine.choices import RiskStatus, TaxDomain, Timeframe
from ruleengine.models import GoldenTestCase, RuleBaseRelease, Strategy, TaxParameter

User = get_user_model()

REVIEW_NOTE = (
    "Seed data drafted for MVP build. Verify citation, pinpoint subsection, "
    "and verbatim extract against the primary source before release approval."
)


class Command(BaseCommand):
    help = "Seed the rule base with 2024/25 and 2025/26 parameters, authorities, and strategies."

    def add_arguments(self, parser):
        parser.add_argument(
            "--release",
            action="store_true",
            help="Mark the rule-base releases RELEASED (dev/test convenience only).",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            editor, reviewer = self._get_or_create_editorial_users()
            release_2024, release_2025, release_iht, release_property = self._create_releases(
                editor, reviewer, options["release"]
            )
            authorities = self._create_authorities()
            self._create_parameters(release_2024, release_2025)
            self._create_iht_parameters(release_iht)
            self._create_property_parameters(release_property)
            self._create_strategies(release_2024, release_iht, release_property, authorities)
            self._create_golden_cases()

        self.stdout.write(self.style.SUCCESS("Rule base seeded."))
        if not options["release"]:
            self.stdout.write(
                self.style.WARNING(
                    "Releases created as DRAFT. Log into /admin/, review, and mark "
                    "RuleBaseRelease 2024.1 / 2025.1 as Released (with a distinct "
                    "reviewer) before advice can be generated."
                )
            )

    def _get_or_create_editorial_users(self):
        editor, created = User.objects.get_or_create(
            username="tax_editor",
            defaults={"is_staff": True, "is_superuser": True, "email": "tax.editor@example.invalid"},
        )
        if created:
            editor.set_password("changeme-tax-editor")
            editor.save()

        reviewer, created = User.objects.get_or_create(
            username="tax_reviewer",
            defaults={"is_staff": True, "is_superuser": True, "email": "tax.reviewer@example.invalid"},
        )
        if created:
            reviewer.set_password("changeme-tax-reviewer")
            reviewer.save()

        return editor, reviewer

    def _create_releases(self, editor, reviewer, mark_released):
        status = RuleBaseRelease.Status.RELEASED if mark_released else RuleBaseRelease.Status.DRAFT
        release_2024, _ = RuleBaseRelease.objects.update_or_create(
            version="2024.1",
            defaults={
                "changelog": "Initial seed: 2024/25 income tax, dividend tax, NIC, corporation tax, "
                "pension annual allowance and Marriage Allowance parameters.",
                "effective_date": datetime.date(2024, 4, 6),
                "status": status,
                "editor": editor,
                "reviewer": reviewer if mark_released else None,
            },
        )
        release_2025, _ = RuleBaseRelease.objects.update_or_create(
            version="2025.1",
            defaults={
                "changelog": "2025/26 uprating: Employer NIC secondary threshold and rate change "
                "(Autumn Budget 2024), Employment Allowance increase.",
                "effective_date": datetime.date(2025, 4, 6),
                "status": status,
                "editor": editor,
                "reviewer": reviewer if mark_released else None,
            },
        )
        release_iht, _ = RuleBaseRelease.objects.update_or_create(
            version="2025.2",
            defaults={
                "changelog": "IHT module: nil-rate band and residence nil-rate band parameters "
                "(frozen through 2029/30 per FA 2025), death/reduced-rate/lifetime rates, gift "
                "exemptions and taper relief schedule; strategies for spouse exemption with "
                "transferable bands, lifetime gifting (PETs), and the 36% charitable rate.",
                "effective_date": datetime.date(2026, 7, 4),
                "status": status,
                "editor": editor,
                "reviewer": reviewer if mark_released else None,
            },
        )
        release_property, _ = RuleBaseRelease.objects.update_or_create(
            version="2025.3",
            defaults={
                "changelog": "Property/CGT module: CGT annual exempt amount and rates "
                "(post-30 Oct 2024 alignment), SDLT residential bands with the 5% "
                "additional-dwellings surcharge and first-time buyers' relief; strategies "
                "for private residence relief, spousal transfer before disposal, and SDLT "
                "purchase planning.",
                "effective_date": datetime.date(2026, 7, 4),
                "status": status,
                "editor": editor,
                "reviewer": reviewer if mark_released else None,
            },
        )
        return release_2024, release_2025, release_iht, release_property

    def _create_authorities(self) -> dict[str, Authority]:
        specs = [
            dict(
                key="ita2007_s35",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax Act 2007 s.35",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2007/3/section/35",
                verbatim_extract="Entitlement to personal allowance for those born after 5 April 1948, "
                "and its reduction under section 35(2) where adjusted net income exceeds the income limit.",
            ),
            dict(
                key="ita2007_s10",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax Act 2007 s.10",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2007/3/section/10",
                verbatim_extract="Basic rate, higher rate, and additional rate of income tax on "
                "non-savings, non-dividend income.",
            ),
            dict(
                key="ittoia2005_s383",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="ITTOIA 2005 s.383",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2005/5/section/383",
                verbatim_extract="Charge to tax on dividends and other distributions of a UK resident company.",
            ),
            dict(
                key="ita2007_s13a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax Act 2007 s.13A",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2007/3/section/13A",
                verbatim_extract="Dividend nil rate: the dividend allowance against which dividend "
                "income is charged at 0%, introduced by Finance Act 2016 s.5.",
            ),
            dict(
                key="sscba1992_s6",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Social Security Contributions and Benefits Act 1992 s.6",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/4/section/6",
                verbatim_extract="Liability for Class 1 primary and secondary National Insurance "
                "contributions on earnings from employment.",
            ),
            dict(
                key="sscba1992_s15",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Social Security Contributions and Benefits Act 1992 s.15",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/4/section/15",
                verbatim_extract="Class 4 National Insurance contributions on profits of a trade, "
                "profession or vocation carried on by a self-employed earner.",
            ),
            dict(
                key="nica2014_s1",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="National Insurance Contributions Act 2014 s.1",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2014/7/section/1",
                verbatim_extract="Employment Allowance against employer Class 1 NIC liability, "
                "subject to the excluded-companies regulations (SI 2016/344), which exclude a "
                "company whose sole employee is also a director.",
            ),
            dict(
                key="cta2010_part3a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Corporation Tax Act 2010 Part 3A (ss.18A-18M)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2010/4/part/3A",
                verbatim_extract="Small profits rate and marginal relief on corporation tax profits, "
                "reintroduced with effect from 1 April 2023 by Finance Act 2021 s.7 and Sch.1.",
            ),
            dict(
                key="fa2004_s228",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Finance Act 2004 s.228",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2004/12/section/228",
                verbatim_extract="The annual allowance for tax-relieved pension savings, and (via "
                "s.228ZA, inserted by Finance (No.2) Act 2015) its tapering for high-income individuals.",
            ),
            dict(
                key="tcga1992_s58",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Taxation of Chargeable Gains Act 1992 s.58",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/12/section/58",
                verbatim_extract="Disposals between spouses or civil partners living together "
                "are treated as made for a consideration giving neither gain nor loss.",
            ),
            dict(
                key="tcga1992_s222",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Taxation of Chargeable Gains Act 1992 ss.222-223",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/12/section/222",
                verbatim_extract="Relief on disposal of a dwelling-house that is or has been "
                "the individual's only or main residence; s.223(2) treats the final nine "
                "months of ownership as qualifying in any event.",
            ),
            dict(
                key="tcga1992_s1h",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Taxation of Chargeable Gains Act 1992 ss.1H-1K",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/12/section/1H",
                verbatim_extract="Rates of capital gains tax by reference to unused basic-rate "
                "band, and the annual exempt amount (s.1K).",
            ),
            dict(
                key="fa2003_s55",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Finance Act 2003 s.55 and Sch 4ZA",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/14/section/55",
                verbatim_extract="Amount of stamp duty land tax chargeable on residential "
                "property; Schedule 4ZA imposes higher rates for additional dwellings, "
                "refundable where a main residence is replaced within three years.",
            ),
            dict(
                key="fa2003_sch6za",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Finance Act 2003 Sch 6ZA",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/14/schedule/6ZA",
                verbatim_extract="Relief for first-time buyers: no SDLT up to the relief "
                "threshold and a reduced rate above it, unavailable where the price exceeds "
                "the cap.",
            ),
            dict(
                key="jones_v_garnett_2007",
                authority_type=Authority.AuthorityType.COURT_JUDGMENT,
                canonical_citation="Jones v Garnett (Arctic Systems) [2007] UKHL 35",
                canonical_uri="https://caselaw.nationalarchives.gov.uk/ukhl/2007/35",
                verbatim_extract="The House of Lords held that the ordinary-share arrangement "
                "between spouses was a settlement within ITTOIA 2005 s.620, but fell within the "
                "s.626 outright-gifts-between-spouses exemption because the shares were not "
                "wholly or substantially a right to income. Dividend income splitting through "
                "ordinary shares held by a spouse therefore stands, subject to the arrangement "
                "involving full ordinary shares rather than income-only rights.",
            ),
            dict(
                key="ihta1984_s18",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 s.18",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/section/18",
                verbatim_extract="Transfers between spouses or civil partners are exempt "
                "transfers (unlimited where the transferee is UK-domiciled).",
            ),
            dict(
                key="ihta1984_s3a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 s.3A",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/section/3A",
                verbatim_extract="A potentially exempt transfer becomes an exempt transfer if "
                "the transferor survives seven years; otherwise it is a chargeable transfer.",
            ),
            dict(
                key="ihta1984_s7",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 s.7 and Sch 1",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/section/7",
                verbatim_extract="Rates of tax, including taper relief under s.7(4) reducing the "
                "tax charged on chargeable transfers made three to seven years before death.",
            ),
            dict(
                key="ihta1984_s8a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 s.8A",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/section/8A",
                verbatim_extract="Transfer of unused nil-rate band between spouses and civil "
                "partners: the survivor's nil-rate band is increased by the unused percentage.",
            ),
            dict(
                key="ihta1984_s8d",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 s.8D",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/section/8D",
                verbatim_extract="Residence nil-rate amount where a qualifying residential "
                "interest is closely inherited; tapered by £1 for every £2 the estate exceeds "
                "the taper threshold.",
            ),
            dict(
                key="ihta1984_s19",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 s.19",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/section/19",
                verbatim_extract="Annual exemption: transfers of value up to £3,000 in a tax "
                "year are exempt; unused exemption carries forward one year.",
            ),
            dict(
                key="ihta1984_sch1a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 Sch 1A",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/schedule/1A",
                verbatim_extract="Where at least 10% of the baseline amount passes to charity, "
                "inheritance tax is charged at 36% instead of 40%.",
            ),
            dict(
                key="fa2004_s190",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Finance Act 2004 s.190",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2004/12/section/190",
                verbatim_extract="The maximum amount of relief for an individual's pension "
                "contributions in a tax year is the greater of the basic amount (£3,600) and "
                "the individual's relevant UK earnings chargeable to income tax for that year.",
            ),
            dict(
                key="cta2009_s54",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Corporation Tax Act 2009 s.54",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2009/4/section/54",
                verbatim_extract="No deduction is allowed for expenses not incurred wholly and "
                "exclusively for the purposes of the trade — the condition governing "
                "deductibility of employer pension contributions as part of a reasonable "
                "remuneration package.",
            ),
            dict(
                key="ita2007_s55b",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax Act 2007 ss.55B-55E",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
                verbatim_extract="Transferable tax allowance for married couples and civil partners "
                "(Marriage Allowance), inserted by Finance Act 2014 s.11.",
            ),
        ]
        result = {}
        for spec in specs:
            key = spec.pop("key")
            authority, _ = Authority.objects.update_or_create(
                canonical_citation=spec["canonical_citation"],
                defaults={
                    **spec,
                    "date_retrieved": datetime.date.today(),
                    "status": Authority.Status.IN_FORCE,
                    "notes": REVIEW_NOTE,
                },
            )
            result[key] = authority
        return result

    def _create_parameters(self, release_2024, release_2025):
        y2024 = Range(datetime.date(2024, 4, 6), datetime.date(2025, 4, 6), bounds="[)")
        y2025 = Range(datetime.date(2025, 4, 6), None, bounds="[)")

        rows = [
            # key, label, domain, payload (same for both years unless noted), only_2025_payload=None
            ("income_tax.personal_allowance", "Personal Allowance", TaxDomain.PERSONAL_INCOME_TAX,
             {"amount": 12570, "taper_threshold": 100000, "taper_rate": 0.5}, None),
            ("income_tax.bands", "Income tax bands (non-savings, non-dividend)", TaxDomain.PERSONAL_INCOME_TAX,
             {"bands": [{"upper": 37700, "rate": 0.20}, {"upper": 125140, "rate": 0.40}, {"upper": None, "rate": 0.45}]},
             None),
            ("dividend_tax.allowance", "Dividend allowance", TaxDomain.PERSONAL_INCOME_TAX,
             {"amount": 500}, None),
            ("dividend_tax.bands", "Dividend tax bands", TaxDomain.PERSONAL_INCOME_TAX,
             {"bands": [{"upper": 37700, "rate": 0.0875}, {"upper": 125140, "rate": 0.3375}, {"upper": None, "rate": 0.3935}]},
             None),
            ("income_tax.marriage_allowance", "Marriage Allowance transferable amount", TaxDomain.PERSONAL_INCOME_TAX,
             {"transferable_amount": 1260}, None),
            ("national_insurance.employee_class1", "Employee Class 1 NIC", TaxDomain.PERSONAL_INCOME_TAX,
             {"primary_threshold": 12570, "upper_earnings_limit": 50270, "rate": 0.08, "upper_rate": 0.02}, None),
            ("national_insurance.employer_class1", "Employer (secondary) Class 1 NIC", TaxDomain.CORPORATION_TAX,
             {"secondary_threshold": 9100, "rate": 0.138},
             {"secondary_threshold": 5000, "rate": 0.15}),
            ("national_insurance.employment_allowance", "Employment Allowance", TaxDomain.CORPORATION_TAX,
             {"amount": 5000}, {"amount": 10500}),
            ("national_insurance.class4", "Class 4 NIC (self-employed)", TaxDomain.PERSONAL_INCOME_TAX,
             {"lower_profits_limit": 12570, "upper_profits_limit": 50270, "rate": 0.06, "upper_rate": 0.02}, None),
            ("corporation_tax.rates", "Corporation tax rates and marginal relief", TaxDomain.CORPORATION_TAX,
             {"small_profits_rate": 0.19, "small_profits_limit": 50000, "main_rate": 0.25,
              "main_rate_limit": 250000, "marginal_relief_fraction": 0.015}, None),
            ("pension.annual_allowance", "Pension annual allowance and taper", TaxDomain.PERSONAL_INCOME_TAX,
             {"standard_amount": 60000, "taper_threshold_income": 200000,
              "taper_adjusted_income_limit": 260000, "minimum_tapered_amount": 10000}, None),
        ]

        for key, label, domain, payload_2024, payload_2025 in rows:
            TaxParameter.objects.filter(key=key, effective_range=y2024).delete()
            TaxParameter.objects.filter(key=key, effective_range=y2025).delete()
            TaxParameter.objects.create(
                key=key, label=label, tax_domain=domain, effective_range=y2024,
                payload=payload_2024, risk_classification=RiskStatus.SETTLED,
                introduced_in_release=release_2024,
            )
            TaxParameter.objects.create(
                key=key, label=label, tax_domain=domain, effective_range=y2025,
                payload=payload_2025 if payload_2025 is not None else payload_2024,
                risk_classification=RiskStatus.SETTLED, introduced_in_release=release_2025,
            )

    def _create_iht_parameters(self, release_iht):
        y2024 = Range(datetime.date(2024, 4, 6), datetime.date(2025, 4, 6), bounds="[)")
        y2025 = Range(datetime.date(2025, 4, 6), None, bounds="[)")

        rows = [
            ("iht.nil_rate_band", "IHT nil-rate band (frozen through 2029/30)",
             {"amount": 325000}),
            ("iht.residence_nil_rate_band", "IHT residence nil-rate band and taper",
             {"amount": 175000, "taper_threshold": 2000000, "taper_rate": 0.5}),
            ("iht.rates", "IHT rates: death, reduced charitable, lifetime CLT",
             {"death_rate": 0.40, "reduced_charity_rate": 0.36,
              "charity_baseline_fraction": 0.10, "lifetime_clt_rate": 0.20}),
            ("iht.gift_exemptions", "IHT gift exemptions and PET taper relief",
             {"annual_exemption": 3000, "small_gift_exemption": 250,
              "taper_relief": [
                  {"years_survived_from": 3, "years_survived_to": 4, "tax_reduction": 0.20},
                  {"years_survived_from": 4, "years_survived_to": 5, "tax_reduction": 0.40},
                  {"years_survived_from": 5, "years_survived_to": 6, "tax_reduction": 0.60},
                  {"years_survived_from": 6, "years_survived_to": 7, "tax_reduction": 0.80},
              ]}),
        ]
        for key, label, payload in rows:
            for effective_range in (y2024, y2025):
                TaxParameter.objects.filter(key=key, effective_range=effective_range).delete()
                TaxParameter.objects.create(
                    key=key, label=label, tax_domain=TaxDomain.INHERITANCE_TAX,
                    effective_range=effective_range, payload=payload,
                    risk_classification=RiskStatus.SETTLED,
                    introduced_in_release=release_iht,
                )

    def _create_property_parameters(self, release_property):
        # 2025/26 onward only: the 2024/25 CGT year had mid-year rate changes
        # (30 Oct 2024) that the effective-dating model would need intra-year
        # ranges to represent honestly; deferred until prior-year CGT
        # computations are in scope.
        y2025 = Range(datetime.date(2025, 4, 6), None, bounds="[)")

        rows = [
            ("cgt.annual_exempt_amount", "CGT annual exempt amount",
             {"amount": 3000}),
            ("cgt.rates", "CGT rates by asset class (lower = within basic band)",
             {"residential": {"lower": 0.18, "higher": 0.24},
              "other": {"lower": 0.18, "higher": 0.24}}),
            ("sdlt.residential_bands", "SDLT residential bands, surcharge, FTB relief (England/NI)",
             {"bands": [
                 {"upper": 125000, "rate": 0.0},
                 {"upper": 250000, "rate": 0.02},
                 {"upper": 925000, "rate": 0.05},
                 {"upper": 1500000, "rate": 0.10},
                 {"upper": None, "rate": 0.12},
             ],
              "additional_dwelling_surcharge": 0.05,
              "first_time_buyer": {"relief_threshold": 300000, "cap": 500000,
                                   "rate_above_threshold": 0.05}}),
        ]
        for key, label, payload in rows:
            TaxParameter.objects.filter(key=key, effective_range=y2025).delete()
            TaxParameter.objects.create(
                key=key, label=label, tax_domain=TaxDomain.PROPERTY_TAXES,
                effective_range=y2025, payload=payload,
                risk_classification=RiskStatus.SETTLED,
                introduced_in_release=release_property,
            )

    def _create_strategies(self, release_2024, release_iht, release_property, authorities):
        open_range = Range(datetime.date(2024, 4, 6), None, bounds="[)")

        specs = [
            dict(
                code="salary-dividend-mix",
                name="Salary/dividend extraction mix",
                tax_domain=TaxDomain.CROSS_CUTTING,
                calculator_key="strategy.salary_dividend_mix",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="An owner-manager can choose how much of their reward is taken as salary "
                "(deductible against corporation tax, but subject to employer/employee NIC) versus "
                "dividends (paid from post-tax company profit, no NIC, taxed at dividend rates). "
                "Comparing the combined company and personal tax cost across salary levels identifies "
                "the extraction mix with the lowest total tax and NIC for the profit available.",
                authority_keys=["sscba1992_s6", "cta2010_part3a", "ita2007_s13a", "ita2007_s35", "jones_v_garnett_2007"],
                eligibility_conditions={"all": [{"path": "company.profit_before_remuneration", "op": "gt", "value": 0}]},
            ),
            dict(
                code="pension-annual-allowance-carry-forward",
                name="Pension annual allowance carry-forward",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.pension_annual_allowance_carry_forward",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Unused pension annual allowance from the three preceding tax years can be "
                "carried forward, allowing a larger contribution in the current year. Personal "
                "contributions attract relief only up to the greater of £3,600 and relevant UK "
                "earnings (employment and trading income; dividends do not count). Where earnings "
                "are the constraint, an employer contribution from the individual's own company "
                "avoids the cap entirely and is deductible against corporation tax, subject to the "
                "wholly-and-exclusively condition as part of a reasonable remuneration package.",
                authority_keys=["fa2004_s228", "fa2004_s190", "cta2009_s54"],
                eligibility_conditions={"all": [{"path": "pension.desired_contribution", "op": "gt", "value": 0}]},
            ),
            dict(
                code="incorporation-vs-sole-trade",
                name="Incorporation versus remaining a sole trader",
                tax_domain=TaxDomain.CROSS_CUTTING,
                calculator_key="strategy.incorporation_vs_sole_trade",
                timeframe=Timeframe.MEDIUM,
                risk_status=RiskStatus.BORDERLINE,
                dotas_notifiable=False,
                gaar_exposure=False,
                plain_english_explanation="Trading through a company rather than as a sole trader changes the tax base "
                "from income tax plus Class 4 NIC on all profits, to corporation tax on retained profit "
                "plus income tax/NIC only on amounts extracted as salary or dividends. Whether this saves "
                "tax depends on profit level and how much is drawn out; HMRC scrutinises incorporations "
                "that appear to have no commercial purpose beyond tax saving.",
                authority_keys=["sscba1992_s15", "cta2010_part3a", "ita2007_s35"],
                eligibility_conditions={"all": [{"path": "sole_trade.annual_profit", "op": "gt", "value": 0}]},
            ),
            dict(
                code="marriage-allowance-transfer",
                name="Marriage Allowance transfer",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.marriage_allowance_transfer",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Where one spouse or civil partner does not use their full personal allowance "
                "and the other is a basic-rate taxpayer, 10% of the unused allowance can be transferred, "
                "reducing the recipient's tax bill by a fixed amount.",
                authority_keys=["ita2007_s55b"],
                eligibility_conditions={"all": [{"path": "personal.spouse_income", "op": "gt", "value": 0}]},
            ),
            dict(
                code="iht-spousal-transfer-and-nil-rate-bands",
                name="Spouse exemption and transferable nil-rate bands",
                tax_domain=TaxDomain.INHERITANCE_TAX,
                calculator_key="strategy.iht_spousal_transfer_nil_rate_bands",
                timeframe=Timeframe.LONG,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Transfers between spouses or civil partners are wholly exempt from "
                "inheritance tax, and any nil-rate band and residence nil-rate band unused on the "
                "first death transfers to the survivor. Leaving the estate to the surviving spouse "
                "defers all tax to the second death, where up to double both bands (currently "
                "£650,000 plus £350,000 where the home passes to direct descendants) shelter the "
                "combined estate. The transferred bands must be claimed by the survivor's personal "
                "representatives within two years.",
                authority_keys=["ihta1984_s18", "ihta1984_s8a", "ihta1984_s8d"],
                eligibility_conditions={"all": [{"path": "estate.combined_estate_second_death", "op": "gt", "value": 0}]},
                release=release_iht,
            ),
            dict(
                code="iht-lifetime-gifting-pets",
                name="Lifetime gifting: exemptions and potentially exempt transfers",
                tax_domain=TaxDomain.INHERITANCE_TAX,
                calculator_key="strategy.iht_lifetime_gifting",
                timeframe=Timeframe.LONG,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Outright lifetime gifts to individuals are potentially exempt transfers: "
                "no tax if the donor survives seven years, with taper relief reducing the tax (not "
                "the transfer) where death occurs in years three to seven and the gift exceeds the "
                "nil-rate band. The first £3,000 given each tax year is immediately exempt, plus "
                "one year's unused prior exemption. The donor must not retain a benefit in the "
                "gifted asset, or the gift-with-reservation rules put it back in the estate.",
                authority_keys=["ihta1984_s3a", "ihta1984_s19", "ihta1984_s7"],
                eligibility_conditions={"all": [{"path": "estate.planned_lifetime_gift", "op": "gt", "value": 0}]},
                release=release_iht,
            ),
            dict(
                code="iht-charitable-legacy-reduced-rate",
                name="Charitable legacy and the 36% reduced rate",
                tax_domain=TaxDomain.INHERITANCE_TAX,
                calculator_key="strategy.iht_charitable_legacy_reduced_rate",
                timeframe=Timeframe.MEDIUM,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Where at least 10% of the baseline amount of the estate is left to "
                "charity, the whole taxable estate is charged at 36% rather than 40%. Because the "
                "charitable legacy is itself exempt, topping a smaller legacy up to the 10% "
                "threshold often costs the residuary beneficiaries far less than the legacy's face "
                "value, and in some estates makes them better off outright.",
                authority_keys=["ihta1984_sch1a"],
                eligibility_conditions={"any": [
                    {"path": "estate.combined_estate_second_death", "op": "gt", "value": 0},
                    {"path": "estate.gross_value", "op": "gt", "value": 0},
                ]},
                release=release_iht,
            ),
        ]

        for spec in specs:
            authority_keys = spec.pop("authority_keys")
            eligibility_conditions = spec.pop("eligibility_conditions")
            release = spec.pop("release", release_2024)
            strategy, _ = Strategy.objects.update_or_create(
                code=spec["code"],
                defaults={
                    **{k: v for k, v in spec.items() if k != "code"},
                    "eligibility_conditions": eligibility_conditions,
                    "effective_range": open_range,
                    "introduced_in_release": release,
                },
            )
            strategy.authorities.set([authorities[k] for k in authority_keys])

    def _create_golden_cases(self):
        cases = [
            dict(
                calculator_key="income_tax_on_earned_income",
                description="Basic rate taxpayer, no taper, 2025/26",
                source="Hand-computed from published 2025/26 rates",
                input_facts={"total_income": 50000},
                expected_output={"tax_due": 7486.0},
            ),
            dict(
                calculator_key="income_tax_on_earned_income",
                description="Additional rate taxpayer, personal allowance fully tapered away, 2025/26",
                source="Hand-computed from published 2025/26 rates",
                input_facts={"total_income": 130000},
                expected_output={"tax_due": 44703.0, "personal_allowance": 0.0},
            ),
            dict(
                calculator_key="dividend_tax",
                description="Dividend allowance absorbed within basic-rate band, 2025/26",
                source="Hand-computed from published 2025/26 rates",
                input_facts={"other_taxable_income": 30000, "dividend_income": 20000},
                expected_output={"tax_due": 4781.25},
            ),
            dict(
                calculator_key="employee_class1_nic",
                description="Salary above UEL, 2025/26",
                source="Hand-computed from published 2025/26 rates",
                input_facts={"annual_salary": 60000},
                expected_output={"nic_due": 3210.6},
            ),
            dict(
                calculator_key="employer_class1_nic",
                description="Salary above secondary threshold, no Employment Allowance, 2025/26",
                source="Hand-computed from published 2025/26 rates",
                input_facts={"annual_salary": 60000, "employment_allowance_available": False},
                expected_output={"nic_due": 8250.0},
            ),
            dict(
                calculator_key="corporation_tax",
                description="Profit within marginal relief band, 2025/26",
                source="Hand-computed from published FY2023-onwards rates",
                input_facts={"taxable_profit": 100000},
                expected_output={"tax_due": 22750.0, "marginal_relief": 2250.0},
            ),
            dict(
                calculator_key="combined_personal_tax",
                description="Earned income and dividends together, no taper, 2025/26",
                source="Hand-computed: earned 40,000 (tax 5,486) + dividends 60,000 stacked "
                "above taxable earned 27,430 (10,270 in basic band at 8.75%, remainder at "
                "33.75%, less 500 allowance relief at 8.75%)",
                input_facts={"earned_income": 40000, "dividend_income": 60000},
                expected_output={
                    "earned_tax": 5486.0,
                    "dividend_tax_due": 17638.75,
                    "total_tax": 23124.75,
                    "personal_allowance": 12570,
                },
            ),
            dict(
                calculator_key="combined_personal_tax",
                description="Dividends push total income into personal allowance taper, 2025/26",
                source="Hand-computed: earned 28,000 + dividends 73,575 = 101,575 total; "
                "excess 1,575 halves PA by 787.50 to 11,782.50",
                input_facts={"earned_income": 28000, "dividend_income": 73575},
                expected_output={
                    "personal_allowance": 11782.50,
                    "earned_tax": 3243.50,
                    "dividend_tax_due": 19417.19,
                    "total_tax": 22660.69,
                },
            ),
            dict(
                calculator_key="iht_estate_liability",
                description="Single person, home to children, NRB + RNRB both fully available",
                source="Hand-computed: 800,000 estate - 325,000 NRB - 175,000 RNRB (home 300,000 "
                "caps nothing) = 300,000 at 40%",
                input_facts={
                    "gross_estate_value": 800000,
                    "home_equity_value": 300000,
                    "home_passes_to_direct_descendants": True,
                },
                expected_output={
                    "nil_rate_band": 325000.0,
                    "residence_nil_rate_band": 175000.0,
                    "taxable_amount": 300000.0,
                    "tax_due": 120000.0,
                },
            ),
            dict(
                calculator_key="iht_estate_liability",
                description="RNRB tapered: estate 200,000 over the 2m threshold",
                source="Hand-computed: RNRB 175,000 - (200,000 / 2) = 75,000; taxable "
                "2,200,000 - 325,000 - 75,000 = 1,800,000 at 40% = 720,000",
                input_facts={
                    "gross_estate_value": 2200000,
                    "home_equity_value": 400000,
                    "home_passes_to_direct_descendants": True,
                },
                expected_output={
                    "residence_nil_rate_band": 75000.0,
                    "taxable_amount": 1800000.0,
                    "tax_due": 720000.0,
                },
            ),
            dict(
                calculator_key="iht_estate_liability",
                description="Charitable legacy exactly 10% of baseline: 36% rate applies",
                source="Hand-computed: baseline 1,000,000 - 325,000 = 675,000; charity 67,500 "
                "qualifies; taxable 1,000,000 - 67,500 - 325,000 = 607,500 at 36% = 218,700 "
                "(vs 270,000 at 40% with no charity)",
                input_facts={
                    "gross_estate_value": 1000000,
                    "charitable_legacy": 67500,
                },
                expected_output={
                    "qualifies_reduced_charity_rate": True,
                    "rate_applied": 0.36,
                    "taxable_amount": 607500.0,
                    "tax_due": 218700.0,
                },
            ),
            dict(
                calculator_key="strategy.pension_annual_allowance_carry_forward",
                description="Owner-manager: desired contribution exceeds relevant earnings; employer route quantified, 2025/26",
                source="Hand-computed: desired 40,000 vs relevant earnings 28,000 -> relievable "
                "capped at 28,000 (FA 2004 s.190); AA 60,000 + 25,000 carry-forward = 85,000; "
                "employer contribution of 40,000 from 95,000 profit saves CT 21,425 - 10,825 = 10,600",
                input_facts={
                    "desired_contribution": 40000,
                    "earned_income": 28000,
                    "relevant_uk_earnings": 28000,
                    "dividend_income": 0,
                    "company_profit_before_remuneration": 95000,
                    "unused_aa_prior_3_years": [12000, 8000, 5000],
                },
                expected_output={
                    "available_annual_allowance": 85000.0,
                    "fits_within_allowance": True,
                    "personal_route": {
                        "relievable_gross": 28000.0,
                        "unrelieved_amount": 12000.0,
                        "basic_rate_credit_to_pension": 5600.0,
                        "personal_tax_saving": 0.0,
                        "total_relief_value": 5600.0,
                    },
                    "employer_route": {
                        "contribution": 40000.0,
                        "corporation_tax_saving": 10600.0,
                        "no_relevant_earnings_cap": True,
                    },
                },
            ),
            dict(
                calculator_key="strategy.marriage_allowance_transfer",
                description="Eligible transfer, 2025/26",
                source="Hand-computed from published 2025/26 rates",
                input_facts={"transferor_income": 8000, "transferee_income": 30000},
                expected_output={"eligible": True, "estimated_annual_tax_saving": 252.0},
            ),
        ]
        for case in cases:
            GoldenTestCase.objects.update_or_create(
                calculator_key=case["calculator_key"],
                description=case["description"],
                defaults={
                    "source": case["source"],
                    "input_facts": case["input_facts"],
                    "expected_output": case["expected_output"],
                },
            )
