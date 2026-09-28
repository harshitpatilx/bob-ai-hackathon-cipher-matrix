# DRAFT FIR / CASE BRIEF - Jamtara SIM-Swap & UPI Mule Network

**Case file:** jamtara_sim_swap  
**Police Station:** Cyber Crime Police Station, Jamtara  
**District:** Jamtara  
**State:** Jharkhand  
**Complainant:** Ramesh Kumar Sahu and 5 other victims  
**Date of occurrence:** 2024-03-18  
**Date of reporting:** 2024-03-19  
**Generated:** 28 Sep 2026 09:30 UTC by CFNA (Bob backend: rule-assisted network analysis)

> Draft prepared for review by the Investigating Officer. Sections, jurisdiction and
> witness details must be verified against the case diary before filing u/s 173 BNSS, 2023.

---

## 1. Case at a glance

| Parameter | Value |
| --- | --- |
| Fraud pattern identified | Sim Swap Otp (confidence 100%) |
| Entities extracted | 132 |
| Relationships extracted | 254 |
| Documents processed | 7 |
| Structured records | 170 |
| Money trail volume | Rs.3,321,714.00 |
| Kingpins / Operators / Recruiters | 5 / 18 / 0 |
| Mule accounts | 21 |
| Victim identifiers | 20 |
| Connected components | 4 |
| Highest risk node | 5001000040001 (77.7/99) |

## 2. Facts of the case

That the complainant herein was defrauded of money through the misuse of digital payment systems. It is alleged that between 2021-07-02 00:00:00 and 2024-03-19 00:00:00, fraudulent transactions aggregating to Rs.3,321,714.00 were executed involving 19 financial/telecom identifiers, which stand captured in the transaction annexure of this case file.

The technical analysis of the material on record points to the modus operandi of Sim Swap Otp (SIM_SWAP_OTP). SIM-swap / OTP-relay fraud: telecom identity is hijacked, victim SIM is re-issued to the syndicate, OTPs are read on their device and UPI debits are executed.

The money trail converges on 5 terminal beneficiary account(s)/identifier(s) (BHOLA RAM RAI, 9431100099, 89914700000000000000) which show no commensurate legitimate credit, indicating that these accounts are the end of the layering chain controlled by the kingpin of the syndicate.

A total of 21 mule account(s) have been identified which received the defrauded money and forwarded 85% or more of their inflow to the next layer, demonstrating the organised pass-through structure of the network.

20 victim identifier(s) are recorded in the annexure with quantified loss of Rs.1,900,000.00; their statements be recorded under s.180 BNSS (03) 2023.

## 3. Modus operandi / fraud pattern analysis

**Sim Swap Otp (SIM_SWAP_OTP)** - SIM-swap / OTP-relay fraud: telecom identity is hijacked, victim SIM is re-issued to the syndicate, OTPs are read on their device and UPI debits are executed.

Signals relied upon:
1. 8/19 MSISDNs seen on 2+ devices/SIMs - classic SIM-swap signature (e.g. phone:9431100001, phone:9431100002, phone:9431100003)
2. 2 device(s) controlling 3+ SIMs: device:356938035643801, device:356938035643804
3. 7 SIM re-activation/porting records with dates on file
4. language markers matched: kyc update, network went off, no signal, otp, ported, reissued

Secondary pattern on record: Phish Vish at 85% confidence (Phishing/vishing campaign: a small set of broadcast caller IDs or fake links harvest credentials which are used against many victims.)

## 4. Organisational hierarchy (kingpin -> operator -> mule -> victim)

```
KINGPIN (terminal beneficiary)
  |-- 5001000000001
  |-- 89914700000000000000
  |-- BHOLA RAM RAI
  |-- Mule (layer not established)
  |     |-- 89914500000000000000
  |     |-- 89914400000000000000
  |     |-- 89914600000000000000
  |     |-- SANJAY PRASAD
  |     |-- DEEPAK MAHATO
  |     |-- MANOJ GUPTA
  |     |-- ... 6 more
  |-- Tier-1
  |     |-- 5001000040001
  |     |-- 5001000040002
  |-- Tier-2
  |     |-- 5001000030001
  |     |-- 5001000030002
  |     |-- 5001000030003
  |-- Tier-3
  |     |-- 5001000020001
  |     |-- 5001000020002
  |     |-- 5001000020003
  |     |-- 5001000020004
  |-- OPERATOR (18)
  |     |-- 9431100021
  |     |-- 9431100010
  |     |-- 9431100041
  |     |-- 9431100033
  |     |-- 9431100031
  |     |-- 9431100032
  |     |-- ... 12 more
  |-- VICTIM (20)
  |     |-- 5001000010001
  |     |-- 5001000010002
  |     |-- 5001000010003
  |     |-- 5001000010004
  |     |-- 5001000010005
  |     |-- 5001000010006
  |     |-- ... 14 more
```

### 4.1 Accused / suspect assessment

| Identifier | Type | Role | Tier | Risk | Basis of assessment |
| --- | --- | --- | --- | --- | --- |
| 5001000040001 | account | mule | T1 | 77.7 | pass-through: forwarded 90% of Rs.730,710 inflow; layer position: Tier-1 (hops from cash-out = 1) |
| 5001000000001 | account | kingpin | - | 74.8 | terminal beneficiary: net inflow Rs.707,940; PageRank 0.0581 among top nodes |
| 5001000030001 | account | mule | T2 | 69.6 | pass-through: forwarded 90% of Rs.618,700 inflow; layer position: Tier-2 (hops from cash-out = 2) |
| 5001000020001 | account | mule | T3 | 59.6 | pass-through: forwarded 92% of Rs.465,000 inflow; layer position: Tier-3 (hops from cash-out = 3) |
| 9431100021 | phone | operator | - | 57.2 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: operator |
| 9431100010 | phone | operator | - | 52.6 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: recruiter |
| 9431100041 | phone | operator | - | 52.6 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: mule |
| 89914700000000000000 | sim | kingpin | - | 50.2 | terminal beneficiary: net inflow Rs.0; PageRank 0.0065 among top nodes |
| 5001000020002 | account | mule | T3 | 49.8 | pass-through: forwarded 92% of Rs.207,500 inflow; layer position: Tier-3 (hops from cash-out = 3) |
| 5001000020003 | account | mule | T3 | 48.5 | pass-through: forwarded 92% of Rs.210,000 inflow; layer position: Tier-3 (hops from cash-out = 3) |
| 5001000030002 | account | mule | T2 | 48.1 | pass-through: forwarded 90% of Rs.193,200 inflow; layer position: Tier-2 (hops from cash-out = 2) |
| 9431100033 | phone | operator | - | 46.3 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: mule |
| 9431100032 | phone | operator | - | 46.2 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: mule |
| 9431100031 | phone | operator | - | 46.2 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: mule |
| 5001000040002 | account | mule | T1 | 45.2 | pass-through: forwarded 90% of Rs.55,890 inflow; layer position: Tier-1 (hops from cash-out = 1) |
| 9431100052 | phone | operator | - | 45.2 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: mule |
| BHOLA RAM RAI | person | kingpin | - | 45.1 | terminal beneficiary: net inflow Rs.0; PageRank 0.0027 among top nodes |
| 9431100034 | phone | operator | - | 44.7 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: mule |
| 9431100043 | phone | operator | - | 44.1 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: mule |
| 9431100022 | phone | operator | - | 44.0 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: operator |
| 9431100099 | phone | kingpin | - | 43.3 | terminal beneficiary: net inflow Rs.0; PageRank 0.0066 among top nodes |
| 5001000030003 | account | mule | T2 | 43.0 | pass-through: forwarded 90% of Rs.62,100 inflow; layer position: Tier-2 (hops from cash-out = 2) |
| 356938035643804 | device | operator | - | 43.0 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: operator |
| 9431100051 | phone | operator | - | 42.6 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: mule |
| 89914500000000000000 | sim | mule | - | 42.5 | pass-through: forwarded 0% of Rs.0 inflow; corroborated by narrative markers: mule |
| 89914400000000000000 | sim | mule | - | 42.4 | pass-through: forwarded 0% of Rs.0 inflow; corroborated by narrative markers: mule |
| 9431100042 | phone | operator | - | 42.4 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: mule |
| 89914300000000000000 | sim | operator | - | 42.3 | controls multiple SIM/device identities (telecom-side actor); corroborated by narrative markers: operator |
| bhola.rai@okaxis | upi_id | kingpin | - | 41.9 | terminal beneficiary: net inflow Rs.0; PageRank 0.0033 among top nodes |
| 5001000020004 | account | mule | T3 | 41.1 | pass-through: forwarded 92% of Rs.67,500 inflow; layer position: Tier-3 (hops from cash-out = 3) |

## 5. Financial trail - accounts to be frozen

| Identifier | Type | Bank | UPI handle | Inflow (Rs.) | Outflow (Rs.) | Role | Tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5001000000001 | account | AXIS | bhola.rai@okaxis | 707,940.00 | 0.00 | kingpin | - |
| 5001000040001 | account | UCO | sanjay.prasad@okaxis | 730,710.00 | 657,639.00 | mule | T1 |
| 5001000030001 | account | BOB | manoj.gupta@ybl | 618,700.00 | 556,830.00 | mule | T2 |
| 5001000020001 | account | SBI | deepak.mahato@ybl | 465,000.00 | 427,800.00 | mule | T3 |
| 5001000020003 | account | SBI | sunil.raut@paytm | 210,000.00 | 193,200.00 | mule | T3 |
| 5001000020002 | account | SBI | vikas.mandal@ybl | 207,500.00 | 190,900.00 | mule | T3 |
| 5001000030002 | account | BOB | ravi.yadav@ybl | 193,200.00 | 173,880.00 | mule | T2 |
| 5001000020004 | account | SBI | pintu.sah@okaxis | 67,500.00 | 62,100.00 | mule | T3 |
| 5001000030003 | account | BOB | amit.sinha@paytm | 62,100.00 | 55,890.00 | mule | T2 |
| 5001000040002 | account | UCO | harpender.singh@ybl | 55,890.00 | 50,301.00 | mule | T1 |

### 5.1 Largest recorded transfers

| When | From | To | Amount (Rs.) | Source remark |
| --- | --- | --- | --- | --- |
|  | 5001000040001 | 5001000000001 | 657,639.00 | TXN00016: Rs.657,639.00 5001000040001 -> 5001000000001 [final layer to master ac |
|  | 5001000030001 | 5001000040001 | 556,830.00 | TXN00013: Rs.556,830.00 5001000030001 -> 5001000040001 [layer-2 consolidation] |
|  | 5001000020001 | 5001000030001 | 427,800.00 | TXN00009: Rs.427,800.00 5001000020001 -> 5001000030001 [layer-1 consolidation] |
|  | 5001000010005 | 5001000020001 | 320,000.00 | TXN00006: Rs.192,000.00 5001000010005 -> 5001000020001 [victim debit layer-0] |
|  | 5001000010003 | 5001000020003 | 210,000.00 | TXN00003: Rs.126,000.00 5001000010003 -> 5001000020003 [victim debit layer-0] |
|  | 5001000020003 | 5001000030002 | 193,200.00 | TXN00011: Rs.193,200.00 5001000020003 -> 5001000030002 [layer-1 consolidation] |
|  | 5001000020002 | 5001000030001 | 190,900.00 | TXN00010: Rs.190,900.00 5001000020002 -> 5001000030001 [layer-1 consolidation] |
|  | 5001000030002 | 5001000040001 | 173,880.00 | TXN00014: Rs.173,880.00 5001000030002 -> 5001000040001 [layer-2 consolidation] |
|  | 5001000010001 | 5001000020001 | 145,000.00 | TXN00001: Rs.145,000.00 5001000010001 -> 5001000020001 [victim debit layer-0] |
|  | 5001000010006 | 5001000020002 | 118,000.00 | TXN00008: Rs.118,000.00 5001000010006 -> 5001000020002 [victim debit layer-0] |
|  | 5001000010002 | 5001000020002 | 89,500.00 | TXN00002: Rs.89,500.00 5001000010002 -> 5001000020002 [victim debit layer-0] |
|  | 5001000010004 | 5001000020004 | 67,500.00 | TXN00005: Rs.67,500.00 5001000010004 -> 5001000020004 [victim debit layer-0] |
|  | 5001000020004 | 5001000030003 | 62,100.00 | TXN00012: Rs.62,100.00 5001000020004 -> 5001000030003 [layer-1 consolidation] |
|  | 5001000030003 | 5001000040002 | 55,890.00 | TXN00015: Rs.55,890.00 5001000030003 -> 5001000040002 [layer-2 consolidation] |
|  | 5001000040002 | 5001000000001 | 50,301.00 | TXN00017: Rs.50,301.00 5001000040002 -> 5001000000001 [final layer to master acc |
|  | 5001000050001 | 5001000050002 | 1,525.00 | TXN00018: Rs.763.00 5001000050001 -> 5001000050002 [routine merchant settle] |
|  | 5001000050002 | 5001000050003 | 873.00 | TXN00019: Rs.873.00 5001000050002 -> 5001000050003 [routine merchant settle] |
|  | 5001000050003 | 5001000050001 | 776.00 | TXN00020: Rs.776.00 5001000050003 -> 5001000050001 [routine merchant settle] |

## 6. Victim annexure

| Victim identifier | Type | Amount lost (Rs.) | Paid into |
| --- | --- | --- | --- |
| 9431100005 | phone | 320,000.00 |  |
| 5001000010005 | account | 320,000.00 | 5001000020001 |
| 9431100003 | phone | 210,000.00 |  |
| 5001000010003 | account | 210,000.00 | 5001000020003 |
| 9431100001 | phone | 145,000.00 |  |
| 5001000010001 | account | 145,000.00 | 5001000020001 |
| 9431100006 | phone | 118,000.00 |  |
| 5001000010006 | account | 118,000.00 | 5001000020002 |
| 5001000010002 | account | 89,500.00 | 5001000020002 |
| 9431100002 | phone | 89,500.00 |  |
| 5001000010004 | account | 67,500.00 | 5001000020004 |
| 9431100004 | phone | 67,500.00 |  |
| RAMESH KUMAR SAHU | person | 0.00 |  |
| MOHAMMED IRFAN ANSARI | person | 0.00 |  |
| 89914100000000000000 | sim | 0.00 |  |
| KAVITA MAHATO | person | 0.00 |  |
| PRAKASH ORAON | person | 0.00 |  |
| ASHA LAKRA | person | 0.00 |  |
| 89914200000000000000 | sim | 0.00 |  |
| SUNITA DEVI | person | 0.00 |  |

## 7. Telecom / device evidence

### 7.1 SIM-swap bindings (MSISDN with more than one SIM / re-issued SIM)

| MSISDN | Subscriber | #SIMs | SIM bindings (ICCID, activation, status) |
| --- | --- | --- | --- |
| 9431100001 | - | 2 | 89914100000000000000 since 2021-07-02 (DEACTIVATED); 89914200000000000000 since 2024-03-18 09:30:00 (ACTIVE) |
| 9431100002 | - | 2 | 89914100000000000000 since 2021-07-02 (DEACTIVATED); 89914200000000000000 since 2024-03-18 09:33:00 (ACTIVE) |
| 9431100003 | - | 2 | 89914100000000000000 since 2021-07-02 (DEACTIVATED); 89914200000000000000 since 2024-03-18 09:36:00 (ACTIVE) |
| 9431100004 | - | 2 | 89914100000000000000 since 2021-07-02 (DEACTIVATED); 89914200000000000000 since 2024-03-18 09:39:00 (ACTIVE) |
| 9431100005 | - | 2 | 89914100000000000000 since 2021-07-02 (DEACTIVATED); 89914200000000000000 since 2024-03-18 09:42:00 (ACTIVE) |
| 9431100006 | - | 2 | 89914100000000000000 since 2021-07-02 (DEACTIVATED); 89914200000000000000 since 2024-03-18 09:45:00 (ACTIVE) |

### 7.2 Devices (IMEI) and identities used

| IMEI | #SIMs | #MSISDNs | SIMs | MSISDNs |
| --- | --- | --- | --- | --- |
| 356938035643801 | 2 | 4 | 89914200000000000000, 89914300000000000000 | 9431100001, 9431100003, 9431100005 |
| 356938035643804 | 2 | 4 | 89914200000000000000, 89914300000000000000 | 9431100002, 9431100004, 9431100006 |
| 356938035643101 | 1 | 1 | 89914100000000000000 | 9431100001 |
| 356938035643102 | 1 | 1 | 89914100000000000000 | 9431100002 |
| 356938035643103 | 1 | 1 | 89914100000000000000 | 9431100003 |
| 356938035643104 | 1 | 1 | 89914100000000000000 | 9431100004 |
| 356938035643105 | 1 | 1 | 89914100000000000000 | 9431100005 |
| 356938035643106 | 1 | 1 | 89914100000000000000 | 9431100006 |
| 356938035643201 | 1 | 1 | 89914400000000000000 | 9431100031 |
| 356938035643202 | 1 | 1 | 89914400000000000000 | 9431100032 |
| 356938035643203 | 1 | 1 | 89914400000000000000 | 9431100033 |
| 356938035643204 | 1 | 1 | 89914400000000000000 | 9431100034 |
| 356938035643210 | 1 | 1 | 89914700000000000000 | 9431100010 |
| 356938035643211 | 1 | 1 | 89914500000000000000 | 9431100041 |
| 356938035643212 | 1 | 1 | 89914500000000000000 | 9431100042 |
| 356938035643213 | 1 | 1 | 89914500000000000000 | 9431100043 |
| 356938035643221 | 1 | 1 | 89914600000000000000 | 9431100051 |
| 356938035643222 | 1 | 1 | 89914600000000000000 | 9431100052 |
| 356938035643299 | 1 | 1 | 89914700000000000000 | 9431100099 |
| 356938035643802 | 1 | 1 | 89914300000000000000 | 9431100021 |
| 356938035643803 | 1 | 1 | 89914300000000000000 | 9431100022 |

### 7.3 Call detail record highlights

| Calling MSISDN | Called MSISDN | CDR count | First seen | Note |
| --- | --- | --- | --- | --- |
| 9431100021 | 9431100010 | 1 | - | C00001: 9431100021 -> 9431100010 (84s) tower CEL620 |
| 9431100010 | 9431100021 | 1 | - | C00002: 9431100010 -> 9431100021 (41s) tower CEL975 |
| 9431100022 | 9431100010 | 1 | - | C00003: 9431100022 -> 9431100010 (66s) tower CEL701 |
| 9431100010 | 9431100031 | 1 | - | C00004: 9431100010 -> 9431100031 (42s) tower CEL289 |
| 9431100010 | 9431100032 | 1 | - | C00005: 9431100010 -> 9431100032 (81s) tower CEL624 |
| 9431100010 | 9431100033 | 1 | - | C00006: 9431100010 -> 9431100033 (60s) tower CEL744 |
| 9431100010 | 9431100034 | 1 | - | C00007: 9431100010 -> 9431100034 (69s) tower CEL912 |
| 9431100031 | 9431100041 | 1 | - | C00008: 9431100031 -> 9431100041 (31s) tower CEL196 |
| 9431100032 | 9431100041 | 1 | - | C00009: 9431100032 -> 9431100041 (48s) tower CEL410 |
| 9431100033 | 9431100041 | 1 | - | C00010: 9431100033 -> 9431100041 (29s) tower CEL192 |
| 9431100043 | 9431100052 | 1 | - | C00011: 9431100043 -> 9431100052 (55s) tower CEL651 |
| 9431100021 | 9431100001 | 1 | - | C00012: 9431100021 -> 9431100001 (40s) tower CEL709 |
| 9431100001 | 9431100021 | 1 | - | C00013: 9431100001 -> 9431100021 (20s) tower CEL563 |
| 9431100022 | 9431100002 | 1 | - | C00014: 9431100022 -> 9431100002 (55s) tower CEL738 |
| 9431100021 | 9431100003 | 1 | - | C00015: 9431100021 -> 9431100003 (36s) tower CEL951 |
| 9431100003 | 9431100021 | 1 | - | C00016: 9431100003 -> 9431100021 (24s) tower CEL164 |
| 9431100022 | 9431100004 | 1 | - | C00017: 9431100022 -> 9431100004 (42s) tower CEL136 |
| 9431100021 | 9431100005 | 1 | - | C00018: 9431100021 -> 9431100005 (59s) tower CEL347 |
| 9431100005 | 9431100021 | 1 | - | C00019: 9431100005 -> 9431100021 (8s) tower CEL896 |
| 9431100022 | 9431100006 | 1 | - | C00020: 9431100022 -> 9431100006 (94s) tower CEL434 |

## 8. Timeline of occurrences

| Timestamp | Event | Detail |
| --- | --- | --- |
| 2021-07-02 00:00:00 | sim_event | SIM 89914100000000000000 bound to 9431100001 |
| 2021-07-02 00:00:00 | sim_event | SIM 89914100000000000000 bound to 9431100002 |
| 2021-07-02 00:00:00 | sim_event | SIM 89914100000000000000 bound to 9431100003 |
| 2021-07-02 00:00:00 | sim_event | SIM 89914100000000000000 bound to 9431100004 |
| 2021-07-02 00:00:00 | sim_event | SIM 89914100000000000000 bound to 9431100005 |
| 2021-07-02 00:00:00 | sim_event | SIM 89914100000000000000 bound to 9431100006 |
| 2021-07-02 00:00:00 | sim_activation | SIM 89914100000000000000 activated/re-issued |
| 2023-09-08 00:00:00 | sim_event | SIM 89914700000000000000 bound to 9431100099 |
| 2023-09-08 00:00:00 | sim_activation | SIM 89914700000000000000 activated/re-issued |
| 2023-10-19 00:00:00 | sim_event | SIM 89914700000000000000 bound to 9431100010 |
| 2023-11-05 00:00:00 | sim_event | SIM 89914400000000000000 bound to 9431100031 |
| 2023-11-05 00:00:00 | sim_event | SIM 89914400000000000000 bound to 9431100032 |
| 2023-11-05 00:00:00 | sim_event | SIM 89914400000000000000 bound to 9431100033 |
| 2023-11-05 00:00:00 | sim_event | SIM 89914400000000000000 bound to 9431100034 |
| 2023-11-05 00:00:00 | sim_activation | SIM 89914400000000000000 activated/re-issued |
| 2023-12-01 00:00:00 | sim_event | SIM 89914500000000000000 bound to 9431100041 |
| 2023-12-01 00:00:00 | sim_event | SIM 89914500000000000000 bound to 9431100042 |
| 2023-12-01 00:00:00 | sim_event | SIM 89914500000000000000 bound to 9431100043 |
| 2023-12-01 00:00:00 | sim_activation | SIM 89914500000000000000 activated/re-issued |
| 2024-01-04 00:00:00 | sim_event | SIM 89914600000000000000 bound to 9431100051 |
| 2024-01-04 00:00:00 | sim_event | SIM 89914600000000000000 bound to 9431100052 |
| 2024-01-04 00:00:00 | sim_activation | SIM 89914600000000000000 activated/re-issued |
| 2024-02-11 00:00:00 | sim_event | SIM 89914300000000000000 bound to 9431100021 |
| 2024-02-11 00:00:00 | sim_event | SIM 89914300000000000000 bound to 9431100022 |
| 2024-02-11 00:00:00 | sim_activation | SIM 89914300000000000000 activated/re-issued |
| 2024-03-18 00:00:00 | offence | offence reported to have occurred |
| 2024-03-18 09:30:00 | sim_event | SIM 89914200000000000000 bound to 9431100001 |
| 2024-03-18 09:33:00 | sim_event | SIM 89914200000000000000 bound to 9431100002 |
| 2024-03-18 09:36:00 | sim_event | SIM 89914200000000000000 bound to 9431100003 |
| 2024-03-18 09:39:00 | sim_event | SIM 89914200000000000000 bound to 9431100004 |
| 2024-03-18 09:42:00 | sim_event | SIM 89914200000000000000 bound to 9431100005 |
| 2024-03-18 09:45:00 | sim_event | SIM 89914200000000000000 bound to 9431100006 |
| 2024-03-18 09:45:00 | sim_activation | SIM 89914200000000000000 activated/re-issued |
| 2024-03-19 00:00:00 | report | complaint/FIR lodged |

**Period:** 2021-07-02 00:00:00 to 2024-03-19 00:00:00

## 9. Sections of law invoked

1. BNS 2023, s.318(4) - cheating by impersonation [IPC 419/420]
2. IT Act 2000, s.66C - identity theft (OTP/SIM credentials)
3. IT Act 2000, s.66D - cheating by personation using computer resource
4. BNS 2023, s.61 - criminal conspiracy [IPC 120B]
5. Indian Telegraph Act 1885, s.4 / TRAI regulations - unauthorised SIM acquisition (as applicable)
6. PMLA 2002, s.3 & s.4 - laundering of fraud proceeds (if cross-state fund layering proved)
7. BNS 2023, s.318(4) - cheating by personation [IPC 419/420]
8. IT Act 2000, s.66C - identity theft
9. IT Act 2000, s.67 - false/misleading digital publication
10. BNS 2023, s.318 - cheating [IPC 420]
11. PMLA 2002, s.3 & s.4 - money laundering (bank accounts used for layering)
12. BNS 2023, s.316(4) - criminal breach of trust by banker/agent [IPC 409] (account holders)
13. IT Act 2000, s.67 - obscene material in electronic form
14. BNS 2023, s.351 - criminal intimidation [IPC 503/506]
15. BNS 2023, s.96-99 - outrage of modesty (where applicable) [IPC 354A]
16. IT Act 2000, s.66D - cheating by personation
17. BNS 2023, s.318(4) - cheating by personation [IPC 419]
18. BNS 2023, s.336/338 - forgery [IPC 465/468]
19. BNS 2023, s.340 - using forged document [IPC 471]

_Note: BNS 2023 applies to offences from 01 July 2024; for offences before that date, the 
corresponding IPC sections recorded in brackets are to be invoked. PMLA applicability to be 
confirmed by the IO with the ED regional office._

## 10. Recommended investigation actions

1. Obtain SIM swap/port activation logs, HLR/KYC dump and the porting request records from the operator for each victim MSISDN.
2. Establish time gap between SIM swap timestamp and first fraudulent UPI debit; this is the core causation link for the FIR.
3. Map each re-issued SIM (ICCID) to the operator device (IMEI) used at the time of swap and to the cell tower/CDR location.
4. Question telecom dealer / retailer who processed the port request; verify KYC photo and address submitted at swap.
5. Trace the broadcast caller ID/SMS sender to VoIP/SMPP route; obtain the originating gateway records.
6. Capture the phishing page/domain WHOIS and hosting records; request takedown through CERT-In.
7. Correlate OTP window (5-10 minutes) with debits for every victim to prove OTP relay.
8. Lay down hop-by-hop fund flow chart (victim -> Tier-3 -> Tier-2 -> Tier-1 -> cash-out) as an annexure to the FIR.
9. Attach the pass-through analysis: ratio of inflow immediately re-transferred, to establish knowledge under PMLA s.3.
10. Interrogate Tier-1 mules first (closest to cash-out) and offer collaborator status to lower tiers.
11. Freeze all identified bank accounts / UPI handles of accused and issue notice u/s 91 BNSS (03) 2023 to banks for KYC, IP and device logs.
12. Obtain NPCI mapping (UPI handle -> bank account -> IFSC) and full statement of accounts for last 12 months.
13. Get certified CDRs (call detail records) and IPDR data for accused MSISDNs from telecom operators for the offence period.
14. Flag IMEIs on CEIR/CENTRAL Equipment Identity Register for blocking/recovery; verify IMEI-swap history with operator HLR.
15. Register the complaint on cybercrime.gov.in / NCRP and inform I4C, MHA; report to CERT-In within 6 hours under the CERT-In Directions, 2022.
16. Identify and verify beneficiaries of every withdrawal; obtain ATM/branch CCTV footage and UPI QR/cash-out points.
17. Prepare a seizure memo for devices recovered; extract digital evidence with a certified examiner (ITA s.65B admissibility).

## 11. Intelligence gaps flagged by Bob

- 18 transfer(s) lack timestamps - pull certified statements with value dates.

## 12. Analyst (Bob) key observations

- Pattern verdict: Sim Swap Otp (confidence 100%). 8/19 MSISDNs seen on 2+ devices/SIMs - classic SIM-swap signature (e.g. phone:9431100001, phone:9431100002, phone:9431100003)
- Secondary pattern Phish Vish scores 85% - investigate as a compound modality (same syndicate, different lure).
- Network shape: 132 entities, 254 relationships across 4 connected component(s); documented money trail Rs.3,321,714.
- Hierarchy: 5 kingpin node(s), 18 operator(s), 21 mule account(s) in 4 layer(s), 20 victim node(s). Primary beneficiary 5001000000001 (risk 74.8/99).
- Layering map: Tier-0: 12, Tier-1: 2, Tier-2: 3, Tier-3: 4. Layers closer to Tier-1 are closest to cash-out.
- Victim loss quantified at Rs.1,900,000 across 20 victim identifiers - use as the 'property' line in the FIR.
- Time window of recorded activity: 2021-07-02 00:00:00 to 2024-03-19 00:00:00.
- Telecom evidence: 7 SIM(s) bound to multiple MSISDNs / re-issued - seize swap and porting logs from the operator before they age out.
- Priority interrogations: 5001000040001 (mule, risk 77.7); 5001000000001 (kingpin, risk 74.8); 5001000030001 (mule, risk 69.6).
- Bob scored 132 identifiers and 254 edges using backend 'bob-local-rules-v1' (0 bob-coin calls so far; IBM Bob hook available for narrative expansion).

## Annexures

A. Transaction ledger (certified statements to be obtained under s.91 BNSS)
B. Call detail records of accused MSISDNs
C. SIM / device mapping (ICCID - MSISDN - IMEI)
D. Bank accounts freeze chart with IFSC and KYC status
E. Victim loss chart
F. Network graph (see `report.html` for the interactive graph)
G. Underlying machine-readable analysis (`case_data.json`)

---

**Place:** Jamtara  
**Date:** 28 09 2026  

_______________________________  
Investigating Officer, Cyber Crime PS Jamtara  
Cyber Crime Police Station, Jamtara
