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
