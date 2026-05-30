# Louisiana Redistricting Dashboard
Spatial equity dashboard tracking Louisiana's SB 121- ACT 2 redistricting — 5R/1D cracking of Black voting power. Post-Callais VRA analysis. #Built by Tia Fields.#

www.tiafields.com 

Louisiana Redistricting Equity Dashboard
Tracking Black Voting Power Under SB 121 Now Act 2


# What This Is

This is an open-source, interactive spatial analysis dashboard tracking how Louisiana's 2026 Regular Session Senate Bill 121 — authored by Sen. Jay Morris (R-West Monroe) and amended by Rep. Dixon McMakin (R-Baton Rouge) — cracks Black voting communities across five Republican-controlled congressional districts while packing residual Black political power into a single Democratic district.
The dashboard was built in direct response to the U.S. Supreme Court's April 29, 2026 ruling in Louisiana v. Callais, 608 U.S. ___ (2026), which gutted Section 2 of the Voting Rights Act of 1965 by reinstating an intentional discrimination standard that Congress explicitly rejected in 1982. Combined with Rucho v. Common Cause (2019), which made partisan gerrymandering nonjusticiable in federal courts, the Callais ruling effectively removes every federal judicial check on racially motivated redistricting dressed in partisan clothing.
This tool is designed to make that process visible — in data, in geography, and in plain language.

# The Core Finding

Black Louisianans represent 31.2% of all registered voters statewide — 925,657 people as of May 1, 2026.
Under the proposed SB 121 McMakin Amendment:
WhatNumberMajority-Black seats1 of 6 (16.7%)Black voters in Republican-controlled districts731,722 (79%)Proportional expectation2 of 6 seats (33%)Representational deficit−1 seat, −16.7 points
This is not a partisan coincidence. In Louisiana's hyper-polarized electorate, Black voters register and vote Democratic at rates exceeding 90%. Every strategy that "maximizes Republican advantage" is mathematically indistinguishable from targeting Black voters. The partisan shield is the racial shield.

# What's in This Dashboard

McMakin district polygons from the official shapefile. Toggle: district colors, Black voter % heat, Democrat % heat, REI deviation view. Click any district for real SOS voter data.Charts5 visualizations: Black voter count by district, Black % vs. 31.2% baseline, party registration breakdown, total registered voters (exposes malapportionment), stacked racial composition.Parish TableAll 64 Louisiana parishes with real SOS registration data — sortable, color-coded PACKED or CRACKED.Data AnomaliesThe impossible VAP metrics embedded in SB 121's own text: Jefferson Parish lists 196,528 registered voters against a stated VAP of 133,984 — a 146.7% registration rate. Six parishes show this pattern. A gap of 124,280 phantom residents separates D1's parish-level VAP sum from the district total declared in the bill.AboutData sources, methodology, legal citations, contact.

# Data Sources

SourceDescriptionDateLouisiana Secretary of StateStatewide Report of Registered Voters by Party and Race — Active voters5/1/2026HCA SB121-5662 (McMakin)Official district boundary shapefile, 2026 Regular SessionMay 2026SB 121 Reengrossed (Morris)Parish summary tables — VAP anomalies identified by Rep. C. Denise MarcelleMay 2026U.S. Census 2020 P.L. 94-171Block-level population data (for future BVAP integration)2020

# Representational Equity Index (REI)

The REI measures how far each district deviates from proportional Black representation.
REI = District Black % − Statewide Black % (31.2%)
REI ScoreClassification> +8ppSEVERELY PACKED+5 to +8ppPACKED−5 to +5ppNear proportional−5 to −8ppCRACKED< −8ppSEVERELY CRACKED
District 1 scores −8.82pp — the most severely cracked district in the proposed map.

# Key Legal Context

Louisiana v. Callais, 608 U.S. ___ (Apr. 29, 2026) — Gutted Section 2 VRA. Reinstated intent standard. Made it near-impossible to prove racial vote dilution when a state can point to partisan goals. Justice Kagan dissent: effectively "eviscerates" the VRA.
Rucho v. Common Cause, 588 U.S. 684 (2019) — Partisan gerrymandering nonjusticiable in federal courts. Combined with Callais: all gerrymandering is now effectively constitutional.
Thornburg v. Gingles, 478 U.S. 30 (1986) — Original framework for Section 2 vote dilution claims. Significantly narrowed by Callais.
Alexander v. SC NAACP, 602 U.S. 1 (2024) — Set evidentiary presumption of legislative good faith; required plaintiffs to produce alternative maps satisfying state's partisan goals.
14th Amendment / One-Person-One-Vote — The remaining viable challenge. SB 121's own data tables show impossible VAP figures and a 124,280-person internal discrepancy. No VRA claim required.
