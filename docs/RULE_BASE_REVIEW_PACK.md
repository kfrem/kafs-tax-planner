# Rule-base review pack — editorial sign-off

Generated 05 July 2026. Machine pre-check: **0 failed checks** across 18 parameters, 10 strategies, 25 authorities.

**How to approve:** read each numbered item; the primary source is one
click away. Reply YES to approve all items, or list the item numbers you
question. Your approval is recorded as the §5.6 editorial review on every
rule-base release, with your name and the date.

---
## A. Tax parameters (the rates and thresholds the engine uses)

### 1. Corporation tax rates and marginal relief  
`corporation_tax.rates` — corporation_tax — release 2025.1
- main_rate: **0.25**
- main_rate_limit: **250,000**
- small_profits_rate: **0.19**
- small_profits_limit: **50,000**
- marginal_relief_fraction: **0.015**
- PASS — consumed by a registered calculator (corporation_tax, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (corporation_tax, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 50,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 s.55 and Sch 4ZA; Inheritance Tax Act 1984 s.8D
- Source cross-reference: 250,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 s.55 and Sch 4ZA

### 2. Employer (secondary) Class 1 NIC  
`national_insurance.employer_class1` — corporation_tax — release 2025.1
- rate: **0.15**
- secondary_threshold: **5,000**
- PASS — consumed by a registered calculator (employer_class1_nic, strategy.salary_dividend_mix, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (employer_class1_nic, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 5,000 appears in: Finance Act 2003 s.55 and Sch 4ZA; Inheritance Tax Act 1984 s.8D; Jones v Garnett (Arctic Systems) [2007] UKHL 35

### 3. Employment Allowance  
`national_insurance.employment_allowance` — corporation_tax — release 2025.1
- amount: **10,500**
- PASS — consumed by a registered calculator (employer_class1_nic, strategy.salary_dividend_mix, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (employer_class1_nic, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 10,500 appears in: National Insurance Contributions Act 2014 s.1

### 4. IHT gift exemptions and PET taper relief  
`iht.gift_exemptions` — inheritance_tax — release 2025.2
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
- Source cross-reference: 250 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 s.55 and Sch 4ZA
- Source cross-reference: 3,000 appears in: Inheritance Tax Act 1984 s.19

### 5. IHT nil-rate band (frozen through 2029/30)  
`iht.nil_rate_band` — inheritance_tax — release 2025.2
- amount: **325,000**
- PASS — consumed by a registered calculator (iht_estate_liability, strategy.iht_spousal_transfer_nil_rate_bands, strategy.iht_lifetime_gifting, strategy.iht_charitable_legacy_reduced_rate)
- PASS — figure exercised by golden test cases (iht_estate_liability, strategy.iht_lifetime_gifting)
- PASS — belongs to a released rule-base version (2025.2)

### 6. IHT rates: death, reduced charitable, lifetime CLT  
`iht.rates` — inheritance_tax — release 2025.2
- death_rate: **0.4**
- lifetime_clt_rate: **0.2**
- reduced_charity_rate: **0.36**
- charity_baseline_fraction: **0.1**
- PASS — consumed by a registered calculator (iht_estate_liability, strategy.iht_spousal_transfer_nil_rate_bands, strategy.iht_lifetime_gifting, strategy.iht_charitable_legacy_reduced_rate)
- PASS — figure exercised by golden test cases (iht_estate_liability, strategy.iht_lifetime_gifting)
- PASS — belongs to a released rule-base version (2025.2)

### 7. IHT residence nil-rate band and taper  
`iht.residence_nil_rate_band` — inheritance_tax — release 2025.2
- amount: **175,000**
- taper_rate: **0.5**
- taper_threshold: **2,000,000**
- PASS — consumed by a registered calculator (iht_estate_liability, strategy.iht_spousal_transfer_nil_rate_bands, strategy.iht_lifetime_gifting, strategy.iht_charitable_legacy_reduced_rate)
- PASS — figure exercised by golden test cases (iht_estate_liability, strategy.iht_lifetime_gifting)
- PASS — belongs to a released rule-base version (2025.2)
- Source cross-reference: 175,000 appears in: Inheritance Tax Act 1984 s.8D
- Source cross-reference: 2,000,000 appears in: Inheritance Tax Act 1984 s.8D

### 8. Dividend allowance  
`dividend_tax.allowance` — personal_income_tax — release 2025.1
- amount: **500**
- PASS — consumed by a registered calculator (dividend_tax, combined_personal_tax, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (dividend_tax, combined_personal_tax, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 500 appears in: Finance Act 2003 Sch 6ZA; Finance Act 2003 s.55 and Sch 4ZA; Income Tax Act 2007 s.13A

### 9. Dividend tax bands  
`dividend_tax.bands` — personal_income_tax — release 2025.1
- bands:
  - rate: **0.0875**
  - upper: **37,700**
  - rate: **0.3375**
  - upper: **125,140**
  - rate: **0.3935**
  - upper: **None**
- PASS — consumed by a registered calculator (dividend_tax, combined_personal_tax, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (dividend_tax, combined_personal_tax, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 37,700 appears in: Income Tax Act 2007 s.10

### 10. Income tax bands (non-savings, non-dividend)  
`income_tax.bands` — personal_income_tax — release 2025.1
- bands:
  - rate: **0.2**
  - upper: **37,700**
  - rate: **0.4**
  - upper: **125,140**
  - rate: **0.45**
  - upper: **None**
- PASS — consumed by a registered calculator (income_tax_on_earned_income, combined_personal_tax, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade, cgt_liability, strategy.cgt_ppr_relief, strategy.cgt_spousal_transfer_before_disposal)
- PASS — figure exercised by golden test cases (income_tax_on_earned_income, combined_personal_tax, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade, cgt_liability)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 37,700 appears in: Income Tax Act 2007 s.10

### 11. Marriage Allowance transferable amount  
`income_tax.marriage_allowance` — personal_income_tax — release 2025.1
- transferable_amount: **1,260**
- PASS — consumed by a registered calculator (strategy.marriage_allowance_transfer)
- PASS — figure exercised by golden test cases (strategy.marriage_allowance_transfer)
- PASS — belongs to a released rule-base version (2025.1)

### 12. Personal Allowance  
`income_tax.personal_allowance` — personal_income_tax — release 2025.1
- amount: **12,570**
- taper_rate: **0.5**
- taper_threshold: **100,000**
- PASS — consumed by a registered calculator (income_tax_on_earned_income, combined_personal_tax, strategy.salary_dividend_mix, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade, strategy.marriage_allowance_transfer, cgt_liability, strategy.cgt_ppr_relief, strategy.cgt_spousal_transfer_before_disposal)
- PASS — figure exercised by golden test cases (income_tax_on_earned_income, combined_personal_tax, strategy.pension_annual_allowance_carry_forward, strategy.incorporation_vs_sole_trade, strategy.marriage_allowance_transfer, cgt_liability)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 12,570 appears in: Income Tax Act 2007 s.35; Social Security Contributions and Benefits Act 1992 s.15
- Source cross-reference: 100,000 appears in: Income Tax Act 2007 s.35; Inheritance Tax Act 1984 s.8D

### 13. Class 4 NIC (self-employed)  
`national_insurance.class4` — personal_income_tax — release 2025.1
- rate: **0.06**
- upper_rate: **0.02**
- lower_profits_limit: **12,570**
- upper_profits_limit: **50,270**
- PASS — consumed by a registered calculator (strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 12,570 appears in: Income Tax Act 2007 s.35; Social Security Contributions and Benefits Act 1992 s.15
- Source cross-reference: 50,270 appears in: Social Security Contributions and Benefits Act 1992 s.15

### 14. Employee Class 1 NIC  
`national_insurance.employee_class1` — personal_income_tax — release 2025.1
- rate: **0.08**
- upper_rate: **0.02**
- primary_threshold: **12,570**
- upper_earnings_limit: **50,270**
- PASS — consumed by a registered calculator (employee_class1_nic, strategy.salary_dividend_mix, strategy.incorporation_vs_sole_trade)
- PASS — figure exercised by golden test cases (employee_class1_nic, strategy.incorporation_vs_sole_trade)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 12,570 appears in: Income Tax Act 2007 s.35; Social Security Contributions and Benefits Act 1992 s.15
- Source cross-reference: 50,270 appears in: Social Security Contributions and Benefits Act 1992 s.15

### 15. Pension annual allowance and taper  
`pension.annual_allowance` — personal_income_tax — release 2025.1
- standard_amount: **60,000**
- minimum_tapered_amount: **10,000**
- taper_threshold_income: **200,000**
- taper_adjusted_income_limit: **260,000**
- PASS — consumed by a registered calculator (pension_available_annual_allowance, strategy.pension_annual_allowance_carry_forward)
- PASS — figure exercised by golden test cases (strategy.pension_annual_allowance_carry_forward)
- PASS — belongs to a released rule-base version (2025.1)
- Source cross-reference: 60,000 appears in: Finance Act 2004 s.228

### 16. CGT annual exempt amount  
`cgt.annual_exempt_amount` — property_taxes — release 2025.3
- amount: **3,000**
- PASS — consumed by a registered calculator (cgt_liability, strategy.cgt_ppr_relief, strategy.cgt_spousal_transfer_before_disposal)
- PASS — figure exercised by golden test cases (cgt_liability)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 3,000 appears in: Inheritance Tax Act 1984 s.19

### 17. CGT rates by asset class (lower = within basic band)  
`cgt.rates` — property_taxes — release 2025.3
- other:
  - lower: **0.18**
  - higher: **0.24**
- residential:
  - lower: **0.18**
  - higher: **0.24**
- PASS — consumed by a registered calculator (cgt_liability, strategy.cgt_ppr_relief, strategy.cgt_spousal_transfer_before_disposal)
- PASS — figure exercised by golden test cases (cgt_liability)
- PASS — belongs to a released rule-base version (2025.3)

### 18. SDLT residential bands, surcharge, FTB relief (England/NI)  
`sdlt.residential_bands` — property_taxes — release 2025.3
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
- PASS — consumed by a registered calculator (sdlt_residential, strategy.sdlt_purchase_planning)
- PASS — figure exercised by golden test cases (sdlt_residential)
- PASS — belongs to a released rule-base version (2025.3)
- Source cross-reference: 125,000 appears in: Finance Act 2003 s.55 and Sch 4ZA; Inheritance Tax Act 1984 s.8D
- Source cross-reference: 250,000 appears in: Corporation Tax Act 2010 Part 3A (ss.18A-18M); Finance Act 2003 s.55 and Sch 4ZA
- Source cross-reference: 300,000 appears in: Finance Act 2003 Sch 6ZA
- Source cross-reference: 500,000 appears in: Finance Act 2003 Sch 6ZA; Finance Act 2003 s.55 and Sch 4ZA
- Source cross-reference: 925,000 appears in: Finance Act 2003 s.55 and Sch 4ZA
- Source cross-reference: 1,500,000 appears in: Finance Act 2003 s.55 and Sch 4ZA

---
## B. Strategies (the planning advice, with legal basis)

### 19. Incorporation versus remaining a sole trader  
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

### 20. Salary/dividend extraction mix  
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

### 21. Charitable legacy and the 36% reduced rate  
`iht-charitable-legacy-reduced-rate` — inheritance_tax — risk **settled**, timeframe medium
> Where at least 10% of the baseline amount of the estate is left to charity, the whole taxable estate is charged at 36% rather than 40%. Because the charitable legacy is itself exempt, topping a smaller legacy up to the 10% threshold often costs the residuary beneficiaries far less than the legacy's face value, and in some estates makes them better off outright.
- Authority: [Inheritance Tax Act 1984 Sch 1A](https://www.legislation.gov.uk/ukpga/1984/51/schedule/1A) (in_force)
- PASS — calculator registered (strategy.iht_charitable_legacy_reduced_rate)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (363 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (medium)

### 22. Lifetime gifting: exemptions and potentially exempt transfers  
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

### 23. Spouse exemption and transferable nil-rate bands  
`iht-spousal-transfer-and-nil-rate-bands` — inheritance_tax — risk **settled**, timeframe long
> Transfers between spouses or civil partners are wholly exempt from inheritance tax, and any nil-rate band and residence nil-rate band unused on the first death transfers to the survivor. Leaving the estate to the surviving spouse defers all tax to the second death, where up to double both bands (currently £650,000 plus £350,000 where the home passes to direct descendants) shelter the combined estate. The transferred bands must be claimed by the survivor's personal representatives within two years.
- Authority: [Inheritance Tax Act 1984 s.18](https://www.legislation.gov.uk/ukpga/1984/51/section/18) (in_force)
- Authority: [Inheritance Tax Act 1984 s.8A](https://www.legislation.gov.uk/ukpga/1984/51/section/8A) (in_force)
- Authority: [Inheritance Tax Act 1984 s.8D](https://www.legislation.gov.uk/ukpga/1984/51/section/8D) (in_force)
- PASS — calculator registered (strategy.iht_spousal_transfer_nil_rate_bands)
- PASS — adapter registered
- PASS — has legal authorities (3 cited)
- PASS — plain-English explanation present (502 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (long)

### 24. Marriage Allowance transfer  
`marriage-allowance-transfer` — personal_income_tax — risk **settled**, timeframe short
> Where one spouse or civil partner does not use their full personal allowance and the other is a basic-rate taxpayer, 10% of the unused allowance can be transferred, reducing the recipient's tax bill by a fixed amount.
- Authority: [Income Tax Act 2007 ss.55B-55E](https://www.legislation.gov.uk/ukpga/2007/3/section/55B) (in_force)
- PASS — calculator registered (strategy.marriage_allowance_transfer)
- PASS — adapter registered
- PASS — has legal authorities (1 cited)
- PASS — plain-English explanation present (217 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 25. Pension annual allowance carry-forward  
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

### 26. Private residence relief on property disposal  
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

### 27. Spousal transfer before disposal  
`cgt-spousal-transfer-before-disposal` — property_taxes — risk **settled**, timeframe short
> Transfers between spouses or civil partners living together are at no gain/no loss, so a half share transferred before an arm's-length disposal uses both annual exempt amounts and both basic-rate bands. The transfer must be an outright gift of beneficial ownership made before any unconditional contract to sell exists.
- Authority: [Taxation of Chargeable Gains Act 1992 s.58](https://www.legislation.gov.uk/ukpga/1992/12/section/58) (in_force)
- Authority: [Taxation of Chargeable Gains Act 1992 ss.1H-1K](https://www.legislation.gov.uk/ukpga/1992/12/section/1H) (in_force)
- PASS — calculator registered (strategy.cgt_spousal_transfer_before_disposal)
- PASS — adapter registered
- PASS — has legal authorities (2 cited)
- PASS — plain-English explanation present (319 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

### 28. SDLT on planned property purchase  
`sdlt-purchase-planning` — property_taxes — risk **settled**, timeframe short
> Quantifies the SDLT on a planned residential purchase, including the 5% additional-dwellings surcharge and first-time buyers' relief. Where the purchase replaces a main residence sold within three years, the surcharge is recoverable — timing the sale matters as much as the price.
- Authority: [Finance Act 2003 s.55 and Sch 4ZA](https://www.legislation.gov.uk/ukpga/2003/14/section/55) (in_force)
- Authority: [Finance Act 2003 Sch 6ZA](https://www.legislation.gov.uk/ukpga/2003/14/schedule/6ZA) (in_force)
- PASS — calculator registered (strategy.sdlt_purchase_planning)
- PASS — adapter registered
- PASS — has legal authorities (2 cited)
- PASS — plain-English explanation present (280 chars)
- PASS — risk status set (settled)
- PASS — timeframe set (short)

---
## C. Authority registry (every citation, verified fetchable)

### 29. [Corporation Tax Act 2009 s.54](https://www.legislation.gov.uk/ukpga/2009/4/section/54) — Statute
> No deduction is allowed for expenses not incurred wholly and exclusively for the purposes of the trade — the condition governing deductibility of employer pension contributions as part of a reasonable remuneration package.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2009/4/section/54)
- PASS — primary source fetched by watcher (1,518 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 30. [Corporation Tax Act 2010 Part 3A (ss.18A-18M)](https://www.legislation.gov.uk/ukpga/2010/4/part/3A) — Statute
> Small profits rate and marginal relief on corporation tax profits, reintroduced with effect from 1 April 2023 by Finance Act 2021 s.7 and Sch.1.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2010/4/part/3A)
- PASS — primary source fetched by watcher (19,154 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 31. [Finance Act 2003 s.55 and Sch 4ZA](https://www.legislation.gov.uk/ukpga/2003/14/section/55) — Statute
> Amount of stamp duty land tax chargeable on residential property; Schedule 4ZA imposes higher rates for additional dwellings, refundable where a main residence is replaced within three years.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2003/14/section/55)
- PASS — primary source fetched by watcher (10,845 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 32. [Finance Act 2003 Sch 6ZA](https://www.legislation.gov.uk/ukpga/2003/14/schedule/6ZA) — Statute
> Relief for first-time buyers: no SDLT up to the relief threshold and a reduced rate above it, unavailable where the price exceeds the cap.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2003/14/schedule/6ZA)
- PASS — primary source fetched by watcher (10,677 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 33. [Finance Act 2004 s.190](https://www.legislation.gov.uk/ukpga/2004/12/section/190) — Statute
> The maximum amount of relief for an individual's pension contributions in a tax year is the greater of the basic amount (£3,600) and the individual's relevant UK earnings chargeable to income tax for that year.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2004/12/section/190)
- PASS — primary source fetched by watcher (3,902 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 34. [Finance Act 2004 s.228](https://www.legislation.gov.uk/ukpga/2004/12/section/228) — Statute
> The annual allowance for tax-relieved pension savings, and (via s.228ZA, inserted by Finance (No.2) Act 2015) its tapering for high-income individuals.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2004/12/section/228)
- PASS — primary source fetched by watcher (3,094 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 35. [Income Tax Act 2007 s.10](https://www.legislation.gov.uk/ukpga/2007/3/section/10) — Statute
> Basic rate, higher rate, and additional rate of income tax on non-savings, non-dividend income.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2007/3/section/10)
- PASS — primary source fetched by watcher (6,064 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 36. [Income Tax Act 2007 s.13A](https://www.legislation.gov.uk/ukpga/2007/3/section/13A) — Statute
> Dividend nil rate: the dividend allowance against which dividend income is charged at 0%, introduced by Finance Act 2016 s.5.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2007/3/section/13A)
- PASS — primary source fetched by watcher (3,513 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 37. [Income Tax Act 2007 s.35](https://www.legislation.gov.uk/ukpga/2007/3/section/35) — Statute
> Entitlement to personal allowance for those born after 5 April 1948, and its reduction under section 35(2) where adjusted net income exceeds the income limit.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2007/3/section/35)
- PASS — primary source fetched by watcher (1,915 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 38. [Income Tax Act 2007 ss.55B-55E](https://www.legislation.gov.uk/ukpga/2007/3/section/55B) — Statute
> Transferable tax allowance for married couples and civil partners (Marriage Allowance), inserted by Finance Act 2014 s.11.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2007/3/section/55B)
- PASS — primary source fetched by watcher (6,900 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 39. [Inheritance Tax Act 1984 s.18](https://www.legislation.gov.uk/ukpga/1984/51/section/18) — Statute
> Transfers between spouses or civil partners are exempt transfers (unlimited where the transferee is UK-domiciled).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/18)
- PASS — primary source fetched by watcher (3,808 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 40. [Inheritance Tax Act 1984 s.19](https://www.legislation.gov.uk/ukpga/1984/51/section/19) — Statute
> Annual exemption: transfers of value up to £3,000 in a tax year are exempt; unused exemption carries forward one year.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/19)
- PASS — primary source fetched by watcher (1,844 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 41. [Inheritance Tax Act 1984 s.3A](https://www.legislation.gov.uk/ukpga/1984/51/section/3A) — Statute
> A potentially exempt transfer becomes an exempt transfer if the transferor survives seven years; otherwise it is a chargeable transfer.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/3A)
- PASS — primary source fetched by watcher (6,263 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 42. [Inheritance Tax Act 1984 s.7 and Sch 1](https://www.legislation.gov.uk/ukpga/1984/51/section/7) — Statute
> Rates of tax, including taper relief under s.7(4) reducing the tax charged on chargeable transfers made three to seven years before death.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/7)
- PASS — primary source fetched by watcher (3,992 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 43. [Inheritance Tax Act 1984 s.8A](https://www.legislation.gov.uk/ukpga/1984/51/section/8A) — Statute
> Transfer of unused nil-rate band between spouses and civil partners: the survivor's nil-rate band is increased by the unused percentage.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/8A)
- PASS — primary source fetched by watcher (3,172 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 44. [Inheritance Tax Act 1984 s.8D](https://www.legislation.gov.uk/ukpga/1984/51/section/8D) — Statute
> Residence nil-rate amount where a qualifying residential interest is closely inherited; tapered by £1 for every £2 the estate exceeds the taper threshold.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/section/8D)
- PASS — primary source fetched by watcher (3,682 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 45. [Inheritance Tax Act 1984 Sch 1A](https://www.legislation.gov.uk/ukpga/1984/51/schedule/1A) — Statute
> Where at least 10% of the baseline amount passes to charity, inheritance tax is charged at 36% instead of 40%.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1984/51/schedule/1A)
- PASS — primary source fetched by watcher (8,527 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 46. [ITTOIA 2005 s.383](https://www.legislation.gov.uk/ukpga/2005/5/section/383) — Statute
> Charge to tax on dividends and other distributions of a UK resident company.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2005/5/section/383)
- PASS — primary source fetched by watcher (1,484 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 47. [Jones v Garnett (Arctic Systems) [2007] UKHL 35](https://www.bailii.org/uk/cases/UKHL/2007/35.html) — Court Judgment
> The House of Lords held that the ordinary-share arrangement between spouses was a settlement within ITTOIA 2005 s.620, but fell within the s.626 outright-gifts-between-spouses exemption because the shares were not wholly or substantially a right to income. Dividend income splitting through ordinary shares held by a spouse therefore stands, subject to the arrangement involving full ordinary shares rather than income-only rights.
- PASS — canonical URI recorded (https://www.bailii.org/uk/cases/UKHL/2007/35.html)
- PASS — primary source fetched by watcher (80,451 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 48. [National Insurance Contributions Act 2014 s.1](https://www.legislation.gov.uk/ukpga/2014/7/section/1) — Statute
> Employment Allowance against employer Class 1 NIC liability, subject to the excluded-companies regulations (SI 2016/344), which exclude a company whose sole employee is also a director.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/2014/7/section/1)
- PASS — primary source fetched by watcher (1,837 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 49. [Social Security Contributions and Benefits Act 1992 s.15](https://www.legislation.gov.uk/ukpga/1992/4/section/15) — Statute
> Class 4 National Insurance contributions on profits of a trade, profession or vocation carried on by a self-employed earner.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/4/section/15)
- PASS — primary source fetched by watcher (14,848 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 50. [Social Security Contributions and Benefits Act 1992 s.6](https://www.legislation.gov.uk/ukpga/1992/4/section/6) — Statute
> Liability for Class 1 primary and secondary National Insurance contributions on earnings from employment.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/4/section/6)
- PASS — primary source fetched by watcher (11,910 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 51. [Taxation of Chargeable Gains Act 1992 s.58](https://www.legislation.gov.uk/ukpga/1992/12/section/58) — Statute
> Disposals between spouses or civil partners living together are treated as made for a consideration giving neither gain nor loss.
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/12/section/58)
- PASS — primary source fetched by watcher (6,329 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 52. [Taxation of Chargeable Gains Act 1992 ss.1H-1K](https://www.legislation.gov.uk/ukpga/1992/12/section/1H) — Statute
> Rates of capital gains tax by reference to unused basic-rate band, and the annual exempt amount (s.1K).
- PASS — canonical URI recorded (https://www.legislation.gov.uk/ukpga/1992/12/section/1H)
- PASS — primary source fetched by watcher (7,522 chars of source text on file)
- PASS — status is in force (in_force)
- PASS — verbatim extract on file

### 53. [Taxation of Chargeable Gains Act 1992 ss.222-223](https://www.legislation.gov.uk/ukpga/1992/12/section/222) — Statute
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
| 1–53 | _(name)_ | _(YES / exceptions)_ | _(date)_ |
