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
            self._create_iht_parameters(release_iht, release_2026)
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
                key="tcga1992_s236h",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Taxation of Chargeable Gains Act 1992 s.236H (Employee Ownership Trust)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/12/section/236H",
                verbatim_extract="A disposal of shares in a trading company to an Employee "
                "Ownership Trust that acquires a controlling interest is treated as made on a "
                "no-gain/no-loss basis — the gain is fully exempt from capital gains tax — provided "
                "the qualifying conditions are met. Finance Act 2024/2025 tightened the rules "
                "(UK-resident trustees, former owners not to retain control, a longer clawback "
                "period and an independent valuation), which the adviser must confirm.",
            ),
            dict(
                key="ihta1984_s5",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 s.5 (meaning of estate)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/section/5",
                verbatim_extract="A person's estate is the aggregate of all the property to which "
                "they are beneficially entitled at death. Property held in a properly constituted "
                "trust to which the deceased was not beneficially entitled — such as the proceeds "
                "of a life policy written in trust — does not form part of the estate, so the "
                "proceeds pass free of inheritance tax and can fund the estate's IHT bill.",
            ),
            dict(
                key="ihta1984_pension_2027",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="IHTA 1984 s.3 (as to be amended from 6 April 2027, Finance Bill 2025-26)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/section/3",
                verbatim_extract="Announced at Autumn Budget 2024: from 6 April 2027 most unused "
                "pension funds and death benefits will be brought within the value of a person's "
                "estate for inheritance tax, reversing the current position where they normally "
                "pass outside the estate. This is a forward-looking planning point subject to final "
                "legislation — modelled here as a clearly-flagged borderline projection.",
            ),
            dict(
                key="cta2009_part13",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Corporation Tax Act 2009 Part 13 (as amended, merged R&D scheme)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2009/4/part/13",
                verbatim_extract="Relief for expenditure on research and development. For "
                "accounting periods beginning on or after 1 April 2024 the merged scheme gives a "
                "20% taxable 'above the line' expenditure credit (RDEC) on qualifying R&D spend; "
                "the credit is itself chargeable to corporation tax, so the net benefit is 20% "
                "less tax. Loss-making R&D-intensive SMEs (qualifying R&D at least 30% of total "
                "expenditure) instead claim enhanced support with a 14.5% payable credit.",
            ),
            dict(
                key="cta2010_part8a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Corporation Tax Act 2010 Part 8A (Patent Box)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2010/4/part/8A",
                verbatim_extract="A company may elect for profits attributable to patented "
                "inventions (and certain other qualifying IP) to be taxed at an effective "
                "corporation-tax rate of 10%, delivered by a deduction from those profits. Post-"
                "2016 entrants must meet the modified nexus requirement linking the relief to the "
                "company's own R&D.",
            ),
            dict(
                key="caa2001_s33a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Capital Allowances Act 2001 ss.33A-33B & s.187A (integral features / fixtures)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2001/2/section/33A",
                verbatim_extract="Expenditure on integral features and fixtures within a "
                "commercial building (electrical, heating, water, lifts, etc.) qualifies for plant "
                "and machinery capital allowances — the Annual Investment Allowance up to its limit "
                "then the special-rate writing-down allowance. On a second-hand building the fixtures "
                "claim depends on the s.187A pooling/fixed-value requirements being met by the seller.",
            ),
            dict(
                key="tcga1992_s162",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Taxation of Chargeable Gains Act 1992 s.162",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/12/section/162",
                verbatim_extract="Incorporation relief: where a person transfers a business as a "
                "going concern, together with the whole of its assets (other than cash), to a "
                "company wholly or partly in exchange for shares, the chargeable gain on the "
                "transferred assets is rolled into the base cost of the shares to the extent the "
                "consideration is shares. Whether a property letting activity is a 'business' for "
                "s.162 depends on the degree of activity (Ramsay v HMRC [2013] UKUT 226). The "
                "transfer is at market value and a company acquiring residential property pays SDLT "
                "including the additional-dwelling surcharge (and potentially ATED).",
            ),
            dict(
                key="ihta1984_relevant_property",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 ss.58-69 (relevant property)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/part/III/chapter/III",
                verbatim_extract="Property in a relevant-property trust (most discretionary and, "
                "since 2006, most lifetime trusts) is subject to its own IHT charges outside a "
                "person's estate: a lifetime entry charge at half the death rate (20%) on value "
                "settled above the available nil-rate band; a ten-year anniversary charge (s.64) "
                "of up to 6% of the value above the band, being 30% of the lifetime effective "
                "rate; and a proportionate exit charge (s.65) when property leaves the trust, by "
                "reference to the last ten-year rate and the complete quarters since the last "
                "anniversary.",
            ),
            dict(
                key="ittoia2005_s850",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Trading and Other Income) Act 2005 s.850",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2005/5/section/850",
                verbatim_extract="A partnership is transparent for tax: each partner is treated as "
                "carrying on the trade and is taxed on their share of the firm's profit determined "
                "by the firm's profit-sharing arrangement, as trading income (income tax and Class "
                "4 NIC). The profit-sharing ratio must reflect the commercial arrangement between "
                "the partners; HMRC can challenge allocations made to divert income for tax "
                "advantage (see also the settlements rules, ITTOIA 2005 Part 5 Ch 5).",
            ),
            dict(
                key="ittoia2005_s850c",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Trading and Other Income) Act 2005 s.850C",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2005/5/section/850C",
                verbatim_extract="Excess profit allocation to non-individual partners (the "
                "mixed-member anti-avoidance rule): where an individual partner's deferred "
                "profit appears in a non-individual member's share, or a company member's "
                "share exceeds the appropriate notional profit and the individual has the "
                "power to enjoy it, the individual's taxable share is increased on a just and "
                "reasonable basis. Introduced by FA 2014 against mixed partnerships routing "
                "profit through corporate members taxed at lower rates.",
            ),
            dict(
                key="fa2004_s197",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Finance Act 2004 s.197",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2004/12/section/197",
                verbatim_extract="Spreading of relief: where employer pension contributions in "
                "the current chargeable period exceed 210% of the previous period's, the excess "
                "above 110% of the previous period's contributions is spread — half to the next "
                "period where the excess is £500,000 or more, one third across two periods from "
                "£1,000,000, and one quarter across three periods from £2,000,000 — rather than "
                "relieved in full at once. Contributions for excepted purposes (e.g. cost-of-"
                "living increases, new employees) are excluded.",
            ),
            dict(
                key="lbtta2013_sch2a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Land and Buildings Transaction Tax (Scotland) Act 2013 Sch 2A",
                canonical_uri="https://www.legislation.gov.uk/asp/2013/11/schedule/2A",
                verbatim_extract="Additional amount: transactions relating to second homes etc. "
                "— the Additional Dwelling Supplement. An additional charge (8% of the relevant "
                "consideration since 5 December 2024) applies where a buyer acquires a dwelling "
                "of £40,000 or more and owns another dwelling at the end of the effective date, "
                "unless replacing a main residence. Repayment may be claimed where the previous "
                "main residence is disposed of within 36 months.",
            ),
            dict(
                key="ltta2017_sch5",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Land Transaction Tax and Anti-avoidance of Devolved Taxes "
                "(Wales) Act 2017 Sch 5",
                canonical_uri="https://www.legislation.gov.uk/anaw/2017/1/schedule/5",
                verbatim_extract="Higher rates residential property transactions: a chargeable "
                "transaction is a higher-rates transaction where an individual buys a dwelling "
                "for £40,000 or more and owns an interest in another dwelling at the end of the "
                "day of the transaction (with a replacement-of-main-residence exception, "
                "normally within three years), and for all purchases by non-individuals. Higher "
                "rates are prescribed under s.24(1)(b) in the Welsh rates regulations.",
            ),
            dict(
                key="ittoia2005_s383_384",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Trading and Other Income) Act 2005 ss.383-384",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2005/5/section/383",
                verbatim_extract="Income tax is charged on dividends and other distributions "
                "of a UK resident company, which are treated as income (s.383); tax is "
                "charged on the amount or value of the dividends paid and other "
                "distributions made in the tax year (s.384). The year a dividend is paid "
                "therefore fixes the year — and the rates — under which it is taxed, which "
                "is the statutory basis for timing a declaration either side of 6 April.",
            ),
            dict(
                key="itepa2003_s18",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Earnings and Pensions) Act 2003 s.18",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/1/section/18",
                verbatim_extract="Receipt of money earnings: general earnings consisting of "
                "money are treated as received at the earliest of the time payment is made "
                "(or on account) and the time the person becomes entitled to payment; for "
                "directors, also the earliest of sums being credited in the company's "
                "accounts or records, the end of a period whose earnings are determined by "
                "then, and the time the amount is determined. This receipts basis fixes the "
                "tax year a bonus falls into.",
            ),
            dict(
                key="ita2007_s431",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax Act 2007 s.431",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2007/3/section/431",
                verbatim_extract="Relief for gifts of shares, securities and real property "
                "to charities etc: an individual who disposes of the whole of their "
                "beneficial interest in a qualifying investment (s.432 listed shares and "
                "securities, units, and qualifying interests in land, s.433) to a charity "
                "otherwise than by way of a bargain at arm's length may, on a claim, deduct "
                "the relievable amount (s.434, broadly market value plus incidental costs) "
                "in calculating net income for the tax year of the disposal.",
            ),
            dict(
                key="tcga1992_s257",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Taxation of Chargeable Gains Act 1992 s.257",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/12/section/257",
                verbatim_extract="Gifts to charities etc: where a disposal to a charity is "
                "otherwise than by way of a bargain at arm's length, the disposal and "
                "acquisition are treated as made for such consideration as secures that "
                "neither a gain nor a loss accrues to the donor — so no capital gains tax "
                "arises on the held gain, and the charity takes the donor's base cost.",
            ),
            dict(
                key="itepa2003_part12",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Earnings and Pensions) Act 2003 Part 12 (ss.713-715)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/1/section/713",
                verbatim_extract="Payroll giving: where an individual receiving PAYE income "
                "asks the employer to withhold sums as donations to charity under an "
                "approved payroll deduction scheme, the withheld amounts are allowed as "
                "deductions from taxable employment income in the tax year withheld — full "
                "relief at the donor's marginal rate with no grossing-up or claim. Subject "
                "to the tainted-donation rules (ITA 2007 ss.809ZM, 809ZMB).",
            ),
            dict(
                key="tcga1992_s152",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Taxation of Chargeable Gains Act 1992 s.152",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/12/section/152",
                verbatim_extract="Roll-over relief: where the consideration for the disposal "
                "of assets used only for the purposes of the trade throughout ownership is "
                "applied in acquiring other assets taken into use only for the trade (both "
                "within the s.155 classes), acquired in the period beginning 12 months "
                "before and ending 3 years after the disposal, the trader may claim to be "
                "treated as disposing of the old assets for no gain/no loss, with the new "
                "assets' acquisition cost reduced accordingly; partial reinvestment leaves "
                "the proceeds not reinvested in charge (s.153).",
            ),
            dict(
                key="ittoia2005_s272a",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Trading and Other Income) Act 2005 ss.272A-274C",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2005/5/section/272A",
                verbatim_extract="Costs of a dwelling-related loan (mortgage interest and other "
                "finance costs) are not deductible in computing the profits of a residential "
                "property business. Instead the individual is entitled to a basic-rate tax "
                "reduction (s.274A) of 20% of the lower of the finance costs, the property "
                "business profits, and the individual's adjusted total income above the personal "
                "allowance. Fully in force from 2020/21 (phased in from 2017/18 by F(No.2)A 2015 "
                "s.24). Companies are unaffected — they still deduct the interest in full.",
            ),
            dict(
                key="ita2007_venture_capital",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax Act 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2007/3/part/5",
                verbatim_extract="Income tax relief for venture-capital investment: the Enterprise "
                "Investment Scheme gives relief at 30% on up to £1,000,000 a year (£2,000,000 for "
                "knowledge-intensive companies), the Seed Enterprise Investment Scheme 50% on up "
                "to £200,000, and Venture Capital Trusts 30% on up to £200,000. Relief cannot "
                "exceed the investor's income tax liability. EIS also allows unlimited deferral of "
                "a chargeable gain reinvested in the shares (TCGA 1992 Sch 5B); SEIS exempts 50% "
                "of a reinvested gain (Sch 5BB); VCT dividends and disposals are tax-free. Gains "
                "on EIS/SEIS shares held for the minimum period are themselves exempt.",
            ),
            dict(
                key="ihta1984_bpr_apr",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Inheritance Tax Act 1984 ss.103-114 (BPR) and ss.115-124C (APR)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1984/51/part/V/chapter/I",
                verbatim_extract="Business property relief reduces the value transferred by "
                "relevant business property by 100% (unquoted trading businesses and unquoted "
                "shares) or 50% (controlling quoted holdings, certain land and machinery). "
                "Agricultural property relief similarly relieves the agricultural value of "
                "qualifying farmland at 100% or 50%. From 6 April 2026 the 100% rate is limited "
                "to a combined £1,000,000 of qualifying business and agricultural property, with "
                "50% relief on value above that cap (Finance Act 2025).",
            ),
            dict(
                key="ittoia2005_s694",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Trading and Other Income) Act 2005 s.694",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2005/5/section/694",
                verbatim_extract="Income arising from investments held in an individual savings "
                "account (ISA) is exempt from income tax, subject to the ISA regulations. The "
                "annual subscription limit is set by those regulations (SI 1998/1870); gains on "
                "ISA investments are likewise exempt from capital gains tax (TCGA 1992 s.151).",
            ),
            dict(
                key="cta2010_part5",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Corporation Tax Act 2010 Part 5 (ss.97-188)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2010/4/part/5",
                verbatim_extract="Group relief: a company may surrender its current-period trading "
                "losses (and certain other amounts) to another company in the same group, which "
                "claims them against its total profits of the corresponding period. Companies are "
                "in a group for this purpose where one is a 75% subsidiary of the other, or both "
                "are 75% subsidiaries of a third (s.152). The claimant's profits are reduced by the "
                "amount surrendered, so the loss is relieved at the claimant's marginal rate.",
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
                canonical_citation="Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/14/section/55",
                verbatim_extract="Amount of stamp duty land tax chargeable: s.55 sets the rates by "
                "reference to Table A (residential property) and, under s.55(1B), Table B "
                "(non-residential or mixed-use property). The residential additional-dwelling "
                "surcharge (Sch 4ZA) and first-time buyer relief (Sch 6ZA), and the lease-rent "
                "charge on net present value (Sch 5), sit in the referenced schedules.",
            ),
            dict(
                key="fa2003_sch4za",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Finance Act 2003 Sch 4ZA (higher rates for additional dwellings)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/14/schedule/4ZA",
                verbatim_extract="Schedule 4ZA imposes the higher rates of SDLT on purchases of "
                "additional residential dwellings (and dwellings bought by companies), refundable "
                "where a former main residence is replaced within the time limit. It applies to "
                "residential property only, not to non-residential or mixed-use transactions.",
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
                key="fa2003_sch5",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Finance Act 2003 Sch 5 (amount of tax chargeable: rent)",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/14/schedule/5",
                verbatim_extract="The SDLT charge on the rent under a lease is calculated on the "
                "net present value of the rent payable over the term, discounted at the statutory "
                "rate, with the non-residential 0%/1%/2% NPV bands. Any lease premium is charged "
                "separately under s.55.",
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
            dict(
                key="itepa2003_s401",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Earnings and Pensions) Act 2003 s.401",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/1/section/401",
                verbatim_extract="Charges to income tax on payments and other benefits received "
                "in connection with the termination of a person's employment, or a change in its "
                "duties or earnings, so far as they are not otherwise chargeable as earnings.",
            ),
            dict(
                key="itepa2003_s403",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Earnings and Pensions) Act 2003 s.403",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/1/section/403",
                verbatim_extract="Termination payments within s.401 are only chargeable to income "
                "tax on the amount by which they exceed the £30,000 threshold; the first £30,000 "
                "is exempt. The excess is treated as employment income for the year of receipt.",
            ),
            dict(
                key="itepa2003_s402d",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Income Tax (Earnings and Pensions) Act 2003 s.402D",
                canonical_uri="https://www.legislation.gov.uk/ukpga/2003/1/section/402D",
                verbatim_extract="Post-employment notice pay (PENP) is treated as earnings and "
                "taxed in full; it does not benefit from the £30,000 termination exemption. PENP "
                "is calculated by the statutory formula on basic pay for the unworked notice period.",
            ),
            dict(
                key="sscba1992_s10",
                authority_type=Authority.AuthorityType.STATUTE,
                canonical_citation="Social Security Contributions and Benefits Act 1992 s.10",
                canonical_uri="https://www.legislation.gov.uk/ukpga/1992/4/section/10",
                verbatim_extract="Class 1A National Insurance contributions are payable by the "
                "employer on the amount of a termination award that exceeds the £30,000 threshold "
                "and is chargeable to income tax under ITEPA 2003, at the Class 1A percentage.",
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
            ("isa.allowance", "ISA annual subscription limit", TaxDomain.PERSONAL_INCOME_TAX,
             {"amount": 20000}, None),
            ("property_income.finance_cost_restriction",
             "Residential landlord finance-cost (mortgage interest) tax-reducer rate",
             TaxDomain.PERSONAL_INCOME_TAX,
             {"reducer_rate": 0.20}, None),
            ("termination_payment.exemption",
             "Termination payment income-tax exemption (ITEPA 2003 s.403)",
             TaxDomain.PERSONAL_INCOME_TAX,
             {"amount": 30000}, None),
            ("rd.merged_scheme",
             "R&D merged-scheme (RDEC) above-the-line credit rate",
             TaxDomain.CORPORATION_TAX,
             {"rdec_rate": 0.20, "rd_intensive_threshold": 0.30,
              "rd_intensive_credit_rate": 0.145}, None),
            ("patent_box.rate", "Patent Box effective corporation-tax rate",
             TaxDomain.CORPORATION_TAX, {"rate": 0.10}, None),
            ("venture_capital.schemes",
             "EIS/SEIS/VCT income-tax relief rates, annual limits and CGT treatment",
             TaxDomain.PERSONAL_INCOME_TAX,
             {"eis": {"relief_rate": 0.30, "annual_limit": 1000000, "min_holding_years": 3,
                      "cgt_deferral": True, "cgt_reinvestment_relief_rate": 0.0,
                      "tax_free_dividends": False},
              "seis": {"relief_rate": 0.50, "annual_limit": 200000, "min_holding_years": 3,
                       "cgt_deferral": False, "cgt_reinvestment_relief_rate": 0.50,
                       "tax_free_dividends": False},
              "vct": {"relief_rate": 0.30, "annual_limit": 200000, "min_holding_years": 5,
                      "cgt_deferral": False, "cgt_reinvestment_relief_rate": 0.0,
                      "tax_free_dividends": True}},
             None),
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

    def _create_iht_parameters(self, release_iht, release_2026):
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

        # Business Property Relief / Agricultural Property Relief. Finance Act
        # 2025 reforms these from 6 April 2026: the 100% rate is capped at a
        # combined £1,000,000 of qualifying business + agricultural property,
        # with 50% relief on the excess (and AIM/unlisted shares dropping to
        # 50%). Per A5 a rate change is a NEW effective-dated row: the pre-reform
        # row (unlimited 100%) is CLOSED at 6 April 2026 and the reformed row
        # opens there under the 2026.1 release. Delete-all-by-key keeps the seed
        # idempotent regardless of any earlier single-row shape.
        bpr_key = "iht.business_property_relief"
        bpr_label = "IHT Business/Agricultural Property Relief: 100% rate and combined cap"
        bpr_rows = [
            (Range(datetime.date(2024, 4, 6), datetime.date(2026, 4, 6), bounds="[)"),
             {"full_relief_cap": None, "rate_above_cap": 1.0}, release_iht),
            (Range(datetime.date(2026, 4, 6), None, bounds="[)"),
             {"full_relief_cap": 1000000, "rate_above_cap": 0.5}, release_2026),
        ]
        TaxParameter.objects.filter(key=bpr_key).delete()
        for effective_range, payload, release in bpr_rows:
            TaxParameter.objects.create(
                key=bpr_key, label=bpr_label, tax_domain=TaxDomain.INHERITANCE_TAX,
                effective_range=effective_range, payload=payload,
                risk_classification=RiskStatus.SETTLED,
                introduced_in_release=release,
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
            ("cgt.rates", "CGT rates by asset class (lower = within basic band; "
             "residential and other deliberately aligned at 18%/24% since 30 Oct 2024)",
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
            ("cgt.rates", "CGT rates by asset class (lower = within basic band; "
             "residential and other deliberately aligned at 18%/24% since 30 Oct 2024)",
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
                code="termination-payment",
                name="Termination payment (£30,000 exemption)",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.termination_payment",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="When an employment ends, a genuine (non-contractual) "
                "termination payment is exempt from income tax up to £30,000; only the excess is "
                "taxed, and it is taxed as the top slice of the employee's income for the year, so "
                "a large payment can also strip the personal allowance. The employer pays Class 1A "
                "National Insurance on that same excess. Contractual sums and post-employment "
                "notice pay (PENP) do NOT get the exemption — they are taxed in full as ordinary "
                "earnings — so only the qualifying amount should be entered. This quantifies the "
                "tax on the excess, the employer's NIC, and the employee's net receipt.",
                authority_keys=["itepa2003_s401", "itepa2003_s403", "itepa2003_s402d", "sscba1992_s10"],
                eligibility_conditions={"all": [
                    {"path": "employment.termination_payment", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="personal-pension-contribution",
                name="Personal pension contribution (relief at source)",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.personal_pension_contribution",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="A personal pension contribution is paid net of basic-rate "
                "tax, which the provider reclaims into the pot. A higher or additional-rate taxpayer "
                "claims further relief because the grossed-up contribution extends the basic-rate "
                "band. Where income is in the 100,000-125,140 personal-allowance taper the "
                "contribution also reduces adjusted net income and restores personal allowance, so "
                "the effective relief can reach 60%. Relief is capped at the greater of £3,600 and "
                "relevant UK earnings; dividends and savings/rental income do not count towards it.",
                authority_keys=["fa2004_s190"],
                eligibility_conditions={"all": [
                    {"path": "personal.desired_pension_contribution", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="employer-pension-contribution",
                name="Employer pension contribution",
                tax_domain=TaxDomain.CORPORATION_TAX,
                calculator_key="strategy.employer_pension_contribution",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="An employer pension contribution from the individual's own "
                "company is not restricted by relevant UK earnings and carries no employee or "
                "employer National Insurance. The company deducts it against corporation tax, subject "
                "to the wholly-and-exclusively condition as part of a reasonable remuneration package. "
                "This quantifies the corporation tax saved, the employer NIC saved versus paying the "
                "same amount as salary, and the net cost to the company.",
                authority_keys=["cta2009_s54", "fa2004_s197"],
                eligibility_conditions={"all": [
                    {"path": "company.desired_employer_pension_contribution", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="group-loss-relief",
                name="Group relief for company losses",
                tax_domain=TaxDomain.CORPORATION_TAX,
                calculator_key="strategy.group_loss_relief",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Where one company in a 75% group makes a loss and "
                "another makes a profit, the loss can be surrendered as group relief and set "
                "against the profitable company's profits. This relieves the loss now, at the "
                "claimant company's marginal rate — worth 26.5% where the claimant is in the "
                "marginal-relief band (profits between £50,000 and £250,000), which is more "
                "valuable than carrying the loss forward at 19% or the 25% main rate. Any loss "
                "not covered by the claimant's profit is carried forward. Establishing the 75% "
                "group relationship is a precondition the accountant confirms.",
                authority_keys=["cta2010_part5"],
                eligibility_conditions={"all": [
                    {"path": "company.surrendering_company_loss", "op": "gt", "value": 0},
                    {"path": "company.claimant_company_profit", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="isa-bed-and-isa",
                name="Bed-and-ISA (shelter investments in an ISA)",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.isa_bed_and_isa",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Selling unwrapped investments and repurchasing them "
                "inside an ISA (a 'bed-and-ISA') moves them into a wrapper where future dividends "
                "and capital growth are tax-free. Timing the sale so the gain stays within the "
                "annual CGT exempt amount means no capital gains tax on the transfer. This "
                "quantifies the amount sheltered (capped at the £20,000 ISA limit), any CGT due "
                "on the transfer, and the yearly dividend tax saved once the holding is inside the "
                "ISA. Future growth is also CGT-free but is not projected here as it depends on "
                "the growth rate.",
                authority_keys=["ittoia2005_s694"],
                eligibility_conditions={"all": [
                    {"path": "personal.isa_amount_to_shelter", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="business-property-relief",
                name="Business / Agricultural Property Relief",
                tax_domain=TaxDomain.INHERITANCE_TAX,
                calculator_key="strategy.business_property_relief",
                timeframe=Timeframe.LONG,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Qualifying business and agricultural property is "
                "relieved from inheritance tax — at 100% for an unquoted trading business or "
                "qualifying farmland. From 6 April 2026 the 100% rate is capped at a combined "
                "£1,000,000, with 50% relief on anything above that (Finance Act 2025), so a "
                "large business or farm can face inheritance tax for the first time. This "
                "quantifies the value relieved, the taxable value left after relief, and the IHT "
                "saved. It assumes the rest of the estate has used the nil-rate bands, which is "
                "the usual position where seven figures of business property are in point. "
                "Whether specific assets qualify (trading vs investment, two-year ownership) is a "
                "judgement the accountant confirms.",
                authority_keys=["ihta1984_bpr_apr"],
                eligibility_conditions={"all": [
                    {"path": "estate.qualifying_business_property", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="property-income-finance-cost",
                name="Landlord finance-cost restriction (s.24)",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.property_income_finance_cost",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Since April 2020 an individual residential landlord can "
                "no longer deduct mortgage interest from rental profit. The interest is relieved "
                "instead as a basic-rate (20%) tax reducer, on the lower of the finance costs, the "
                "rental profit and adjusted total income. A basic-rate landlord is unaffected, but "
                "a higher or additional-rate landlord effectively loses relief at 40%/45% and pays "
                "more tax. This quantifies the rental profit, the tax reducer, the tax with and "
                "without the restriction, and the extra tax it costs — which is the main reason "
                "landlords consider holding property through a company (which still deducts the "
                "interest in full).",
                authority_keys=["ittoia2005_s272a"],
                eligibility_conditions={"all": [
                    {"path": "property.rental_income", "op": "gt", "value": 0},
                    {"path": "property.finance_costs", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="partnership-profit-allocation",
                name="Partnership / LLP profit-share allocation",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.partnership_profit_allocation",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.BORDERLINE,
                gaar_exposure=False,
                plain_english_explanation="A partnership does not pay tax itself — each partner is "
                "taxed on their share of the profit as trading income (income tax plus Class 4 "
                "NIC), on top of their other income. When partners are in different tax bands, the "
                "profit-sharing ratio changes the combined tax bill: shifting profit toward a "
                "lower-rate partner can reduce it. This compares the current split with a proposed "
                "one and quantifies the difference. Crucially the ratio must reflect the partners' "
                "genuine commercial contribution — it cannot be set purely to save tax, and HMRC "
                "can challenge allocations that divert income (settlements rules) — which is why "
                "this is flagged as a borderline judgement for the accountant to stand behind.",
                authority_keys=["ittoia2005_s850", "ittoia2005_s850c"],
                eligibility_conditions={"all": [
                    {"path": "partnership.total_profit", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="relevant-property-trust-charges",
                name="Relevant-property trust IHT charges",
                tax_domain=TaxDomain.INHERITANCE_TAX,
                calculator_key="strategy.relevant_property_trust_charges",
                timeframe=Timeframe.LONG,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="A discretionary trust (and most lifetime trusts) is "
                "'relevant property' with its own inheritance tax charges, separate from anyone's "
                "estate: a 20% entry charge on the value settled above the available nil-rate "
                "band; a charge on each ten-year anniversary of up to 6% of the value above the "
                "band; and a proportionate exit charge when capital leaves the trust. This "
                "quantifies all three, so a settlor can compare putting assets in trust (control "
                "and protection, but these ongoing charges) against outright gifts (a potentially "
                "exempt transfer with no charge if they survive seven years). Whether the trust is "
                "relevant property, and the settlor's prior chargeable transfers, are matters the "
                "adviser confirms.",
                authority_keys=["ihta1984_relevant_property"],
                eligibility_conditions={"all": [
                    {"path": "trust.trust_value", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="property-incorporation",
                name="Property portfolio incorporation (should the landlord incorporate?)",
                tax_domain=TaxDomain.CROSS_CUTTING,
                calculator_key="strategy.property_incorporation",
                timeframe=Timeframe.LONG,
                risk_status=RiskStatus.BORDERLINE,
                gaar_exposure=False,
                plain_english_explanation="A landlord holding property personally is caught by the "
                "s.24 restriction (mortgage interest relieved at only 20%); a company deducts the "
                "interest in full and pays corporation tax. That gives an annual saving for a "
                "higher-rate landlord — but moving the properties into a company is a disposal at "
                "market value, so it triggers SDLT (with the 5% surcharge) and a capital gain "
                "(deferred only if s.162 incorporation relief applies). This weighs the annual "
                "saving against those one-off costs and reports the break-even in years, so the "
                "landlord can see whether incorporation actually pays. It assumes profits are "
                "retained (extracting them adds dividend tax) and an England/SDLT portfolio; "
                "whether the letting is a 'business' for s.162, and any ATED charge, are matters "
                "the accountant confirms — which is why it is flagged borderline.",
                authority_keys=["tcga1992_s162", "ittoia2005_s272a"],
                eligibility_conditions={"all": [
                    {"path": "property.portfolio_value", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="rd-tax-relief",
                name="R&D tax relief (merged scheme)",
                tax_domain=TaxDomain.CORPORATION_TAX,
                calculator_key="strategy.rd_tax_relief",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="A company carrying out qualifying research and "
                "development can claim R&D tax relief. Under the merged scheme (from April 2024) "
                "this is a 20% 'above the line' expenditure credit on the qualifying spend. The "
                "credit is taxable, so the net cash benefit is 20% less corporation tax — about "
                "15% of the spend for a main-rate company. This quantifies the gross credit, the "
                "tax on it and the net benefit. What counts as qualifying R&D (the advance in "
                "science or technology and the qualifying cost categories) is a technical "
                "judgement the adviser and, often, an R&D specialist confirm.",
                authority_keys=["cta2009_part13"],
                eligibility_conditions={"all": [
                    {"path": "company.qualifying_rd_spend", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="patent-box",
                name="Patent Box (10% rate on patented-product profits)",
                tax_domain=TaxDomain.CORPORATION_TAX,
                calculator_key="strategy.patent_box",
                timeframe=Timeframe.MEDIUM,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="A company that owns or exclusively licenses patents can "
                "elect for the profits attributable to those patented inventions to be taxed at an "
                "effective 10% corporation-tax rate instead of the main rate. This quantifies the "
                "tax at the main rate, the tax under the Patent Box and the saving. Identifying the "
                "profit attributable to the qualifying IP, and meeting the modified-nexus R&D "
                "requirement, are specialist steps the adviser establishes.",
                authority_keys=["cta2010_part8a"],
                eligibility_conditions={"all": [
                    {"path": "company.patent_profit", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="commercial-property-fixtures",
                name="Capital allowances on commercial-property fixtures",
                tax_domain=TaxDomain.CORPORATION_TAX,
                calculator_key="strategy.commercial_property_fixtures",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="When a business buys or refurbishes a commercial "
                "building, a large part of the cost is often 'integral features' and fixtures "
                "(heating, electrics, lifts, water systems) that qualify for capital allowances. "
                "Claiming them gives 100% relief through the Annual Investment Allowance up to its "
                "limit, then the special-rate writing-down allowance on the excess. This quantifies "
                "the first-year allowance and the tax it saves. On a second-hand building the "
                "fixtures claim depends on the seller's pooling/fixed-value position (CAA 2001 "
                "s.187A) — the adviser confirms it, ideally with a specialist survey.",
                authority_keys=["caa2001_s33a"],
                eligibility_conditions={"all": [
                    {"path": "company.fixtures_value", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="eot-disposal-relief",
                name="Employee Ownership Trust sale (CGT-free)",
                tax_domain=TaxDomain.CROSS_CUTTING,
                calculator_key="strategy.eot_disposal_relief",
                timeframe=Timeframe.LONG,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="An owner who sells a controlling stake in their trading "
                "company to an Employee Ownership Trust pays no capital gains tax on the sale — a "
                "full exemption. This quantifies the CGT a normal third-party sale would cost "
                "instead (Business Asset Disposal Relief at 14% on the first £1m, then the standard "
                "share rate) and therefore the tax saved by the EOT route. The qualifying "
                "conditions were tightened by Finance Act 2024/2025 (UK-resident trustees, the "
                "former owners not keeping control, a four-year clawback and an independent "
                "valuation) — the adviser confirms them.",
                authority_keys=["tcga1992_s236h"],
                eligibility_conditions={"all": [
                    {"path": "company.eot_disposal_gain", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="pension-death-benefit",
                name="Pension death-benefit IHT (from April 2027)",
                tax_domain=TaxDomain.INHERITANCE_TAX,
                calculator_key="strategy.pension_death_benefit",
                timeframe=Timeframe.LONG,
                risk_status=RiskStatus.BORDERLINE,
                gaar_exposure=False,
                plain_english_explanation="Today an unused pension pot normally passes on death "
                "outside the estate, free of inheritance tax. From 6 April 2027 (announced at "
                "Autumn Budget 2024) most pension funds are expected to be brought into the estate "
                "for IHT. This shows the extra inheritance tax a pot would attract from that date — "
                "40% where the estate is already above the nil-rate band — so a client can plan "
                "(for example, drawing the pension down or gifting) ahead of the change. It is a "
                "forward-looking projection based on the announcement and is flagged borderline "
                "until the Finance Bill 2025-26 is enacted.",
                authority_keys=["ihta1984_pension_2027"],
                eligibility_conditions={"all": [
                    {"path": "estate.pension_pot_value", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="life-policy-in-trust",
                name="Life policy in trust to fund the IHT bill",
                tax_domain=TaxDomain.INHERITANCE_TAX,
                calculator_key="strategy.life_policy_in_trust",
                timeframe=Timeframe.LONG,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="A whole-of-life policy written in trust pays out on "
                "death to the trust, outside the estate, giving the family tax-free cash to pay the "
                "inheritance tax bill without having to sell assets. If the same policy were held "
                "personally, its proceeds would instead add to the estate and attract 40% IHT. "
                "This quantifies the IHT saved by writing it in trust and the payout available to "
                "meet the bill. The trust must be validly set up with no benefit reserved to the "
                "settlor.",
                authority_keys=["ihta1984_s5"],
                eligibility_conditions={"all": [
                    {"path": "estate.life_policy_sum_assured", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="venture-capital-investment",
                name="EIS / SEIS / VCT investment relief",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.venture_capital_investment",
                timeframe=Timeframe.MEDIUM,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Investing in a qualifying venture-capital scheme gives "
                "income tax relief: 30% under the Enterprise Investment Scheme (up to £1m a year), "
                "50% under the Seed Enterprise Investment Scheme (up to £200k), or 30% through a "
                "Venture Capital Trust (up to £200k). The relief cannot exceed the investor's "
                "income tax bill. EIS also defers a chargeable gain reinvested in the shares, SEIS "
                "exempts half of a reinvested gain, and VCT dividends are tax-free. This quantifies "
                "the income tax relief, the CGT deferred or saved, and the net cost after relief. "
                "These are higher-risk investments and relief is withdrawn if the shares are not "
                "held for the minimum period — the adviser confirms the company and shares qualify.",
                authority_keys=["ita2007_venture_capital"],
                eligibility_conditions={"all": [
                    {"path": "personal.venture_capital_investment", "op": "gt", "value": 0},
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
                code="income-timing-across-years",
                name="Timing of income across tax years",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.income_timing",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Where the client controls when income lands — a "
                "dividend they can declare either side of 6 April, or a bonus whose payment "
                "date they set — the year it falls in fixes the rates it is taxed at and the "
                "income it stacks on top of. This compares the extra tax the amount causes "
                "in the current year against the following year, using each year's own "
                "rates and the client's expected income in each, and recommends the cheaper "
                "year. With dividend rates rising two percentage points from April 2026, "
                "bringing a planned dividend forward can produce a real, quantified saving; "
                "equally a bonus deferred out of the £100,000-£125,140 taper zone can attract "
                "relief at up to 60%. The income must genuinely be controllable — the "
                "receipts basis, not paperwork, decides the year.",
                authority_keys=["ittoia2005_s383_384", "itepa2003_s18"],
                eligibility_conditions={"all": [
                    {"path": "personal.shiftable_income", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="payroll-giving",
                name="Payroll Giving (pre-tax donation from salary)",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.payroll_giving",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="A donation made through an employer's approved "
                "payroll deduction scheme comes out of pay before PAYE is applied, so the "
                "donor gets relief at their full marginal rate immediately — with no "
                "grossing-up, no claim, and no self-assessment entry — and the charity "
                "receives the whole amount without needing to reclaim anything. For a "
                "higher-rate employee this beats Gift Aid on simplicity: a £1,200 donation "
                "costs a 40% taxpayer only £720. National Insurance remains due on the "
                "donated pay, and the employer must operate a scheme with an approved "
                "agency, which is the practical condition to confirm.",
                authority_keys=["itepa2003_part12"],
                eligibility_conditions={"all": [
                    {"path": "personal.payroll_giving_annual", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="charity-gift-of-assets",
                name="Gift of shares or property to charity",
                tax_domain=TaxDomain.PERSONAL_INCOME_TAX,
                calculator_key="strategy.charity_gift_of_assets",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Giving qualifying listed shares, securities or "
                "land to charity earns two reliefs at once: the full market value is "
                "deducted from the donor's income for the year, giving income tax relief at "
                "their marginal rate, and the disposal is treated as no-gain/no-loss so any "
                "capital gain held in the asset escapes CGT entirely. For an asset standing "
                "at a large gain this is often the most tax-efficient way to give: the "
                "combined relief can exceed 60% of the value given. The asset must be a "
                "qualifying investment (listed shares/securities, units, or a qualifying "
                "interest in land) and the whole beneficial interest must pass — conditions "
                "the adviser confirms, along with the land certificate requirements.",
                authority_keys=["ita2007_s431", "tcga1992_s257"],
                eligibility_conditions={"all": [
                    {"path": "personal.charity_asset_gift_value", "op": "gt", "value": 0},
                ]},
            ),
            dict(
                code="cgt-rollover-relief",
                name="Business-asset rollover relief",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.cgt_rollover_relief",
                timeframe=Timeframe.MEDIUM,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="When a trader sells a qualifying business asset "
                "(land and buildings occupied and used for the trade, fixed plant and "
                "machinery, goodwill) and reinvests the proceeds in replacement qualifying "
                "assets within the window from 12 months before to 3 years after the "
                "disposal, the gain can be rolled into the base cost of the new assets "
                "instead of being taxed now. Full reinvestment defers the whole gain; if "
                "part of the proceeds is kept back, the smaller of the gain and the amount "
                "not reinvested is chargeable now. The deferred gain re-emerges on a future "
                "disposal of the replacement asset, so this is a deferral, not an "
                "exemption — but it keeps the full proceeds working in the trade. Both "
                "assets must be used only for the trade, which the adviser confirms.",
                authority_keys=["tcga1992_s152"],
                eligibility_conditions={"all": [
                    {"path": "property.rollover_disposal_gain", "op": "gt", "value": 0},
                    {"path": "property.rollover_replacement_cost", "op": "gt", "value": 0},
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
                name="SDLT on planned residential property purchase (England/NI)",
                tax_domain=TaxDomain.PROPERTY_TAXES,
                calculator_key="strategy.sdlt_purchase_planning",
                timeframe=Timeframe.SHORT,
                risk_status=RiskStatus.SETTLED,
                plain_english_explanation="Quantifies the SDLT on a planned residential purchase in "
                "England or Northern Ireland, including the 5% additional-dwellings surcharge and "
                "first-time buyers' relief. Where the purchase replaces a main residence sold "
                "within three years, the surcharge is recoverable — timing the sale matters as "
                "much as the price. Scotland (LBTT) and Wales (LTT) set their own rates.",
                authority_keys=["fa2003_s55", "fa2003_sch4za", "fa2003_sch6za"],
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
                authority_keys=["lbtt_scotland_act_2013_s24", "lbtta2013_sch2a"],
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
                authority_keys=["ltt_wales_act_2017_s24", "ltta2017_sch5"],
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
                authority_keys=["fa2003_s55", "fa2003_sch5"],
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
                calculator_key="strategy.salary_sacrifice",
                description="5,000 salary sacrifice from a 50,000 salary, 2025/26",
                source="Hand-computed: IT on 50k=7,486 & EE NIC=2,994.40; on 45k IT=6,486 & "
                "EE NIC=2,594.40 -> employee saves 1,400. ER NIC 6,750 vs 6,000 -> 750. "
                "5,000 into pension.",
                input_facts={"salary": 50000, "sacrifice_amount": 5000},
                expected_output={
                    "salary_sacrificed": 5000.0,
                    "employee_income_tax_and_ni_saved": 1400.0,
                    "employer_ni_saved": 750.0,
                    "into_pension": 5000.0,
                    "net_cost_of_pension_to_employee": 3600.0,
                    "total_saving": 2150.0,
                },
            ),
            dict(
                calculator_key="strategy.termination_payment",
                description="50,000 ex-gratia termination payment, employee on 40,000 other income, 2025/26",
                source="Hand-computed: 30,000 exempt -> 20,000 excess taxed as top slice on top of "
                "40,000. IT(60,000)=11,432 less IT(40,000)=5,486 -> 5,946 (10,270 at 20% + 9,730 at "
                "40%). Employer Class 1A = 20,000 at 15% = 3,000. Net to employee = 50,000 - 5,946 = 44,054.",
                input_facts={"termination_payment": 50000, "other_income": 40000},
                expected_output={
                    "exempt_amount": 30000.0,
                    "taxable_excess": 20000.0,
                    "income_tax_on_excess": 5946.0,
                    "employer_class1a_nic": 3000.0,
                    "net_to_employee": 44054.0,
                },
            ),
            dict(
                calculator_key="strategy.termination_payment",
                description="25,000 termination payment fully within the exemption, 2025/26",
                source="Hand-computed: 25,000 is below the 30,000 exemption -> wholly exempt, no "
                "income tax and no employer Class 1A NIC; the employee receives all 25,000.",
                input_facts={"termination_payment": 25000, "other_income": 40000},
                expected_output={
                    "exempt_amount": 25000.0,
                    "taxable_excess": 0.0,
                    "income_tax_on_excess": 0.0,
                    "employer_class1a_nic": 0.0,
                    "net_to_employee": 25000.0,
                },
            ),
            dict(
                calculator_key="strategy.personal_pension_contribution",
                description="Personal pension contribution in the 60% taper, 2025/26",
                source="Hand-computed: earned 110,000, 10,000 gross. PA restored 7,570->12,570 "
                "and basic band extended 10,000: tax 33,432->29,432 = 4,000 saved; plus the "
                "2,000 basic-rate credit = 6,000 relief on 10,000 = 60% effective.",
                input_facts={"earned_income": 110000, "desired_contribution": 10000},
                expected_output={
                    "relievable_gross": 10000.0,
                    "basic_rate_credit_to_pension": 2000.0,
                    "higher_rate_and_taper_saving": 4000.0,
                    "personal_allowance_restored": 5000.0,
                    "total_relief_value": 6000.0,
                    "effective_relief_rate": 0.6,
                    "net_cost_to_member": 4000.0,
                },
            ),
            dict(
                calculator_key="strategy.employer_pension_contribution",
                description="Employer pension contribution, company at the CT main rate, 2025/26",
                source="Hand-computed: 300,000 profit (25% flat) contributing 20,000 -> CT "
                "75,000->70,000 = 5,000 saved; employer NIC saved vs salary 20,000*15% = 3,000; "
                "net cost 15,000.",
                input_facts={"company_profit": 300000, "contribution": 20000},
                expected_output={
                    "contribution": 20000.0,
                    "corporation_tax_saving": 5000.0,
                    "employer_ni_saved_vs_salary": 3000.0,
                    "net_cost_to_company": 15000.0,
                },
            ),
            dict(
                calculator_key="strategy.group_loss_relief",
                description="Group relief surrendered into the marginal-relief band, 2025/26",
                source="Hand-computed: 50,000 loss into a 250,000-profit claimant. CT "
                "62,500 (25% at the 250k upper limit) vs CT on 200,000 = 50,000 - 750 marginal "
                "relief = 49,250; saved 13,250 = 26.5% marginal rate on the 50,000 relieved.",
                input_facts={"claimant_company_profit": 250000, "surrendering_company_loss": 50000},
                expected_output={
                    "loss_surrendered": 50000.0,
                    "corporation_tax_saved": 13250.0,
                    "unrelieved_loss_carried_forward": 0.0,
                    "effective_relief_rate": 0.265,
                },
            ),
            dict(
                calculator_key="strategy.isa_bed_and_isa",
                description="Bed-and-ISA within the CGT exemption, higher-rate investor, 2025/26",
                source="Hand-computed: shelter 20,000 (the full ISA limit); 2,500 gain is within "
                "the 3,000 annual exemption so no CGT on transfer; 800 of annual dividends then "
                "escape the 33.75% upper rate = 270 saved a year.",
                input_facts={"amount_to_shelter": 20000, "realised_gain": 2500,
                             "annual_dividend_income": 800, "is_higher_rate": True},
                expected_output={
                    "amount_sheltered": 20000.0,
                    "isa_allowance_remaining": 0.0,
                    "gain_covered_by_exemption": 2500.0,
                    "cgt_payable_on_transfer": 0.0,
                    "annual_dividend_tax_saved": 270.0,
                },
            ),
            dict(
                calculator_key="strategy.business_property_relief",
                description="BPR on a 2m business, pre-reform (unlimited 100%), 2025/26",
                source="Hand-computed: 2,000,000 qualifying at 100% -> fully relieved, no "
                "taxable value, 800,000 IHT saved at 40%.",
                input_facts={"qualifying_value": 2000000},
                expected_output={
                    "full_relief_cap": None,
                    "total_relieved_value": 2000000.0,
                    "taxable_value_after_relief": 0.0,
                    "iht_saved_by_relief": 800000.0,
                },
            ),
            dict(
                calculator_key="strategy.business_property_relief",
                description="Same 2m business under the 2026/27 reformed 1m cap",
                source="Hand-computed: 1,000,000 at 100% + 1,000,000 at 50% = 1,500,000 "
                "relieved; 500,000 taxable; 600,000 IHT saved at 40% (200,000 more IHT than "
                "before the cap).",
                tax_year="2026/27",
                input_facts={"qualifying_value": 2000000},
                expected_output={
                    "full_relief_cap": 1000000,
                    "value_relieved_at_100pc": 1000000.0,
                    "value_above_cap": 1000000.0,
                    "total_relieved_value": 1500000.0,
                    "taxable_value_after_relief": 500000.0,
                    "iht_saved_by_relief": 600000.0,
                },
            ),
            dict(
                calculator_key="strategy.eot_disposal_relief",
                description="EOT sale vs a normal BADR sale, 2025/26",
                source="Hand-computed: 2,000,000 gain — normal sale BADR 14% on 1,000,000 "
                "(140,000) + 24% on 1,000,000 (240,000) = 380,000; EOT sale is exempt, so 380,000 "
                "saved.",
                input_facts={"disposal_gain": 2000000, "badr_available": True,
                             "badr_lifetime_used": 0},
                expected_output={"cgt_without_eot": 380000.0, "cgt_under_eot": 0.0,
                                 "cgt_saved": 380000.0},
            ),
            dict(
                calculator_key="strategy.pension_death_benefit",
                description="Pension pot brought into the estate from April 2027, 2025/26",
                source="Hand-computed: 500,000 pot, estate above the NRB -> 40% = 200,000 extra "
                "IHT from 6 April 2027 (zero before).",
                input_facts={"pension_pot_value": 500000, "estate_above_nrb": True},
                expected_output={"iht_before_april_2027": 0.0, "iht_from_april_2027": 200000.0,
                                 "extra_iht_from_reform": 200000.0},
            ),
            dict(
                calculator_key="strategy.life_policy_in_trust",
                description="Life policy in trust vs held personally, 2025/26",
                source="Hand-computed: 400,000 sum assured, estate above the NRB — held personally "
                "it would add 40% = 160,000 IHT; in trust it is outside the estate (0), so 160,000 "
                "saved and 400,000 available for the bill.",
                input_facts={"sum_assured": 400000, "estate_above_nrb": True},
                expected_output={"iht_if_held_personally": 160000.0, "iht_if_written_in_trust": 0.0,
                                 "iht_saved_by_writing_in_trust": 160000.0,
                                 "payout_available_for_iht_bill": 400000.0},
            ),
            dict(
                calculator_key="strategy.rd_tax_relief",
                description="R&D merged-scheme credit, main-rate company, 2025/26",
                source="Hand-computed: 100,000 qualifying spend -> 20% RDEC = 20,000 gross; "
                "the credit is taxable at 25% (5,000); net benefit 15,000.",
                input_facts={"qualifying_rd_spend": 100000, "marginal_rate": 0.25},
                expected_output={"gross_credit": 20000.0, "tax_on_credit": 5000.0,
                                 "net_benefit": 15000.0},
            ),
            dict(
                calculator_key="strategy.patent_box",
                description="Patent Box vs the 25% main rate, 2025/26",
                source="Hand-computed: 200,000 patented-product profit at 10% (20,000) vs the "
                "25% main rate (50,000) = 30,000 saved.",
                input_facts={"patent_profit": 200000, "marginal_rate": 0.25},
                expected_output={"tax_at_main_rate": 50000.0, "tax_under_patent_box": 20000.0,
                                 "tax_saving": 30000.0},
            ),
            dict(
                calculator_key="strategy.commercial_property_fixtures",
                description="Commercial fixtures within the AIA, main-rate company, 2025/26",
                source="Hand-computed: 200,000 fixtures fully within the 1,000,000 AIA -> "
                "200,000 first-year allowance; at 25% that saves 50,000.",
                input_facts={"fixtures_value": 200000, "marginal_rate": 0.25},
                expected_output={"aia_used": 200000.0, "first_year_allowance": 200000.0,
                                 "tax_saved_year_one": 50000.0},
            ),
            dict(
                calculator_key="strategy.property_incorporation",
                description="Landlord incorporation break-even with s.162 relief, 2025/26",
                source="Hand-computed: personal s.24 tax on 50k rental (40k other income) = "
                "17,946 IT less 6,000 reducer = 11,946; company CT on 20k = 3,800; saving 8,146. "
                "SDLT on 1m at additional rates = 93,750; s.162 defers CGT; break-even 11.51 yrs.",
                input_facts={"portfolio_value": 1000000, "rental_profit": 50000,
                             "finance_costs": 30000, "other_income": 40000,
                             "latent_gain": 300000, "s162_relief_available": True},
                expected_output={
                    "personal_annual_tax": 11946.0,
                    "company_annual_tax": 3800.0,
                    "annual_tax_saving": 8146.0,
                    "sdlt_on_transfer": 93750.0,
                    "cgt_on_transfer": 0.0,
                    "one_off_cost": 93750.0,
                    "break_even_years": 11.51,
                },
            ),
            dict(
                calculator_key="strategy.property_incorporation",
                description="Incorporation with profits extracted as dividends, 2025/26",
                source="Hand-computed: post-CT profit 16,200 drawn as dividends over 40k income "
                "(taxable 27,430) -> 2,856.25 dividend tax; company total 6,656.25; the after-"
                "extraction saving falls from 8,146 to 5,289.75.",
                input_facts={"portfolio_value": 1000000, "rental_profit": 50000,
                             "finance_costs": 30000, "other_income": 40000,
                             "latent_gain": 300000, "s162_relief_available": True,
                             "extract_profits": True},
                expected_output={
                    "dividend_tax_on_extraction": 2856.25,
                    "company_total_tax_if_extracted": 6656.25,
                    "annual_saving_after_extraction": 5289.75,
                },
            ),
            dict(
                calculator_key="strategy.relevant_property_trust_charges",
                description="Discretionary trust: entry, ten-year and exit charges, 2025/26",
                source="Hand-computed: 500k settled, 325k NRB -> 20% entry on 175k = 35,000; "
                "600k at the 10-year point -> 6% of 275k = 16,500 (rate 2.75%); a 100k exit at "
                "20 quarters -> 2.75% x 0.5 x 100k = 1,375.",
                input_facts={"amount_settled": 500000, "trust_value": 600000,
                             "amount_distributed": 100000, "quarters_since_last_charge": 20},
                expected_output={
                    "entry_charge": 35000.0,
                    "ten_year_charge": 16500.0,
                    "ten_year_effective_rate": 0.0275,
                    "exit_charge": 1375.0,
                },
            ),
            dict(
                calculator_key="strategy.partnership_profit_allocation",
                description="Three-partner firm, each taxed on their share, 2025/26",
                source="Hand-computed: 90,000 profit split 40/35/25 = 36,000/31,500/22,500; "
                "partners' other income 50,000/10,000/0 -> tax 23,237.80 + 6,921.80 + 2,581.80 "
                "= 32,741.40.",
                input_facts={"total_profit": 90000, "partners": [
                    {"profit_share": 0.4, "other_income": 50000},
                    {"profit_share": 0.35, "other_income": 10000},
                    {"profit_share": 0.25, "other_income": 0},
                ]},
                expected_output={"number_of_partners": 3, "total_tax": 32741.40},
            ),
            dict(
                calculator_key="strategy.relevant_property_trust_charges",
                description="Trust NRB reduced by same-day related settlements, 2025/26",
                source="Hand-computed: 500,000 settled; 200,000 of same-day related settlements "
                "cut the available band from 325,000 to 125,000, so the 20% entry charge bites on "
                "375,000 = 75,000.",
                input_facts={"amount_settled": 500000, "trust_value": 500000,
                             "same_day_settlements_value": 200000},
                expected_output={"available_nrb": 125000.0, "entry_charge": 75000.0},
            ),
            dict(
                calculator_key="strategy.partnership_profit_allocation",
                description="Two-partner split, one with other income, 2025/26",
                source="Hand-computed: 100k profit; partner A has 40k other income. 50/50 -> "
                "tax 25,677.80 + 9,731.80 = 35,409.60; shifting to 30/70 -> 16,477.80 + "
                "18,088.60 = 34,566.40; saving 843.20.",
                input_facts={"total_profit": 100000, "partner1_other_income": 40000,
                             "partner2_other_income": 0, "current_partner1_share": 0.5,
                             "proposed_partner1_share": 0.3},
                expected_output={
                    "total_profit": 100000.0,
                    "current_total_tax": 35409.60,
                    "proposed_total_tax": 34566.40,
                    "tax_saving": 843.20,
                },
            ),
            dict(
                calculator_key="strategy.property_income_finance_cost",
                description="Higher-rate landlord hit by the s.24 restriction, 2025/26",
                source="Hand-computed: 20k profit + 50k income -> tax on 70k=15,432 less 20% "
                "reducer on 10k interest (2,000)=13,432; full deduction (tax on 60k)=11,432 -> "
                "s.24 costs 2,000 extra.",
                input_facts={"rental_income": 24000, "allowable_expenses": 4000,
                             "finance_costs": 10000, "other_income": 50000},
                expected_output={
                    "rental_profit": 20000.0,
                    "basic_rate_tax_reducer": 2000.0,
                    "tax_under_s24": 13432.0,
                    "tax_if_interest_fully_deductible": 11432.0,
                    "extra_tax_from_restriction": 2000.0,
                },
            ),
            dict(
                calculator_key="strategy.venture_capital_investment",
                description="EIS: 30% income tax relief plus CGT deferral, 2025/26",
                source="Hand-computed: 100,000 EIS -> 30,000 income tax relief (within the "
                "50,000 IT bill); a 40,000 gain reinvested is deferred = 40,000*24% = 9,600 "
                "CGT deferred; net cost 70,000.",
                input_facts={"scheme": "eis", "amount_invested": 100000,
                             "income_tax_liability": 50000, "gain_reinvested": 40000,
                             "is_higher_rate": True},
                expected_output={
                    "eligible_investment": 100000.0,
                    "income_tax_relief": 30000.0,
                    "cgt_deferred": 9600.0,
                    "cgt_permanently_saved": 0.0,
                    "net_cost_after_relief": 70000.0,
                },
            ),
            dict(
                calculator_key="strategy.venture_capital_investment",
                description="SEIS: 50% income tax relief plus 50% CGT reinvestment relief, 2025/26",
                source="Hand-computed: 100,000 SEIS -> 50,000 income tax relief; half of a "
                "40,000 reinvested gain (20,000) is exempt = 20,000*24% = 4,800 CGT saved; net "
                "cost 45,200.",
                input_facts={"scheme": "seis", "amount_invested": 100000,
                             "income_tax_liability": 60000, "gain_reinvested": 40000,
                             "is_higher_rate": True},
                expected_output={
                    "income_tax_relief": 50000.0,
                    "cgt_permanently_saved": 4800.0,
                    "net_cost_after_relief": 45200.0,
                },
            ),
            dict(
                calculator_key="strategy.venture_capital_investment",
                description="VCT: 30% relief capped at the income tax bill, tax-free dividends, 2025/26",
                source="Hand-computed: 50,000 VCT would give 15,000 relief but the IT bill is "
                "only 10,000, so relief is capped at 10,000; dividends are tax-free; net cost "
                "40,000.",
                input_facts={"scheme": "vct", "amount_invested": 50000,
                             "income_tax_liability": 10000, "is_higher_rate": True},
                expected_output={
                    "income_tax_relief": 10000.0,
                    "capped_by_income_tax_liability": True,
                    "tax_free_dividends": True,
                    "net_cost_after_relief": 40000.0,
                },
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
                calculator_key="strategy.income_timing",
                description="Dividend timed 2025/26 vs 2026/27 (+2pp rise), higher-rate",
                source="Hand-computed: earned 60,000 both years; 20,000 dividend at "
                "33.75% less 500 allowance = 6,581.25 this year vs 6,971.25 at the "
                "2026/27 35.75% rate; taking it this year saves 390.00.",
                input_facts={"shiftable_amount": 20000, "income_type": "dividend",
                             "earned_income": 60000},
                expected_output={
                    "incremental_tax_this_year": 6581.25,
                    "incremental_tax_next_year": 6971.25,
                    "recommendation": "take_this_year",
                    "saving": 390.0,
                },
            ),
            dict(
                calculator_key="strategy.payroll_giving",
                description="Payroll Giving by a higher-rate employee, 2025/26",
                source="Hand-computed: salary 60,000, taxable 47,430, tax 11,432.00; "
                "donating 1,200 pre-tax leaves taxable 46,230, tax 10,952.00 — saving "
                "480.00 (40% of 1,200); the charity receives the full 1,200 and the "
                "donor's net cost is 720.00.",
                input_facts={"earned_income": 60000, "annual_donation": 1200},
                expected_output={
                    "charity_receives": 1200.0,
                    "income_tax_saved": 480.0,
                    "net_cost_to_donor": 720.0,
                },
            ),
            dict(
                calculator_key="strategy.charity_gift_of_assets",
                description="Listed shares worth 20,000 (gain 10,000) gifted, 2025/26",
                source="Hand-computed: earned 80,000 (taxable 67,430, tax 19,432.00); "
                "s.431 deducts 20,000 -> taxable 47,430, tax 11,432.00 = 8,000.00 income "
                "tax saved (all at 40%). s.257 no-gain/no-loss: selling instead would "
                "charge 10,000 - 3,000 AEA = 7,000 at 24% ('other', income above the "
                "basic band) = 1,680.00 CGT avoided. Total benefit 9,680.00; net cost "
                "of the gift 20,000 - 8,000 = 12,000.00.",
                input_facts={"gift_value": 20000, "held_gain": 10000,
                             "earned_income": 80000},
                expected_output={
                    "income_tax_saved": 8000.0,
                    "cgt_avoided": 1680.0,
                    "total_tax_benefit": 9680.0,
                    "net_cost_of_gift": 12000.0,
                },
            ),
            dict(
                calculator_key="strategy.cgt_rollover_relief",
                description="Partial reinvestment: 450k of 500k proceeds, 2025/26",
                source="Hand-computed: proceeds 500,000, gain 200,000, replacement "
                "450,000 -> 50,000 not reinvested, chargeable now (s.153); 150,000 "
                "rolled over. Earned 60,000 (taxable 47,430, above the basic band) so "
                "the 'other' higher rate 24% applies throughout. Without relief: "
                "(200,000 - 3,000 AEA) x 24% = 47,280.00. With relief: (50,000 - 3,000) "
                "x 24% = 11,280.00. Tax deferred 36,000.00.",
                input_facts={"disposal_proceeds": 500000, "disposal_gain": 200000,
                             "replacement_cost": 450000, "earned_income": 60000},
                expected_output={
                    "amount_not_reinvested": 50000.0,
                    "gain_chargeable_now": 50000.0,
                    "gain_rolled_over": 150000.0,
                    "cgt_without_relief": 47280.0,
                    "cgt_with_relief": 11280.0,
                    "tax_deferred": 36000.0,
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
