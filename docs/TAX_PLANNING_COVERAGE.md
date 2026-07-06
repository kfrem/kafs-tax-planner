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

Last updated: 6 July 2026.

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
| Timing of income (shift between years) | ○ | The engine is multi-tax-year; needs a strategy that compares landing income in year A vs B. | Med |

## Companies / business owners

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Salary vs dividend mix | ✓ | `salary-dividend-mix` | — |
| Directors' loan account / s.455 (33.75% charge) | ✓ | `directors-loan-s455` — the charge on the balance outstanding after the 9-month window, and the amount avoided by repaying in time (CTA 2010 s.455). | — |
| Capital allowances / Annual Investment Allowance | ✓ | `capital-allowances-aia` — 100% AIA up to £1m, 18% WDA on the excess, tax saved at the marginal rate (CAA 2001 s.51A). Full expensing not yet added. | — |
| R&D tax relief | ○ | Valuable, specialist; the merged-scheme rules from April 2024. | Med |
| Employer pension contributions (CT relief, no NI) | ✓ | `employer-pension-contribution` — standalone recommendation: corporation-tax saving, employer NIC saved versus paying the same as salary, no relevant-earnings cap, net cost to the company (CTA 2009 s.54 wholly-and-exclusively test flagged for the reviewer). | — |
| Employee Ownership Trust (EOT) — CGT-free sale | ○ | Specialist, high value; note the Autumn 2024 tightening. | Med |
| Group relief / loss relief | ✓ | `group-loss-relief` — surrenders a current-period loss from a 75%-group company to a profitable member, relieving it at the claimant's marginal rate (26.5% in the marginal band vs a 19%/25% carry-forward), and carries forward any excess (CTA 2010 Part 5). Carry-back is a documented next step. | — |
| Patent Box | ○ | Niche (10% CT on patented-product profits). | Low |
| Business Asset Disposal Relief | ✓ | `cgt-business-asset-disposal-relief` (10%/14%/18% by year) | — |
| Holding company structuring | ○ | Structural/advisory; ring-fencing + tax-efficient exit. | Low–Med |

## Partnerships & LLPs

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Partnership profit-share allocation | ✓ | `partnership-profit-allocation` — a partnership is tax-transparent; each partner is taxed on their share (income tax + Class 4 NIC) on top of their other income. Compares the current split with a proposed one and quantifies the household tax difference; flagged **borderline** because the ratio must reflect genuine commercial contribution, not tax (ITTOIA 2005 s.850). | — |

## Property & landlords

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Landlord finance-cost restriction (s.24) | ✓ | `property-income-finance-cost` — mortgage interest relieved as a 20% tax reducer (lower of finance costs, rental profit, adjusted total income); quantifies the extra tax a higher/additional-rate landlord pays vs full deductibility, and carries forward unrelieved interest (ITTOIA 2005 ss.272A-274C). The headline driver for the incorporation question. | — |
| Incorporation of property portfolios | ○ | **Scoped as the flagship build** — see `SCOPE_landlord_planning_and_guided_intake.md` (Section 24, s.162, SDLT-on-transfer, ATED, break-even). The s.24 cost above is the break-even numerator. | High |
| Furnished Holiday Lettings transitional planning | ○ | FHL regime abolished from April 2025 — model the transitional position. | Low |
| SDLT reliefs (multiple/mixed-use/uninhabitable) | ◐ | SDLT built with the additional-dwelling surcharge + FTB relief. Missing: mixed-use rate, uninhabitable/derelict. (Multiple Dwellings Relief was abolished June 2024.) | Med |
| Capital allowances on commercial property (fixtures) | ○ | Fixtures/integral features within commercial buildings. | Med |

## Family & inheritance tax

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Lifetime gifting (annual/small-gift exemptions) | ✓ | `iht-lifetime-gifting-pets` | — |
| Potentially Exempt Transfers (7-year) | ✓ | Taper relief modelled in the gifting strategy | — |
| Trusts (assets out of estate, retain control) | ✓ | `relevant-property-trust-charges` — the relevant-property regime: 20% entry charge above the available NRB, the ten-year anniversary charge (up to 6% of the excess), and the proportionate exit charge, all quantified so a settlor can weigh a trust against outright gifts (IHTA 1984 ss.58-69). Multiple-trust/same-day-addition interactions and IIP/BMT variants are documented next steps. | — |
| Nil-Rate Band / Residence NRB (transferable) | ✓ | `iht-spousal-transfer-and-nil-rate-bands` | — |
| Business Relief / Agricultural Relief (capped Apr 2026) | ✓ | `business-property-relief` — 100% relief on qualifying business/agricultural property with the **effective-dated April 2026 £1m combined cap** (100% within, 50% above; Finance Act 2025), quantifying the value relieved, the taxable value left and the IHT saved — and, run across the tax-year boundary, the extra IHT the reform costs (IHTA 1984 ss.103-124C). Asset-qualification judgement left to the accountant. | — |
| Life insurance in trust (covers the IHT bill) | ○ | Advisory calc: policy in trust pays the bill without adding to the estate. | Med |
| Pension death-benefit planning (Apr 2027 into-estate change) | ○ | Topical; model pre/post April 2027 treatment. | Med |

## Charities

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Gift Aid | ✓ | `gift-aid-relief` (see Individuals). Charity reclaims 20%; higher-rate donor reclaims the difference. | — |
| Payroll Giving | ○ | Pre-tax donation from salary. | Low |
| Gifts of shares / property to charity (IT + CGT relief) | ○ | Relief on the gift's value. | Low–Med |
| Charitable legacies (10% rule, 40%→36%) | ✓ | `iht-charitable-legacy-reduced-rate` | — |
| VAT reliefs for charities | ○ | No VAT module exists yet — larger piece. | Low |

## Capital gains (all client types)

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Bed & ISA / Bed & SIPP | ✓ | Bed-and-ISA built (`isa-bed-and-isa`, see Individuals) — uses the annual CGT exemption on the transfer and shelters future dividends/growth. Bed-and-SIPP follows the same pattern (documented next step). | — |
| Spousal transfers (use both allowances/bands) | ✓ | `cgt-spousal-transfer-before-disposal` | — |
| Timing of disposals (split across tax years) | ✓ | `cgt-timing-of-disposals` — splits a divisible gain over two years to use two AEAs + two basic-rate bands; quantifies the saving. | — |
| Reinvestment reliefs (EIS deferral, rollover) | ◐ | EIS gain deferral and SEIS 50% reinvestment exemption are built inside `venture-capital-investment` (see Individuals). Business-asset rollover relief (TCGA 1992 s.152) is a documented next step. | Low |

---

## Coverage tally

Roughly **27 built, 2 partial, ~10 planned** of ~38 mainstream strategies (the
partnership allocation and relevant-property trust charges are new
client-category strategies beyond the original ~38)
(**Tier 1 complete, 6 Jul 2026**: Gift Aid, directors'-loan/s.455, timing of
disposals, capital allowances / AIA, salary sacrifice, and the standalone
personal + employer pension-contribution recommendations. **Tier 2 quick wins
complete**: group relief for company losses, bed-and-ISA, Business/Agricultural
Property Relief with the April 2026 £1m cap, and EIS/SEIS/VCT investment relief.
**Client-type expansion in progress**: the landlord s.24 finance-cost
restriction and the partnership profit-share allocation are built; richer
entity labels (sole trader, partnership, trust, estate) added. Trusts and the
guided adaptive intake are next.)
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
~~EIS / SEIS / VCT + reinvestment reliefs~~ (all quick wins done, 6 Jul 2026) ·
**property incorporation (the scoped landlord flagship) — the only Tier-2 item
left.** Small self-contained wins done first, flagship next.

**Tier 3 — specialist / larger modules:** R&D · EOT · trusts · pension
death-benefit & life-insurance-in-trust · capital allowances on commercial
property · Patent Box · holding-company structuring · charity VAT reliefs.

**Cross-cutting (do alongside Tier 1):** the guided adaptive intake
(`SCOPE_...` Workstream B) — it makes *every* strategy above safer by asking
the right follow-up questions and stating its assumptions.

Every item, whenever built, follows the six-part definition of done and
needs tax-editor sign-off before real-client use.
