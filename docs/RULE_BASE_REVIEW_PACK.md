# Rule-base review pack — editorial sign-off

Generated 07 July 2026. Machine pre-check: **0 failed checks** across 39 parameters, 41 strategies, 46 authorities.

**How to approve:** read each numbered item; the primary source is one
click away. Reply YES to approve all items, or list the item numbers you
question. Your approval is recorded as the §5.6 editorial review on every
rule-base release, with your name and the date.

---
## A. Tax parameters (the rates and thresholds the engine uses)

### 1. Capital allowances: AIA limit and writing-down rates  
`capital_allowances.aia` — corporation_tax — release 2025.1 — effective 2025-04-06 to open
- aia_limit: **1,000,000**
- main_pool_wda: **0.18**
- special_rate_wda: **0.06**
- PASS — consumed by a registered calculator (strategy.capital_allowances, strategy.commercial_property_fixtures)
- PASS — figure exercised by golden test cases (strategy.capital_allowances, strategy.commercial_property_fixtures)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 1,000,000 appears in: Capital Allowances Act 2001 s.51A; Corporation Tax Act 2010 Part 8A (Patent Box)

### 2. Corporation tax rates and marginal relief  
`corporation_tax.rates` — corporation_tax — release 2025.1 — effective 2025-04-06 to open
- main_rate: **0.25**
- main_rate_limit: **250,000**
- small_profits_rate: **0.19**
- small_profits_limit: **50,000**
- marginal_relief_fraction: **0.015**
- PASS — consumed by a registered calculator (corporation_tax, strategy.capital_allowances, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.employer_pension_contribution, strategy.group_loss_relief, strategy.property_incorporation, strategy.rd_tax_relief, strategy.patent_box, strategy.commercial_property_fixtures, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (corporation_tax, strategy.capital_allowances, strategy.pension_annual_allowance_carry_forward, strategy.employer_pension_contribution, strategy.group_loss_relief, strategy.property_incorporation, strategy.rd_tax_relief, strategy.patent_box, strategy.commercial_property_fixtures, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 50,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Corporation Tax Act 2010 Part 8A (Patent Box); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings)
- Source cross-reference: 250,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)

### 3. Directors' loan s.455 charge rate  
`directors_loan.s455` — corporation_tax — release 2025.1 — effective 2025-04-06 to open
- rate: **0.3375**
- beneficial_loan_threshold: **10,000**
- PASS — consumed by a registered calculator (strategy.directors_loan_s455)
- PASS — figure exercised by golden test cases (strategy.directors_loan_s455)
- PASS — belongs to a released rule-base version (2025.1)

### 4. Employer (secondary) Class 1 NIC  
`national_insurance.employer_class1` — corporation_tax — release 2025.1 — effective 2025-04-06 to open
- rate: **0.15**
- secondary_threshold: **5,000**
- PASS — consumed by a registered calculator (employer_class1_nic, strategy.salary_sacrifice, strategy.salary_dividend_mix, strategy.employer_pension_contribution, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (employer_class1_nic, strategy.salary_sacrifice, strategy.employer_pension_contribution, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 5,000 appears in: Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 Sch 5 (amount of tax chargeable: rent); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)

### 5. Employment Allowance  
`national_insurance.employment_allowance` — corporation_tax — release 2025.1 — effective 2025-04-06 to open
- amount: **10,500**
- PASS — consumed by a registered calculator (employer_class1_nic, strategy.salary_dividend_mix, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (employer_class1_nic, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)

### 6. Patent Box effective corporation-tax rate  
`patent_box.rate` — corporation_tax — release 2025.1 — effective 2025-04-06 to open
- rate: **0.1**
- PASS — consumed by a registered calculator (strategy.patent_box)
- PASS — figure exercised by golden test cases (strategy.patent_box)
- PASS — belongs to a released rule-base version (2025.1)

### 7. R&D merged-scheme (RDEC) above-the-line credit rate  
`rd.merged_scheme` — corporation_tax — release 2025.1 — effective 2025-04-06 to open
- rdec_rate: **0.2**
- rd_intensive_threshold: **0.3**
- rd_intensive_credit_rate: **0.145**
- PASS — consumed by a registered calculator (strategy.rd_tax_relief)
- PASS — figure exercised by golden test cases (strategy.rd_tax_relief)
- PASS — belongs to a released rule-base version (2025.1)

### 8. IHT Business/Agricultural Property Relief: 100% rate and combined cap  
`iht.business_property_relief` — inheritance_tax — release 2025.2 — effective 2024-04-06 to 2026-04-06
- rate_above_cap: **1.0**
- full_relief_cap: **None**
- PASS — consumed by a registered calculator (strategy.business_property_relief)
- PASS — figure exercised by golden test cases (strategy.business_property_relief)
- PASS — belongs to a released rule-base version (2025.2)

### 9. IHT Business/Agricultural Property Relief: 100% rate and combined cap  
`iht.business_property_relief` — inheritance_tax — release 2026.1 — effective 2026-04-06 to open
- rate_above_cap: **0.5**
- full_relief_cap: **1,000,000**
- PASS — consumed by a registered calculator (strategy.business_property_relief)
- PASS — figure exercised by golden test cases (strategy.business_property_relief)
- PASS — belongs to a released rule-base version (2026.1)
- Source cross-reference: 1,000,000 appears in: Capital Allowances Act 2001 s.51A; Corporation Tax Act 2010 Part 8A (Patent Box)

### 10. IHT gift exemptions and PET taper relief  
`iht.gift_exemptions` — inheritance_tax — release 2025.2 — effective 2025-04-06 to open
- taper_relief:
  - tax_reduction: **0.2**
  - years_survived_to: **4**
  - years_survived_from: **3**
  - tax_reduction: **0.4**
  - years_survived_to: **5**
  - years_survived_from: **4**
  - tax_reduction: **0.6**
  - years_survived_to: **6**
  - years_survived_from: **5**
  - tax_reduction: **0.8**
  - years_survived_to: **7**
  - years_survived_from: **6**
- annual_exemption: **3,000**
- small_gift_exemption: **250**
- PASS — consumed by a registered calculator (strategy.iht_lifetime_gifting)
- PASS — figure exercised by golden test cases (strategy.iht_lifetime_gifting)
- PASS — belongs to a released rule-base version (2025.2)
- Source cross-reference: 250 appears in: Corporation Tax Act 2009 Part 13 (as amended, merged R&D scheme); Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings)
- Source cross-reference: 3,000 appears in: Corporation Tax Act 2010 Part 8A (Patent Box); Income Tax Act 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT); Inheritance Tax Act 1984 s.19

### 11. IHT nil-rate band (frozen through 2029/30)  
`iht.nil_rate_band` — inheritance_tax — release 2025.2 — effective 2025-04-06 to open
- amount: **325,000**
- PASS — consumed by a registered calculator (strategy.relevant_property_trust_charges, strategy.pension_death_benefit, iht_estate_liability, strategy.iht_spousal_transfer_nil_rate_bands, strategy.iht_lifetime_gifting, strategy.iht_charitable_legacy_reduced_rate)
- PASS — figure exercised by golden test cases (strategy.relevant_property_trust_charges, strategy.pension_death_benefit, iht_estate_liability, strategy.iht_lifetime_gifting)
- PASS — belongs to a released rule-base version (2025.2)

### 12. IHT rates: death, reduced charitable, lifetime CLT  
`iht.rates` — inheritance_tax — release 2025.2 — effective 2025-04-06 to open
- death_rate: **0.4**
- lifetime_clt_rate: **0.2**
- reduced_charity_rate: **0.36**
- charity_baseline_fraction: **0.1**
- PASS — consumed by a registered calculator (strategy.business_property_relief, strategy.relevant_property_trust_charges, strategy.pension_death_benefit, strategy.life_policy_in_trust, iht_estate_liability, strategy.iht_spousal_transfer_nil_rate_bands, strategy.iht_lifetime_gifting, strategy.iht_charitable_legacy_reduced_rate)
- PASS — figure exercised by golden test cases (strategy.business_property_relief, strategy.relevant_property_trust_charges, strategy.pension_death_benefit, strategy.life_policy_in_trust, iht_estate_liability, strategy.iht_lifetime_gifting)
- PASS — belongs to a released rule-base version (2025.2)

### 13. IHT residence nil-rate band and taper  
`iht.residence_nil_rate_band` — inheritance_tax — release 2025.2 — effective 2025-04-06 to open
- amount: **175,000**
- taper_rate: **0.5**
- taper_threshold: **2,000,000**
- PASS — consumed by a registered calculator (iht_estate_liability, strategy.iht_spousal_transfer_nil_rate_bands, strategy.iht_lifetime_gifting, strategy.iht_charitable_legacy_reduced_rate)
- PASS — figure exercised by golden test cases (iht_estate_liability, strategy.iht_lifetime_gifting)
- PASS — belongs to a released rule-base version (2025.2)
- Source cross-reference: 175,000 appears in: Inheritance Tax Act 1984 s.8D
- Source cross-reference: 2,000,000 appears in: Corporation Tax Act 2010 Part 8A (Patent Box); Inheritance Tax Act 1984 s.8D; Inheritance Tax Act 1984 s.8G

### 14. Dividend allowance  
`dividend_tax.allowance` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- amount: **500**
- PASS — consumed by a registered calculator (dividend_tax, combined_personal_tax, strategy.gift_aid_relief, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_ppr_relief, strategy.cgt_lettings_relief, strategy.cgt_spousal_transfer_before_disposal, strategy.cgt_business_asset_disposal_relief)
- PASS — figure exercised by golden test cases (dividend_tax, combined_personal_tax, strategy.gift_aid_relief, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_lettings_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 500 appears in: Corporation Tax Act 2009 Part 13 (as amended, merged R&D scheme); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 Sch 6ZA

### 15. Dividend tax bands  
`dividend_tax.bands` — personal_income_tax — release 2025.1 — effective 2025-04-06 to 2026-04-06
- bands:
  - rate: **0.0875**
  - upper: **37,700**
  - rate: **0.3375**
  - upper: **125,140**
  - rate: **0.3935**
  - upper: **None**
- PASS — consumed by a registered calculator (dividend_tax, combined_personal_tax, strategy.gift_aid_relief, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.isa_bed_and_isa, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_ppr_relief, strategy.cgt_lettings_relief, strategy.cgt_spousal_transfer_before_disposal, strategy.cgt_business_asset_disposal_relief)
- PASS — figure exercised by golden test cases (dividend_tax, combined_personal_tax, strategy.gift_aid_relief, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.isa_bed_and_isa, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_lettings_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — belongs to a released rule-base version (2025.1)

### 16. Dividend tax bands  
`dividend_tax.bands` — personal_income_tax — release 2026.1 — effective 2026-04-06 to open
- bands:
  - rate: **0.1075**
  - upper: **37,700**
  - rate: **0.3575**
  - upper: **125,140**
  - rate: **0.3935**
  - upper: **None**
- PASS — consumed by a registered calculator (dividend_tax, combined_personal_tax, strategy.gift_aid_relief, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.isa_bed_and_isa, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_ppr_relief, strategy.cgt_lettings_relief, strategy.cgt_spousal_transfer_before_disposal, strategy.cgt_business_asset_disposal_relief)
- PASS — figure exercised by golden test cases (dividend_tax, combined_personal_tax, strategy.gift_aid_relief, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.isa_bed_and_isa, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_lettings_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — belongs to a released rule-base version (2026.1)

### 17. Income tax bands (non-savings, non-dividend)  
`income_tax.bands` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- bands:
  - rate: **0.2**
  - upper: **37,700**
  - rate: **0.4**
  - upper: **125,140**
  - rate: **0.45**
  - upper: **None**
- PASS — consumed by a registered calculator (income_tax_on_earned_income, combined_personal_tax, strategy.gift_aid_relief, strategy.salary_sacrifice, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.property_income_finance_cost, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_ppr_relief, strategy.cgt_lettings_relief, strategy.cgt_spousal_transfer_before_disposal, strategy.cgt_business_asset_disposal_relief)
- PASS — figure exercised by golden test cases (income_tax_on_earned_income, combined_personal_tax, strategy.gift_aid_relief, strategy.salary_sacrifice, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.property_income_finance_cost, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_lettings_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — belongs to a released rule-base version (2025.1)

### 18. Marriage Allowance transferable amount  
`income_tax.marriage_allowance` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- transferable_amount: **1,260**
- PASS — consumed by a registered calculator (strategy.marriage_allowance_transfer)
- PASS — figure exercised by golden test cases (strategy.marriage_allowance_transfer)
- PASS — belongs to a released rule-base version (2025.1)

### 19. Personal Allowance  
`income_tax.personal_allowance` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- amount: **12,570**
- taper_rate: **0.5**
- taper_threshold: **100,000**
- PASS — consumed by a registered calculator (income_tax_on_earned_income, combined_personal_tax, strategy.gift_aid_relief, strategy.salary_sacrifice, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.property_income_finance_cost, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, strategy.marriage_allowance_transfer, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_ppr_relief, strategy.cgt_lettings_relief, strategy.cgt_spousal_transfer_before_disposal, strategy.cgt_business_asset_disposal_relief)
- PASS — figure exercised by golden test cases (income_tax_on_earned_income, combined_personal_tax, strategy.gift_aid_relief, strategy.salary_sacrifice, strategy.pension_annual_allowance_carry_forward, strategy.personal_pension_contribution, strategy.property_income_finance_cost, strategy.partnership_profit_allocation, strategy.property_incorporation, strategy.incorporation_vs_sole_trade, strategy.marriage_allowance_transfer, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_lettings_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 12,570 appears in: Income Tax Act 2007 s.35; Social Security Contributions and Benefits Act 1992 s.15
- Source cross-reference: 100,000 appears in: Income Tax Act 2007 s.35; Inheritance Tax Act 1984 s.8D; Inheritance Tax Act 1984 s.8G

### 20. ISA annual subscription limit  
`isa.allowance` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- amount: **20,000**
- PASS — consumed by a registered calculator (strategy.isa_bed_and_isa)
- PASS — figure exercised by golden test cases (strategy.isa_bed_and_isa)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 20,000 appears in: Corporation Tax Act 2009 Part 13 (as amended, merged R&D scheme)

### 21. Class 4 NIC (self-employed)  
`national_insurance.class4` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- rate: **0.06**
- upper_rate: **0.02**
- lower_profits_limit: **12,570**
- upper_profits_limit: **50,270**
- PASS — consumed by a registered calculator (strategy.partnership_profit_allocation, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (strategy.partnership_profit_allocation, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 12,570 appears in: Income Tax Act 2007 s.35; Social Security Contributions and Benefits Act 1992 s.15
- Source cross-reference: 50,270 appears in: Social Security Contributions and Benefits Act 1992 s.15

### 22. Employee Class 1 NIC  
`national_insurance.employee_class1` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- rate: **0.08**
- upper_rate: **0.02**
- primary_threshold: **12,570**
- upper_earnings_limit: **50,270**
- PASS — consumed by a registered calculator (employee_class1_nic, strategy.salary_sacrifice, strategy.salary_dividend_mix, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (employee_class1_nic, strategy.salary_sacrifice, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 12,570 appears in: Income Tax Act 2007 s.35; Social Security Contributions and Benefits Act 1992 s.15
- Source cross-reference: 50,270 appears in: Social Security Contributions and Benefits Act 1992 s.15

### 23. Pension annual allowance and taper  
`pension.annual_allowance` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- standard_amount: **60,000**
- minimum_tapered_amount: **10,000**
- taper_threshold_income: **200,000**
- taper_adjusted_income_limit: **260,000**
- PASS — consumed by a registered calculator (pension_available_annual_allowance, strategy.pension_annual_allowance_carry_forward)
- PASS — figure exercised by golden test cases (strategy.pension_annual_allowance_carry_forward)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 60,000 appears in: Finance Act 2004 s.228
- Source cross-reference: 200,000 appears in: Income Tax Act 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT)

### 24. Residential landlord finance-cost (mortgage interest) tax-reducer rate  
`property_income.finance_cost_restriction` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- reducer_rate: **0.2**
- PASS — consumed by a registered calculator (strategy.property_income_finance_cost, strategy.property_incorporation)
- PASS — figure exercised by golden test cases (strategy.property_income_finance_cost, strategy.property_incorporation)
- PASS — belongs to a released rule-base version (2025.1)

### 25. EIS/SEIS/VCT income-tax relief rates, annual limits and CGT treatment  
`venture_capital.schemes` — personal_income_tax — release 2025.1 — effective 2025-04-06 to open
- eis:
  - relief_rate: **0.3**
  - annual_limit: **1,000,000**
  - cgt_deferral: **True**
  - min_holding_years: **3**
  - tax_free_dividends: **False**
  - cgt_reinvestment_relief_rate: **0.0**
- vct:
  - relief_rate: **0.3**
  - annual_limit: **200,000**
  - cgt_deferral: **False**
  - min_holding_years: **5**
  - tax_free_dividends: **True**
  - cgt_reinvestment_relief_rate: **0.0**
- seis:
  - relief_rate: **0.5**
  - annual_limit: **200,000**
  - cgt_deferral: **False**
  - min_holding_years: **3**
  - tax_free_dividends: **False**
  - cgt_reinvestment_relief_rate: **0.5**
- PASS — consumed by a registered calculator (strategy.venture_capital_investment)
- PASS — figure exercised by golden test cases (strategy.venture_capital_investment)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 200,000 appears in: Income Tax Act 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT)
- Source cross-reference: 1,000,000 appears in: Capital Allowances Act 2001 s.51A; Corporation Tax Act 2010 Part 8A (Patent Box)

### 26. CGT annual exempt amount  
`cgt.annual_exempt_amount` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- amount: **3,000**
- PASS — consumed by a registered calculator (strategy.isa_bed_and_isa, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_ppr_relief, strategy.cgt_lettings_relief, strategy.cgt_spousal_transfer_before_disposal, strategy.cgt_business_asset_disposal_relief)
- PASS — figure exercised by golden test cases (strategy.isa_bed_and_isa, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_lettings_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 3,000 appears in: Corporation Tax Act 2010 Part 8A (Patent Box); Income Tax Act 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT); Inheritance Tax Act 1984 s.19

### 27. Business Asset Disposal Relief: reduced CGT rate and lifetime limit  
`cgt.business_asset_disposal_relief` — property_taxes — release 2025.3 — effective 2025-04-06 to 2026-04-06
- rate: **0.14**
- lifetime_limit: **1,000,000**
- PASS — consumed by a registered calculator (strategy.eot_disposal_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — figure exercised by golden test cases (strategy.eot_disposal_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 1,000,000 appears in: Capital Allowances Act 2001 s.51A; Corporation Tax Act 2010 Part 8A (Patent Box)

### 28. Business Asset Disposal Relief: reduced CGT rate and lifetime limit  
`cgt.business_asset_disposal_relief` — property_taxes — release 2026.1 — effective 2026-04-06 to open
- rate: **0.18**
- lifetime_limit: **1,000,000**
- PASS — consumed by a registered calculator (strategy.eot_disposal_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — figure exercised by golden test cases (strategy.eot_disposal_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — belongs to a released rule-base version (2026.1)
- Source cross-reference: 1,000,000 appears in: Capital Allowances Act 2001 s.51A; Corporation Tax Act 2010 Part 8A (Patent Box)

### 29. Lettings relief cap (shared-occupancy let, TCGA 1992 s.223B)  
`cgt.lettings_relief` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- cap: **40,000**
- PASS — consumed by a registered calculator (strategy.cgt_lettings_relief)
- PASS — figure exercised by golden test cases (strategy.cgt_lettings_relief)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 40,000 appears in: Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Taxation of Chargeable Gains Act 1992 s.223B

### 30. CGT rates by asset class (lower = within basic band)  
`cgt.rates` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- other:
  - lower: **0.18**
  - higher: **0.24**
- residential:
  - lower: **0.18**
  - higher: **0.24**
- PASS — consumed by a registered calculator (strategy.isa_bed_and_isa, strategy.property_incorporation, strategy.venture_capital_investment, strategy.eot_disposal_relief, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_ppr_relief, strategy.cgt_lettings_relief, strategy.cgt_spousal_transfer_before_disposal, strategy.cgt_business_asset_disposal_relief)
- PASS — figure exercised by golden test cases (strategy.isa_bed_and_isa, strategy.property_incorporation, strategy.venture_capital_investment, strategy.eot_disposal_relief, cgt_liability, strategy.cgt_timing_of_disposals, strategy.cgt_lettings_relief, strategy.cgt_business_asset_disposal_relief)
- PASS — belongs to a released rule-base version (2025.3)

### 31. LBTT lease: NPV discount rate and bands (Scotland)  
`lbtt.lease_npv_bands` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- bands:
  - rate: **0.0**
  - upper: **150,000**
  - rate: **0.01**
  - upper: **2,000,000**
  - rate: **0.02**
  - upper: **None**
- discount_rate: **0.035**
- PASS — consumed by a registered calculator (strategy.lbtt_lease_npv)
- PASS — figure exercised by golden test cases (strategy.lbtt_lease_npv)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 150,000 appears in: Finance Act 2003 Sch 5 (amount of tax chargeable: rent); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed); Inheritance Tax Act 1984 s.8D
- Source cross-reference: 2,000,000 appears in: Corporation Tax Act 2010 Part 8A (Patent Box); Inheritance Tax Act 1984 s.8D; Inheritance Tax Act 1984 s.8G

### 32. LBTT non-residential freehold bands (Scotland)  
`lbtt.non_residential_bands` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- bands:
  - rate: **0.0**
  - upper: **150,000**
  - rate: **0.01**
  - upper: **250,000**
  - rate: **0.05**
  - upper: **None**
- PASS — consumed by a registered calculator (strategy.lbtt_non_residential_purchase)
- PASS — figure exercised by golden test cases (strategy.lbtt_non_residential_purchase)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 150,000 appears in: Finance Act 2003 Sch 5 (amount of tax chargeable: rent); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed); Inheritance Tax Act 1984 s.8D
- Source cross-reference: 250,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)

### 33. LBTT residential bands, Additional Dwelling Supplement, first-time buyer relief (Scotland)  
`lbtt.residential_bands` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- bands:
  - rate: **0.0**
  - upper: **145,000**
  - rate: **0.02**
  - upper: **250,000**
  - rate: **0.05**
  - upper: **325,000**
  - rate: **0.1**
  - upper: **750,000**
  - rate: **0.12**
  - upper: **None**
- additional_dwelling_supplement: **0.08**
- first_time_buyer_nil_rate_threshold: **175,000**
- PASS — consumed by a registered calculator (strategy.property_incorporation, lbtt_residential, strategy.lbtt_purchase_planning)
- PASS — figure exercised by golden test cases (strategy.property_incorporation, lbtt_residential)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 175,000 appears in: Inheritance Tax Act 1984 s.8D
- Source cross-reference: 250,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)

### 34. LTT non-residential lease: NPV discount rate and bands (Wales)  
`ltt.lease_npv_bands` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- bands:
  - rate: **0.0**
  - upper: **225,000**
  - rate: **0.01**
  - upper: **2,000,000**
  - rate: **0.02**
  - upper: **None**
- discount_rate: **0.035**
- PASS — consumed by a registered calculator (strategy.ltt_lease_npv)
- PASS — figure exercised by golden test cases (strategy.ltt_lease_npv)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 2,000,000 appears in: Corporation Tax Act 2010 Part 8A (Patent Box); Inheritance Tax Act 1984 s.8D; Inheritance Tax Act 1984 s.8G

### 35. LTT non-residential freehold bands (Wales)  
`ltt.non_residential_bands` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- bands:
  - rate: **0.0**
  - upper: **225,000**
  - rate: **0.01**
  - upper: **250,000**
  - rate: **0.05**
  - upper: **1,000,000**
  - rate: **0.06**
  - upper: **None**
- PASS — consumed by a registered calculator (strategy.ltt_non_residential_purchase)
- PASS — figure exercised by golden test cases (strategy.ltt_non_residential_purchase)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 250,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)
- Source cross-reference: 1,000,000 appears in: Capital Allowances Act 2001 s.51A; Corporation Tax Act 2010 Part 8A (Patent Box)

### 36. LTT residential main and higher (additional-property) bands (Wales)  
`ltt.residential_bands` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- main_bands:
  - rate: **0.0**
  - upper: **225,000**
  - rate: **0.06**
  - upper: **400,000**
  - rate: **0.075**
  - upper: **750,000**
  - rate: **0.1**
  - upper: **1,500,000**
  - rate: **0.12**
  - upper: **None**
- higher_bands:
  - rate: **0.05**
  - upper: **180,000**
  - rate: **0.085**
  - upper: **250,000**
  - rate: **0.1**
  - upper: **400,000**
  - rate: **0.125**
  - upper: **750,000**
  - rate: **0.15**
  - upper: **1,500,000**
  - rate: **0.17**
  - upper: **None**
- PASS — consumed by a registered calculator (strategy.property_incorporation, ltt_residential, strategy.ltt_purchase_planning)
- PASS — figure exercised by golden test cases (strategy.property_incorporation, ltt_residential)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 250,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)
- Source cross-reference: 1,500,000 appears in: Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)

### 37. SDLT non-residential lease: NPV discount rate and bands (England/NI)  
`sdlt.lease_npv_bands` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- bands:
  - rate: **0.0**
  - upper: **150,000**
  - rate: **0.01**
  - upper: **5,000,000**
  - rate: **0.02**
  - upper: **None**
- discount_rate: **0.035**
- PASS — consumed by a registered calculator (strategy.sdlt_lease_npv)
- PASS — figure exercised by golden test cases (strategy.sdlt_lease_npv)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 150,000 appears in: Finance Act 2003 Sch 5 (amount of tax chargeable: rent); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed); Inheritance Tax Act 1984 s.8D

### 38. SDLT non-residential/mixed freehold bands (England/NI)  
`sdlt.non_residential_bands` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- bands:
  - rate: **0.0**
  - upper: **150,000**
  - rate: **0.02**
  - upper: **250,000**
  - rate: **0.05**
  - upper: **None**
- PASS — consumed by a registered calculator (strategy.sdlt_non_residential_purchase)
- PASS — figure exercised by golden test cases (strategy.sdlt_non_residential_purchase)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 150,000 appears in: Finance Act 2003 Sch 5 (amount of tax chargeable: rent); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed); Inheritance Tax Act 1984 s.8D
- Source cross-reference: 250,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)

### 39. SDLT residential bands, surcharge, FTB relief (England/NI)  
`sdlt.residential_bands` — property_taxes — release 2025.3 — effective 2025-04-06 to open
- bands:
  - rate: **0.0**
  - upper: **125,000**
  - rate: **0.02**
  - upper: **250,000**
  - rate: **0.05**
  - upper: **925,000**
  - rate: **0.1**
  - upper: **1,500,000**
  - rate: **0.12**
  - upper: **None**
- first_time_buyer:
  - cap: **500,000**
  - relief_threshold: **300,000**
  - rate_above_threshold: **0.05**
- additional_dwelling_surcharge: **0.05**
- PASS — consumed by a registered calculator (strategy.property_incorporation, sdlt_residential, strategy.sdlt_purchase_planning)
- PASS — figure exercised by golden test cases (strategy.property_incorporation, sdlt_residential)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 125,000 appears in: Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 Sch 5 (amount of tax chargeable: rent); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)
- Source cross-reference: 250,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)
- Source cross-reference: 300,000 appears in: Finance Act 2003 Sch 6ZA
- Source cross-reference: 500,000 appears in: Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 Sch 6ZA; Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)
- Source cross-reference: 925,000 appears in: Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)
- Source cross-reference: 1,500,000 appears in: Finance Act 2003 Sch 4ZA (higher rates for additional dwellings); Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)

---
## B. Strategies (the planning advice, with legal basis)

### 40. Capital allowances / Annual Investment Allowance  
`capital-allowances-aia` — corporation_tax — risk **settled**, timeframe short
> Qualifying spend on plant and machinery gets 100% tax relief in the year of purchase through the Annual Investment Allowance, up to the AIA limit (currently £1,000,000). Spend above that is written down at 18% a year in the main pool. This quantifies the first-year deduction and the tax it saves at the client's marginal rate — often a reason to time capital spend into a particular period.
- Authority: [Capital Allowances Act 2001 s.51A](https://www.legislation.gov.uk/ukpga/2001/2/section/51A) (in_force)
- PASS — calculator registered (strategy.capital_allowances)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (391 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 41. Capital allowances on commercial-property fixtures  
`commercial-property-fixtures` — corporation_tax — risk **settled**, timeframe short
> When a business buys or refurbishes a commercial building, a large part of the cost is often 'integral features' and fixtures (heating, electrics, lifts, water systems) that qualify for capital allowances. Claiming them gives 100% relief through the Annual Investment Allowance up to its limit, then the special-rate writing-down allowance on the excess. This quantifies the first-year allowance and the tax it saves. On a second-hand building the fixtures claim depends on the seller's pooling/fixed-value position (CAA 2001 s.187A) — the adviser confirms it, ideally with a specialist survey.
- Authority: [Capital Allowances Act 2001 ss.33A-33B & s.187A (integral features / fixtures)](https://www.legislation.gov.uk/ukpga/2001/2/section/33A) (in_force)
- PASS — calculator registered (strategy.commercial_property_fixtures)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (594 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 42. Directors' loan s.455 charge  
`directors-loan-s455` — corporation_tax — risk **settled**, timeframe short
> Where a director-shareholder's loan account is overdrawn, the company faces a temporary 33.75% s.455 charge on any amount still outstanding 9 months and 1 day after the year end. Repaying the loan (or enough of it) within that window avoids the charge; the charge is refunded when the loan is later repaid. This quantifies the charge and the amount avoided by repaying in time.
- Authority: [Corporation Tax Act 2010 s.455](https://www.legislation.gov.uk/ukpga/2010/4/section/455) (in_force)
- PASS — calculator registered (strategy.directors_loan_s455)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (377 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 43. Employer pension contribution  
`employer-pension-contribution` — corporation_tax — risk **settled**, timeframe short
> An employer pension contribution from the individual's own company is not restricted by relevant UK earnings and carries no employee or employer National Insurance. The company deducts it against corporation tax, subject to the wholly-and-exclusively condition as part of a reasonable remuneration package. This quantifies the corporation tax saved, the employer NIC saved versus paying the same amount as salary, and the net cost to the company.
- Authority: [Corporation Tax Act 2009 s.54](https://www.legislation.gov.uk/ukpga/2009/4/section/54) (in_force)
- PASS — calculator registered (strategy.employer_pension_contribution)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (446 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 44. Group relief for company losses  
`group-loss-relief` — corporation_tax — risk **settled**, timeframe short
> Where one company in a 75% group makes a loss and another makes a profit, the loss can be surrendered as group relief and set against the profitable company's profits. This relieves the loss now, at the claimant company's marginal rate — worth 26.5% where the claimant is in the marginal-relief band (profits between £50,000 and £250,000), which is more valuable than carrying the loss forward at 19% or the 25% main rate. Any loss not covered by the claimant's profit is carried forward. Establishing the 75% group relationship is a precondition the accountant confirms.
- Authority: [Corporation Tax Act 2010 Part 5 (ss.97-188)](https://www.legislation.gov.uk/ukpga/2010/4/part/5) (in_force)
- PASS — calculator registered (strategy.group_loss_relief)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (571 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 45. Patent Box (10% rate on patented-product profits)  
`patent-box` — corporation_tax — risk **settled**, timeframe medium
> A company that owns or exclusively licenses patents can elect for the profits attributable to those patented inventions to be taxed at an effective 10% corporation-tax rate instead of the main rate. This quantifies the tax at the main rate, the tax under the Patent Box and the saving. Identifying the profit attributable to the qualifying IP, and meeting the modified-nexus R&D requirement, are specialist steps the adviser establishes.
- Authority: [Corporation Tax Act 2010 Part 8A (Patent Box)](https://www.legislation.gov.uk/ukpga/2010/4/part/8A) (in_force)
- PASS — calculator registered (strategy.patent_box)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (437 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (medium)

### 46. R&D tax relief (merged scheme)  
`rd-tax-relief` — corporation_tax — risk **settled**, timeframe short
> A company carrying out qualifying research and development can claim R&D tax relief. Under the merged scheme (from April 2024) this is a 20% 'above the line' expenditure credit on the qualifying spend. The credit is taxable, so the net cash benefit is 20% less corporation tax — about 15% of the spend for a main-rate company. This quantifies the gross credit, the tax on it and the net benefit. What counts as qualifying R&D (the advance in science or technology and the qualifying cost categories) is a technical judgement the adviser and, often, an R&D specialist confirm.
- Authority: [Corporation Tax Act 2009 Part 13 (as amended, merged R&D scheme)](https://www.legislation.gov.uk/ukpga/2009/4/part/13) (in_force)
- PASS — calculator registered (strategy.rd_tax_relief)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (575 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 47. Employee Ownership Trust sale (CGT-free)  
`eot-disposal-relief` — cross_cutting — risk **settled**, timeframe long
> An owner who sells a controlling stake in their trading company to an Employee Ownership Trust pays no capital gains tax on the sale — a full exemption. This quantifies the CGT a normal third-party sale would cost instead (Business Asset Disposal Relief at 14% on the first £1m, then the standard share rate) and therefore the tax saved by the EOT route. The qualifying conditions were tightened by Finance Act 2024/2025 (UK-resident trustees, the former owners not keeping control, a four-year clawback and an independent valuation) — the adviser confirms them.
- Authority: [Taxation of Chargeable Gains Act 1992 s.236H (Employee Ownership Trust)](https://www.legislation.gov.uk/ukpga/1992/12/section/236H) (in_force)
- PASS — calculator registered (strategy.eot_disposal_relief)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (562 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (long)

### 48. Incorporation versus remaining a sole trader  
`incorporation-vs-sole-trade` — cross_cutting — risk **borderline**, timeframe medium
> Trading through a company rather than as a sole trader changes the tax base from income tax plus Class 4 NIC on all profits, to corporation tax on retained profit plus income tax/NIC only on amounts extracted as salary or dividends. Whether this saves tax depends on profit level and how much is drawn out; HMRC scrutinises incorporations that appear to have no commercial purpose beyond tax saving.
- Authority: [Corporation Tax Act 2010 Part 3A (ss.18A-18M)](https://www.legislation.gov.uk/ukpga/2010/4/part/3A) (in_force)
- Authority: [Income Tax Act 2007 s.35](https://www.legislation.gov.uk/ukpga/2007/3/section/35) (in_force)
- Authority: [Social Security Contributions and Benefits Act 1992 s.15](https://www.legislation.gov.uk/ukpga/1992/4/section/15) (in_force)
- PASS — calculator registered (strategy.incorporation_vs_sole_trade)
- PASS — adapter registered
- PASS — has legal authorities (3 cited)
- PASS — plain-English explanation present (399 chars)
- PASS — risk status set (borderline)
- PASS — timeframe set (medium)

### 49. Property portfolio incorporation (should the landlord incorporate?)  
`property-incorporation` — cross_cutting — risk **borderline**, timeframe long
> A landlord holding property personally is caught by the s.24 restriction (mortgage interest relieved at only 20%); a company deducts the interest in full and pays corporation tax. That gives an annual saving for a higher-rate landlord — but moving the properties into a company is a disposal at market value, so it triggers SDLT (with the 5% surcharge) and a capital gain (deferred only if s.162 incorporation relief applies). This weighs the annual saving against those one-off costs and reports the break-even in years, so the landlord can see whether incorporation actually pays. It assumes profits are retained (extracting them adds dividend tax) and an England/SDLT portfolio; whether the letting is a 'business' for s.162, and any ATED charge, are matters the accountant confirms — which is why it is flagged borderline.
- Authority: [Income Tax (Trading and Other Income) Act 2005 ss.272A-274C](https://www.legislation.gov.uk/ukpga/2005/5/section/272A) (in_force)
- Authority: [Taxation of Chargeable Gains Act 1992 s.162](https://www.legislation.gov.uk/ukpga/1992/12/section/162) (in_force)
- PASS — calculator registered (strategy.property_incorporation)
- PASS — adapter registered
- PASS — has legal authorities (2 cited)
- PASS — plain-English explanation present (826 chars)
- PASS — risk status set (borderline)
- PASS — timeframe set (long)

### 50. Salary/dividend extraction mix  
`salary-dividend-mix` — cross_cutting — risk **settled**, timeframe short
> An owner-manager can choose how much of their reward is taken as salary (deductible against corporation tax, but subject to employer/employee NIC) versus dividends (paid from post-tax company profit, no NIC, taxed at dividend rates). Comparing the combined company and personal tax cost across salary levels identifies the extraction mix with the lowest total tax and NIC for the profit available.
- Authority: [Corporation Tax Act 2010 Part 3A (ss.18A-18M)](https://www.legislation.gov.uk/ukpga/2010/4/part/3A) (in_force)
- Authority: [Income Tax Act 2007 s.13A](https://www.legislation.gov.uk/ukpga/2007/3/section/13A) (in_force)
- Authority: [Income Tax Act 2007 s.35](https://www.legislation.gov.uk/ukpga/2007/3/section/35) (in_force)
- Authority: [Jones v Garnett (Arctic Systems) [2007] UKHL 35](https://www.bailii.org/uk/cases/UKHL/2007/35.html) (in_force)
- Authority: [Social Security Contributions and Benefits Act 1992 s.6](https://www.legislation.gov.uk/ukpga/1992/4/section/6) (in_force)
- PASS — calculator registered (strategy.salary_dividend_mix)
- PASS — adapter registered
- PASS — has legal authorities (5 cited)
- PASS — plain-English explanation present (397 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 51. Business / Agricultural Property Relief  
`business-property-relief` — inheritance_tax — risk **settled**, timeframe long
> Qualifying business and agricultural property is relieved from inheritance tax — at 100% for an unquoted trading business or qualifying farmland. From 6 April 2026 the 100% rate is capped at a combined £1,000,000, with 50% relief on anything above that (Finance Act 2025), so a large business or farm can face inheritance tax for the first time. This quantifies the value relieved, the taxable value left after relief, and the IHT saved. It assumes the rest of the estate has used the nil-rate bands, which is the usual position where seven figures of business property are in point. Whether specific assets qualify (trading vs investment, two-year ownership) is a judgement the accountant confirms.
- Authority: [Inheritance Tax Act 1984 ss.103-114 (BPR) and ss.115-124C (APR)](https://www.legislation.gov.uk/ukpga/1984/51/part/V/chapter/I) (in_force)
- PASS — calculator registered (strategy.business_property_relief)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (699 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (long)

### 52. Charitable legacy and the 36% reduced rate  
`iht-charitable-legacy-reduced-rate` — inheritance_tax — risk **settled**, timeframe medium
> Where at least 10% of the baseline amount of the estate is left to charity, the whole taxable estate is charged at 36% rather than 40%. Because the charitable legacy is itself exempt, topping a smaller legacy up to the 10% threshold often costs the residuary beneficiaries far less than the legacy's face value, and in some estates makes them better off outright.
- Authority: [Inheritance Tax Act 1984 Sch 1A](https://www.legislation.gov.uk/ukpga/1984/51/schedule/1A) (in_force)
- PASS — calculator registered (strategy.iht_charitable_legacy_reduced_rate)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (363 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (medium)

### 53. Lifetime gifting: exemptions and potentially exempt transfers  
`iht-lifetime-gifting-pets` — inheritance_tax — risk **settled**, timeframe long
> Outright lifetime gifts to individuals are potentially exempt transfers: no tax if the donor survives seven years, with taper relief reducing the tax (not the transfer) where death occurs in years three to seven and the gift exceeds the nil-rate band. The first £3,000 given each tax year is immediately exempt, plus one year's unused prior exemption. The donor must not retain a benefit in the gifted asset, or the gift-with-reservation rules put it back in the estate.
- Authority: [Inheritance Tax Act 1984 s.19](https://www.legislation.gov.uk/ukpga/1984/51/section/19) (in_force)
- Authority: [Inheritance Tax Act 1984 s.3A](https://www.legislation.gov.uk/ukpga/1984/51/section/3A) (in_force)
- Authority: [Inheritance Tax Act 1984 s.7 and Sch 1](https://www.legislation.gov.uk/ukpga/1984/51/section/7) (in_force)
- PASS — calculator registered (strategy.iht_lifetime_gifting)
- PASS — adapter registered
- PASS — has legal authorities (3 cited)
- PASS — plain-English explanation present (470 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (long)

### 54. Spouse exemption and transferable nil-rate bands  
`iht-spousal-transfer-and-nil-rate-bands` — inheritance_tax — risk **settled**, timeframe long
> Transfers between spouses or civil partners are wholly exempt from inheritance tax, and any nil-rate band and residence nil-rate band unused on the first death transfers to the survivor. Leaving the estate to the surviving spouse defers all tax to the second death, where up to double both bands (currently £650,000 plus £350,000 where the home passes to direct descendants) shelter the combined estate. The transferred bands must be claimed by the survivor's personal representatives within two years.
- Authority: [Inheritance Tax Act 1984 s.18](https://www.legislation.gov.uk/ukpga/1984/51/section/18) (in_force)
- Authority: [Inheritance Tax Act 1984 s.8A](https://www.legislation.gov.uk/ukpga/1984/51/section/8A) (in_force)
- Authority: [Inheritance Tax Act 1984 s.8D](https://www.legislation.gov.uk/ukpga/1984/51/section/8D) (in_force)
- Authority: [Inheritance Tax Act 1984 s.8G](https://www.legislation.gov.uk/ukpga/1984/51/section/8G) (in_force)
- PASS — calculator registered (strategy.iht_spousal_transfer_nil_rate_bands)
- PASS — adapter registered
- PASS — has legal authorities (4 cited)
- PASS — plain-English explanation present (502 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (long)

### 55. Life policy in trust to fund the IHT bill  
`life-policy-in-trust` — inheritance_tax — risk **settled**, timeframe long
> A whole-of-life policy written in trust pays out on death to the trust, outside the estate, giving the family tax-free cash to pay the inheritance tax bill without having to sell assets. If the same policy were held personally, its proceeds would instead add to the estate and attract 40% IHT. This quantifies the IHT saved by writing it in trust and the payout available to meet the bill. The trust must be validly set up with no benefit reserved to the settlor.
- Authority: [Inheritance Tax Act 1984 s.5 (meaning of estate)](https://www.legislation.gov.uk/ukpga/1984/51/section/5) (in_force)
- PASS — calculator registered (strategy.life_policy_in_trust)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (463 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (long)

### 56. Pension death-benefit IHT (from April 2027)  
`pension-death-benefit` — inheritance_tax — risk **borderline**, timeframe long
> Today an unused pension pot normally passes on death outside the estate, free of inheritance tax. From 6 April 2027 (announced at Autumn Budget 2024) most pension funds are expected to be brought into the estate for IHT. This shows the extra inheritance tax a pot would attract from that date — 40% where the estate is already above the nil-rate band — so a client can plan (for example, drawing the pension down or gifting) ahead of the change. It is a forward-looking projection based on the announcement and is flagged borderline until the Finance Bill 2025-26 is enacted.
- Authority: [IHTA 1984 s.3 (as to be amended from 6 April 2027, Finance Bill 2025-26)](https://www.legislation.gov.uk/ukpga/1984/51/section/3) (in_force)
- PASS — calculator registered (strategy.pension_death_benefit)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (575 chars)
- PASS — risk status set (borderline)
- PASS — timeframe set (long)

### 57. Relevant-property trust IHT charges  
`relevant-property-trust-charges` — inheritance_tax — risk **settled**, timeframe long
> A discretionary trust (and most lifetime trusts) is 'relevant property' with its own inheritance tax charges, separate from anyone's estate: a 20% entry charge on the value settled above the available nil-rate band; a charge on each ten-year anniversary of up to 6% of the value above the band; and a proportionate exit charge when capital leaves the trust. This quantifies all three, so a settlor can compare putting assets in trust (control and protection, but these ongoing charges) against outright gifts (a potentially exempt transfer with no charge if they survive seven years). Whether the trust is relevant property, and the settlor's prior chargeable transfers, are matters the adviser confirms.
- Authority: [Inheritance Tax Act 1984 ss.58-69 (relevant property)](https://www.legislation.gov.uk/ukpga/1984/51/part/III/chapter/III) (in_force)
- PASS — calculator registered (strategy.relevant_property_trust_charges)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (704 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (long)

### 58. Gift Aid higher-rate relief  
`gift-aid-relief` — personal_income_tax — risk **settled**, timeframe short
> A Gift Aid donation is grossed up at the basic rate, which the charity reclaims. For a higher or additional-rate donor the grossed-up amount also extends the basic-rate band, giving personal relief of the difference between their rate and the basic rate. Where income is in the 100,000-125,140 personal-allowance taper, the donation also reduces adjusted net income and can restore some or all of the personal allowance.
- Authority: [Income Tax Act 2007 s.414](https://www.legislation.gov.uk/ukpga/2007/3/section/414) (in_force)
- PASS — calculator registered (strategy.gift_aid_relief)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (420 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 59. Bed-and-ISA (shelter investments in an ISA)  
`isa-bed-and-isa` — personal_income_tax — risk **settled**, timeframe short
> Selling unwrapped investments and repurchasing them inside an ISA (a 'bed-and-ISA') moves them into a wrapper where future dividends and capital growth are tax-free. Timing the sale so the gain stays within the annual CGT exempt amount means no capital gains tax on the transfer. This quantifies the amount sheltered (capped at the £20,000 ISA limit), any CGT due on the transfer, and the yearly dividend tax saved once the holding is inside the ISA. Future growth is also CGT-free but is not projected here as it depends on the growth rate.
- Authority: [Income Tax (Trading and Other Income) Act 2005 s.694](https://www.legislation.gov.uk/ukpga/2005/5/section/694) (in_force)
- PASS — calculator registered (strategy.isa_bed_and_isa)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (541 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 60. Marriage Allowance transfer  
`marriage-allowance-transfer` — personal_income_tax — risk **settled**, timeframe short
> Where one spouse or civil partner does not use their full personal allowance and the other is a basic-rate taxpayer, 10% of the unused allowance can be transferred, reducing the recipient's tax bill by a fixed amount.
- Authority: [Income Tax Act 2007 ss.55A-55E](https://www.legislation.gov.uk/ukpga/2007/3/section/55A) (in_force)
- PASS — calculator registered (strategy.marriage_allowance_transfer)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (217 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 61. Partnership / LLP profit-share allocation  
`partnership-profit-allocation` — personal_income_tax — risk **borderline**, timeframe short
> A partnership does not pay tax itself — each partner is taxed on their share of the profit as trading income (income tax plus Class 4 NIC), on top of their other income. When partners are in different tax bands, the profit-sharing ratio changes the combined tax bill: shifting profit toward a lower-rate partner can reduce it. This compares the current split with a proposed one and quantifies the difference. Crucially the ratio must reflect the partners' genuine commercial contribution — it cannot be set purely to save tax, and HMRC can challenge allocations that divert income (settlements rules) — which is why this is flagged as a borderline judgement for the accountant to stand behind.
- Authority: [Income Tax (Trading and Other Income) Act 2005 s.850](https://www.legislation.gov.uk/ukpga/2005/5/section/850) (in_force)
- PASS — calculator registered (strategy.partnership_profit_allocation)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (694 chars)
- PASS — risk status set (borderline)
- PASS — timeframe set (short)

### 62. Pension annual allowance carry-forward  
`pension-annual-allowance-carry-forward` — personal_income_tax — risk **settled**, timeframe short
> Unused pension annual allowance from the three preceding tax years can be carried forward, allowing a larger contribution in the current year. Personal contributions attract relief only up to the greater of £3,600 and relevant UK earnings (employment and trading income; dividends do not count). Where earnings are the constraint, an employer contribution from the individual's own company avoids the cap entirely and is deductible against corporation tax, subject to the wholly-and-exclusively condition as part of a reasonable remuneration package.
- Authority: [Corporation Tax Act 2009 s.54](https://www.legislation.gov.uk/ukpga/2009/4/section/54) (in_force)
- Authority: [Finance Act 2004 s.190](https://www.legislation.gov.uk/ukpga/2004/12/section/190) (in_force)
- Authority: [Finance Act 2004 s.228](https://www.legislation.gov.uk/ukpga/2004/12/section/228) (in_force)
- PASS — calculator registered (strategy.pension_annual_allowance_carry_forward)
- PASS — adapter registered
- PASS — has legal authorities (3 cited)
- PASS — plain-English explanation present (550 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 63. Personal pension contribution (relief at source)  
`personal-pension-contribution` — personal_income_tax — risk **settled**, timeframe short
> A personal pension contribution is paid net of basic-rate tax, which the provider reclaims into the pot. A higher or additional-rate taxpayer claims further relief because the grossed-up contribution extends the basic-rate band. Where income is in the 100,000-125,140 personal-allowance taper the contribution also reduces adjusted net income and restores personal allowance, so the effective relief can reach 60%. Relief is capped at the greater of £3,600 and relevant UK earnings; dividends and savings/rental income do not count towards it.
- Authority: [Finance Act 2004 s.190](https://www.legislation.gov.uk/ukpga/2004/12/section/190) (in_force)
- PASS — calculator registered (strategy.personal_pension_contribution)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (543 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 64. Landlord finance-cost restriction (s.24)  
`property-income-finance-cost` — personal_income_tax — risk **settled**, timeframe short
> Since April 2020 an individual residential landlord can no longer deduct mortgage interest from rental profit. The interest is relieved instead as a basic-rate (20%) tax reducer, on the lower of the finance costs, the rental profit and adjusted total income. A basic-rate landlord is unaffected, but a higher or additional-rate landlord effectively loses relief at 40%/45% and pays more tax. This quantifies the rental profit, the tax reducer, the tax with and without the restriction, and the extra tax it costs — which is the main reason landlords consider holding property through a company (which still deducts the interest in full).
- Authority: [Income Tax (Trading and Other Income) Act 2005 ss.272A-274C](https://www.legislation.gov.uk/ukpga/2005/5/section/272A) (in_force)
- PASS — calculator registered (strategy.property_income_finance_cost)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (637 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 65. Salary sacrifice into an employer pension  
`salary-sacrifice-into-pension` — personal_income_tax — risk **settled**, timeframe short
> The employee gives up an agreed slice of salary and the employer pays that amount straight into the employee's pension. Because the salary is never received, the employee saves income tax and Class 1 NIC on it, and the employer saves secondary (employer) NIC — a saving the employer can also add to the pension. The whole sacrificed amount goes into the pension gross, so the net cost to the employee is well below the amount invested. This quantifies the employee's income tax and NIC saving, the employer's NIC saving, the amount into the pension and its net cost. (A valid arrangement must reduce contractual pay before it is earned and keep pay above the National Minimum Wage.)
- Authority: [Social Security Contributions and Benefits Act 1992 s.6](https://www.legislation.gov.uk/ukpga/1992/4/section/6) (in_force)
- PASS — calculator registered (strategy.salary_sacrifice)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (682 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 66. EIS / SEIS / VCT investment relief  
`venture-capital-investment` — personal_income_tax — risk **settled**, timeframe medium
> Investing in a qualifying venture-capital scheme gives income tax relief: 30% under the Enterprise Investment Scheme (up to £1m a year), 50% under the Seed Enterprise Investment Scheme (up to £200k), or 30% through a Venture Capital Trust (up to £200k). The relief cannot exceed the investor's income tax bill. EIS also defers a chargeable gain reinvested in the shares, SEIS exempts half of a reinvested gain, and VCT dividends are tax-free. This quantifies the income tax relief, the CGT deferred or saved, and the net cost after relief. These are higher-risk investments and relief is withdrawn if the shares are not held for the minimum period — the adviser confirms the company and shares qualify.
- Authority: [Income Tax Act 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT)](https://www.legislation.gov.uk/ukpga/2007/3/part/5) (in_force)
- PASS — calculator registered (strategy.venture_capital_investment)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (702 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (medium)

### 67. Business Asset Disposal Relief  
`cgt-business-asset-disposal-relief` — property_taxes — risk **settled**, timeframe short
> On a qualifying disposal of all or part of a trading business, or of shares in a personal trading company, gains up to a 1,000,000 lifetime limit are taxed at a reduced flat CGT rate (14% for 2025/26) instead of the standard 18%/24%. The qualifying conditions — a two-year minimum ownership period and, for shares, a 5% personal-company holding — must be met throughout that period. Gains above the lifetime limit are taxed at the normal rate, so the relief is worth up to ten percentage points on the first million pounds of qualifying gains.
- Authority: [Taxation of Chargeable Gains Act 1992 ss.169H-169S](https://www.legislation.gov.uk/ukpga/1992/12/section/169H) (in_force)
- Authority: [Taxation of Chargeable Gains Act 1992 ss.1H-1K](https://www.legislation.gov.uk/ukpga/1992/12/section/1H) (in_force)
- PASS — calculator registered (strategy.cgt_business_asset_disposal_relief)
- PASS — adapter registered
- PASS — has legal authorities (2 cited)
- PASS — plain-English explanation present (543 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 68. Lettings relief (shared-occupancy let)  
`cgt-lettings-relief` — property_taxes — risk **settled**, timeframe short
> Where the owner lets part of their only or main residence to a tenant while continuing to live in another part, lettings relief reduces the gain on the let portion by the lowest of that letting gain, the private residence relief due, and a 40,000 cap. Since 6 April 2020 the relief is available only for periods of shared occupancy with the tenant — the former relief for letting a property after moving out has been withdrawn.
- Authority: [Taxation of Chargeable Gains Act 1992 s.223B](https://www.legislation.gov.uk/ukpga/1992/12/section/223B) (in_force)
- Authority: [Taxation of Chargeable Gains Act 1992 ss.1H-1K](https://www.legislation.gov.uk/ukpga/1992/12/section/1H) (in_force)
- Authority: [Taxation of Chargeable Gains Act 1992 ss.222-223](https://www.legislation.gov.uk/ukpga/1992/12/section/222) (in_force)
- PASS — calculator registered (strategy.cgt_lettings_relief)
- PASS — adapter registered
- PASS — has legal authorities (3 cited)
- PASS — plain-English explanation present (427 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 69. Private residence relief on property disposal  
`cgt-ppr-relief` — property_taxes — risk **settled**, timeframe short
> Gains on a property that has at some time been the owner's only or main residence are exempt for the periods of actual occupation plus the final nine months of ownership, apportioned over the total ownership period. Where a property was the main residence for part of the ownership, the relief often removes more of the gain than clients expect — and the occupation history should be evidenced before disposal.
- Authority: [Taxation of Chargeable Gains Act 1992 ss.1H-1K](https://www.legislation.gov.uk/ukpga/1992/12/section/1H) (in_force)
- Authority: [Taxation of Chargeable Gains Act 1992 ss.222-223](https://www.legislation.gov.uk/ukpga/1992/12/section/222) (in_force)
- PASS — calculator registered (strategy.cgt_ppr_relief)
- PASS — adapter registered
- PASS — has legal authorities (2 cited)
- PASS — plain-English explanation present (410 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 70. Spousal transfer before disposal  
`cgt-spousal-transfer-before-disposal` — property_taxes — risk **settled**, timeframe short
> Transfers between spouses or civil partners are at no gain/no loss, so a half share transferred before an arm's-length disposal uses both annual exempt amounts and both basic-rate bands. Since 6 April 2023 (F(No.2)A 2023 s.41) this treatment also covers separated couples until the end of the third tax year after the tax year of separation, and without time limit under a formal divorce agreement or court order. The transfer must be an outright gift of beneficial ownership made before any unconditional contract to sell exists.
- Authority: [Taxation of Chargeable Gains Act 1992 s.58](https://www.legislation.gov.uk/ukpga/1992/12/section/58) (in_force)
- Authority: [Taxation of Chargeable Gains Act 1992 ss.1H-1K](https://www.legislation.gov.uk/ukpga/1992/12/section/1H) (in_force)
- PASS — calculator registered (strategy.cgt_spousal_transfer_before_disposal)
- PASS — adapter registered
- PASS — has legal authorities (2 cited)
- PASS — plain-English explanation present (530 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 71. Timing of disposals across tax years  
`cgt-timing-of-disposals` — property_taxes — risk **settled**, timeframe short
> Where a divisible holding such as shares or fund units stands at a gain larger than the annual exempt amount, selling it in two tranches across two tax years uses two years' exemptions (and two basic-rate bands) instead of one, cutting the total CGT. A single indivisible asset such as one property cannot be split this way. Quantifies the saving from spreading the disposal.
- Authority: [Taxation of Chargeable Gains Act 1992 ss.1H-1K](https://www.legislation.gov.uk/ukpga/1992/12/section/1H) (in_force)
- PASS — calculator registered (strategy.cgt_timing_of_disposals)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (375 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 72. LBTT on a lease (Scotland)  
`lbtt-lease-npv` — property_taxes — risk **settled**, timeframe short
> Quantifies the LBTT due on the grant of a lease in Scotland. The rent is charged on its net present value over the term, discounted at 3.5%, with 0% up to 150,000 of NPV, 1% to 2,000,000 and 2% above. Scotland uniquely requires the tenant to submit LBTT lease reviews every three years, which can change the tax as rents are revised.
- Authority: [Land and Buildings Transaction Tax (Scotland) Act 2013 s.24](https://www.legislation.gov.uk/asp/2013/11/section/24) (in_force)
- PASS — calculator registered (strategy.lbtt_lease_npv)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (333 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 73. LBTT on non-residential purchase (Scotland)  
`lbtt-non-residential-purchase` — property_taxes — risk **settled**, timeframe short
> Quantifies the LBTT on a planned non-residential freehold purchase in Scotland. Commercial rates run in bands (0% to 150,000, 1% to 250,000, 5% above) — a lower middle band than the English SDLT — with no Additional Dwelling Supplement and no first-time buyer relief on non-residential property.
- Authority: [Land and Buildings Transaction Tax (Scotland) Act 2013 s.24](https://www.legislation.gov.uk/asp/2013/11/section/24) (in_force)
- PASS — calculator registered (strategy.lbtt_non_residential_purchase)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (295 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 74. LBTT on planned property purchase (Scotland)  
`lbtt-purchase-planning` — property_taxes — risk **settled**, timeframe short
> Quantifies Land and Buildings Transaction Tax on a planned Scottish residential purchase, including the 8% Additional Dwelling Supplement on the whole price where a second dwelling is bought, and first-time buyer relief, which raises the nil-rate band to 175,000 and is worth up to 600. Scotland sets its own rates and bands, so the English SDLT figures do not apply north of the border.
- Authority: [Land and Buildings Transaction Tax (Scotland) Act 2013 s.24](https://www.legislation.gov.uk/asp/2013/11/section/24) (in_force)
- PASS — calculator registered (strategy.lbtt_purchase_planning)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (387 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 75. LTT on a non-residential lease (Wales)  
`ltt-lease-npv` — property_taxes — risk **settled**, timeframe short
> Quantifies the LTT due on the grant of a non-residential lease in Wales. The rent is charged on its net present value over the term, discounted at 3.5%, with 0% up to 225,000 of NPV, 1% to 2,000,000 and 2% above. Wales's higher nil-rate threshold means a lease is often cheaper than the equivalent English SDLT. Residential lease rent is not charged.
- Authority: [Land Transaction Tax and Anti-avoidance of Devolved Taxes (Wales) Act 2017 s.24](https://www.legislation.gov.uk/anaw/2017/1/section/24) (in_force)
- PASS — calculator registered (strategy.ltt_lease_npv)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (350 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 76. LTT on non-residential purchase (Wales)  
`ltt-non-residential-purchase` — property_taxes — risk **settled**, timeframe short
> Quantifies the LTT on a planned non-residential freehold purchase in Wales. Commercial rates run in bands (0% to 225,000, 1% to 250,000, 5% to 1,000,000, 6% above), so the Welsh charge has a higher nil-rate threshold but a top band the other regimes lack. There is no surcharge or first-time buyer relief on non-residential property.
- Authority: [Land Transaction Tax and Anti-avoidance of Devolved Taxes (Wales) Act 2017 s.24](https://www.legislation.gov.uk/anaw/2017/1/section/24) (in_force)
- PASS — calculator registered (strategy.ltt_non_residential_purchase)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (333 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 77. LTT on planned property purchase (Wales)  
`ltt-purchase-planning` — property_taxes — risk **settled**, timeframe short
> Quantifies Land Transaction Tax on a planned Welsh residential purchase. Wales applies a separate set of higher-rate bands to additional dwellings rather than a flat surcharge, and has no first-time buyer relief; the main residential nil-rate band runs to 225,000. The devolved rates differ from both English SDLT and Scottish LBTT, so the property's jurisdiction governs the charge.
- Authority: [Land Transaction Tax and Anti-avoidance of Devolved Taxes (Wales) Act 2017 s.24](https://www.legislation.gov.uk/anaw/2017/1/section/24) (in_force)
- PASS — calculator registered (strategy.ltt_purchase_planning)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (383 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 78. SDLT on a non-residential lease (England/NI)  
`sdlt-lease-npv` — property_taxes — risk **settled**, timeframe short
> Quantifies the SDLT due on the grant of a non-residential lease in England or Northern Ireland. The rent is charged on its net present value over the term, discounted at 3.5%, with 0% up to 150,000 of NPV, 1% to 5,000,000 and 2% above. Any lease premium is charged separately at the freehold rates and is not included here.
- Authority: [Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)](https://www.legislation.gov.uk/ukpga/2003/14/section/55) (in_force)
- Authority: [Finance Act 2003 Sch 5 (amount of tax chargeable: rent)](https://www.legislation.gov.uk/ukpga/2003/14/schedule/5) (in_force)
- PASS — calculator registered (strategy.sdlt_lease_npv)
- PASS — adapter registered
- PASS — has legal authorities (2 cited)
- PASS — plain-English explanation present (323 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 79. SDLT on non-residential purchase (England/NI)  
`sdlt-non-residential-purchase` — property_taxes — risk **settled**, timeframe short
> Quantifies the SDLT on a planned non-residential or mixed-use freehold purchase in England or Northern Ireland. Commercial rates run in bands (0% to 150,000, 2% to 250,000, 5% above) and — unlike residential — carry no additional-dwelling surcharge and no first-time buyer relief. A mixed-use property is charged wholly at these non-residential rates.
- Authority: [Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)](https://www.legislation.gov.uk/ukpga/2003/14/section/55) (in_force)
- PASS — calculator registered (strategy.sdlt_non_residential_purchase)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (351 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 80. SDLT on planned residential property purchase (England/NI)  
`sdlt-purchase-planning` — property_taxes — risk **settled**, timeframe short
> Quantifies the SDLT on a planned residential purchase in England or Northern Ireland, including the 5% additional-dwellings surcharge and first-time buyers' relief. Where the purchase replaces a main residence sold within three years, the surcharge is recoverable — timing the sale matters as much as the price. Scotland (LBTT) and Wales (LTT) set their own rates.
- Authority: [Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)](https://www.legislation.gov.uk/ukpga/2003/14/section/55) (in_force)
- Authority: [Finance Act 2003 Sch 4ZA (higher rates for additional dwellings)](https://www.legislation.gov.uk/ukpga/2003/14/schedule/4ZA) (in_force)
- Authority: [Finance Act 2003 Sch 6ZA](https://www.legislation.gov.uk/ukpga/2003/14/schedule/6ZA) (in_force)
- PASS — calculator registered (strategy.sdlt_purchase_planning)
- PASS — adapter registered
- PASS — has legal authorities (3 cited)
- PASS — plain-English explanation present (364 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

---
## C. Authority registry (every citation, verified fetchable)

### 81. [Capital Allowances Act 2001 s.51A](https://www.legislation.gov.uk/ukpga/2001/2/section/51A) — Statute
> Entitlement to the annual investment allowance: 100% relief on qualifying expenditure on plant and machinery up to the AIA maximum for the chargeable period. Expenditure above the maximum is relieved through the capital allowance pools at the writing-down allowance rates (s.56).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2001/2/section/51A)
- PASS — primary source fetched by watcher (5,535 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 82. [Capital Allowances Act 2001 ss.33A-33B & s.187A (integral features / fixtures)](https://www.legislation.gov.uk/ukpga/2001/2/section/33A) — Statute
> Expenditure on integral features and fixtures within a commercial building (electrical, heating, water, lifts, etc.) qualifies for plant and machinery capital allowances — the Annual Investment Allowance up to its limit then the special-rate writing-down allowance. On a second-hand building the fixtures claim depends on the s.187A pooling/fixed-value requirements being met by the seller.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2001/2/section/33A)
- PASS — primary source fetched by watcher (4,405 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 83. [Corporation Tax Act 2009 Part 13 (as amended, merged R&D scheme)](https://www.legislation.gov.uk/ukpga/2009/4/part/13) — Statute
> Relief for expenditure on research and development. For accounting periods beginning on or after 1 April 2024 the merged scheme gives a 20% taxable 'above the line' expenditure credit (RDEC) on qualifying R&D spend; the credit is itself chargeable to corporation tax, so the net benefit is 20% less tax. Loss-making R&D-intensive SMEs (qualifying R&D at least 30% of total expenditure) instead claim enhanced support with a 14.5% payable credit.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2009/4/part/13)
- PASS — primary source fetched by watcher (144,612 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 84. [Corporation Tax Act 2009 s.54](https://www.legislation.gov.uk/ukpga/2009/4/section/54) — Statute
> No deduction is allowed for expenses not incurred wholly and exclusively for the purposes of the trade — the condition governing deductibility of employer pension contributions as part of a reasonable remuneration package.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2009/4/section/54)
- PASS — primary source fetched by watcher (1,518 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 85. [Corporation Tax Act 2010 Part 3A (ss.18A-18M)](https://www.legislation.gov.uk/ukpga/2010/4/part/3A) — Statute
> Small profits rate and marginal relief on corporation tax profits, reintroduced with effect from 1 April 2023 by Finance Act 2021 s.7 and Sch.1.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2010/4/part/3A)
- PASS — primary source fetched by watcher (19,154 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 86. [Corporation Tax Act 2010 Part 5 (ss.97-188)](https://www.legislation.gov.uk/ukpga/2010/4/part/5) — Statute
> Group relief: a company may surrender its current-period trading losses (and certain other amounts) to another company in the same group, which claims them against its total profits of the corresponding period. Companies are in a group for this purpose where one is a 75% subsidiary of the other, or both are 75% subsidiaries of a third (s.152). The claimant's profits are reduced by the amount surrendered, so the loss is relieved at the claimant's marginal rate.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2010/4/part/5)
- PASS — primary source fetched by watcher (131,542 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 87. [Corporation Tax Act 2010 Part 8A (Patent Box)](https://www.legislation.gov.uk/ukpga/2010/4/part/8A) — Statute
> A company may elect for profits attributable to patented inventions (and certain other qualifying IP) to be taxed at an effective corporation-tax rate of 10%, delivered by a deduction from those profits. Post-2016 entrants must meet the modified nexus requirement linking the relief to the company's own R&D.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2010/4/part/8A)
- PASS — primary source fetched by watcher (170,307 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 88. [Corporation Tax Act 2010 s.455](https://www.legislation.gov.uk/ukpga/2010/4/section/455) — Statute
> Charge to tax where a close company makes a loan or advance to a participator (e.g. a director-shareholder): the company pays tax on the amount outstanding at the rate in s.455, currently 33.75%. The charge falls due 9 months and 1 day after the end of the accounting period, and is repaid under s.458 when the loan is repaid or written off.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2010/4/section/455)
- PASS — primary source fetched by watcher (3,346 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 89. [Finance Act 2003 s.55 (SDLT rate tables: s.55(1A) Table A residential; s.55(1B) Table B non-residential/mixed)](https://www.legislation.gov.uk/ukpga/2003/14/section/55) — Statute
> Amount of stamp duty land tax chargeable: s.55 sets the rates by reference to Table A (residential property) and, under s.55(1B), Table B (non-residential or mixed-use property). The residential additional-dwelling surcharge (Sch 4ZA) and first-time buyer relief (Sch 6ZA), and the lease-rent charge on net present value (Sch 5), sit in the referenced schedules.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2003/14/section/55)
- PASS — primary source fetched by watcher (10,845 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 90. [Finance Act 2003 Sch 4ZA (higher rates for additional dwellings)](https://www.legislation.gov.uk/ukpga/2003/14/schedule/4ZA) — Statute
> Schedule 4ZA imposes the higher rates of SDLT on purchases of additional residential dwellings (and dwellings bought by companies), refundable where a former main residence is replaced within the time limit. It applies to residential property only, not to non-residential or mixed-use transactions.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2003/14/schedule/4ZA)
- PASS — primary source fetched by watcher (38,202 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 91. [Finance Act 2003 Sch 5 (amount of tax chargeable: rent)](https://www.legislation.gov.uk/ukpga/2003/14/schedule/5) — Statute
> The SDLT charge on the rent under a lease is calculated on the net present value of the rent payable over the term, discounted at the statutory rate, with the non-residential 0%/1%/2% NPV bands. Any lease premium is charged separately under s.55.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2003/14/schedule/5)
- PASS — primary source fetched by watcher (11,750 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 92. [Finance Act 2003 Sch 6ZA](https://www.legislation.gov.uk/ukpga/2003/14/schedule/6ZA) — Statute
> Relief for first-time buyers: no SDLT up to the relief threshold and a reduced rate above it, unavailable where the price exceeds the cap.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2003/14/schedule/6ZA)
- PASS — primary source fetched by watcher (10,677 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 93. [Finance Act 2004 s.190](https://www.legislation.gov.uk/ukpga/2004/12/section/190) — Statute
> The maximum amount of relief for an individual's pension contributions in a tax year is the greater of the basic amount (£3,600) and the individual's relevant UK earnings chargeable to income tax for that year.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2004/12/section/190)
- PASS — primary source fetched by watcher (3,902 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 94. [Finance Act 2004 s.228](https://www.legislation.gov.uk/ukpga/2004/12/section/228) — Statute
> The annual allowance for tax-relieved pension savings, and (via s.228ZA, inserted by Finance (No.2) Act 2015) its tapering for high-income individuals.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2004/12/section/228)
- PASS — primary source fetched by watcher (3,094 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 95. [IHTA 1984 s.3 (as to be amended from 6 April 2027, Finance Bill 2025-26)](https://www.legislation.gov.uk/ukpga/1984/51/section/3) — Statute
> Announced at Autumn Budget 2024: from 6 April 2027 most unused pension funds and death benefits will be brought within the value of a person's estate for inheritance tax, reversing the current position where they normally pass outside the estate. This is a forward-looking planning point subject to final legislation — modelled here as a clearly-flagged borderline projection.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/3)
- PASS — primary source fetched by watcher (1,918 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 96. [Income Tax Act 2007 Part 5 (EIS), Part 5A (SEIS), Part 6 (VCT)](https://www.legislation.gov.uk/ukpga/2007/3/part/5) — Statute
> Income tax relief for venture-capital investment: the Enterprise Investment Scheme gives relief at 30% on up to £1,000,000 a year (£2,000,000 for knowledge-intensive companies), the Seed Enterprise Investment Scheme 50% on up to £200,000, and Venture Capital Trusts 30% on up to £200,000. Relief cannot exceed the investor's income tax liability. EIS also allows unlimited deferral of a chargeable gain reinvested in the shares (TCGA 1992 Sch 5B); SEIS exempts 50% of a reinvested gain (Sch 5BB); VCT dividends and disposals are tax-free. Gains on EIS/SEIS shares held for the minimum period are themselves exempt.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2007/3/part/5)
- PASS — primary source fetched by watcher (224,226 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 97. [Income Tax Act 2007 s.13A](https://www.legislation.gov.uk/ukpga/2007/3/section/13A) — Statute
> Dividend nil rate: the dividend allowance against which dividend income is charged at 0%, introduced by Finance Act 2016 s.5.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2007/3/section/13A)
- PASS — primary source fetched by watcher (3,513 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 98. [Income Tax Act 2007 s.35](https://www.legislation.gov.uk/ukpga/2007/3/section/35) — Statute
> Entitlement to personal allowance for those born after 5 April 1948, and its reduction under section 35(2) where adjusted net income exceeds the income limit.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2007/3/section/35)
- PASS — primary source fetched by watcher (1,915 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 99. [Income Tax Act 2007 s.414](https://www.legislation.gov.uk/ukpga/2007/3/section/414) — Statute
> Gift Aid: a qualifying donation is treated as made after deduction of basic-rate income tax; the individual's basic-rate limit (and higher-rate limit) are increased by the grossed-up amount, giving relief to higher and additional-rate taxpayers. The grossed-up gift also reduces adjusted net income for the personal-allowance taper.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2007/3/section/414)
- PASS — primary source fetched by watcher (2,244 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 100. [Income Tax Act 2007 ss.55A-55E](https://www.legislation.gov.uk/ukpga/2007/3/section/55A) — Statute
> Transferable tax allowance for married couples and civil partners (Marriage Allowance), inserted by Finance Act 2014 s.11.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2007/3/section/55A)
- PASS — primary source fetched by watcher (1,632 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 101. [Income Tax (Trading and Other Income) Act 2005 s.694](https://www.legislation.gov.uk/ukpga/2005/5/section/694) — Statute
> Income arising from investments held in an individual savings account (ISA) is exempt from income tax, subject to the ISA regulations. The annual subscription limit is set by those regulations (SI 1998/1870); gains on ISA investments are likewise exempt from capital gains tax (TCGA 1992 s.151).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2005/5/section/694)
- PASS — primary source fetched by watcher (1,752 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 102. [Income Tax (Trading and Other Income) Act 2005 s.850](https://www.legislation.gov.uk/ukpga/2005/5/section/850) — Statute
> A partnership is transparent for tax: each partner is treated as carrying on the trade and is taxed on their share of the firm's profit determined by the firm's profit-sharing arrangement, as trading income (income tax and Class 4 NIC). The profit-sharing ratio must reflect the commercial arrangement between the partners; HMRC can challenge allocations made to divert income for tax advantage (see also the settlements rules, ITTOIA 2005 Part 5 Ch 5).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2005/5/section/850)
- PASS — primary source fetched by watcher (2,291 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 103. [Income Tax (Trading and Other Income) Act 2005 ss.272A-274C](https://www.legislation.gov.uk/ukpga/2005/5/section/272A) — Statute
> Costs of a dwelling-related loan (mortgage interest and other finance costs) are not deductible in computing the profits of a residential property business. Instead the individual is entitled to a basic-rate tax reduction (s.274A) of 20% of the lower of the finance costs, the property business profits, and the individual's adjusted total income above the personal allowance. Fully in force from 2020/21 (phased in from 2017/18 by F(No.2)A 2015 s.24). Companies are unaffected — they still deduct the interest in full.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2005/5/section/272A)
- PASS — primary source fetched by watcher (3,258 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 104. [Inheritance Tax Act 1984 s.18](https://www.legislation.gov.uk/ukpga/1984/51/section/18) — Statute
> Transfers between spouses or civil partners are exempt transfers (unlimited where the transferee is UK-domiciled).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/18)
- PASS — primary source fetched by watcher (3,808 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 105. [Inheritance Tax Act 1984 s.19](https://www.legislation.gov.uk/ukpga/1984/51/section/19) — Statute
> Annual exemption: transfers of value up to £3,000 in a tax year are exempt; unused exemption carries forward one year.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/19)
- PASS — primary source fetched by watcher (1,844 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 106. [Inheritance Tax Act 1984 s.3A](https://www.legislation.gov.uk/ukpga/1984/51/section/3A) — Statute
> A potentially exempt transfer becomes an exempt transfer if the transferor survives seven years; otherwise it is a chargeable transfer.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/3A)
- PASS — primary source fetched by watcher (6,263 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 107. [Inheritance Tax Act 1984 s.5 (meaning of estate)](https://www.legislation.gov.uk/ukpga/1984/51/section/5) — Statute
> A person's estate is the aggregate of all the property to which they are beneficially entitled at death. Property held in a properly constituted trust to which the deceased was not beneficially entitled — such as the proceeds of a life policy written in trust — does not form part of the estate, so the proceeds pass free of inheritance tax and can fund the estate's IHT bill.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/5)
- PASS — primary source fetched by watcher (4,037 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 108. [Inheritance Tax Act 1984 s.7 and Sch 1](https://www.legislation.gov.uk/ukpga/1984/51/section/7) — Statute
> Rates of tax, including taper relief under s.7(4) reducing the tax charged on chargeable transfers made three to seven years before death.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/7)
- PASS — primary source fetched by watcher (3,992 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 109. [Inheritance Tax Act 1984 s.8A](https://www.legislation.gov.uk/ukpga/1984/51/section/8A) — Statute
> Transfer of unused nil-rate band between spouses and civil partners: the survivor's nil-rate band is increased by the unused percentage.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/8A)
- PASS — primary source fetched by watcher (3,172 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 110. [Inheritance Tax Act 1984 s.8D](https://www.legislation.gov.uk/ukpga/1984/51/section/8D) — Statute
> Residence nil-rate amount where a qualifying residential interest is closely inherited; tapered by £1 for every £2 the estate exceeds the taper threshold.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/8D)
- PASS — primary source fetched by watcher (3,682 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 111. [Inheritance Tax Act 1984 s.8G](https://www.legislation.gov.uk/ukpga/1984/51/section/8G) — Statute
> Transfer of any unused residence nil-rate amount to a surviving spouse or civil partner, by claim, mirroring the s.8A transfer of the ordinary nil-rate band.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/8G)
- PASS — primary source fetched by watcher (2,334 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 112. [Inheritance Tax Act 1984 Sch 1A](https://www.legislation.gov.uk/ukpga/1984/51/schedule/1A) — Statute
> Where at least 10% of the baseline amount passes to charity, inheritance tax is charged at 36% instead of 40%.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/schedule/1A)
- PASS — primary source fetched by watcher (8,527 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 113. [Inheritance Tax Act 1984 ss.103-114 (BPR) and ss.115-124C (APR)](https://www.legislation.gov.uk/ukpga/1984/51/part/V/chapter/I) — Statute
> Business property relief reduces the value transferred by relevant business property by 100% (unquoted trading businesses and unquoted shares) or 50% (controlling quoted holdings, certain land and machinery). Agricultural property relief similarly relieves the agricultural value of qualifying farmland at 100% or 50%. From 6 April 2026 the 100% rate is limited to a combined £1,000,000 of qualifying business and agricultural property, with 50% relief on value above that cap (Finance Act 2025).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/part/V/chapter/I)
- PASS — primary source fetched by watcher (34,554 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 114. [Inheritance Tax Act 1984 ss.58-69 (relevant property)](https://www.legislation.gov.uk/ukpga/1984/51/part/III/chapter/III) — Statute
> Property in a relevant-property trust (most discretionary and, since 2006, most lifetime trusts) is subject to its own IHT charges outside a person's estate: a lifetime entry charge at half the death rate (20%) on value settled above the available nil-rate band; a ten-year anniversary charge (s.64) of up to 6% of the value above the band, being 30% of the lifetime effective rate; and a proportionate exit charge (s.65) when property leaves the trust, by reference to the last ten-year rate and the complete quarters since the last anniversary.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/part/III/chapter/III)
- PASS — primary source fetched by watcher (133,938 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 115. [Jones v Garnett (Arctic Systems) [2007] UKHL 35](https://www.bailii.org/uk/cases/UKHL/2007/35.html) — Court Judgment
> The House of Lords held that the ordinary-share arrangement between spouses was a settlement within ITTOIA 2005 s.620, but fell within the s.626 outright-gifts-between-spouses exemption because the shares were not wholly or substantially a right to income. Dividend income splitting through ordinary shares held by a spouse therefore stands, subject to the arrangement involving full ordinary shares rather than income-only rights.
- PASS — canonical URI recorded (https://www.bailii.org/uk/cases/UKHL/2007/35.html)
- PASS — primary source fetched by watcher (79,967 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 116. [Land and Buildings Transaction Tax (Scotland) Act 2013 s.24](https://www.legislation.gov.uk/asp/2013/11/section/24) — Statute
> Empowers the Scottish Ministers to set, by order, the tax bands and percentage rates for Land and Buildings Transaction Tax, including a nil-rate band for residential transactions; the Additional Dwelling Supplement (Schedule 2A) and first-time buyer relief operate alongside these rates.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/asp/2013/11/section/24)
- PASS — primary source fetched by watcher (1,850 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 117. [Land Transaction Tax and Anti-avoidance of Devolved Taxes (Wales) Act 2017 s.24](https://www.legislation.gov.uk/anaw/2017/1/section/24) — Statute
> Empowers the Welsh Ministers to specify, by regulations, the tax bands and percentage rates for Land Transaction Tax across three categories: residential, higher-rates residential (additional properties), and non-residential transactions.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/anaw/2017/1/section/24)
- PASS — primary source fetched by watcher (4,020 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 118. [Social Security Contributions and Benefits Act 1992 s.15](https://www.legislation.gov.uk/ukpga/1992/4/section/15) — Statute
> Class 4 National Insurance contributions on profits of a trade, profession or vocation carried on by a self-employed earner.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/4/section/15)
- PASS — primary source fetched by watcher (14,848 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 119. [Social Security Contributions and Benefits Act 1992 s.6](https://www.legislation.gov.uk/ukpga/1992/4/section/6) — Statute
> Liability for Class 1 primary and secondary National Insurance contributions on earnings from employment.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/4/section/6)
- PASS — primary source fetched by watcher (11,910 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 120. [Taxation of Chargeable Gains Act 1992 s.162](https://www.legislation.gov.uk/ukpga/1992/12/section/162) — Statute
> Incorporation relief: where a person transfers a business as a going concern, together with the whole of its assets (other than cash), to a company wholly or partly in exchange for shares, the chargeable gain on the transferred assets is rolled into the base cost of the shares to the extent the consideration is shares. Whether a property letting activity is a 'business' for s.162 depends on the degree of activity (Ramsay v HMRC [2013] UKUT 226). The transfer is at market value and a company acquiring residential property pays SDLT including the additional-dwelling surcharge (and potentially ATED).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/12/section/162)
- PASS — primary source fetched by watcher (6,784 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 121. [Taxation of Chargeable Gains Act 1992 s.223B](https://www.legislation.gov.uk/ukpga/1992/12/section/223B) — Statute
> Additional relief where part of the dwelling-house is the individual's only or main residence and another part is let as residential accommodation: the let-portion gain is relieved by the lowest of that gain, the s.223 private residence relief, and 40,000. For disposals from 6 April 2020 the relief requires shared occupancy with the tenant.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/12/section/223B)
- PASS — primary source fetched by watcher (4,529 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 122. [Taxation of Chargeable Gains Act 1992 s.236H (Employee Ownership Trust)](https://www.legislation.gov.uk/ukpga/1992/12/section/236H) — Statute
> A disposal of shares in a trading company to an Employee Ownership Trust that acquires a controlling interest is treated as made on a no-gain/no-loss basis — the gain is fully exempt from capital gains tax — provided the qualifying conditions are met. Finance Act 2024/2025 tightened the rules (UK-resident trustees, former owners not to retain control, a longer clawback period and an independent valuation), which the adviser must confirm.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/12/section/236H)
- PASS — primary source fetched by watcher (9,703 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 123. [Taxation of Chargeable Gains Act 1992 s.58](https://www.legislation.gov.uk/ukpga/1992/12/section/58) — Statute
> Disposals between spouses or civil partners are on a no-gain/no-loss basis: while living together; where separated, until the end of the third tax year after the tax year of separation; and without time limit where made under a formal divorce/dissolution agreement or court order (as substituted by Finance (No.2) Act 2023 s.41 for disposals from 6 April 2023).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/12/section/58)
- PASS — primary source fetched by watcher (6,329 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 124. [Taxation of Chargeable Gains Act 1992 ss.169H-169S](https://www.legislation.gov.uk/ukpga/1992/12/section/169H) — Statute
> Business Asset Disposal Relief: a qualifying business disposal (s.169I) is charged to capital gains tax at the reduced rate in s.169N, subject to a 1,000,000 lifetime limit on qualifying gains. The reduced rate is 14% for disposals on or after 6 April 2025 (10% before that date; 18% from 6 April 2026).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/12/section/169H)
- PASS — primary source fetched by watcher (4,883 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 125. [Taxation of Chargeable Gains Act 1992 ss.1H-1K](https://www.legislation.gov.uk/ukpga/1992/12/section/1H) — Statute
> Rates of capital gains tax by reference to unused basic-rate band, and the annual exempt amount (s.1K).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/12/section/1H)
- PASS — primary source fetched by watcher (7,522 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 126. [Taxation of Chargeable Gains Act 1992 ss.222-223](https://www.legislation.gov.uk/ukpga/1992/12/section/222) — Statute
> Relief on disposal of a dwelling-house that is or has been the individual's only or main residence; s.223(2) treats the final nine months of ownership as qualifying in any event.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/12/section/222)
- PASS — primary source fetched by watcher (14,352 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

---
## Sign-off

By approving, the reviewing professional confirms they have read each
item, spot-checked values against the linked primary sources where
judgement required it, and accept editorial responsibility for this
rule-base content under §5.6 of the architecture document.

| Item range | Reviewer | Decision | Date |
|---|---|---|---|
| 1–126 | kfrem (editor / first reviewer) | Approved with exceptions — SDLT items #39 & #40 corrected | 2026-07-06 |
| 1–126 | Paul Mixer (independent second reviewer) | Approved, subject to the two SDLT corrections (now applied) | 2026-07-07 |

**Four-eyes review complete.** Both reviewers independently flagged the same two
defects — the non-residential SDLT strategies (#39 lease-NPV, #40 non-residential
purchase) cited the residential-surcharge Schedule 4ZA instead of s.55(1B) Table B
and Schedule 5. Both citations have been corrected in the seed and re-verified; the
underlying calculators were confirmed unaffected (they consume only the
non-residential / lease-NPV bands, never the residential tables). Orphaned
authorities left by earlier citation edits were removed (50 → 46). Non-blocking
next-cycle refinements are logged in [`EDITORIAL_SIGNOFF.md`](EDITORIAL_SIGNOFF.md).

The only remaining go-live action is a human marking the `RuleBaseRelease` as
**Released** in `/admin/` — a governance step Claude does not perform.
