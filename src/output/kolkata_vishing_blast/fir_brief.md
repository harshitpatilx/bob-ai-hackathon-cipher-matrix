# DRAFT FIR / CASE BRIEF - Kolkata Spoofed Customer Care Vishing Blast

**Case file:** kolkata_vishing_blast  
**Police Station:** Cyber Crime Cell, Kolkata Police  
**District:** Kolkata  
**State:** West Bengal  
**Complainant:** 9 victims (aggregated)  
**Date of occurrence:** 2024-03-06  
**Date of reporting:** 2024-03-06  
**Generated:** 28 Sep 2026 07:34 UTC by CFNA (Bob backend: rule-assisted network analysis)

> Draft prepared for review by the Investigating Officer. Sections, jurisdiction and
> witness details must be verified against the case diary before filing u/s 173 BNSS, 2023.

---

## 1. Case at a glance

| Parameter | Value |
| --- | --- |
| Fraud pattern identified | Phish Vish (confidence 100%) |
| Entities extracted | 93 |
| Relationships extracted | 113 |
| Documents processed | 6 |
| Structured records | 82 |
| Money trail volume | Rs.2,322,271.00 |
| Kingpins / Operators / Recruiters | 2 / 0 / 0 |
| Mule accounts | 8 |
| Victim identifiers | 28 |
| Connected components | 3 |
| Highest risk node | 5003000000001 (73.5/99) |

## 2. Facts of the case

That the complainant herein was defrauded of money through the misuse of digital payment systems. It is alleged that between 2024-03-06 00:00:00 and 2024-03-06 00:00:00, fraudulent transactions aggregating to Rs.2,322,271.00 were executed involving 17 financial/telecom identifiers, which stand captured in the transaction annexure of this case file.

The technical analysis of the material on record points to the modus operandi of Phish Vish (PHISH_VISH). Phishing/vishing campaign: a small set of broadcast caller IDs or fake links harvest credentials which are used against many victims.

The money trail converges on 2 terminal beneficiary account(s)/identifier(s) (ANUP SAHA, 5003000000001) which show no commensurate legitimate credit, indicating that these accounts are the end of the layering chain controlled by the kingpin of the syndicate.

A total of 8 mule account(s) have been identified which received the defrauded money and forwarded 85% or more of their inflow to the next layer, demonstrating the organised pass-through structure of the network.

28 victim identifier(s) are recorded in the annexure with quantified loss of Rs.1,713,000.00; their statements be recorded under s.180 BNSS (03) 2023.

## 3. Modus operandi / fraud pattern analysis

**Phish Vish (PHISH_VISH)** - Phishing/vishing campaign: a small set of broadcast caller IDs or fake links harvest credentials which are used against many victims.

Signals relied upon:
1. one-way broadcast number 9003199999 contacted 9 parties with no inbound calls
2. language markers matched: customer care, helpline, kyc, otp, phishing, verification

Secondary pattern on record: Mule Chain at 33% confidence (Layered money-mule network: funds hop through serial pass-through accounts with near-full forwarding before cash-out.)

## 4. Organisational hierarchy (kingpin -> operator -> mule -> victim)

```
KINGPIN (terminal beneficiary)
  |-- 5003000000001
  |-- ANUP SAHA
  |-- Mule (layer not established)
  |     |-- BIKASH MONDAL
  |     |-- DEEPAK ROY
  |     |-- JAVED ANSARI
  |     |-- SNEHA SARKAR
  |-- Tier-1
  |     |-- 5003000030001
  |-- Tier-2
  |     |-- 5003000020002
  |     |-- 5003000020001
  |     |-- 5003000020003
  |-- VICTIM (28)
  |     |-- 5003000010001
  |     |-- 5003000010002
  |     |-- 5003000010003
  |     |-- 5003000010004
  |     |-- 5003000010005
  |     |-- 5003000010006
  |     |-- ... 22 more
```

### 4.1 Accused / suspect assessment

| Identifier | Type | Role | Tier | Risk | Basis of assessment |
| --- | --- | --- | --- | --- | --- |
| 5003000000001 | account | kingpin | - | 73.5 | terminal beneficiary: net inflow Rs.693,765; PageRank 0.2336 among top nodes |
| 5003000030001 | account | mule | T1 | 67.2 | pass-through: forwarded 90% of Rs.770,850 inflow; layer position: Tier-1 (hops from cash-out = 1) |
| ANUP SAHA | person | kingpin | - | 53.3 | terminal beneficiary: net inflow Rs.0; PageRank 0.2012 among top nodes |
| 5003000020002 | account | mule | T2 | 50.4 | pass-through: forwarded 90% of Rs.405,500 inflow; layer position: Tier-2 (hops from cash-out = 2) |
| 5003000020001 | account | mule | T2 | 46.3 | pass-through: forwarded 90% of Rs.191,000 inflow; layer position: Tier-2 (hops from cash-out = 2) |
| 5003000020003 | account | mule | T2 | 45.1 | pass-through: forwarded 90% of Rs.260,000 inflow; layer position: Tier-2 (hops from cash-out = 2) |
| BIKASH MONDAL | person | mule | - | 26.8 | pass-through: forwarded 0% of Rs.0 inflow; corroborated by narrative markers: suspect |
| SNEHA SARKAR | person | mule | - | 26.8 | pass-through: forwarded 0% of Rs.0 inflow; corroborated by narrative markers: suspect |
| JAVED ANSARI | person | mule | - | 26.8 | pass-through: forwarded 0% of Rs.0 inflow |
| DEEPAK ROY | person | mule | - | 26.8 | pass-through: forwarded 0% of Rs.0 inflow; corroborated by narrative markers: suspect |

## 5. Financial trail - accounts to be frozen

| Identifier | Type | Bank | UPI handle | Inflow (Rs.) | Outflow (Rs.) | Role | Tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5003000000001 | account | PNB | anup.saha@okaxis | 693,765.00 | 0.00 | kingpin | - |
| 5003000030001 | account | AXIS | deepak.roy@ybl | 770,850.00 | 693,765.00 | mule | T1 |
| 5003000020002 | account | SBI | sneha.sarkar@ybl | 405,500.00 | 364,950.00 | mule | T2 |
| 5003000020003 | account | SBI | javed.ansari@ybl | 260,000.00 | 234,000.00 | mule | T2 |
| 5003000020001 | account | SBI | bikash.mondal@ybl | 191,000.00 | 171,900.00 | mule | T2 |

### 5.1 Largest recorded transfers

| When | From | To | Amount (Rs.) | Source remark |
| --- | --- | --- | --- | --- |
|  | 5003000030001 | 5003000000001 | 693,765.00 | TXN00013: Rs.693,765.00 5003000030001 -> 5003000000001 [layer to cashout] |
|  | 5003000020002 | 5003000030001 | 364,950.00 | TXN00011: Rs.364,950.00 5003000020002 -> 5003000030001 [collector consolidation] |
|  | 5003000020003 | 5003000030001 | 234,000.00 | TXN00012: Rs.234,000.00 5003000020003 -> 5003000030001 [collector consolidation] |
|  | 5003000010005 | 5003000020002 | 215,000.00 | TXN00005: Rs.215,000.00 5003000010005 -> 5003000020002 [UPI debit after vishing  |
|  | 5003000020001 | 5003000030001 | 171,900.00 | TXN00010: Rs.171,900.00 5003000020001 -> 5003000030001 [collector consolidation] |
|  | 5003000010008 | 5003000020002 | 143,000.00 | TXN00008: Rs.143,000.00 5003000010008 -> 5003000020002 [UPI debit after vishing  |
|  | 5003000010003 | 5003000020003 | 132,000.00 | TXN00003: Rs.132,000.00 5003000010003 -> 5003000020003 [UPI debit after vishing  |
|  | 5003000010007 | 5003000020001 | 89,000.00 | TXN00007: Rs.89,000.00 5003000010007 -> 5003000020001 [UPI debit after vishing c |
|  | 5003000010009 | 5003000020003 | 76,000.00 | TXN00009: Rs.76,000.00 5003000010009 -> 5003000020003 [UPI debit after vishing c |
|  | 5003000010001 | 5003000020001 | 64,000.00 | TXN00001: Rs.64,000.00 5003000010001 -> 5003000020001 [UPI debit after vishing c |
|  | 5003000010006 | 5003000020003 | 52,000.00 | TXN00006: Rs.52,000.00 5003000010006 -> 5003000020003 [UPI debit after vishing c |
|  | 5003000010002 | 5003000020002 | 47,500.00 | TXN00002: Rs.47,500.00 5003000010002 -> 5003000020002 [UPI debit after vishing c |
|  | 5003000010004 | 5003000020001 | 38,000.00 | TXN00004: Rs.38,000.00 5003000010004 -> 5003000020001 [UPI debit after vishing c |
|  | 5003000050000 | 5003000050001 | 499.00 | TXN00014: Rs.499.00 5003000050000 -> 5003000050001 [routine settle] |
|  | 5003000050001 | 5003000050002 | 461.00 | TXN00015: Rs.461.00 5003000050001 -> 5003000050002 [routine settle] |
|  | 5003000050002 | 5003000050000 | 196.00 | TXN00016: Rs.196.00 5003000050002 -> 5003000050000 [routine settle] |

## 6. Victim annexure

| Victim identifier | Type | Amount lost (Rs.) | Paid into |
| --- | --- | --- | --- |
| 9003100005 | phone | 215,000.00 |  |
| 5003000010005 | account | 215,000.00 | 5003000020002 |
| 5003000010008 | account | 143,000.00 | 5003000020002 |
| 9003100008 | phone | 143,000.00 |  |
| 5003000010003 | account | 132,000.00 | 5003000020003 |
| 9003100003 | phone | 132,000.00 |  |
| 9003100007 | phone | 89,000.00 |  |
| 5003000010007 | account | 89,000.00 | 5003000020001 |
| 9003100009 | phone | 76,000.00 |  |
| 5003000010009 | account | 76,000.00 | 5003000020003 |
| 9003100001 | phone | 64,000.00 |  |
| 5003000010001 | account | 64,000.00 | 5003000020001 |
| 5003000010006 | account | 52,000.00 | 5003000020003 |
| 9003100006 | phone | 52,000.00 |  |
| 5003000010002 | account | 47,500.00 | 5003000020002 |
| 9003100002 | phone | 47,500.00 |  |
| 9003100004 | phone | 38,000.00 |  |
| 5003000010004 | account | 38,000.00 | 5003000020001 |
| RUPA GHOSH | person | 0.00 |  |
| TANMAY ROY | person | 0.00 |  |
| IMRAN SHEIKH | person | 0.00 |  |
| MOUMITA PAL | person | 0.00 |  |
| 9003199999 | phone | 0.00 |  |
| SOURAV BANERJEE | person | 0.00 |  |
| RAKESH AGARWAL | person | 0.00 |  |
| NAZIA KHAN | person | 0.00 |  |
| ARJUN DUTTA | person | 0.00 |  |
| PRIYA DAS | person | 0.00 |  |

## 7. Telecom / device evidence

### 7.1 SIM-swap bindings (MSISDN with more than one SIM / re-issued SIM)

_none recorded in the dataset_

### 7.2 Devices (IMEI) and identities used

| IMEI | #SIMs | #MSISDNs | SIMs | MSISDNs |
| --- | --- | --- | --- | --- |
| 356938035661101 | 0 | 1 |  | 9003100001 |
| 356938035661102 | 0 | 1 |  | 9003100002 |
| 356938035661103 | 0 | 1 |  | 9003100003 |
| 356938035661104 | 0 | 1 |  | 9003100004 |
| 356938035661105 | 0 | 1 |  | 9003100005 |
| 356938035661106 | 0 | 1 |  | 9003100006 |
| 356938035661107 | 0 | 1 |  | 9003100007 |
| 356938035661108 | 0 | 1 |  | 9003100008 |
| 356938035661109 | 0 | 1 |  | 9003100009 |
| 356938035661201 | 0 | 1 |  | 9003100021 |
| 356938035661202 | 0 | 1 |  | 9003100022 |
| 356938035661203 | 0 | 1 |  | 9003100023 |
| 356938035661211 | 0 | 1 |  | 9003100031 |
| 356938035661299 | 0 | 1 |  | 9003100099 |

### 7.3 Call detail record highlights

| Calling MSISDN | Called MSISDN | CDR count | First seen | Note |
| --- | --- | --- | --- | --- |
| 9003199999 | 9003100001 | 1 | - | C00001: 9003199999 -> 9003100001 (90s) tower CEL136 |
| 9003199999 | 9003100002 | 1 | - | C00002: 9003199999 -> 9003100002 (72s) tower CEL548 |
| 9003199999 | 9003100003 | 1 | - | C00003: 9003199999 -> 9003100003 (92s) tower CEL908 |
| 9003199999 | 9003100004 | 1 | - | C00004: 9003199999 -> 9003100004 (38s) tower CEL799 |
| 9003199999 | 9003100005 | 1 | - | C00005: 9003199999 -> 9003100005 (83s) tower CEL715 |
| 9003199999 | 9003100006 | 1 | - | C00006: 9003199999 -> 9003100006 (61s) tower CEL487 |
| 9003199999 | 9003100007 | 1 | - | C00007: 9003199999 -> 9003100007 (79s) tower CEL554 |
| 9003199999 | 9003100008 | 1 | - | C00008: 9003199999 -> 9003100008 (43s) tower CEL919 |
| 9003199999 | 9003100009 | 1 | - | C00009: 9003199999 -> 9003100009 (31s) tower CEL193 |
| 9003100021 | 9003100031 | 1 | - | C00010: 9003100021 -> 9003100031 (33s) tower CEL176 |
| 9003100022 | 9003100031 | 1 | - | C00011: 9003100022 -> 9003100031 (37s) tower CEL395 |
| 9003100023 | 9003100031 | 1 | - | C00012: 9003100023 -> 9003100031 (49s) tower CEL469 |

## 8. Timeline of occurrences

| Timestamp | Event | Detail |
| --- | --- | --- |
| 2024-03-06 00:00:00 | offence | offence reported to have occurred |
| 2024-03-06 00:00:00 | report | complaint/FIR lodged |

**Period:** 2024-03-06 00:00:00 to 2024-03-06 00:00:00

## 9. Sections of law invoked

1. BNS 2023, s.318(4) - cheating by personation [IPC 419/420]
2. IT Act 2000, s.66C - identity theft
3. IT Act 2000, s.66D - cheating by personation using computer resource
4. IT Act 2000, s.67 - false/misleading digital publication
5. BNS 2023, s.61 - criminal conspiracy [IPC 120B]
6. BNS 2023, s.318 - cheating [IPC 420]
7. PMLA 2002, s.3 & s.4 - money laundering (bank accounts used for layering)
8. BNS 2023, s.316(4) - criminal breach of trust by banker/agent [IPC 409] (account holders)
9. IT Act 2000, s.66D - cheating by personation
10. PMLA 2002, s.3 & s.4 - proceeds of crime
11. BNS 2023, s.318(4) - cheating by personation [IPC 419]
12. BNS 2023, s.336/338 - forgery [IPC 465/468]
13. BNS 2023, s.340 - using forged document [IPC 471]
14. IT Act 2000, s.66C - identity theft (card credentials)
15. BNS 2023, s.303 - theft [IPC 379]
16. BNS 2023, s.318(4) - cheating by impersonation [IPC 419/420]
17. IT Act 2000, s.66C - identity theft (OTP/SIM credentials)
18. Indian Telegraph Act 1885, s.4 / TRAI regulations - unauthorised SIM acquisition (as applicable)
19. PMLA 2002, s.3 & s.4 - laundering of fraud proceeds (if cross-state fund layering proved)

_Note: BNS 2023 applies to offences from 01 July 2024; for offences before that date, the 
corresponding IPC sections recorded in brackets are to be invoked. PMLA applicability to be 
confirmed by the IO with the ED regional office._

## 10. Recommended investigation actions

1. Trace the broadcast caller ID/SMS sender to VoIP/SMPP route; obtain the originating gateway records.
2. Capture the phishing page/domain WHOIS and hosting records; request takedown through CERT-In.
3. Correlate OTP window (5-10 minutes) with debits for every victim to prove OTP relay.
4. Lay down hop-by-hop fund flow chart (victim -> Tier-3 -> Tier-2 -> Tier-1 -> cash-out) as an annexure to the FIR.
5. Attach the pass-through analysis: ratio of inflow immediately re-transferred, to establish knowledge under PMLA s.3.
6. Interrogate Tier-1 mules first (closest to cash-out) and offer collaborator status to lower tiers.
7. Map all profiles/photographs used by the accused; obtain platform account creation IP logs.
8. Trace 'processing fee' / 'custom duty' payments to beneficiary accounts and freeze.
9. Freeze all identified bank accounts / UPI handles of accused and issue notice u/s 91 BNSS (03) 2023 to banks for KYC, IP and device logs.
10. Obtain NPCI mapping (UPI handle -> bank account -> IFSC) and full statement of accounts for last 12 months.
11. Get certified CDRs (call detail records) and IPDR data for accused MSISDNs from telecom operators for the offence period.
12. Flag IMEIs on CEIR/CENTRAL Equipment Identity Register for blocking/recovery; verify IMEI-swap history with operator HLR.
13. Register the complaint on cybercrime.gov.in / NCRP and inform I4C, MHA; report to CERT-In within 6 hours under the CERT-In Directions, 2022.
14. Identify and verify beneficiaries of every withdrawal; obtain ATM/branch CCTV footage and UPI QR/cash-out points.
15. Prepare a seizure memo for devices recovered; extract digital evidence with a certified examiner (ITA s.65B admissibility).

## 11. Intelligence gaps flagged by Bob

- 16 transfer(s) lack timestamps - pull certified statements with value dates.
- 1 MSISDN(s) have no device mapping - request HLR/IMEI mapping from operators.

## 12. Analyst (Bob) key observations

- Pattern verdict: Phish Vish (confidence 100%). one-way broadcast number 9003199999 contacted 9 parties with no inbound calls
- Network shape: 93 entities, 113 relationships across 3 connected component(s); documented money trail Rs.2,322,271.
- Hierarchy: 2 kingpin node(s), 0 operator(s), 8 mule account(s) in 3 layer(s), 28 victim node(s). Primary beneficiary 5003000000001 (risk 73.5/99).
- Layering map: Tier-0: 4, Tier-1: 1, Tier-2: 3. Layers closer to Tier-1 are closest to cash-out.
- Victim loss quantified at Rs.1,713,000 across 28 victim identifiers - use as the 'property' line in the FIR.
- Time window of recorded activity: 2024-03-06 00:00:00 to 2024-03-06 00:00:00.
- Priority interrogations: 5003000000001 (kingpin, risk 73.5); 5003000030001 (mule, risk 67.2); ANUP SAHA (kingpin, risk 53.3).
- Bob scored 93 identifiers and 113 edges using backend 'bob-local-rules-v1' (0 bob-coin calls so far; IBM Bob hook available for narrative expansion).

## Annexures

A. Transaction ledger (certified statements to be obtained under s.91 BNSS)
B. Call detail records of accused MSISDNs
C. SIM / device mapping (ICCID - MSISDN - IMEI)
D. Bank accounts freeze chart with IFSC and KYC status
E. Victim loss chart
F. Network graph (see `report.html` for the interactive graph)
G. Underlying machine-readable analysis (`case_data.json`)

---

**Place:** Kolkata  
**Date:** 28 09 2026  

_______________________________  
Investigating Officer, Cyber Crime Cell Kolkata  
Cyber Crime Cell, Kolkata Police
