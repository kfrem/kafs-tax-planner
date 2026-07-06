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
            (
                release_2024,
                release_2025,
                release_iht,
                release_property,
                release_cgt_2024,
                release_2026,
            ) = self._create_releases(editor, reviewer, options["release"])
            authorities = self._create_authorities()
            self._create_parameters(release_2024, release_2025, release_2026)
            self._create_iht_parameters(release_iht)
            self._create_property_parameters(
                release_property, release_cgt_2024, release_2026
            )
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
        release_cgt_2024, _ = RuleBaseRelease.objects.update_or_create(
            version="2024.2",
            defaults={
                "changelog": "2024/25 CGT rates, including the 30 October 2024 intra-year "
                "change: non-residential/other-asset gains rise from 10%/20% to 18%/24% for "
                "disposals on or after 30 October 2024 (Autumn Budget 2024); residential "
                "rates stay 18%/24% throughout. Modelled as two intra-year effective ranges.",
                "effective_date": datetime.date(2024, 4, 6),
                "status": status,
                "editor": editor,
                "reviewer": reviewer if mark_released else None,
            },
        )
        release_2026, _ = RuleBaseRelease.objects.update_or_create(
            version="2026.1",
            defaults={
                "changelog": "2026/27 scaffolding: Business Asset Disposal Relief rate rises "
                "from 14% to 18% for disposals on or after 6 April 2026 (Finance Act 2025). "
                "First future-tax-year release — other 2025/26 parameters carry forward on "
                "their open effective ranges until a confirmed 2026/27 figure closes them.",
                "effective_date": datetime.date(2026, 4, 6),
                "status": status,
                "editor": editor,
                "reviewer": reviewer if mark_released else None,
            },
        )
        return (
            release_2024,
            release_2025,
            release_iht,
            release_property,
            release_cgt_2024,
            release_2026,
        )

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
                key="cta2010_s455",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Corporation Tax Act 2010 s.455",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2010/4/section/455",
                verbatim_extract="Charge to tax where a close company makes a loan or advance "
                "to a participator (e.g. a director-shareholder): the company pays tax on the "
                "amount outstanding at the rate in s.455, currently 33.75%. The charge falls "
                "due 9 months and 1 day after the end of the accounting period, and is "
                "repaid under s.458 when the loan is repaid or written off.",
            ),
            dict(
                key="caa2001_s51a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Capital Allowances Act 2001 s.51A",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2001/2/section/51A",
                verbatim_extract="Entitlement to the annual investment allowance: 100% relief "
                "on qualifying expenditure on plant and machinery up to the AIA maximum for "
                "the chargeable period. Expenditure above the maximum is relieved through the "
                "capital allowance pools at the writing-down allowance rates (s.56).",
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
                verbatim_extract="Disposals between spouses or civil partners are on a "
                "no-gain/no-loss basis: while living together; where separated, until the "
                "end of the third tax year after the tax year of separation; and without "
                "time limit where made under a formal divorce/dissolution agreement or "
                "court order (as substituted by Finance (No.2) Act 2023 s.41 for disposals "
                "from 6 April 2023).",
            ),
            dict(
                key="tcga1992_s169h",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Taxation of Chargeable Gains Act 1992 ss.169H-169S",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/12/section/169H",
                verbatim_extract="Business Asset Disposal Relief: a qualifying business "
                "disposal (s.169I) is charged to capital gains tax at the reduced rate in "
                "s.169N, subject to a 1,000,000 lifetime limit on qualifying gains. The "
                "reduced rate is 14% for disposals on or after 6 April 2025 (10% before "
                "that date; 18% from 6 April 2026).",
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
                key="tcga1992_s223b",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Taxation of Chargeable Gains Act 1992 s.223B",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/12/section/223B",
                verbatim_extract="Additional relief where part of the dwelling-house is the "
                "individual's only or main residence and another part is let as residential "
                "accommodation: the let-portion gain is relieved by the lowest of that gain, "
                "the s.223 private residence relief, and 40,000. For disposals from 6 April "
                "2020 the relief requires shared occupancy with the tenant.",
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
                key="lbtt_scotland_act_2013_s24",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Land and Buildings Transaction Tax (Scotland) Act 2013 s.24",
                canonical_uri="https://www.legislation.gov.uk/asp/2013/11/section/24",
                verbatim_extract="Empowers the Scottish Ministers to set, by order, the tax "
                "bands and percentage rates for Land and Buildings Transaction Tax, "
                "including a nil-rate band for residential transactions; the Additional "
                "Dwelling Supplement (Schedule 2A) and first-time buyer relief operate "
                "alongside these rates.",
            ),
            dict(
                key="ltt_wales_act_2017_s24",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Land Transaction Tax and Anti-avoidance of Devolved "
                "Taxes (Wales) Act 2017 s.24",
                canonical_uri="https://www.legislation.gov.uk/anaw/2017/1/section/24",
                verbatim_extract="Empowers the Welsh Ministers to specify, by regulations, "
                "the tax bands and percentage rates for Land Transaction Tax across three "
                "categories: residential, higher-rates residential (additional properties), "
                "and non-residential transactions.",
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
                canonical_uri="https://www.bailii.org/uk/cases/UKHL/2007/35.html",
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
                # Added at editorial review (05/07/2026): s.8A transfers the
                # ordinary NRB; the parallel RNRB transfer needed citing too.
                key="ihta1984_s8g",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 s.8G",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/section/8G",
                verbatim_extract="Transfer of any unused residence nil-rate amount to a "
                "surviving spouse or civil partner, by claim, mirroring the s.8A transfer "
                "of the ordinary nil-rate band.",
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
                canonical_citation="Income Tax Act 2007 ss.55A-55E",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2007/3/section/55A",
                verbatim_extract="Transferable tax allowance for married couples and civil partners "
                "(Marriage Allowance), inserted by Finance Act 2014 s.11.",
            ),
            dict(
                key="ita2007_s414",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax Act 2007 s.414",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2007/3/section/414",
                verbatim_extract="Gift Aid: a qualifying donation is treated as made after "
                "deduction of basic-rate income tax; the individual's basic-rate limit (and "
                "higher-rate limit) are increased by the grossed-up amount, giving relief to "
                "higher and additional-rate taxpayers. The grossed-up gift also reduces "
                "adjusted net income for the personal-allowance taper.",
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

    def _create_parameters(self, release_2024, release_2025, release_2026):
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
            ("directors_loan.s455", "Directors' loan s.455 charge rate", TaxDomain.CORPORATION_TAX,
             {"rate": 0.3375, "beneficial_loan_threshold": 10000}, None),
            ("capital_allowances.aia", "Capital allowances: AIA limit and writing-down rates",
             TaxDomain.CORPORATION_TAX,
             {"aia_limit": 1000000, "main_pool_wda": 0.18, "special_rate_wda": 0.06}, None),
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

        # Dividend tax rates rise 2 percentage points on 6 April 2026 (Budget
        # 2025): ordinary 8.75% -> 10.75%, upper 33.75% -> 35.75%; the
        # additional rate (39.35%), the band thresholds and the £500 allowance
        # are unchanged. Per A5 a rate change is a new row, so the 2025/26 row
        # is CLOSED at 6 April 2026 and the 2026/27 row opens under 2026.1.
        div_2024_25 = {"bands": [
            {"upper": 37700, "rate": 0.0875}, {"upper": 125140, "rate": 0.3375},
            {"upper": None, "rate": 0.3935},
        ]}
        div_2026 = {"bands": [
            {"upper": 37700, "rate": 0.1075}, {"upper": 125140, "rate": 0.3575},
            {"upper": None, "rate": 0.3935},
        ]}
        dividend_rows = [
            (y2024, div_2024_25, release_2024),
            (Range(datetime.date(2025, 4, 6), datetime.date(2026, 4, 6), bounds="[)"),
             div_2024_25, release_2025),
            (Range(datetime.date(2026, 4, 6), None, bounds="[)"), div_2026, release_2026),
        ]
        TaxParameter.objects.filter(key="dividend_tax.bands").delete()
        for effective_range, payload, release in dividend_rows:
            TaxParameter.objects.create(
                key="dividend_tax.bands", label="Dividend tax bands",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX, effective_range=effective_range,
                payload=payload, risk_classification=RiskStatus.SETTLED,
                introduced_in_release=release,
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

    def _create_property_parameters(self, release_property, release_cgt_2024, release_2026):
        y2025 = Range(datetime.date(2025, 4, 6), None, bounds="[)")

        # 2024/25 CGT with the 30 October 2024 intra-year change. The engine
        # resolves these by disposal date (get_parameter as_of=...), so a
        # non-residential disposal before 30 Oct 2024 is taxed at 10%/20% and
        # one on/after at 18%/24%; residential is 18%/24% throughout. This is
        # the intra-year effective-range case the module previously deferred.
        cgt_2024_h1 = Range(datetime.date(2024, 4, 6), datetime.date(2024, 10, 30), bounds="[)")
        cgt_2024_h2 = Range(datetime.date(2024, 10, 30), datetime.date(2025, 4, 6), bounds="[)")
        cgt_2024_full = Range(datetime.date(2024, 4, 6), datetime.date(2025, 4, 6), bounds="[)")
        prior_cgt = [
            ("cgt.rates", "CGT rates by asset class (lower = within basic band)",
             cgt_2024_h1,
             {"residential": {"lower": 0.18, "higher": 0.24},
              "other": {"lower": 0.10, "higher": 0.20}}),
            ("cgt.rates", "CGT rates by asset class (lower = within basic band)",
             cgt_2024_h2,
             {"residential": {"lower": 0.18, "higher": 0.24},
              "other": {"lower": 0.18, "higher": 0.24}}),
            ("cgt.annual_exempt_amount", "CGT annual exempt amount",
             cgt_2024_full, {"amount": 3000}),
        ]
        for key, label, effective_range, payload in prior_cgt:
            TaxParameter.objects.filter(key=key, effective_range=effective_range).delete()
            TaxParameter.objects.create(
                key=key, label=label, tax_domain=TaxDomain.PROPERTY_TAXES,
                effective_range=effective_range, payload=payload,
                risk_classification=RiskStatus.SETTLED,
                introduced_in_release=release_cgt_2024,
            )

        rows = [
            ("cgt.annual_exempt_amount", "CGT annual exempt amount",
             {"amount": 3000}),
            ("cgt.rates", "CGT rates by asset class (lower = within basic band)",
             {"residential": {"lower": 0.18, "higher": 0.24},
              "other": {"lower": 0.18, "higher": 0.24}}),
            ("cgt.lettings_relief",
             "Lettings relief cap (shared-occupancy let, TCGA 1992 s.223B)",
             {"cap": 40000}),
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
            ("lbtt.residential_bands",
             "LBTT residential bands, Additional Dwelling Supplement, first-time buyer relief (Scotland)",
             {"bands": [
                 {"upper": 145000, "rate": 0.0},
                 {"upper": 250000, "rate": 0.02},
                 {"upper": 325000, "rate": 0.05},
                 {"upper": 750000, "rate": 0.10},
                 {"upper": None, "rate": 0.12},
             ],
              "additional_dwelling_supplement": 0.08,
              "first_time_buyer_nil_rate_threshold": 175000}),
            ("ltt.residential_bands",
             "LTT residential main and higher (additional-property) bands (Wales)",
             {"main_bands": [
                 {"upper": 225000, "rate": 0.0},
                 {"upper": 400000, "rate": 0.06},
                 {"upper": 750000, "rate": 0.075},
                 {"upper": 1500000, "rate": 0.10},
                 {"upper": None, "rate": 0.12},
             ],
              "higher_bands": [
                 {"upper": 180000, "rate": 0.05},
                 {"upper": 250000, "rate": 0.085},
                 {"upper": 400000, "rate": 0.10},
                 {"upper": 750000, "rate": 0.125},
                 {"upper": 1500000, "rate": 0.15},
                 {"upper": None, "rate": 0.17},
             ]}),
            ("sdlt.non_residential_bands",
             "SDLT non-residential/mixed freehold bands (England/NI)",
             {"bands": [
                 {"upper": 150000, "rate": 0.0},
                 {"upper": 250000, "rate": 0.02},
                 {"upper": None, "rate": 0.05},
             ]}),
            ("lbtt.non_residential_bands",
             "LBTT non-residential freehold bands (Scotland)",
             {"bands": [
                 {"upper": 150000, "rate": 0.0},
                 {"upper": 250000, "rate": 0.01},
                 {"upper": None, "rate": 0.05},
             ]}),
            ("ltt.non_residential_bands",
             "LTT non-residential freehold bands (Wales)",
             {"bands": [
                 {"upper": 225000, "rate": 0.0},
                 {"upper": 250000, "rate": 0.01},
                 {"upper": 1000000, "rate": 0.05},
                 {"upper": None, "rate": 0.06},
             ]}),
            ("sdlt.lease_npv_bands",
             "SDLT non-residential lease: NPV discount rate and bands (England/NI)",
             {"discount_rate": 0.035,
              "bands": [
                  {"upper": 150000, "rate": 0.0},
                  {"upper": 5000000, "rate": 0.01},
                  {"upper": None, "rate": 0.02},
              ]}),
            ("lbtt.lease_npv_bands",
             "LBTT lease: NPV discount rate and bands (Scotland)",
             {"discount_rate": 0.035,
              "bands": [
                  {"upper": 150000, "rate": 0.0},
                  {"upper": 2000000, "rate": 0.01},
                  {"upper": None, "rate": 0.02},
              ]}),
            ("ltt.lease_npv_bands",
             "LTT non-residential lease: NPV discount rate and bands (Wales)",
             {"discount_rate": 0.035,
              "bands": [
                  {"upper": 225000, "rate": 0.0},
                  {"upper": 2000000, "rate": 0.01},
                  {"upper": None, "rate": 0.02},
              ]}),
        ]
        for key, label, payload in rows:
            TaxParameter.objects.filter(key=key, effective_range=y2025).delete()
            TaxParameter.objects.create(
                key=key, label=label, tax_domain=TaxDomain.PROPERTY_TAXES,
                effective_range=y2025, payload=payload,
                risk_classification=RiskStatus.SETTLED,
                introduced_in_release=release_property,
            )

        # Business Asset Disposal Relief: the rate rises from 14% to 18% on
        # 6 April 2026 (Finance Act 2025). Per A5 a rate change is a NEW row,
        # so BADR is two non-overlapping effective-dated rows across the
        # tax-year boundary — the 2025/26 row is CLOSED at 6 April 2026, the
        # 2026/27 row opens there under the 2026.1 release. This is the first
        # future-tax-year row and the proof that the engine resolves rates by
        # tax year. Delete-all-by-key keeps the seed idempotent regardless of
        # any earlier single-row shape.
        badr_key = "cgt.business_asset_disposal_relief"
        badr_label = "Business Asset Disposal Relief: reduced CGT rate and lifetime limit"
        badr_rows = [
            (Range(datetime.date(2025, 4, 6), datetime.date(2026, 4, 6), bounds="[)"),
             {"rate": 0.14, "lifetime_limit": 1000000}, release_property),
            (Range(datetime.date(2026, 4, 6), None, bounds="[)"),
             {"rate": 0.18, "lifetime_limit": 1000000}, release_2026),
        ]
        TaxParameter.objects.filter(key=badr_key).delete()
        for effective_range, payload, release in badr_rows:
            TaxParameter.objects.create(
                key=badr_key, label=badr_label, tax_domain=TaxDomain.PROPERTY_TAXES,
                effective_range=effective_range, payload=payload,
                risk_classification=RiskStatus.SETTLED, introduced_in_release=release,
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
                code="directors-loan-s455",
                name="Directors' loan s.455 charge",
                tax_domain=TaxDomain.CORPORATION_TAX,
                calculator_key="strategy.directors_loan_s455",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Where a director-shareholder's loan account is "
                "overdrawn, the company faces a temporary 33.75% s.455 charge on any amount "
                "still outstanding 9 months and 1 day after the year end. Repaying the loan "
                "(or enough of it) within that window avoids the charge; the charge is "
                "refunded when the loan is later repaid. This quantifies the charge and the "
                "amount avoided by repaying in time.",
                authority_keys=["cta2010_s455"],
                eligibility_conditions={"all": [
                    {"path": "company.overdrawn_loan_balance", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="capital-allowances-aia",
                name="Capital allowances / Annual Investment Allowance",
                tax_domain=TaxDomain.CORPORATION_TAX,
                calculator_key="strategy.capital_allowances",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Qualifying spend on plant and machinery gets 100% "
                "tax relief in the year of purchase through the Annual Investment Allowance, "
                "up to the AIA limit (currently £1,000,000). Spend above that is written down "
                "at 18% a year in the main pool. This quantifies the first-year deduction and "
                "the tax it saves at the client's marginal rate — often a reason to time "
                "capital spend into a particular period.",
                authority_keys=["caa2001_s51a"],
                eligibility_conditions={"all": [
                    {"path": "company.qualifying_capital_spend", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="salary-sacrifice-into-pension",
                name="Salary sacrifice into an employer pension",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.salary_sacrifice",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="The employee gives up an agreed slice of salary and the "
                "employer pays that amount straight into the employee's pension. Because the salary "
                "is never received, the employee saves income tax and Class 1 NIC on it, and the "
                "employer saves secondary (employer) NIC — a saving the employer can also add to the "
                "pension. The whole sacrificed amount goes into the pension gross, so the net cost to "
                "the employee is well below the amount invested. This quantifies the employee's income "
                "tax and NIC saving, the employer's NIC saving, the amount into the pension and its "
                "net cost. (A valid arrangement must reduce contractual pay before it is earned and "
                "keep pay above the National Minimum Wage.)",
                authority_keys=["sscba1992_s6"],
                eligibility_conditions={"all": [
                    {"path": "personal.salary_sacrifice_amount", "op": "gt", "value": 0},
                ]},
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
                code="gift-aid-relief",
                name="Gift Aid higher-rate relief",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.gift_aid_relief",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="A Gift Aid donation is grossed up at the basic rate, "
                "which the charity reclaims. For a higher or additional-rate donor the grossed-up "
                "amount also extends the basic-rate band, giving personal relief of the difference "
                "between their rate and the basic rate. Where income is in the 100,000-125,140 "
                "personal-allowance taper, the donation also reduces adjusted net income and can "
                "restore some or all of the personal allowance.",
                authority_keys=["ita2007_s414"],
                eligibility_conditions={"all": [
                    {"path": "personal.gift_aid_donation", "op": "gt", "value": 0},
                ]},
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
                authority_keys=["ihta1984_s18", "ihta1984_s8a", "ihta1984_s8g", "ihta1984_s8d"],
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
            dict(
                code="cgt-ppr-relief",
                name="Private residence relief on property disposal",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.cgt_ppr_relief",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Gains on a property that has at some time been the owner's only or "
                "main residence are exempt for the periods of actual occupation plus the final "
                "nine months of ownership, apportioned over the total ownership period. Where a "
                "property was the main residence for part of the ownership, the relief often "
                "removes more of the gain than clients expect — and the occupation history "
                "should be evidenced before disposal.",
                authority_keys=["tcga1992_s222", "tcga1992_s1h"],
                eligibility_conditions={"all": [
                    {"path": "property.disposal_gain", "op": "gt", "value": 0},
                    {"path": "property.occupied_as_main_residence_months", "op": "gt", "value": 0},
                ]},
                release=release_property,
            ),
            dict(
                code="cgt-lettings-relief",
                name="Lettings relief (shared-occupancy let)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.cgt_lettings_relief",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Where the owner lets part of their only or main "
                "residence to a tenant while continuing to live in another part, lettings "
                "relief reduces the gain on the let portion by the lowest of that letting "
                "gain, the private residence relief due, and a 40,000 cap. Since 6 April "
                "2020 the relief is available only for periods of shared occupancy with the "
                "tenant — the former relief for letting a property after moving out has been "
                "withdrawn.",
                authority_keys=["tcga1992_s223b", "tcga1992_s222", "tcga1992_s1h"],
                eligibility_conditions={"all": [
                    {"path": "property.disposal_gain", "op": "gt", "value": 0},
                    {"path": "property.shared_occupancy_let_fraction", "op": "gt", "value": 0},
                ]},
                release=release_property,
            ),
            dict(
                code="cgt-timing-of-disposals",
                name="Timing of disposals across tax years",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.cgt_timing_of_disposals",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Where a divisible holding such as shares or fund "
                "units stands at a gain larger than the annual exempt amount, selling it in "
                "two tranches across two tax years uses two years' exemptions (and two "
                "basic-rate bands) instead of one, cutting the total CGT. A single indivisible "
                "asset such as one property cannot be split this way. Quantifies the saving "
                "from spreading the disposal.",
                authority_keys=["tcga1992_s1h"],
                eligibility_conditions={"all": [
                    {"path": "personal.divisible_capital_gain", "op": "gt", "value": 0},
                ]},
                release=release_property,
            ),
            dict(
                code="cgt-spousal-transfer-before-disposal",
                name="Spousal transfer before disposal",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.cgt_spousal_transfer_before_disposal",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Transfers between spouses or civil partners are at no gain/no loss, "
                "so a half share transferred before an arm's-length disposal uses both annual "
                "exempt amounts and both basic-rate bands. Since 6 April 2023 (F(No.2)A 2023 "
                "s.41) this treatment also covers separated couples until the end of the third "
                "tax year after the tax year of separation, and without time limit under a "
                "formal divorce agreement or court order. The transfer must be an outright "
                "gift of beneficial ownership made before any unconditional contract to sell "
                "exists.",
                authority_keys=["tcga1992_s58", "tcga1992_s1h"],
                eligibility_conditions={"all": [
                    {"path": "property.disposal_gain", "op": "gt", "value": 0},
                    {"path": "property.spouse_available_for_transfer", "op": "eq", "value": True},
                ]},
                release=release_property,
            ),
            dict(
                code="cgt-business-asset-disposal-relief",
                name="Business Asset Disposal Relief",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.cgt_business_asset_disposal_relief",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="On a qualifying disposal of all or part of a "
                "trading business, or of shares in a personal trading company, gains up to "
                "a 1,000,000 lifetime limit are taxed at a reduced flat CGT rate (14% for "
                "2025/26) instead of the standard 18%/24%. The qualifying conditions — a "
                "two-year minimum ownership period and, for shares, a 5% personal-company "
                "holding — must be met throughout that period. Gains above the lifetime "
                "limit are taxed at the normal rate, so the relief is worth up to ten "
                "percentage points on the first million pounds of qualifying gains.",
                authority_keys=["tcga1992_s169h", "tcga1992_s1h"],
                eligibility_conditions={"all": [
                    {"path": "property.badr_qualifying_gain", "op": "gt", "value": 0},
                ]},
                release=release_property,
            ),
            dict(
                code="sdlt-purchase-planning",
                name="SDLT on planned property purchase",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.sdlt_purchase_planning",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies the SDLT on a planned residential purchase in "
                "England or Northern Ireland, including the 5% additional-dwellings surcharge and "
                "first-time buyers' relief. Where the purchase replaces a main residence sold "
                "within three years, the surcharge is recoverable — timing the sale matters as "
                "much as the price. Scotland (LBTT) and Wales (LTT) set their own rates.",
                authority_keys=["fa2003_s55", "fa2003_sch6za"],
                eligibility_conditions={"all": [
                    {"path": "property.purchase_price", "op": "gt", "value": 0},
                    {"path": "property.jurisdiction", "op": "not_in", "value": ["scotland", "wales"]},
                ]},
                release=release_property,
            ),
            dict(
                code="lbtt-purchase-planning",
                name="LBTT on planned property purchase (Scotland)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.lbtt_purchase_planning",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies Land and Buildings Transaction Tax on a "
                "planned Scottish residential purchase, including the 8% Additional Dwelling "
                "Supplement on the whole price where a second dwelling is bought, and first-time "
                "buyer relief, which raises the nil-rate band to 175,000 and is worth up to 600. "
                "Scotland sets its own rates and bands, so the English SDLT figures do not apply "
                "north of the border.",
                authority_keys=["lbtt_scotland_act_2013_s24"],
                eligibility_conditions={"all": [
                    {"path": "property.purchase_price", "op": "gt", "value": 0},
                    {"path": "property.jurisdiction", "op": "eq", "value": "scotland"},
                ]},
                release=release_property,
            ),
            dict(
                code="ltt-purchase-planning",
                name="LTT on planned property purchase (Wales)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.ltt_purchase_planning",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies Land Transaction Tax on a planned Welsh "
                "residential purchase. Wales applies a separate set of higher-rate bands to "
                "additional dwellings rather than a flat surcharge, and has no first-time buyer "
                "relief; the main residential nil-rate band runs to 225,000. The devolved rates "
                "differ from both English SDLT and Scottish LBTT, so the property's jurisdiction "
                "governs the charge.",
                authority_keys=["ltt_wales_act_2017_s24"],
                eligibility_conditions={"all": [
                    {"path": "property.purchase_price", "op": "gt", "value": 0},
                    {"path": "property.jurisdiction", "op": "eq", "value": "wales"},
                ]},
                release=release_property,
            ),
            dict(
                code="sdlt-non-residential-purchase",
                name="SDLT on non-residential purchase (England/NI)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.sdlt_non_residential_purchase",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies the SDLT on a planned non-residential or "
                "mixed-use freehold purchase in England or Northern Ireland. Commercial rates run "
                "in bands (0% to 150,000, 2% to 250,000, 5% above) and — unlike residential — carry "
                "no additional-dwelling surcharge and no first-time buyer relief. A mixed-use "
                "property is charged wholly at these non-residential rates.",
                authority_keys=["fa2003_s55"],
                eligibility_conditions={"all": [
                    {"path": "property.purchase_price", "op": "gt", "value": 0},
                    {"path": "property.property_type", "op": "eq", "value": "non_residential"},
                    {"path": "property.jurisdiction", "op": "not_in", "value": ["scotland", "wales"]},
                ]},
                release=release_property,
            ),
            dict(
                code="lbtt-non-residential-purchase",
                name="LBTT on non-residential purchase (Scotland)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.lbtt_non_residential_purchase",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies the LBTT on a planned non-residential "
                "freehold purchase in Scotland. Commercial rates run in bands (0% to 150,000, 1% "
                "to 250,000, 5% above) — a lower middle band than the English SDLT — with no "
                "Additional Dwelling Supplement and no first-time buyer relief on non-residential "
                "property.",
                authority_keys=["lbtt_scotland_act_2013_s24"],
                eligibility_conditions={"all": [
                    {"path": "property.purchase_price", "op": "gt", "value": 0},
                    {"path": "property.property_type", "op": "eq", "value": "non_residential"},
                    {"path": "property.jurisdiction", "op": "eq", "value": "scotland"},
                ]},
                release=release_property,
            ),
            dict(
                code="ltt-non-residential-purchase",
                name="LTT on non-residential purchase (Wales)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.ltt_non_residential_purchase",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies the LTT on a planned non-residential "
                "freehold purchase in Wales. Commercial rates run in bands (0% to 225,000, 1% to "
                "250,000, 5% to 1,000,000, 6% above), so the Welsh charge has a higher nil-rate "
                "threshold but a top band the other regimes lack. There is no surcharge or "
                "first-time buyer relief on non-residential property.",
                authority_keys=["ltt_wales_act_2017_s24"],
                eligibility_conditions={"all": [
                    {"path": "property.purchase_price", "op": "gt", "value": 0},
                    {"path": "property.property_type", "op": "eq", "value": "non_residential"},
                    {"path": "property.jurisdiction", "op": "eq", "value": "wales"},
                ]},
                release=release_property,
            ),
            dict(
                code="sdlt-lease-npv",
                name="SDLT on a non-residential lease (England/NI)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.sdlt_lease_npv",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies the SDLT due on the grant of a "
                "non-residential lease in England or Northern Ireland. The rent is charged on "
                "its net present value over the term, discounted at 3.5%, with 0% up to "
                "150,000 of NPV, 1% to 5,000,000 and 2% above. Any lease premium is charged "
                "separately at the freehold rates and is not included here.",
                authority_keys=["fa2003_s55"],
                eligibility_conditions={"all": [
                    {"path": "property.lease_annual_rent", "op": "gt", "value": 0},
                    {"path": "property.jurisdiction", "op": "not_in", "value": ["scotland", "wales"]},
                ]},
                release=release_property,
            ),
            dict(
                code="lbtt-lease-npv",
                name="LBTT on a lease (Scotland)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.lbtt_lease_npv",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies the LBTT due on the grant of a lease in "
                "Scotland. The rent is charged on its net present value over the term, "
                "discounted at 3.5%, with 0% up to 150,000 of NPV, 1% to 2,000,000 and 2% "
                "above. Scotland uniquely requires the tenant to submit LBTT lease reviews "
                "every three years, which can change the tax as rents are revised.",
                authority_keys=["lbtt_scotland_act_2013_s24"],
                eligibility_conditions={"all": [
                    {"path": "property.lease_annual_rent", "op": "gt", "value": 0},
                    {"path": "property.jurisdiction", "op": "eq", "value": "scotland"},
                ]},
                release=release_property,
            ),
            dict(
                code="ltt-lease-npv",
                name="LTT on a non-residential lease (Wales)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.ltt_lease_npv",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies the LTT due on the grant of a "
                "non-residential lease in Wales. The rent is charged on its net present value "
                "over the term, discounted at 3.5%, with 0% up to 225,000 of NPV, 1% to "
                "2,000,000 and 2% above. Wales's higher nil-rate threshold means a lease is "
                "often cheaper than the equivalent English SDLT. Residential lease rent is "
                "not charged.",
                authority_keys=["ltt_wales_act_2017_s24"],
                eligibility_conditions={"all": [
                    {"path": "property.lease_annual_rent", "op": "gt", "value": 0},
                    {"path": "property.jurisdiction", "op": "eq", "value": "wales"},
                ]},
                release=release_property,
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
                calculator_key="dividend_tax",
                description="Same dividends at the 2026/27 rates (+2pp, Budget 2025)",
                source="Hand-computed: 7,700 at 10.75% (827.75) + 12,300 at 35.75% "
                "(4,397.25) - 500 allowance at 10.75% (53.75) = 5,171.25 (vs 4,781.25 in "
                "2025/26)",
                tax_year="2026/27",
                input_facts={"other_taxable_income": 30000, "dividend_income": 20000},
                expected_output={"tax_due": 5171.25},
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
                calculator_key="strategy.directors_loan_s455",
                description="Overdrawn director's loan partly repaid in time, 2025/26",
                source="Hand-computed: 50,000 overdrawn, 20,000 repaid within 9 months -> "
                "30,000 outstanding at 33.75% = 10,125",
                input_facts={"overdrawn_loan_balance": 50000, "repaid_within_9_months": 20000},
                expected_output={"outstanding_after_deadline": 30000.0, "s455_charge": 10125.0},
            ),
            dict(
                calculator_key="strategy.capital_allowances",
                description="Qualifying spend within the AIA, company main rate, 2025/26",
                source="Hand-computed: 50,000 spend is fully within the 1,000,000 AIA -> "
                "50,000 first-year allowance; at the 25% main CT rate that saves 12,500",
                input_facts={"qualifying_spend": 50000, "marginal_rate": 0.25},
                expected_output={"annual_investment_allowance_used": 50000.0,
                                 "first_year_allowance": 50000.0, "tax_saved_year_one": 12500.0},
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
                calculator_key="strategy.gift_aid_relief",
                description="Gift Aid by a higher-rate donor, 2025/26",
                source="Hand-computed: 800 net grosses up to 1,000; the basic-rate band "
                "extends by 1,000, so 1,000 of income shifts from 40% to 20% = 200 personal "
                "relief; the charity reclaims 200",
                input_facts={"earned_income": 60000, "gift_aid_donation": 800},
                expected_output={"gross_donation": 1000.0, "charity_reclaims": 200.0,
                                 "personal_higher_rate_relief": 200.0},
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
                calculator_key="cgt_liability",
                description="Gain straddling the basic-rate band boundary, 2025/26",
                source="Hand-computed: earned 42,270 -> taxable income 29,700, basic band "
                "remaining 8,000; gain 15,000 - 3,000 AEA = 12,000: 8,000 at 18% (1,440) + "
                "4,000 at 24% (960) = 2,400",
                input_facts={"chargeable_gain": 15000, "asset_type": "residential", "earned_income": 42270},
                expected_output={"taxable_gain": 12000.0, "gain_at_lower_rate": 8000.0,
                                 "gain_at_higher_rate": 4000.0, "tax_due": 2400.0},
            ),
            dict(
                calculator_key="strategy.cgt_timing_of_disposals",
                description="Splitting a 15,000 share gain across two tax years, 2025/26",
                source="Hand-computed: whole 12,000 taxable (8,000 at 18% + 4,000 at 24%) = "
                "2,400; split 7,500 each -> 4,500 taxable both in the basic band at 18% = 810 "
                "each = 1,620; saving 780 (second AEA at 18% plus 4,000 kept out of 24%)",
                input_facts={"disposal_gain": 15000, "asset_type": "other", "earned_income": 42270},
                expected_output={"cgt_if_sold_in_one_year": 2400.0,
                                 "cgt_if_split_over_two_years": 1620.0,
                                 "saving_from_splitting": 780.0},
            ),
            dict(
                calculator_key="cgt_liability",
                description="Gain composed with dividends: dividends consume the band "
                "before the gain, 2025/26",
                source="Hand-computed: taxable earned 17,430 + dividends 20,000 = 37,430 "
                "below the gain; band left 270. Gain 17,000: 270 at 18% + 16,730 at 24% = "
                "4,063.80 (vs 3,060 ignoring dividends)",
                input_facts={"chargeable_gain": 20000, "asset_type": "residential",
                             "earned_income": 30000, "dividend_income": 20000},
                expected_output={"income_below_gain": 37430.0, "gain_at_lower_rate": 270.0,
                                 "tax_due": 4063.80},
            ),
            dict(
                calculator_key="cgt_liability",
                description="Non-residential gain disposed BEFORE 30 Oct 2024: old 10% "
                "basic rate, 2024/25",
                source="Hand-computed: earned 20,000 -> taxable 7,430, basic band left "
                "30,270; gain 20,000 - 3,000 AEA = 17,000 all within the band at the "
                "pre-Budget 10% rate = 1,700",
                tax_year="2024/25",
                input_facts={"chargeable_gain": 20000, "asset_type": "other",
                             "earned_income": 20000, "disposal_date": "2024-06-01"},
                expected_output={"taxable_gain": 17000.0, "tax_due": 1700.0},
            ),
            dict(
                calculator_key="cgt_liability",
                description="Non-residential gain disposed ON/AFTER 30 Oct 2024: new 18% "
                "basic rate, 2024/25",
                source="Hand-computed: same 17,000 taxable gain within the basic band, but "
                "at the post-Budget 18% rate = 3,060 (proves the intra-year row resolves by "
                "disposal date)",
                tax_year="2024/25",
                input_facts={"chargeable_gain": 20000, "asset_type": "other",
                             "earned_income": 20000, "disposal_date": "2024-11-15"},
                expected_output={"taxable_gain": 17000.0, "tax_due": 3060.0},
            ),
            dict(
                calculator_key="strategy.cgt_business_asset_disposal_relief",
                description="Qualifying business disposal within the lifetime limit, "
                "higher-rate owner, 2025/26",
                source="Hand-computed: gain 500,000 - 3,000 AEA = 497,000, all within the "
                "1,000,000 limit at 14% = 69,580; without relief the same 497,000 at 24% "
                "(earned 60,000 fills the basic band) = 119,280; saving 49,700",
                input_facts={"disposal_gain": 500000, "earned_income": 60000},
                expected_output={"gain_at_badr_rate": 497000.0, "cgt_with_badr": 69580.0,
                                 "cgt_without_badr": 119280.0, "saving": 49700.0},
            ),
            dict(
                calculator_key="strategy.cgt_business_asset_disposal_relief",
                description="BADR at the 2026/27 rate of 18% (Finance Act 2025), same "
                "500,000 higher-rate disposal",
                source="Hand-computed: 497,000 (post-AEA) at 18% = 89,460; without relief "
                "497,000 at 24% = 119,280; saving 29,820. Proves the 6 April 2026 rate row "
                "resolves for tax year 2026/27",
                tax_year="2026/27",
                input_facts={"disposal_gain": 500000, "earned_income": 60000},
                expected_output={"gain_at_badr_rate": 497000.0, "badr_rate": 0.18,
                                 "cgt_with_badr": 89460.0, "cgt_without_badr": 119280.0,
                                 "saving": 29820.0},
            ),
            dict(
                calculator_key="strategy.cgt_lettings_relief",
                description="Shared-occupancy let, 60% let / 40% owner-occupied "
                "(HS283 example), higher-rate owner, 2025/26",
                source="Hand-computed (HMRC HS283): gain 60,000, PPR 40% = 24,000, letting "
                "gain 60% = 36,000; lettings relief = lowest of (36,000, 24,000, 40,000) = "
                "24,000; chargeable 36,000 - 24,000 = 12,000; less 3,000 AEA = 9,000 at 24% "
                "(band full at earned 60,000) = 2,160",
                input_facts={"disposal_gain": 60000, "let_fraction": 0.60, "earned_income": 60000},
                expected_output={"private_residence_relief": 24000.0, "letting_gain": 36000.0,
                                 "lettings_relief": 24000.0, "chargeable_gain_after_reliefs": 12000.0,
                                 "cgt_due": 2160.0},
            ),
            dict(
                calculator_key="sdlt_residential",
                description="Standard residential purchase at 350,000, 2025/26",
                source="Hand-computed: 125,000 at 0% + 125,000 at 2% (2,500) + 100,000 at "
                "5% (5,000) = 7,500",
                input_facts={"price": 350000},
                expected_output={"banded_sdlt": 7500.0, "total_sdlt": 7500.0},
            ),
            dict(
                calculator_key="sdlt_residential",
                description="Additional dwelling at 350,000: 5% surcharge on whole price",
                source="Hand-computed: banded 7,500 + surcharge 17,500 = 25,000",
                input_facts={"price": 350000, "additional_dwelling": True},
                expected_output={"banded_sdlt": 7500.0, "additional_dwelling_surcharge": 17500.0,
                                 "total_sdlt": 25000.0},
            ),
            dict(
                calculator_key="lbtt_residential",
                description="Standard Scottish residential purchase at 350,000, 2025/26",
                source="Hand-computed: 145,000 at 0% + 105,000 at 2% (2,100) + 75,000 at "
                "5% (3,750) + 25,000 at 10% (2,500) = 8,350",
                input_facts={"price": 350000},
                expected_output={"banded_lbtt": 8350.0, "total_lbtt": 8350.0},
            ),
            dict(
                calculator_key="ltt_residential",
                description="Standard Welsh residential purchase at 400,000, main rates, 2025/26",
                source="Hand-computed: 225,000 at 0% + 175,000 at 6% (10,500) = 10,500",
                input_facts={"price": 400000},
                expected_output={"total_ltt": 10500.0},
            ),
            dict(
                calculator_key="strategy.sdlt_non_residential_purchase",
                description="Non-residential freehold at 500,000, England/NI, 2025/26",
                source="Hand-computed: 150,000 at 0% + 100,000 at 2% (2,000) + 250,000 at "
                "5% (12,500) = 14,500",
                input_facts={"price": 500000},
                expected_output={"total_sdlt": 14500.0},
            ),
            dict(
                calculator_key="strategy.lbtt_non_residential_purchase",
                description="Non-residential freehold at 500,000, Scotland, 2025/26",
                source="Hand-computed: 150,000 at 0% + 100,000 at 1% (1,000) + 250,000 at "
                "5% (12,500) = 13,500",
                input_facts={"price": 500000},
                expected_output={"total_lbtt": 13500.0},
            ),
            dict(
                calculator_key="strategy.ltt_non_residential_purchase",
                description="Non-residential freehold at 500,000, Wales, 2025/26",
                source="Hand-computed: 225,000 at 0% + 25,000 at 1% (250) + 250,000 at "
                "5% (12,500) = 12,750",
                input_facts={"price": 500000},
                expected_output={"total_ltt": 12750.0},
            ),
            dict(
                calculator_key="strategy.sdlt_lease_npv",
                description="Non-residential lease, 50,000 rent over 10 years, England/NI",
                source="Hand-computed: NPV = sum 50,000/1.035^i (i=1..10) = 415,830.27; "
                "SDLT = (415,830.27 - 150,000) at 1% = 2,658.30",
                input_facts={"annual_rent": 50000, "term_years": 10},
                expected_output={"net_present_value": 415830.27, "total_sdlt": 2658.30},
            ),
            dict(
                calculator_key="strategy.lbtt_lease_npv",
                description="Lease, 250,000 rent over 10 years, Scotland (exercises the 2% band)",
                source="Hand-computed: NPV = sum 250,000/1.035^i (i=1..10) = 2,079,151.33; "
                "LBTT = 1,850,000 at 1% (18,500) + 79,151.33 at 2% (1,583.03) = 20,083.03",
                input_facts={"annual_rent": 250000, "term_years": 10},
                expected_output={"net_present_value": 2079151.33, "total_lbtt": 20083.03},
            ),
            dict(
                calculator_key="strategy.ltt_lease_npv",
                description="Non-residential lease, 50,000 rent over 10 years, Wales",
                source="Hand-computed: NPV 415,830.27; LTT = (415,830.27 - 225,000) at 1% = "
                "1,908.30 (Wales's higher nil threshold beats the 2,658.30 English SDLT)",
                input_facts={"annual_rent": 50000, "term_years": 10},
                expected_output={"net_present_value": 415830.27, "total_ltt": 1908.30},
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
                calculator_key="strategy.incorporation_vs_sole_trade",
                description="Sole trader at 28,000 profit: Class 4 NIC and the stay/incorporate comparison, 2025/26",
                source="Hand-computed: IT (28,000-12,570) x 20% = 3,086; Class 4 "
                "(28,000-12,570) x 6% = 925.80; total 4,011.80 beats the best "
                "incorporated extraction at this profit level",
                input_facts={"annual_profit": 28000, "other_personal_income": 0},
                expected_output={
                    "sole_trader": {"income_tax": 3086.0, "class4_nic": 925.80,
                                    "total_tax_and_nic": 4011.80},
                    "recommendation": "remain_sole_trader",
                },
            ),
            dict(
                calculator_key="strategy.iht_lifetime_gifting",
                description="100,000 gift with both annual exemptions, 1.9m estate with full transferred bands",
                source="Hand-computed: exemptions 2 x 3,000 = 6,000 immediate; PET 94,000; "
                "estate tax falls 360,000 -> 320,000 if survived 7 years (saving 40,000 at 40%)",
                input_facts={
                    "planned_gift": 100000,
                    "estate_basis_value": 1900000,
                    "home_equity_value": 600000,
                    "home_passes_to_direct_descendants": True,
                    "transferred_nrb_fraction": 1,
                    "transferred_rnrb_fraction": 1,
                    "prior_year_annual_exemption_unused": True,
                },
                expected_output={
                    "immediately_exempt_amount": 6000,
                    "pet_amount": 94000.0,
                    "estate_tax_before_gift": 360000.0,
                    "estate_tax_if_survive_7_years": 320000.0,
                    "saving_if_survive_7_years": 40000.0,
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
                    "tax_year": case.get("tax_year", "2025/26"),
                    "input_facts": case["input_facts"],
                    "expected_output": case["expected_output"],
                },
            )
