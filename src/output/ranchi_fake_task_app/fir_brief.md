# DRAFT FIR / CASE BRIEF - Ranchi Fake Task App Investment Scam

**Case file:** ranchi_fake_task_app  
**Police Station:** PS Kanke Road, Ranchi  
**District:** Ranchi  
**State:** Jharkhand  
**Complainant:** 8 victims (aggregated)  
**Date of occurrence:** 2024-03-05  
**Date of reporting:** 2024-03-09  
**Generated:** 28 Sep 2026 07:34 UTC by CFNA (Bob backend: rule-assisted network analysis)

> Draft prepared for review by the Investigating Officer. Sections, jurisdiction and
> witness details must be verified against the case diary before filing u/s 173 BNSS, 2023.

---

## 1. Case at a glance

| Parameter | Value |
| --- | --- |
| Fraud pattern identified | Task Investment Scam (confidence 85%) |
| Entities extracted | 85 |
| Relationships extracted | 96 |
| Documents processed | 5 |
| Structured records | 58 |
| Money trail volume | Rs.1,929,115.00 |
| Kingpins / Operators / Recruiters | 2 / 0 / 0 |
| Mule accounts | 8 |
| Victim identifiers | 16 |
| Connected components | 4 |
| Highest risk node | 5002000000001 (76.6/99) |

## 2. Facts of the case

That the complainant herein was defrauded of money through the misuse of digital payment systems. It is alleged that between 2024-03-05 00:00:00 and 2024-03-09 00:00:00, fraudulent transactions aggregating to Rs.1,929,115.00 were executed involving 17 financial/telecom identifiers, which stand captured in the transaction annexure of this case file.

The technical analysis of the material on record points to the modus operandi of Task Investment Scam (TASK_INVESTMENT_SCAM). Fake task/investment work scam: many victims are induced to 'recharge' for task bonuses into a small set of collector accounts.

The money trail converges on 2 terminal beneficiary account(s)/identifier(s) (ROHIT SINHA, 5002000000001) which show no commensurate legitimate credit, indicating that these accounts are the end of the layering chain controlled by the kingpin of the syndicate.

A total of 8 mule account(s) have been identified which received the defrauded money and forwarded 85% or more of their inflow to the next layer, demonstrating the organised pass-through structure of the network.

16 victim identifier(s) are recorded in the annexure with quantified loss of Rs.711,000.00; their statements be recorded under s.180 BNSS (03) 2023.

## 3. Modus operandi / fraud pattern analysis

**Task Investment Scam (TASK_INVESTMENT_SCAM)** - Fake task/investment work scam: many victims are induced to 'recharge' for task bonuses into a small set of collector accounts.

Signals relied upon:
1. 2 collector accounts with fan-in >=4 (e.g. 5002000020002 received from 4 parties, Rs.388,000)
2. language markers matched: bonus, coach, earning app, group, investment, premium plan

Secondary pattern on record: Sextortion at 33% confidence (Sextortion: explicit video/chat leverage used to extract money through UPI.)

## 4. Organisational hierarchy (kingpin -> operator -> mule -> victim)

```
KINGPIN (terminal beneficiary)
  |-- 5002000000001
  |-- ROHIT SINHA
  |-- Mule (layer not established)
  |     |-- ASHOK VERMA
  |     |-- FAIZAN ALAM
  |     |-- NEHA SINGH
  |     |-- RITU KUMARI
  |-- Tier-1
  |     |-- 5002000030002
  |     |-- 5002000030001
  |-- Tier-2
  |     |-- 5002000020002
  |     |-- 5002000020001
  |-- VICTIM (16)
  |     |-- 5002000010001
  |     |-- 5002000010002
  |     |-- 5002000010003
  |     |-- 5002000010004
  |     |-- 5002000010005
  |     |-- 5002000010006
  |     |-- ... 10 more
```

### 4.1 Accused / suspect assessment

| Identifier | Type | Role | Tier | Risk | Basis of assessment |
| --- | --- | --- | --- | --- | --- |
| 5002000000001 | account | kingpin | - | 76.6 | terminal beneficiary: net inflow Rs.575,910; PageRank 0.1686 among top nodes |
| 5002000020002 | account | mule | T2 | 63.8 | pass-through: forwarded 90% of Rs.388,000 inflow; layer position: Tier-2 (hops from cash-out = 2) |
| 5002000020001 | account | mule | T2 | 59.8 | pass-through: forwarded 90% of Rs.323,000 inflow; layer position: Tier-2 (hops from cash-out = 2) |
| 5002000030002 | account | mule | T1 | 56.7 | pass-through: forwarded 90% of Rs.319,950 inflow; layer position: Tier-1 (hops from cash-out = 1) |
| 5002000030001 | account | mule | T1 | 56.0 | pass-through: forwarded 90% of Rs.319,950 inflow; layer position: Tier-1 (hops from cash-out = 1) |
| ROHIT SINHA | person | kingpin | - | 54.5 | terminal beneficiary: net inflow Rs.0; PageRank 0.1465 among top nodes |
| ASHOK VERMA | person | mule | - | 26.9 | pass-through: forwarded 0% of Rs.0 inflow; corroborated by narrative markers: suspect |
| NEHA SINGH | person | mule | - | 26.9 | pass-through: forwarded 0% of Rs.0 inflow; corroborated by narrative markers: suspect |
| FAIZAN ALAM | person | mule | - | 26.9 | pass-through: forwarded 0% of Rs.0 inflow; corroborated by narrative markers: suspect |
| RITU KUMARI | person | mule | - | 26.9 | pass-through: forwarded 0% of Rs.0 inflow |

## 5. Financial trail - accounts to be frozen

| Identifier | Type | Bank | UPI handle | Inflow (Rs.) | Outflow (Rs.) | Role | Tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5002000000001 | account | HDFC | rohit.sinha@okaxis | 575,910.00 | 0.00 | kingpin | - |
| 5002000020002 | account | SBI | neha.singh@ybl | 388,000.00 | 349,200.00 | mule | T2 |
| 5002000020001 | account | SBI | ashok.verma@ybl | 323,000.00 | 290,700.00 | mule | T2 |
| 5002000030002 | account | AXIS | ritu.kumari@ybl | 319,950.00 | 287,955.00 | mule | T1 |
| 5002000030001 | account | AXIS | faizan.alam@ybl | 319,950.00 | 287,955.00 | mule | T1 |

### 5.1 Largest recorded transfers

| When | From | To | Amount (Rs.) | Source remark |
| --- | --- | --- | --- | --- |
|  | 5002000030001 | 5002000000001 | 287,955.00 | TXN00013: Rs.287,955.00 5002000030001 -> 5002000000001 [consolidation to admin] |
|  | 5002000030002 | 5002000000001 | 287,955.00 | TXN00014: Rs.287,955.00 5002000030002 -> 5002000000001 [consolidation to admin] |
|  | 5002000020002 | 5002000030001 | 174,600.00 | TXN00011: Rs.174,600.00 5002000020002 -> 5002000030001 [upline transfer] |
|  | 5002000020002 | 5002000030002 | 174,600.00 | TXN00012: Rs.174,600.00 5002000020002 -> 5002000030002 [upline transfer] |
|  | 5002000020001 | 5002000030001 | 145,350.00 | TXN00009: Rs.145,350.00 5002000020001 -> 5002000030001 [upline transfer] |
|  | 5002000020001 | 5002000030002 | 145,350.00 | TXN00010: Rs.145,350.00 5002000020001 -> 5002000030002 [upline transfer] |
|  | 5002000010006 | 5002000020002 | 145,000.00 | TXN00006: Rs.145,000.00 5002000010006 -> 5002000020002 [recharge task payment] |
|  | 5002000010003 | 5002000020001 | 120,000.00 | TXN00003: Rs.120,000.00 5002000010003 -> 5002000020001 [recharge task payment] |
|  | 5002000010004 | 5002000020002 | 95,000.00 | TXN00004: Rs.95,000.00 5002000010004 -> 5002000020002 [recharge task payment] |
|  | 5002000010007 | 5002000020001 | 88,000.00 | TXN00007: Rs.88,000.00 5002000010007 -> 5002000020001 [recharge task payment] |
|  | 5002000010002 | 5002000020002 | 78,000.00 | TXN00002: Rs.78,000.00 5002000010002 -> 5002000020002 [recharge task payment] |
|  | 5002000010008 | 5002000020002 | 70,000.00 | TXN00008: Rs.70,000.00 5002000010008 -> 5002000020002 [recharge task payment] |
|  | 5002000010005 | 5002000020001 | 60,000.00 | TXN00005: Rs.60,000.00 5002000010005 -> 5002000020001 [recharge task payment] |
|  | 5002000010001 | 5002000020001 | 55,000.00 | TXN00001: Rs.55,000.00 5002000010001 -> 5002000020001 [recharge task payment] |
|  | 5002000050002 | 5002000050003 | 685.00 | TXN00017: Rs.685.00 5002000050002 -> 5002000050003 [routine settle] |
|  | 5002000050000 | 5002000050001 | 673.00 | TXN00015: Rs.673.00 5002000050000 -> 5002000050001 [routine settle] |
|  | 5002000050001 | 5002000050002 | 599.00 | TXN00016: Rs.599.00 5002000050001 -> 5002000050002 [routine settle] |
|  | 5002000050003 | 5002000050000 | 348.00 | TXN00018: Rs.348.00 5002000050003 -> 5002000050000 [routine settle] |

## 6. Victim annexure

| Victim identifier | Type | Amount lost (Rs.) | Paid into |
| --- | --- | --- | --- |
| 5002000010006 | account | 145,000.00 | 5002000020002 |
| 5002000010003 | account | 120,000.00 | 5002000020001 |
| 5002000010004 | account | 95,000.00 | 5002000020002 |
| 5002000010007 | account | 88,000.00 | 5002000020001 |
| 5002000010002 | account | 78,000.00 | 5002000020002 |
| 5002000010008 | account | 70,000.00 | 5002000020002 |
| 5002000010005 | account | 60,000.00 | 5002000020001 |
| 5002000010001 | account | 55,000.00 | 5002000020001 |
| DEVENDRA MEHTA | person | 0.00 |  |
| AFTAB ALAM | person | 0.00 |  |
| SARITA GUPTA | person | 0.00 |  |
| NEERAJ CHAUHAN | person | 0.00 |  |
| MUKESH SAHANI | person | 0.00 |  |
| RINA TIGGA | person | 0.00 |  |
| POOJA KUMARI | person | 0.00 |  |
| JYOTI MISHRA | person | 0.00 |  |

## 7. Telecom / device evidence

### 7.1 SIM-swap bindings (MSISDN with more than one SIM / re-issued SIM)

_none recorded in the dataset_

### 7.2 Devices (IMEI) and identities used

| IMEI | #SIMs | #MSISDNs | SIMs | MSISDNs |
| --- | --- | --- | --- | --- |
| 356938035651101 | 0 | 1 |  | 9871200001 |
| 356938035651102 | 0 | 1 |  | 9871200002 |
| 356938035651103 | 0 | 1 |  | 9871200003 |
| 356938035651104 | 0 | 1 |  | 9871200004 |
| 356938035651105 | 0 | 1 |  | 9871200005 |
| 356938035651106 | 0 | 1 |  | 9871200006 |
| 356938035651107 | 0 | 1 |  | 9871200007 |
| 356938035651108 | 0 | 1 |  | 9871200008 |
| 356938035651201 | 0 | 1 |  | 9871200021 |
| 356938035651202 | 0 | 1 |  | 9871200022 |
| 356938035651299 | 0 | 1 |  | 9871200099 |

### 7.3 Call detail record highlights

_none recorded in the dataset_

## 8. Timeline of occurrences

| Timestamp | Event | Detail |
| --- | --- | --- |
| 2024-03-05 00:00:00 | offence | offence reported to have occurred |
| 2024-03-09 00:00:00 | report | complaint/FIR lodged |

**Period:** 2024-03-05 00:00:00 to 2024-03-09 00:00:00

## 9. Sections of law invoked

1. BNS 2023, s.318 - cheating [IPC 420]
2. BNS 2023, s.61 - criminal conspiracy [IPC 120B]
3. IT Act 2000, s.66D - cheating by personation using computer resource
4. IT Act 2000, s.67 - publishing misleading material (app/group content)
5. PMLA 2002, s.3 & s.4 - proceeds of crime
6. IT Act 2000, s.67 - obscene material in electronic form
7. BNS 2023, s.351 - criminal intimidation [IPC 503/506]
8. BNS 2023, s.96-99 - outrage of modesty (where applicable) [IPC 354A]
9. PMLA 2002, s.3 & s.4 - money laundering (bank accounts used for layering)
10. BNS 2023, s.316(4) - criminal breach of trust by banker/agent [IPC 409] (account holders)
11. BNS 2023, s.308/309 - extortion / extortion with threat [IPC 383/384]
12. IT Act 2000, s.67 - publication of obscene/morphed material in electronic form
13. IT Act 2000, s.66C - identity theft
14. IT Act 2000, s.66D - cheating by personation
15. BNS 2023, s.318(4) - cheating by personation [IPC 419]
16. BNS 2023, s.336/338 - forgery [IPC 465/468]
17. BNS 2023, s.340 - using forged document [IPC 471]

_Note: BNS 2023 applies to offences from 01 July 2024; for offences before that date, the 
corresponding IPC sections recorded in brackets are to be invoked. PMLA applicability to be 
confirmed by the IO with the ED regional office._

## 10. Recommended investigation actions

1. Preserve group/app data (Telegram/WhatsApp group membership, recharge wallet IDs) from victim devices.
2. Trace recharge wallet top-ups to the exchange/crypto rails; issue freezing request to virtual-asset service providers.
3. Identify the 'coach/admin' handles controlling the group and map them to payout accounts.
4. Preserve chat/transaction records from victim device; obtain Telegram handle ownership records.
5. Do not publish victim identity; follow victim-sensitive procedure under CrPC/BNSS victim protocol.
6. Lay down hop-by-hop fund flow chart (victim -> Tier-3 -> Tier-2 -> Tier-1 -> cash-out) as an annexure to the FIR.
7. Attach the pass-through analysis: ratio of inflow immediately re-transferred, to establish knowledge under PMLA s.3.
8. Interrogate Tier-1 mules first (closest to cash-out) and offer collaborator status to lower tiers.
9. Freeze all identified bank accounts / UPI handles of accused and issue notice u/s 91 BNSS (03) 2023 to banks for KYC, IP and device logs.
10. Obtain NPCI mapping (UPI handle -> bank account -> IFSC) and full statement of accounts for last 12 months.
11. Get certified CDRs (call detail records) and IPDR data for accused MSISDNs from telecom operators for the offence period.
12. Flag IMEIs on CEIR/CENTRAL Equipment Identity Register for blocking/recovery; verify IMEI-swap history with operator HLR.
13. Register the complaint on cybercrime.gov.in / NCRP and inform I4C, MHA; report to CERT-In within 6 hours under the CERT-In Directions, 2022.
14. Identify and verify beneficiaries of every withdrawal; obtain ATM/branch CCTV footage and UPI QR/cash-out points.
15. Prepare a seizure memo for devices recovered; extract digital evidence with a certified examiner (ITA s.65B admissibility).

## 11. Intelligence gaps flagged by Bob

- 18 transfer(s) lack timestamps - pull certified statements with value dates.
- 1 MSISDN(s) have no device mapping - request HLR/IMEI mapping from operators.

## 12. Analyst (Bob) key observations

- Pattern verdict: Task Investment Scam (confidence 85%). 2 collector accounts with fan-in >=4 (e.g. 5002000020002 received from 4 parties, Rs.388,000)
- Network shape: 85 entities, 96 relationships across 4 connected component(s); documented money trail Rs.1,929,115.
- Hierarchy: 2 kingpin node(s), 0 operator(s), 8 mule account(s) in 3 layer(s), 16 victim node(s). Primary beneficiary 5002000000001 (risk 76.6/99).
- Layering map: Tier-0: 4, Tier-1: 2, Tier-2: 2. Layers closer to Tier-1 are closest to cash-out.
- Victim loss quantified at Rs.711,000 across 16 victim identifiers - use as the 'property' line in the FIR.
- Time window of recorded activity: 2024-03-05 00:00:00 to 2024-03-09 00:00:00.
- Priority interrogations: 5002000000001 (kingpin, risk 76.6); 5002000020002 (mule, risk 63.8); 5002000020001 (mule, risk 59.8).
- Bob scored 85 identifiers and 96 edges using backend 'bob-local-rules-v1' (0 bob-coin calls so far; IBM Bob hook available for narrative expansion).

## Annexures

A. Transaction ledger (certified statements to be obtained under s.91 BNSS)
B. Call detail records of accused MSISDNs
C. SIM / device mapping (ICCID - MSISDN - IMEI)
D. Bank accounts freeze chart with IFSC and KYC status
E. Victim loss chart
F. Network graph (see `report.html` for the interactive graph)
G. Underlying machine-readable analysis (`case_data.json`)

---

**Place:** Ranchi  
**Date:** 28 09 2026  

_______________________________  
Investigating Officer, Cyber Crime Ranchi  
PS Kanke Road, Ranchi
