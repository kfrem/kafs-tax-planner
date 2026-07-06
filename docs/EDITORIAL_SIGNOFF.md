# Editorial sign-off record

## Review of 5 July 2026 — full rule base (2025/26)

**Reviewing professional:** kfrem (chartered accountant; system account
`kfrem`, recorded as reviewer on rule-base releases 2024.1, 2025.1,
2025.2, 2025.3).

**Scope:** all 53 items of `RULE_BASE_REVIEW_PACK.md` as generated
5 July 2026 — 18 current-year parameters, 10 strategies, 25 authorities —
plus prior-turn verification of the IHTA 1984 citations and
*Jones v Garnett* [2007] UKHL 35. Machine pre-check: 0 failures at time
of review. Reviewer verified statutory references independently against
legislation.gov.uk and HMRC manuals (Sch 1A cross-checked to IHTM45001).

**Verdict:** YES on all 53 items. No fabricated or wrong citations
found. Three editorial corrections required and applied the same day:

| # | Finding | Correction applied |
|---|---|---|
| 1 | Spousal nil-rate-band strategy cited s.8A (ordinary NRB transfer) but not **IHTA 1984 s.8G** (RNRB transfer), leaving the combined-bands claim half-supported | s.8G added to the authority registry, cited on the strategy, and placed under watch |
| 2 | Marriage Allowance cited as ss.55B-55E, omitting the **s.55A** overview provision | Citation corrected to ITA 2007 ss.55A-55E; canonical URI repointed to s.55A |
| 3 | **TCGA 1992 s.58** described pre-F(No.2)A 2023: since 6 April 2023 no-gain/no-loss extends to separated couples (to end of third tax year after separation; unlimited under formal divorce agreement/court order) | Authority extract and strategy explanation rewritten to the current law; deeper modelling of the separation window noted as future work |

**Forward-dated changes noted by the reviewer** for future rule-base
releases (to be seeded with appropriate effective dates and re-reviewed):
- Dividend tax rate changes announced for April 2026
- BADR rate change (to 18%) from April 2026
- Savings/property income measures from April 2027
- Unused pensions brought into the IHT estate from April 2027

These are logged as monitoring targets; none affects 2025/26
computations.

**Standing arrangement:** future rule-base releases require the same
pack-based review before their status is set to released. The
`generate_review_pack` command regenerates the pack; the editorial
pre-check (`ruleengine/editorial.py`) runs in the test suite, so an
unwired rule cannot reach a reviewable state.

## Addendum, 5 July 2026 — Business Asset Disposal Relief (CGT depth)

**Reviewing professional:** kfrem.

**Scope:** the new BADR content added to the property-taxes module —
parameter `cgt.business_asset_disposal_relief` (pack item 17), strategy
`cgt-business-asset-disposal-relief` (item 27), and authority TCGA 1992
ss.169H-169S (item 55). Machine pre-check: 0 failures across 19
parameters, 11 strategies, 27 authorities; the new authority's primary
source was fetched by the watcher (legislation.gov.uk s.169H).

**Figures verified independently against HMRC guidance:**
- Reduced rate **14%** for disposals on or after 6 April 2025 (10% before;
  18% from 6 April 2026) — HMRC CG64174 and helpsheet HS275 (2025/26),
  statutory basis TCGA 1992 s.169N.
- **£1,000,000** lifetime limit on qualifying gains — HS275, s.169N.
- Excess over the lifetime limit charged at the normal CGT rate — HS275.

**Verdict:** YES. The rate and limit are correct for 2025/26 and are held
as data (a new row, effective 6 April 2025), so the April 2026 move to
18% is a future row, not a code change. Modelling simplifications
(qualifying gains above the £1m limit charged at the standard higher
rate; AEA set against the relieved gain; qualifying conditions assumed
met) are documented at the calculator and are conservative — see
`ruleengine/calculators.py` and DEVELOPER_HANDOVER §5.

**Noted for a future release:** the 18% BADR rate from 6 April 2026 (to be
seeded as an intra-year/next-year row with its effective date and
re-reviewed) — already on the monitoring watch-list above.

## Addendum, 5 July 2026 — Devolved land taxes: Scottish LBTT & Welsh LTT

**Reviewing professional:** kfrem.

**Scope:** the devolved land-transaction-tax variants added to the
property-taxes module — parameters `lbtt.residential_bands` (pack item 19)
and `ltt.residential_bands` (item 20), strategies
`lbtt-purchase-planning` (item 32) and `ltt-purchase-planning` (item 33),
and authorities LBTT(S)A 2013 s.24 and LTTA 2017 s.24. Machine pre-check:
0 failures across 21 parameters, 13 strategies, 29 authorities; both new
authorities' primary sources were fetched by the watcher
(legislation.gov.uk asp/2013/11 s.24 and anaw/2017/1 s.24).

**Figures verified independently against the devolved tax authorities:**
- **LBTT (Scotland)** residential bands 0% to £145k, 2% to £250k, 5% to
  £325k, 10% to £750k, 12% above; first-time buyer relief raises the
  nil-rate band to £175,000 (worth up to £600); Additional Dwelling
  Supplement **8%** on the whole price (up from 6% for contracts after
  4 December 2024) — revenue.scot residential-property guidance.
- **LTT (Wales)** main residential bands 0% to £225k, 6% to £400k, 7.5% to
  £750k, 10% to £1.5m, 12% above; **separate higher-rate table** for
  additional dwellings (5% / 8.5% / 10% / 12.5% / 15% / 17%, from
  11 December 2024) — not a flat surcharge; **no first-time buyer relief**
  in Wales — gov.wales LTT rates and bands.

**Verdict:** YES. The bands are correct for 2025/26 and are held as data
(new rows effective 6 April 2025), and the SDLT strategy is now gated to
England/NI so a Scottish or Welsh purchase routes to the correct devolved
charge (a property with no jurisdiction recorded still defaults to
England, unchanged). Both devolved statutes delegate rate-setting to
secondary legislation, so the data-not-code design mirrors the law.

## Addendum, 5 July 2026 — Lettings relief (CGT, shared occupancy)

**Reviewing professional:** kfrem.

**Scope:** parameter `cgt.lettings_relief` (pack item 18), strategy
`cgt-lettings-relief` (item 31), and authority TCGA 1992 s.223B (item 62).
Machine pre-check: 0 failures across 22 parameters, 14 strategies, 30
authorities; the new authority's primary source was fetched by the
watcher (legislation.gov.uk s.223B).

**Rules verified against HMRC HS283 and TCGA 1992 s.223B:**
- The relief equals the **lowest of** the gain attributable to the
  letting, the private residence relief due on the disposal, and
  **£40,000**.
- From **6 April 2020** the relief applies **only to periods of shared
  occupancy** with the tenant — the former relief for letting a property
  after moving out was withdrawn.
- Reconciled to the HS283 worked example (60% let / 40% owner-occupied,
  £60,000 gain → £24,000 PPR, £24,000 lettings relief, £12,000
  chargeable), which is the golden case.

**Verdict:** YES. The £40,000 cap is held as data; the calculator applies
the statutory lowest-of-three and is gated on a shared-occupancy let
fraction, so it cannot fire on a buy-to-let never lived in (e.g. the
Victor persona). Documented simplification: a space-based part-let
occupied throughout ownership; time-apportioned mixed occupation is not
composed in (DEVELOPER_HANDOVER §5).

## Addendum, 5 July 2026 — Non-residential (commercial) land taxes

**Reviewing professional:** kfrem.

**Scope:** commercial freehold coverage across all three UK regimes —
parameters `sdlt.non_residential_bands`, `lbtt.non_residential_bands`,
`ltt.non_residential_bands`, and strategies
`{sdlt,lbtt,ltt}-non-residential-purchase`, each citing the same
enabling statute as its residential counterpart (FA 2003 s.55, LBTT(S)A
2013 s.24, LTTA 2017 s.24 — no new authorities). Machine pre-check: 0
failures across 25 parameters, 17 strategies, 30 authorities.

**Freehold bands verified against the tax authorities:**
- **SDLT (England/NI):** 0% to £150k, 2% to £250k, 5% above — gov.uk
  non-residential rates.
- **LBTT (Scotland):** 0% to £150k, **1%** to £250k, 5% above — the 1%
  middle band undercuts England's 2% — revenue.scot non-residential.
- **LTT (Wales):** 0% to £225k, 1% to £250k, 5% to £1m, **6%** above —
  gov.wales non-residential.
- Cross-checked on a £500,000 freehold: SDLT £14,500, LBTT £13,500, LTT
  £12,750 (the three golden cases).

**Verdict:** YES. Bands are correct for 2025/26 and held as data; the
residential purchase strategies are now gated on `property.property_type`
so a commercial purchase (type `non_residential`) routes to the correct
regime while an unset type still defaults to residential. Scope:
freehold consideration only — leases (charged on rent NPV) and the
mixed-use apportionment rules are not modelled (DEVELOPER_HANDOVER §5).

## Addendum, 5 July 2026 — 2026/27 release scaffolding (BADR 18%)

**Reviewing professional:** kfrem.

**Scope:** the first future-tax-year release, `2026.1` (effective
6 April 2026), and the Business Asset Disposal Relief rate row it carries.
BADR is now two non-overlapping effective-dated rows: 14% for
[2025-04-06, 2026-04-06) under 2025.3, and **18%** for [2026-04-06, open)
under 2026.1. Machine pre-check: 0 failures across 26 parameters, 17
strategies, 30 authorities; the editorial pre-check now reviews both the
2025/26 and 2026/27 anchors, so the future row appears in this pack with
its effective range.

**Verified against HMRC and the legislation:**
- BADR rate **18%** for disposals on or after 6 April 2026 (14% for
  6 April 2025 to 5 April 2026; 10% before) — HMRC CG64174 / HS275,
  Finance Act 2025 amending TCGA 1992 s.169N. The £1,000,000 lifetime
  limit is unchanged.
- Reconciled: a £500,000 higher-rate disposal gives £69,580 CGT in
  2025/26 (14%) and £89,460 in 2026/27 (18%) — the two BADR golden cases.

**Governance verified:** while release 2026.1 is DRAFT (its real state
until a second reviewer approves it), the engine returns NO BADR figure
for 2026/27 and refuses rather than reusing the 2025/26 rate — pinned by
`test_property.py::TestFutureYearBadr::test_unapproved_2026_release_is_invisible_to_the_engine`.
So this YES records approval of the *content*; setting 2026.1 to Released
in Admin remains the separate four-eyes act.

**Verdict:** YES on the 18% row. Scaffolding note: only BADR has a
distinct 2026/27 row; all other parameters carry forward on their open
2025/26 ranges and must be closed with a confirmed 2026/27 figure (and
re-reviewed) before that year's advice relies on them.

## Addendum, 6 July 2026 — 2024/25 intra-year CGT (30 October 2024)

**Reviewing professional:** kfrem.

**Scope:** prior-year 2024/25 CGT under release `2024.2`, modelling the
30 October 2024 mid-year rate change with two intra-year effective ranges
of `cgt.rates` plus the 2024/25 `cgt.annual_exempt_amount`. These are
prior-year rows (before the 2025/26 review anchor) so they do not appear
in the forward-looking pack; they are validated by golden cases and
hand-computed tests instead.

**Verified against HMRC guidance:**
- Non-residential / other-asset CGT rose from **10%/20%** to **18%/24%**
  for disposals **on or after 30 October 2024** (Autumn Budget 2024);
  disposals before that date keep 10%/20%.
- Residential rates were **18%/24% throughout 2024/25** (unchanged by the
  30 October change), so a residential disposal is taxed the same either
  side of the boundary — pinned by a test.
- Reconciled: a £20,000 other-asset gain (£17,000 after AEA, within the
  basic band) is £1,700 before 30 Oct and £3,060 on/after — the two
  2024/25 golden cases.

**Engine change reviewed:** `get_parameter` gained an optional `as_of`
disposal date. It resolves the intra-year row by that date, rejects a date
outside the stated tax year (a mismatched fact is an error, not a wrong
answer), and remains deterministic (the date is a fact, not a wall clock).
When omitted it uses the 6 April anchor, so every existing year-boundary
parameter is unchanged.

**Verdict:** YES. Rates and the intra-year boundary are correct for
2024/25 and held as data; the effective-dating model now spans intra-year,
year-boundary, and future-year changes.

## Addendum, 6 July 2026 — Land-tax leases (rent NPV)

**Reviewing professional:** kfrem.

**Scope:** the grant of a lease charged on the net present value of rent,
for all three regimes — parameters `sdlt.lease_npv_bands`,
`lbtt.lease_npv_bands`, `ltt.lease_npv_bands` and strategies
`{sdlt,lbtt,ltt}-lease-npv`, each citing the same charging statute as its
freehold counterpart. Machine pre-check: 0 failures across 29 parameters,
20 strategies, 30 authorities.

**Method and bands verified against the tax authorities:**
- NPV = sum of rent / 1.035^i over the term, at the statutory **3.5%**
  temporal discount rate (FA 2003 Sch 5 / LBTT(S)A Sch 19 / LTTA).
- **SDLT (Eng/NI):** 0% to £150k NPV, 1% to £5m, 2% above — HMRC SDLTM.
- **LBTT (Scot):** 0% to £150k, 1% to £2m, 2% above — revenue.scot
  LBTT6013.
- **LTT (Wales):** 0% to £225k, 1% to £2m, 2% above — gov.wales.
- Reconciled: £50,000 rent over 10 years gives NPV £415,830.27, so SDLT
  and LBTT are £2,658.30 and the Welsh LTT £1,908.30 (higher nil band); a
  £250,000 rent over 10 years (NPV £2,079,151.33) exercises the LBTT 2%
  band at £20,083.03 — the three lease golden cases.

**Verdict:** YES. Bands and the 3.5% discount are correct and held as
data. Documented scope (DEVELOPER_HANDOVER §5): a constant annual rent
over a whole number of years; stepped/uncertain rent, the five-year
highest-rent rule, any lease premium (charged separately at the freehold
rates), Scotland's 3-yearly LBTT lease reviews, and residential leases
are not modelled.

## Addendum, 6 July 2026 — CGT whole-income composition

**Reviewing professional:** kfrem.

**Scope:** a computation change (no new rates). `cgt_liability` now treats
the gain as the top slice (TCGA 1992 s.1I): the basic-rate band available
for the gain is reduced by the client's earned income AND dividends, and
extended by a gross relief-at-source pension contribution. Threaded
through all four CGT strategies (PPR, spousal transfer, BADR, lettings)
and their adapters, which now supply the client's dividends.

**Correctness confirmed:**
- With no dividends and no pension the result is byte-identical to the
  prior earned-only behaviour (regression test), so existing golden cases
  and persona numbers are unchanged (the personas take no dividends where
  they have a disposal).
- Reconciled: earned £30,000 + dividends £20,000 leave only £270 of the
  basic-rate band, so a £17,000 residential gain is £4,063.80 (270 @ 18% +
  16,730 @ 24%) — versus £3,060 if dividends were ignored. A £10,000 gross
  pension contribution extends the band and saves £600 of CGT (6% on the
  £10,000 shifted from 24% to 18%). These are the composition golden case
  and tests.

**Verdict:** YES. This corrects a prior understatement of CGT for
owner-managers who take dividends. Documented follow-on: composing the
gain with the *recommended* (optimiser) extraction, not just the recorded
dividends, remains future work (as for the incorporation comparison).

## Addendum, 6 July 2026 — 2026/27 fill-out (dividend rates + carry-forward)

**Reviewing professional:** kfrem.

**Scope:** completing the 2026/27 position now that the release scaffolding
exists. A confirmed rate change was found and added; the remaining modelled
parameters are frozen and carry forward.

**Confirmed 2026/27 change (added, under release 2026.1):**
- **Dividend tax rates rise 2 percentage points from 6 April 2026**
  (Budget 2025): ordinary **8.75% → 10.75%**, upper **33.75% → 35.75%**;
  the additional rate (39.35%), the band thresholds and the £500 allowance
  are unchanged. Held as a new effective-dated `dividend_tax.bands` row
  (the 2025/26 row is closed at 6 April 2026). Verified against the HMRC
  technical note "Change to tax rates for property, savings and dividend
  income". Reconciled: 30,000 other income + 20,000 dividends gives
  £4,781.25 in 2025/26 and £5,171.25 in 2026/27 — the two dividend golden
  cases. (Property/savings income rate changes are 6 April 2027 and are not
  modelled — the tool does not separate savings income.)

**Verified as frozen for 2026/27 (carry forward on open rows, no new row):**
personal allowance £12,570, income tax bands (£37,700 / £125,140), the
£500 dividend allowance, CGT annual exempt amount £3,000, IHT nil-rate band
£325,000, and corporation tax 25%/19% — pinned by
`test_calculators.py::TestFutureYear2026::test_frozen_parameters_carry_forward_to_2026_27`,
so a future edit cannot silently break the carry-forward.

**Verdict:** YES. With BADR 18% and the dividend rise, the 2026/27 modelled
parameter set is complete against currently-confirmed law; further changes
(e.g. a future Budget) are tracked on the monitoring watch-list and become
new effective-dated rows when legislated.

## Addendum, 6 July 2026 — Gift Aid higher-rate relief (Tier-1 build 1/…)

**Reviewing professional:** kfrem.

**Scope:** first Tier-1 strategy from `TAX_PLANNING_COVERAGE.md` — strategy
`gift-aid-relief` and authority ITA 2007 s.414. No new rate parameter (Gift
Aid uses the existing basic rate). `combined_personal_tax` was generalised
to accept a Gift Aid gross alongside the pension gross — mechanically
identical (both extend the band and reduce adjusted net income) and
backward-compatible (all 218 prior tests unchanged).

**Verified against ITA 2007 s.414:**
- The net donation is grossed up at the **basic rate** (£800 → £1,000); the
  charity reclaims the 20%.
- The grossed-up amount **extends the basic-rate limit**, so a higher-rate
  donor gets relief of the rate difference — £200 on a £1,000 gross gift
  (the golden case).
- The grossed-up amount **reduces adjusted net income**, so in the
  £100,000–125,140 taper it restores the personal allowance — a £10,000
  gross gift by a £110,000 earner restores £5,000 of PA and is worth £4,000
  (40% effective). A basic-rate donor correctly gets no *extra* personal
  relief. Both pinned by hand-computed tests.

**Verdict:** YES. Correct and defensible; the composition with the existing
band/taper engine is exact.

## Addendum, 6 July 2026 — Directors' loan s.455 (Tier-1 build 2/…)

**Reviewing professional:** kfrem.

**Scope:** strategy `directors-loan-s455`, new parameter
`directors_loan.s455` (rate 0.3375, beneficial-loan threshold 10,000),
authority CTA 2010 s.455.

**Verified against CTA 2010 s.455 / s.458:**
- A close company that lends to a participator pays a temporary charge of
  **33.75%** on the amount still outstanding **9 months and 1 day** after
  the accounting-period end; it is refunded (s.458) when the loan is repaid.
- Reconciled: £50,000 overdrawn with £20,000 repaid in time leaves £30,000
  at 33.75% = £10,125; repaying in full avoids the whole charge (the golden
  case and hand-computed tests pin all three branches). A beneficial-loan
  benefit-in-kind above £10,000 is flagged (not quantified).

**Verdict:** YES. Rate and mechanism correct; the 33.75% is held as data so
a future alignment change is a new row, not a code change.

## Addendum, 6 July 2026 — Timing of disposals (Tier-1 build 3/…)

**Reviewing professional:** kfrem.

**Scope:** strategy `cgt-timing-of-disposals` (no new parameter or
authority — reuses the CGT rates/AEA and TCGA 1992 ss.1H-1K).

**Verified:** splitting a *divisible* holding (shares/units) across two tax
years uses two annual exempt amounts and two basic-rate bands. Reconciled:
a £15,000 gain (higher-rate boundary) is £2,400 in one year but £1,620 split
(saving £780 = the second AEA at 18% plus £4,000 kept out of the 24% band);
a £5,000 gain split falls entirely within two £3,000 exemptions, cutting
£360 to nil. Gated on `personal.divisible_capital_gain` so it correctly does
**not** fire on a single indivisible property (Victor persona unaffected).

**Documented assumption:** the second year is modelled at the same rates and
income position — a reasonable planning estimate, flagged at the calculator.

**Verdict:** YES.

## Addendum, 6 July 2026 — Capital allowances / AIA (Tier-1 build 4/…)

**Reviewing professional:** kfrem.

**Scope:** strategy `capital-allowances-aia`, parameter
`capital_allowances.aia` (AIA limit £1,000,000; main-pool WDA 18%; special
rate 6%), authority CAA 2001 s.51A.

**Verified against CAA 2001:** 100% Annual Investment Allowance on qualifying
plant and machinery up to the AIA limit; expenditure above it is written down
at 18% in the main pool. Reconciled: £50,000 spend is fully within the AIA
(£12,500 saved at the 25% CT main rate); £1,200,000 spend gives £1,000,000
AIA + £36,000 WDA on the £200,000 excess = £1,036,000 first-year allowance,
saving £259,000. Marginal rate defaults to the CT main rate when not given.

**Documented simplification:** full expensing (unlimited 100% FYA on new
main-rate P&M for companies, from April 2023) and the special-rate/first-year
allowances are not yet modelled — only AIA + main-pool WDA. Flagged in the
coverage map.

**Verdict:** YES for the modelled AIA + WDA scope; full expensing is a
documented next step.
