# Tax-planning coverage map & backlog

The master checklist: every mainstream UK planning strategy an accountant
offers, mapped to what the app does **today** vs what is still to build.
This is the single source of truth for "is X covered?" — keep it current as
strategies land.

Legend: **✓ Built** (a live strategy) · **◐ Partial** (foundations exist,
needs a dedicated strategy or finishing) · **○ Planned** (not started).

Honest headline: the app covers the **high-frequency owner-manager, IHT and
CGT core** — the technically hardest, highest-value part (~a third of the
full menu below). The rest is a well-defined backlog; the architecture adds
each one systematically (the six-part recipe in `ONBOARDING.md` §5). Build
by value × frequency, not top-to-bottom — see the recommended order at the
end.

Last updated: 25 July 2026.

---

## Individuals

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Pension contributions (band extension, PA restoration in £100k–125k taper) | ✓ | `personal-pension-contribution` — standalone recommendation delegating to `combined_personal_tax`: basic-rate credit + higher-rate/taper relief through band extension, PA restoration, **effective relief rate up to 60%** in the £100k–125,140 taper, net cost, and the FA 2004 s.190 relevant-earnings cap. | — |
| Marriage Allowance | ✓ | `marriage-allowance-transfer` | — |
| ISA maximisation / Bed-and-ISA | ✓ | `isa-bed-and-isa` — shelters investments in an ISA (capped at the £20,000 limit); quantifies CGT on the transfer (nil where the gain is within the annual exemption) and the yearly dividend tax saved once inside the wrapper (ITTOIA 2005 s.694). Future growth is CGT-free but not projected (depends on growth rate). | — |
| Salary sacrifice (pension / EV / childcare) | ✓ | `salary-sacrifice-into-pension` — swaps salary for an employer pension contribution; quantifies the employee's income tax + Class 1 NIC saving, the employer's secondary NIC saving, the amount into the pension gross and its net cost (SSCBA 1992 s.6). EV/childcare variants follow the same engine. | — |
| Gift Aid (extends basic-rate band) | ✓ | `gift-aid-relief` — basic-rate gross-up, higher-rate band relief + PA restoration in the taper (ITA 2007 s.414). | — |
| Dividend vs salary optimisation | ✓ | `salary-dividend-mix` | — |
| EIS / SEIS / VCT (IT relief + CGT defer/exempt) | ✓ | `venture-capital-investment` — income-tax relief (EIS 30%/£1m, SEIS 50%/£200k, VCT 30%/£200k), capped at the investor's IT bill, plus the CGT treatment (EIS gain deferral, SEIS 50% reinvestment exemption, VCT tax-free dividends), and the net cost after relief (ITA 2007 Parts 5/5A/6). Parameterised by scheme (rates-as-data). | — |
| Timing of income (shift between years) | ✓ | `income-timing-across-years` — compares the incremental tax on a controllable amount (dividend, ITTOIA 2005 ss.383-384; or bonus, ITEPA 2003 s.18 receipts basis) landing this year vs next, using each year's own released rates (so the April-2026 dividend rise is priced in) and the client's expected income in each year. | — |

## Companies / business owners

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Salary vs dividend mix | ✓ | `salary-dividend-mix` | — |
| Directors' loan account / s.455 (33.75% charge) | ✓ | `directors-loan-s455` — the charge on the balance outstanding after the 9-month window, and the amount avoided by repaying in time (CTA 2010 s.455). | — |
| Capital allowances / Annual Investment Allowance | ✓ | `capital-allowances-aia` — 100% AIA up to £1m, 18% WDA on the excess, tax saved at the marginal rate (CAA 2001 s.51A). **Full expensing now added** — `capital-allowances-full-expensing` (CAA 2001 s.45S): 100% FYA on new main-rate plant with no cap, quantified against the AIA-then-WDA route. | — |
| R&D tax relief | ✓ | `rd-tax-relief` — the merged-scheme 20% RDEC on qualifying spend; quantifies the gross credit, the tax on it (the credit is taxable) and the net cash benefit (~15% for a main-rate company) (CTA 2009 Part 13). R&D-intensive-SME rate flagged for the adviser. | — |
| Employer pension contributions (CT relief, no NI) | ✓ | `employer-pension-contribution` — standalone recommendation: corporation-tax saving, employer NIC saved versus paying the same as salary, no relevant-earnings cap, net cost to the company (CTA 2009 s.54 wholly-and-exclusively test flagged for the reviewer). | — |
| Employee Ownership Trust (EOT) — CGT-free sale | ✓ | `eot-disposal-relief` — quantifies the CGT saved by selling a controlling stake to an EOT (0%) vs a normal sale (BADR 14% to £1m then the standard rate) (TCGA 1992 s.236H). Finance Act 2024/2025 tightening flagged. | — |
| Group relief / loss relief | ✓ | `group-loss-relief` — surrenders a current-period loss from a 75%-group company to a profitable member, relieving it at the claimant's marginal rate (26.5% in the marginal band vs a 19%/25% carry-forward), and carries forward any excess (CTA 2010 Part 5). Carry-back is a documented next step. | — |
| Patent Box | ✓ | `patent-box` — the 10% effective CT rate on patented-product profits vs the main rate; quantifies the saving (CTA 2010 Part 8A). IP-profit apportionment and the modified-nexus fraction flagged for the adviser. | — |
| Business Asset Disposal Relief | ✓ | `cgt-business-asset-disposal-relief` (10%/14%/18% by year) | — |
| Holding company structuring | ✓ | `holding-company-structuring` — intercompany dividends exempt (CTA 2009 Part 9A s.931A): quantifies the personal dividend tax deferred by retaining profits in the group vs extracting now (incl. PA-taper effects). Share-for-share setup, s.138 clearance and commercial purpose left to the adviser. | — |

## Partnerships & LLPs

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Partnership profit-share allocation | ✓ | `partnership-profit-allocation` — a partnership is tax-transparent; each partner is taxed on their share (income tax + Class 4 NIC) on top of their other income. Two-partner current-vs-proposed comparison **and an N-partner mode** (an explicit partner list, each taxed on their share); flagged **borderline** — the ratio must reflect genuine commercial contribution (ITTOIA 2005 s.850). | — |

## Property & landlords

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Landlord finance-cost restriction (s.24) | ✓ | `property-income-finance-cost` — mortgage interest relieved as a 20% tax reducer (lower of finance costs, rental profit, adjusted total income); quantifies the extra tax a higher/additional-rate landlord pays vs full deductibility, and carries forward unrelieved interest (ITTOIA 2005 ss.272A-274C). The headline driver for the incorporation question. | — |
| Incorporation of property portfolios | ✓ | `property-incorporation` — **the flagship (v2)**: compares personal s.24 tax against corporation tax, weighs the annual saving against the one-off land-tax-on-transfer (**SDLT/LBTT/LTT by nation**, additional-dwelling rate) and CGT (deferred under s.162), and reports the **break-even in years**; v2 adds a **profit-extraction** view (dividend tax on drawing profits out) and surfaces **ATED** via the guided intake (TCGA 1992 s.162). Remaining: a multi-year NPV of the extraction path and an explicit ATED charge table. Flagged borderline. | — |
| Furnished Holiday Lettings transitional planning | ✓ | `fhl-abolition-transition` — the FHL regime was abolished from 6 April 2025 (Finance Act 2025 Sch 5); quantifies the two annual hits a former FHL now faces (the s.24 finance-cost restriction it was exempt from, and the loss of capital allowances on new furnishings), plus the WDA still claimable on the pool carried forward at 5 April 2025. Drives the incorporate/sell/hold decision. | — |
| SDLT reliefs (multiple/mixed-use/uninhabitable) | ✓ | SDLT built with the additional-dwelling surcharge + FTB relief; **mixed-use built** — `sdlt-mixed-use-classification` (FA 2003 s.55(1B) Table B, borderline); **uninhabitable/derelict now built** — `sdlt-uninhabitable-classification` (FA 2003 s.116, the P N Bewley principle, borderline): a building not "suitable for use as a dwelling" charged at non-residential rates, quantified. (Multiple Dwellings Relief was abolished June 2024, so not modelled.) | — |
| Capital allowances on commercial property (fixtures) | ✓ | `commercial-property-fixtures` — integral features/fixtures within a commercial building relieved via AIA (100% to the limit) then the special-rate WDA; quantifies the first-year allowance and tax saved (CAA 2001 ss.33A/187A). Second-hand s.187A pooling/fixed-value conditions flagged. | — |

## Family & inheritance tax

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Lifetime gifting (annual/small-gift exemptions) | ✓ | `iht-lifetime-gifting-pets` | — |
| Potentially Exempt Transfers (7-year) | ✓ | Taper relief modelled in the gifting strategy | — |
| Trusts (assets out of estate, retain control) | ✓ | `relevant-property-trust-charges` — the relevant-property regime: 20% entry charge above the available NRB, the ten-year anniversary charge (up to 6% of the excess), and the proportionate exit charge (IHTA 1984 ss.58-69). **Same-day related settlements** now reduce the available band (the anti-Rysaffe multiple-trust rule). IIP/BMT variants remain documented next steps. | — |
| Nil-Rate Band / Residence NRB (transferable) | ✓ | `iht-spousal-transfer-and-nil-rate-bands` | — |
| Business Relief / Agricultural Relief (capped Apr 2026) | ✓ | `business-property-relief` — 100% relief on qualifying business/agricultural property with the **effective-dated April 2026 £1m combined cap** (100% within, 50% above; Finance Act 2025), quantifying the value relieved, the taxable value left and the IHT saved — and, run across the tax-year boundary, the extra IHT the reform costs (IHTA 1984 ss.103-124C). Asset-qualification judgement left to the accountant. | — |
| Life insurance in trust (covers the IHT bill) | ✓ | `life-policy-in-trust` — quantifies the IHT saved by writing the policy in trust (outside the estate) vs held personally (proceeds +40%), and the payout available for the bill (IHTA 1984 s.5). | — |
| Pension death-benefit planning (Apr 2027 into-estate change) | ✓ | `pension-death-benefit` — the extra IHT a pension pot attracts from 6 April 2027 (40% where the estate is above the NRB), so clients can plan ahead. **Borderline / forward-looking** — flagged pending Finance Bill 2025-26. | — |

## Charities

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Gift Aid | ✓ | `gift-aid-relief` (see Individuals). Charity reclaims 20%; higher-rate donor reclaims the difference. | — |
| Payroll Giving | ✓ | `payroll-giving` — pre-tax donation under an approved payroll deduction scheme (ITEPA 2003 Part 12): full marginal-rate relief with no grossing-up (60% effective in the PA taper); NIC still due; charity receives the whole amount. | — |
| Gifts of shares / property to charity (IT + CGT relief) | ✓ | `charity-gift-of-assets` — market value deducted from net income (ITA 2007 s.431) plus no-gain/no-loss on the disposal (TCGA 1992 s.257); quantifies both reliefs and the net cost. Qualifying-investment/land-certificate conditions left to the adviser. | — |
| Charitable legacies (10% rule, 40%→36%) | ✓ | `iht-charitable-legacy-reduced-rate` | — |
| VAT reliefs for charities | ○ | No VAT module exists yet — larger piece. | Low |

## Capital gains (all client types)

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Bed & ISA / Bed & SIPP | ✓ | Bed-and-ISA built (`isa-bed-and-isa`, see Individuals) — uses the annual CGT exemption on the transfer and shelters future dividends/growth. Bed-and-SIPP follows the same pattern (documented next step). | — |
| Spousal transfers (use both allowances/bands) | ✓ | `cgt-spousal-transfer-before-disposal` | — |
| Timing of disposals (split across tax years) | ✓ | `cgt-timing-of-disposals` — splits a divisible gain over two years to use two AEAs + two basic-rate bands; quantifies the saving. | — |
| Reinvestment reliefs (EIS deferral, rollover) | ✓ | EIS gain deferral and SEIS 50% reinvestment exemption inside `venture-capital-investment`; **business-asset rollover relief built** (`cgt-rollover-relief`, TCGA 1992 s.152/s.153): full or partial reinvestment, chargeable-now vs rolled-over split, tax deferred, and the replacement base-cost reduction. | — |

---

## Coverage tally

**24–25 July 2026:** nine more built — timing of income across years, Payroll
Giving, gifts of shares/property to charity, business-asset rollover relief,
**full expensing**, **holding-company structuring**, **SDLT mixed-use
classification**, **SDLT uninhabitable/derelict classification**, and the
**FHL abolition transitional** — taking the app to **51 live strategies**.
The only remaining menu item is **charity VAT reliefs**, which needs a VAT
module the app does not yet have (see the scoping note in DEVELOPER_HANDOVER
§6) — a deliberate, documented deferral rather than an oversight.

Previously: roughly **34 built, 2 partial, ~3 planned** of ~38 mainstream strategies (plus
new client-category strategies — partnership, trust — beyond the original ~38).
**Tier 2 complete** (incl. the flagship); **Tier 3 largely built** (7 Jul 2026):
R&D relief, Patent Box, commercial-property fixtures, EOT sale, pension
death-benefit (Apr 2027, borderline) and life-policy-in-trust. Remaining
specialist items: holding-company structuring, Payroll Giving, charity VAT.
(**Tier 1 complete, 6 Jul 2026**: Gift Aid, directors'-loan/s.455, timing of
disposals, capital allowances / AIA, salary sacrifice, and the standalone
personal + employer pension-contribution recommendations. **Tier 2 quick wins
complete**: group relief for company losses, bed-and-ISA, Business/Agricultural
Property Relief with the April 2026 £1m cap, and EIS/SEIS/VCT investment relief.
**Client-type expansion complete (7 Jul 2026)**: the landlord s.24 finance-cost
restriction, the partnership profit-share allocation, and the relevant-property
trust charges are built; richer entity labels (sole trader, partnership, trust,
estate) added; and the guided-intake engine surfaces the material assumptions as
questions to confirm. All four directions delivered.)
Built = the owner-manager extraction core, the main IHT reliefs, the main
CGT reliefs, and all three nations' land taxes. That is the hardest and
most-used third; the backlog is breadth, not the hard core.

## Recommended build order (value × frequency)

**Tier 1 — quick, high-frequency wins (build on the existing engine):**
~~Gift Aid~~ · ~~directors' loan / s.455~~ · ~~timing of disposals~~ ·
~~capital allowances / AIA~~ · ~~salary sacrifice~~ · ~~standalone personal
pension contribution~~ · ~~employer pension contribution~~ — **all done,
6 Jul 2026. Tier 1 is complete.** Next is Tier 2.

**Tier 2 — the flagship + common modules:** ~~group & loss relief~~ ·
~~ISA / Bed-and-ISA~~ · ~~Business Relief / Agricultural Relief~~ ·
~~EIS / SEIS / VCT + reinvestment reliefs~~ · ~~property incorporation (the
landlord flagship)~~ — **all done (flagship 7 Jul 2026); Tier 2 is complete.**

**Tier 3 — specialist / larger modules:** R&D · EOT · trusts · pension
death-benefit & life-insurance-in-trust · capital allowances on commercial
property · Patent Box · holding-company structuring · charity VAT reliefs.

**Cross-cutting:** the guided adaptive intake (`SCOPE_...` Workstream B) —
**engine built** (`advice/intake.py`): given a client's facts, `intake_gaps`
returns the material questions the engine would otherwise assume (marital
status/spouse income, property jurisdiction, landlord mortgage/s.24, BPR
qualification, pension taper, partnership commerciality, trust prior transfers),
each with why it matters and the assumption being made. Surfaced **both**
before generation (the review page at `/advice/generate/<fact_set>/review/` —
"Questions to confirm first", with Generate / Edit-facts options) **and** on the
advice page after generation, and exercised by the self-audit for every case.
**Guided intake is complete.**

Every item, whenever built, follows the six-part definition of done and
needs tax-editor sign-off before real-client use.
