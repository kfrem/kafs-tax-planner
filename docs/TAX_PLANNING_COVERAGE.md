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
| Pension contributions (band extension, PA restoration in £100k–125k taper) | ◐ | Modelled inside `combined_personal_tax` (gross contribution extends bands; taper uses adjusted net income) and the pension relief calc. Needs a *standalone advice strategy* that recommends the contribution to restore the PA / capture 60% relief. | High |
| Marriage Allowance | ✓ | `marriage-allowance-transfer` | — |
| ISA maximisation | ○ | Needs an investments/ISA-allowance fact set; the "saving" is sheltering future growth (more advisory than a point calc). | Med |
| Salary sacrifice (pension / EV / childcare) | ✓ | `salary-sacrifice-into-pension` — swaps salary for an employer pension contribution; quantifies the employee's income tax + Class 1 NIC saving, the employer's secondary NIC saving, the amount into the pension gross and its net cost (SSCBA 1992 s.6). EV/childcare variants follow the same engine. | — |
| Gift Aid (extends basic-rate band) | ✓ | `gift-aid-relief` — basic-rate gross-up, higher-rate band relief + PA restoration in the taper (ITA 2007 s.414). | — |
| Dividend vs salary optimisation | ✓ | `salary-dividend-mix` | — |
| EIS / SEIS / VCT (IT relief + CGT defer/exempt) | ○ | Real module: income-tax relief calc + CGT deferral/exemption. Ties to reinvestment reliefs below. | Med |
| Timing of income (shift between years) | ○ | The engine is multi-tax-year; needs a strategy that compares landing income in year A vs B. | Med |

## Companies / business owners

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Salary vs dividend mix | ✓ | `salary-dividend-mix` | — |
| Directors' loan account / s.455 (33.75% charge) | ✓ | `directors-loan-s455` — the charge on the balance outstanding after the 9-month window, and the amount avoided by repaying in time (CTA 2010 s.455). | — |
| Capital allowances / Annual Investment Allowance | ✓ | `capital-allowances-aia` — 100% AIA up to £1m, 18% WDA on the excess, tax saved at the marginal rate (CAA 2001 s.51A). Full expensing not yet added. | — |
| R&D tax relief | ○ | Valuable, specialist; the merged-scheme rules from April 2024. | Med |
| Employer pension contributions (CT relief, no NI) | ◐ | The pension strategy already shows the employer-route CT saving; surface it as its own recommendation. | Med |
| Employee Ownership Trust (EOT) — CGT-free sale | ○ | Specialist, high value; note the Autumn 2024 tightening. | Med |
| Group relief / loss relief | ○ | Move losses between group companies / carry back/forward. | Med |
| Patent Box | ○ | Niche (10% CT on patented-product profits). | Low |
| Business Asset Disposal Relief | ✓ | `cgt-business-asset-disposal-relief` (10%/14%/18% by year) | — |
| Holding company structuring | ○ | Structural/advisory; ring-fencing + tax-efficient exit. | Low–Med |

## Property & landlords

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Incorporation of property portfolios | ○ | **Scoped as the flagship build** — see `SCOPE_landlord_planning_and_guided_intake.md` (Section 24, s.162, SDLT-on-transfer, ATED, break-even). | High |
| Furnished Holiday Lettings transitional planning | ○ | FHL regime abolished from April 2025 — model the transitional position. | Low |
| SDLT reliefs (multiple/mixed-use/uninhabitable) | ◐ | SDLT built with the additional-dwelling surcharge + FTB relief. Missing: mixed-use rate, uninhabitable/derelict. (Multiple Dwellings Relief was abolished June 2024.) | Med |
| Capital allowances on commercial property (fixtures) | ○ | Fixtures/integral features within commercial buildings. | Med |

## Family & inheritance tax

| Strategy | Status | Notes / what's needed | Priority |
|---|---|---|---|
| Lifetime gifting (annual/small-gift exemptions) | ✓ | `iht-lifetime-gifting-pets` | — |
| Potentially Exempt Transfers (7-year) | ✓ | Taper relief modelled in the gifting strategy | — |
| Trusts (assets out of estate, retain control) | ○ | Relevant-property regime (entry/10-year/exit charges). Big specialist build; Workstream A7 of the property scope. | Med |
| Nil-Rate Band / Residence NRB (transferable) | ✓ | `iht-spousal-transfer-and-nil-rate-bands` | — |
| Business Relief / Agricultural Relief (capped Apr 2026) | ○ | Currently a documented *simplification* (no BPR/APR). Common for business/farm owners; model the relief and the new £1m cap. | Med–High |
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
| Bed & ISA / Bed & SIPP | ○ | Uses the annual CGT exemption + shelters future growth; needs the ISA/SIPP fact set. | Med |
| Spousal transfers (use both allowances/bands) | ✓ | `cgt-spousal-transfer-before-disposal` | — |
| Timing of disposals (split across tax years) | ✓ | `cgt-timing-of-disposals` — splits a divisible gain over two years to use two AEAs + two basic-rate bands; quantifies the saving. | — |
| Reinvestment reliefs (EIS deferral, rollover) | ○ | Defers the gain into a new qualifying investment; pairs with EIS/SEIS above. | Med |

---

## Coverage tally

Roughly **17 built, 4 partial, ~17 planned** of ~38 mainstream strategies
(Tier-1 so far: Gift Aid, directors'-loan/s.455, timing of disposals,
capital allowances / AIA, salary sacrifice — 6 Jul 2026).
Built = the owner-manager extraction core, the main IHT reliefs, the main
CGT reliefs, and all three nations' land taxes. That is the hardest and
most-used third; the backlog is breadth, not the hard core.

## Recommended build order (value × frequency)

**Tier 1 — quick, high-frequency wins (build on the existing engine):**
~~Gift Aid~~ · ~~directors' loan / s.455~~ · ~~timing of disposals~~ ·
~~capital allowances / AIA~~ (done, 6 Jul 2026) · salary sacrifice · finish
the standalone pension-contribution and employer-pension strategies. Each is
a small, self-contained strategy that firms use constantly.

**Tier 2 — the flagship + common modules:** property incorporation (the
scoped landlord module) · Business Relief / Agricultural Relief · EIS / SEIS
/ VCT + reinvestment reliefs · ISA / Bed-and-ISA · group & loss relief.

**Tier 3 — specialist / larger modules:** R&D · EOT · trusts · pension
death-benefit & life-insurance-in-trust · capital allowances on commercial
property · Patent Box · holding-company structuring · charity VAT reliefs.

**Cross-cutting (do alongside Tier 1):** the guided adaptive intake
(`SCOPE_...` Workstream B) — it makes *every* strategy above safer by asking
the right follow-up questions and stating its assumptions.

Every item, whenever built, follows the six-part definition of done and
needs tax-editor sign-off before real-client use.
