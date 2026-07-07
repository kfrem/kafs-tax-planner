# UK Tax Planner — editorial review checklist

The complete four-eyes review list for a rule-base release: every parameter,
strategy and authority to confirm against the primary source before a
`RuleBaseRelease` is moved from **DRAFT** to **Released**. Generated from the live
rule base (2025/26). Put **Y** or **N** in *Correct?* and record any correction in *Comments*.

| Field | |
|---|---|
| Reviewing professional | _______________________ |
| Second reviewer (distinct from editor) | _______________________ |
| Date | _______________________ |
| Rule-base version | 2025.x |

Totals: **36 parameters · 41 strategies · 50 authorities = 127 items.**

## A. Parameters — rates & thresholds (36)

| # | Parameter | Value (2025/26) | Correct? (Y/N) | Comments / corrections |
|---|---|---|---|---|
| 1 | Capital allowances: AIA limit and writing-down rates (`capital_allowances.aia`) | aia_limit=1,000,000; main_pool_wda=18%; special_rate_wda=6% |  |  |
| 2 | CGT annual exempt amount (`cgt.annual_exempt_amount`) | amount=3,000 |  |  |
| 3 | Business Asset Disposal Relief: reduced CGT rate and lifetime limit (`cgt.business_asset_disposal_relief`) | rate=14%; lifetime_limit=1,000,000 |  |  |
| 4 | Lettings relief cap (shared-occupancy let, TCGA 1992 s.223B) (`cgt.lettings_relief`) | cap=40,000 |  |  |
| 5 | CGT rates by asset class (lower = within basic band) (`cgt.rates`) | lower=18%; higher=24%; lower=18%; higher=24% |  |  |
| 6 | Corporation tax rates and marginal relief (`corporation_tax.rates`) | main_rate=25%; main_rate_limit=250,000; small_profits_rate=19%; small_profits_limit=50,000; marginal_relief_fraction=1.5% |  |  |
| 7 | Directors' loan s.455 charge rate (`directors_loan.s455`) | rate=33.75%; beneficial_loan_threshold=10,000 |  |  |
| 8 | Dividend allowance (`dividend_tax.allowance`) | amount=500 |  |  |
| 9 | Dividend tax bands (`dividend_tax.bands`) | bands: [rate=8.75%; upper=37,700; rate=33.75%; upper=125,140; rate=39.35%; upper=none] |  |  |
| 10 | IHT Business/Agricultural Property Relief: 100% rate and combined cap (`iht.business_property_relief`) | rate_above_cap=1; full_relief_cap=none |  |  |
| 11 | IHT gift exemptions and PET taper relief (`iht.gift_exemptions`) | taper_relief: [tax_reduction=20%; years_survived_to=4; years_survived_from=3; tax_reduction=40%; years_survived_to=5; years_survived_from=4; tax_reduction=60%; years_survived_to=6; years_survived_from=5; tax_reduction=80%; years_survived_to=7; years_survived_from=6]; annual_exemption=3,000; small_gift_exemption=250 |  |  |
| 12 | IHT nil-rate band (frozen through 2029/30) (`iht.nil_rate_band`) | amount=325,000 |  |  |
| 13 | IHT rates: death, reduced charitable, lifetime CLT (`iht.rates`) | death_rate=40%; lifetime_clt_rate=20%; reduced_charity_rate=36%; charity_baseline_fraction=10% |  |  |
| 14 | IHT residence nil-rate band and taper (`iht.residence_nil_rate_band`) | amount=175,000; taper_rate=50%; taper_threshold=2,000,000 |  |  |
| 15 | Income tax bands (non-savings, non-dividend) (`income_tax.bands`) | bands: [rate=20%; upper=37,700; rate=40%; upper=125,140; rate=45%; upper=none] |  |  |
| 16 | Marriage Allowance transferable amount (`income_tax.marriage_allowance`) | transferable_amount=1,260 |  |  |
| 17 | Personal Allowance (`income_tax.personal_allowance`) | amount=12,570; taper_rate=50%; taper_threshold=100,000 |  |  |
| 18 | ISA annual subscription limit (`isa.allowance`) | amount=20,000 |  |  |
| 19 | LBTT lease: NPV discount rate and bands (Scotland) (`lbtt.lease_npv_bands`) | bands: [rate=0; upper=150,000; rate=1%; upper=2,000,000; rate=2%; upper=none]; discount_rate=3.5% |  |  |
| 20 | LBTT non-residential freehold bands (Scotland) (`lbtt.non_residential_bands`) | bands: [rate=0; upper=150,000; rate=1%; upper=250,000; rate=5%; upper=none] |  |  |
| 21 | LBTT residential bands, Additional Dwelling Supplement, first-time buyer relief (Scotland) (`lbtt.residential_bands`) | bands: [rate=0; upper=145,000; rate=2%; upper=250,000; rate=5%; upper=325,000; rate=10%; upper=750,000; rate=12%; upper=none]; additional_dwelling_supplement=8%; first_time_buyer_nil_rate_threshold=175,000 |  |  |
| 22 | LTT non-residential lease: NPV discount rate and bands (Wales) (`ltt.lease_npv_bands`) | bands: [rate=0; upper=225,000; rate=1%; upper=2,000,000; rate=2%; upper=none]; discount_rate=3.5% |  |  |
| 23 | LTT non-residential freehold bands (Wales) (`ltt.non_residential_bands`) | bands: [rate=0; upper=225,000; rate=1%; upper=250,000; rate=5%; upper=1,000,000; rate=6%; upper=none] |  |  |
| 24 | LTT residential main and higher (additional-property) bands (Wales) (`ltt.residential_bands`) | main_bands: [rate=0; upper=225,000; rate=6%; upper=400,000; rate=7.5%; upper=750,000; rate=10%; upper=1,500,000; rate=12%; upper=none]; higher_bands: [rate=5%; upper=180,000; rate=8.5%; upper=250,000; rate=10%; upper=400,000; rate=12.5%; upper=750,000; rate=15%; upper=1,500,000; rate=17%; upper=none] |  |  |
| 25 | Class 4 NIC (self-employed) (`national_insurance.class4`) | rate=6%; upper_rate=2%; lower_profits_limit=12,570; upper_profits_limit=50,270 |  |  |
| 26 | Employee Class 1 NIC (`national_insurance.employee_class1`) | rate=8%; upper_rate=2%; primary_threshold=12,570; upper_earnings_limit=50,270 |  |  |
| 27 | Employer (secondary) Class 1 NIC (`national_insurance.employer_class1`) | rate=15%; secondary_threshold=5,000 |  |  |
| 28 | Employment Allowance (`national_insurance.employment_allowance`) | amount=10,500 |  |  |
| 29 | Patent Box effective corporation-tax rate (`patent_box.rate`) | rate=10% |  |  |
| 30 | Pension annual allowance and taper (`pension.annual_allowance`) | standard_amount=60,000; minimum_tapered_amount=10,000; taper_threshold_income=200,000; taper_adjusted_income_limit=260,000 |  |  |
| 31 | Residential landlord finance-cost (mortgage interest) tax-reducer rate (`property_income.finance_cost_restriction`) | reducer_rate=20% |  |  |
| 32 | R&D merged-scheme (RDEC) above-the-line credit rate (`rd.merged_scheme`) | rdec_rate=20%; rd_intensive_threshold=30%; rd_intensive_credit_rate=14.5% |  |  |
| 33 | SDLT non-residential lease: NPV discount rate and bands (England/NI) (`sdlt.lease_npv_bands`) | bands: [rate=0; upper=150,000; rate=1%; upper=5,000,000; rate=2%; upper=none]; discount_rate=3.5% |  |  |
| 34 | SDLT non-residential/mixed freehold bands (England/NI) (`sdlt.non_residential_bands`) | bands: [rate=0; upper=150,000; rate=2%; upper=250,000; rate=5%; upper=none] |  |  |
| 35 | SDLT residential bands, surcharge, FTB relief (England/NI) (`sdlt.residential_bands`) | bands: [rate=0; upper=125,000; rate=2%; upper=250,000; rate=5%; upper=925,000; rate=10%; upper=1,500,000; rate=12%; upper=none]; cap=500,000; relief_threshold=300,000; rate_above_threshold=5%; additional_dwelling_surcharge=5% |  |  |
| 36 | EIS/SEIS/VCT income-tax relief rates, annual limits and CGT treatment (`venture_capital.schemes`) | relief_rate=30%; annual_limit=1,000,000; cgt_deferral=yes; min_holding_years=3; tax_free_dividends=no; cgt_reinvestment_relief_rate=0; relief_rate=30%; annual_limit=200,000; cgt_deferral=no; min_holding_years=5; tax_free_dividends=yes; cgt_reinvestment_relief_rate=0; relief_rate=50%; annual_limit=200,000; cgt_deferral=no; min_holding_years=3; tax_free_dividends=no; cgt_reinvestment_relief_rate=50% |  |  |

## B. Strategies — tax logic & risk status (41)

Rows marked **borderline** carry a professional-judgement caveat — review with particular care.

| # | Strategy | Risk | Authority cited | Correct? (Y/N) | Comments / corrections |
|---|---|---|---|---|---|
| 1 | Capital allowances / Annual Investment Allowance | settled | Capital Allowances Act 2001 s.51A |  |  |
| 2 | Capital allowances on commercial-property fixtures | settled | Capital Allowances Act 2001 ss.33A-33B & s.187A (integral features / fixtures) |  |  |
| 3 | Directors' loan s.455 charge | settled | Corporation Tax Act 2010 s.455 |  |  |
| 4 | Employer pension contribution | settled | Corporation Tax Act 2009 s.54 |  |  |
| 5 | Group relief for company losses | settled | Corporation Tax Act 2010 Part 5 (ss.97-188) |  |  |
| 6 | Patent Box (10% rate on patented-product profits) | settled | Corporation Tax Act 2010 Part 8A (Patent Box) |  |  |
| 7 | R&D tax relief (merged scheme) | settled | Corporation Tax Act 2009 Part 13 (as amended, merged R&D scheme) |  |  |
| 8 | Employee Ownership Trust sale (CGT-free) | settled | Taxation of Chargeable Gains Act 1992 s.236H (Employee Ownership Trust) |  |  |
| 9 | Incorporation versus remaining a sole trader | **borderline** | Corporation Tax Act 2010 Part 3A (ss.18A-18M); Income Tax Act 2007 s.35; Social Security Contributions and Benefits Act 1992 s.15 |  |  |
| 10 | Property portfolio incorporation (should the landlord incorporate?) | **borderline** | Income Tax (Trading and Other Income) Act 2005 ss.272A-274C; Taxation of Chargeable Gains Act 1992 s.162 |  |  |
| 11 | Salary/dividend extraction mix | settled | Corporation Tax Act 2010 Part 3A (ss.18A-18M); Income Tax Act 2007 s.13A; Income Tax Act 2007 s.35; Jones v Garnett (Arctic Systems) [2007] UKHL 35; Social Security Contributions and Benefits Act 1992 s.6 |  |  |
| 12 | Business / Agricultural Property Relief | settled | Inheritance Tax Act 1984 ss.103-114 (BPR) and ss.115-124C (APR) |  |  |
| 13 | Charitable legacy and the 36% reduced rate | settled | Inheritance Tax Act 1984 Sch 1A |  |  |
| 14 | Lifetime gifting: exemptions and potentially exempt transfers | settled | Inheritance Tax Act 1984 s.19; Inheritance Tax Act 1984 s.3A; Inheritance Tax Act 1984 s.7 and Sch 1 |  |  |
| 15 | Spouse exemption and transferable nil-rate bands | settled | Inheritance Tax Act 1984 s.18; Inheritance Tax Act 1984 s.8A; Inheritance Tax Act 1984 s.8D; Inheritance Tax Act 1984 s.8G |  |  |
| 16 | Life policy in trust to fund the IHT bill | settled | Inheritance Tax Act 1984 s.5 (meaning of estate) |  |  |
| 17 | Pension death-benefit IHT (from April 2027) | **borderline** | IHTA 1984 s.3 (as to be amended from 6 April 2027, Finance Bill 2025-26) |  |  |
| 18 | Relevant-property trust IHT charges | settled | Inheritance Tax Act 1984 ss.58-69 (relevant property) |  |  |
| 19 | Gift Aid higher-rate relief | settled | Income Tax Act 2007 s.414 |  |  |
| 20 | Bed-and-ISA (shelter investments in an ISA) | settled | Income Tax (Trading and Other Income) Act 2005 s.694 |  |  |
| 21 | Marriage Allowance transfer | settled | Income Tax Act 2007 ss.55A-55E |  |  |
| 22 | Partnership / LLP profit-share allocation | **borderline** | Income Tax (Trading and Other Income) Act 2005 s.850 |  |  |
| 23 | Pension annual allowance carry-forward | settled | Corporation Tax Act 2009 s.54; Finance Act 2004 s.190; Finance Act 2004 s.228 |  |  |
| 24 | Personal pension contribution (relief at source) | settled | Finance Act 2004 s.190 |  |  |
| 25 | Landlord finance-cost restriction (s.24) | settled | Income Tax (Trading and Other Income) Act 2005 ss.272A-274C |  |  |
| 26 | Salary sacrifice into an employer pension | settled | Social Security Contributions and Benefits Act 1992 s.6 |  |  |
| 27 | EIS / SEIS / VCT investment relief | settled | Income Tax Act 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT) |  |  |
| 28 | Business Asset Disposal Relief | settled | Taxation of Chargeable Gains Act 1992 ss.169H-169S; Taxation of Chargeable Gains Act 1992 ss.1H-1K |  |  |
| 29 | Lettings relief (shared-occupancy let) | settled | Taxation of Chargeable Gains Act 1992 s.223B; Taxation of Chargeable Gains Act 1992 ss.1H-1K; Taxation of Chargeable Gains Act 1992 ss.222-223 |  |  |
| 30 | Private residence relief on property disposal | settled | Taxation of Chargeable Gains Act 1992 ss.1H-1K; Taxation of Chargeable Gains Act 1992 ss.222-223 |  |  |
| 31 | Spousal transfer before disposal | settled | Taxation of Chargeable Gains Act 1992 s.58; Taxation of Chargeable Gains Act 1992 ss.1H-1K |  |  |
| 32 | Timing of disposals across tax years | settled | Taxation of Chargeable Gains Act 1992 ss.1H-1K |  |  |
| 33 | LBTT on a lease (Scotland) | settled | Land and Buildings Transaction Tax (Scotland) Act 2013 s.24 |  |  |
| 34 | LBTT on non-residential purchase (Scotland) | settled | Land and Buildings Transaction Tax (Scotland) Act 2013 s.24 |  |  |
| 35 | LBTT on planned property purchase (Scotland) | settled | Land and Buildings Transaction Tax (Scotland) Act 2013 s.24 |  |  |
| 36 | LTT on a non-residential lease (Wales) | settled | Land Transaction Tax and Anti-avoidance of Devolved Taxes (Wales) Act 2017 s.24 |  |  |
| 37 | LTT on non-residential purchase (Wales) | settled | Land Transaction Tax and Anti-avoidance of Devolved Taxes (Wales) Act 2017 s.24 |  |  |
| 38 | LTT on planned property purchase (Wales) | settled | Land Transaction Tax and Anti-avoidance of Devolved Taxes (Wales) Act 2017 s.24 |  |  |
| 39 | SDLT on a non-residential lease (England/NI) | settled | Finance Act 2003 Sch 5 (amount of tax chargeable: rent) |  |  |
| 40 | SDLT on non-residential purchase (England/NI) | settled | Finance Act 2003 s.55 (SDLT rates: Table A residential, Table B non-residential/mixed) |  |  |
| 41 | SDLT on planned property purchase | settled | Finance Act 2003 s.55 (SDLT rates: Table A residential, Table B non-residential/mixed); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 Sch 6ZA |  |  |

## C. Authorities — citations still good law (50)

| # | Citation | Status | Correct? (Y/N) | Comments / corrections |
|---|---|---|---|---|
| 1 | Capital Allowances Act 2001 s.51A | in force |  |  |
| 2 | Capital Allowances Act 2001 ss.33A-33B & s.187A (integral features / fixtures) | in force |  |  |
| 3 | Corporation Tax Act 2009 Part 13 (as amended, merged R&D scheme) | in force |  |  |
| 4 | Corporation Tax Act 2009 s.54 | in force |  |  |
| 5 | Corporation Tax Act 2010 Part 3A (ss.18A-18M) | in force |  |  |
| 6 | Corporation Tax Act 2010 Part 5 (ss.97-188) | in force |  |  |
| 7 | Corporation Tax Act 2010 Part 8A (Patent Box) | in force |  |  |
| 8 | Corporation Tax Act 2010 s.455 | in force |  |  |
| 9 | Finance Act 2003 s.55 (SDLT rates: Table A residential, Table B non-residential/mixed) | in force |  |  |
| 10 | Finance Act 2003 Sch 4ZA (higher rates for additional dwellings) | in force |  |  |
| 11 | Finance Act 2003 Sch 5 (amount of tax chargeable: rent) | in force |  |  |
| 12 | Finance Act 2003 Sch 6ZA | in force |  |  |
| 13 | Finance Act 2004 s.190 | in force |  |  |
| 14 | Finance Act 2004 s.228 | in force |  |  |
| 15 | IHTA 1984 s.3 (as to be amended from 6 April 2027, Finance Bill 2025-26) | in force |  |  |
| 16 | Income Tax Act 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT) | in force |  |  |
| 17 | Income Tax Act 2007 s.10 | in force |  |  |
| 18 | Income Tax Act 2007 s.13A | in force |  |  |
| 19 | Income Tax Act 2007 s.35 | in force |  |  |
| 20 | Income Tax Act 2007 s.414 | in force |  |  |
| 21 | Income Tax Act 2007 ss.55A-55E | in force |  |  |
| 22 | Income Tax Act 2007 ss.55B-55E | in force |  |  |
| 23 | Income Tax (Trading and Other Income) Act 2005 s.694 | in force |  |  |
| 24 | Income Tax (Trading and Other Income) Act 2005 s.850 | in force |  |  |
| 25 | Income Tax (Trading and Other Income) Act 2005 ss.272A-274C | in force |  |  |
| 26 | Inheritance Tax Act 1984 s.18 | in force |  |  |
| 27 | Inheritance Tax Act 1984 s.19 | in force |  |  |
| 28 | Inheritance Tax Act 1984 s.3A | in force |  |  |
| 29 | Inheritance Tax Act 1984 s.5 (meaning of estate) | in force |  |  |
| 30 | Inheritance Tax Act 1984 s.7 and Sch 1 | in force |  |  |
| 31 | Inheritance Tax Act 1984 s.8A | in force |  |  |
| 32 | Inheritance Tax Act 1984 s.8D | in force |  |  |
| 33 | Inheritance Tax Act 1984 s.8G | in force |  |  |
| 34 | Inheritance Tax Act 1984 Sch 1A | in force |  |  |
| 35 | Inheritance Tax Act 1984 ss.103-114 (BPR) and ss.115-124C (APR) | in force |  |  |
| 36 | Inheritance Tax Act 1984 ss.58-69 (relevant property) | in force |  |  |
| 37 | ITTOIA 2005 s.383 | in force |  |  |
| 38 | Jones v Garnett (Arctic Systems) [2007] UKHL 35 | in force |  |  |
| 39 | Land and Buildings Transaction Tax (Scotland) Act 2013 s.24 | in force |  |  |
| 40 | Land Transaction Tax and Anti-avoidance of Devolved Taxes (Wales) Act 2017 s.24 | in force |  |  |
| 41 | National Insurance Contributions Act 2014 s.1 | in force |  |  |
| 42 | Social Security Contributions and Benefits Act 1992 s.15 | in force |  |  |
| 43 | Social Security Contributions and Benefits Act 1992 s.6 | in force |  |  |
| 44 | Taxation of Chargeable Gains Act 1992 s.162 | in force |  |  |
| 45 | Taxation of Chargeable Gains Act 1992 s.223B | in force |  |  |
| 46 | Taxation of Chargeable Gains Act 1992 s.236H (Employee Ownership Trust) | in force |  |  |
| 47 | Taxation of Chargeable Gains Act 1992 s.58 | in force |  |  |
| 48 | Taxation of Chargeable Gains Act 1992 ss.169H-169S | in force |  |  |
| 49 | Taxation of Chargeable Gains Act 1992 ss.1H-1K | in force |  |  |
| 50 | Taxation of Chargeable Gains Act 1992 ss.222-223 | in force |  |  |

## Sign-off

| | |
|---|---|
| Overall decision | approve / approve with exceptions / reject |
| Reviewer signature | _______________________ |
| Date | _______________________ |

> Once both reviewers approve, mark the `RuleBaseRelease` as **Released** in `/admin/`
> (the second reviewer must be distinct from the editor). Only then can advice be
> generated for real clients.
