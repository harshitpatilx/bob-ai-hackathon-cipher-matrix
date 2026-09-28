from __future__ import annotations

import random
from pathlib import Path

from cfna.datagen import DATA_ROOT, Ledger, TXN_HEADER, iccid, ts, write_csv, write_json, write_text


def write_jamtara_texts(case_dir: Path) -> None:
    write_text(case_dir / "01_incident_notes.txt", """
INTELLIGENCE NOTE 01 - Cyber Crime Unit, Jamtara (unverified source inputs scrubbed with bank flags and CDR)

KEY FINDING: a sim swap fraud network is operating from Jamtara and Dumka; each loss follows a spoofed KYC update call and a ported SIM on the fraudster handset.
Kingpin Bhola Ram Rai alias Rai Babu holds account 5001000000001 (IFSC PUNB0123456, UPI bhola.rai@okaxis) which is the terminal beneficiary of every layer.
Operator Bittu Mahto (9431100021) runs the SIM desk with burner IMEI 356938035643801 and IMEI 356938035643802.
Operator Kalu Haldar (9431100022) reissues SIMs using burner IMEI 356938035643803 and IMEI 356938035643804.
Recruiter Suraj Ekka (9431100010) sources fresh bank accounts from local youth and hands them to the mule layers.
Mule account 5001000020001 of Deepak Mahato is the entry layer for victim funds from the Jamtara belt.
Mule account 5001000020002 of Vikas Mandal and mule account 5001000020003 of Sunil Kumar Raut also receive victim funds.
Mule account 5001000020004 of Pintu Sah is the fourth entry point.
Mule account 5001000030001 of Manoj Gupta is the second layer which consolidates entry accounts.
Mule account 5001000030002 of Ravi Yadav and mule account 5001000030003 of Amit Sinha complete the second layer.
Mule account 5001000040001 of Sanjay Prasad and mule account 5001000040002 of Harpender Singh form the final layer before the kingpin.
Victim SIMs stop showing network and display no signal minutes before each debit; the OTP is read on the reissued SIM.
CDR places operators Bittu Mahto and Kalu Haldar in contact with recruiter Suraj Ekka on 18/03/2024 between 09:10 and 10:05.
Bank flags show the layered structure where the pass-through ratio of each account stays above ninety percent.
Porting records for the reissued SIMs sit with the telecom dealer; DOT complaint reference JRTP20240318 is pending.
""")

    write_text(case_dir / "06_victim_complaints.txt", """
VICTIM COMPLAINTS - consolidated (6 complaints, PS Jamtara, received 18/03/2024 to 19/03/2024)

Victim Ramesh Kumar Sahu (9431100001) lost Rs.1,45,000 on 18/03/2024 after a caller claimed to be from the bank asking for KYC update.
Victim Sunita Devi (9431100002) lost Rs.89,500 on 18/03/2024 when her SIM showed no signal and the OTP was read by the fraudster.
Victim Mohammed Irfan Ansari (9431100003) lost Rs.2,10,000 on 18/03/2024 through a fake bank verification call.
Victim Kavita Mahato (9431100004) lost Rs.67,500 on 18/03/2024 after clicking a link shared over WhatsApp.
Victim Prakash Oraon (9431100005) lost Rs.3,20,000 on 18/03/2024 after the network went off for two hours.
Victim Asha Lakra (9431100006) lost Rs.1,18,000 on 18/03/2024 after sharing the OTP with a caller posing as bank staff.
Complainant Ramesh Kumar Sahu requests action against the sim swap fraud network operating in Jamtara district.
""")

    write_text(case_dir / "07_accused_statements.txt", """
ACCUSED STATEMENTS - recorded on 20/03/2024 at Cyber Crime Police Station

Accused Deepak Mahato admits that account 5001000020001 was taken on rent and given for commission.
Accused Suraj Ekka states that he recruited five account holders and introduced them to Operator Bittu Mahto.
Accused Sanjay Prasad (PAN BXQPR4521K) admits forwarding the bulk of the credit each time within the hour.
Accused Bittu Mahto admits handling the SIM desk and liaison with the dealer for ported SIMs under Telegram handle @jamtara_ops.
Kingpin Bhola Ram Rai denies everything and claims the terminal account was operated by his nephew.
""")


def gen_ranchi(root: Path) -> dict:
    rng = random.Random(23)
    case_dir = root / "ranchi_fake_task_app"
    case_dir.mkdir(parents=True, exist_ok=True)

    victims = [
        ("5002000010001", "Neeraj Chauhan", "neeraj.chauhan@ybl", "9871200001", 55000, "356938035651101"),
        ("5002000010002", "Pooja Kumari", "pooja.kumari@okaxis", "9871200002", 78000, "356938035651102"),
        ("5002000010003", "Aftab Alam", "aftab.alam@ybl", "9871200003", 120000, "356938035651103"),
        ("5002000010004", "Sarita Gupta", "sarita.gupta@paytm", "9871200004", 95000, "356938035651104"),
        ("5002000010005", "Devendra Mehta", "devendra.mehta@ybl", "9871200005", 60000, "356938035651105"),
        ("5002000010006", "Rina Tigga", "rina.tigga@okaxis", "9871200006", 145000, "356938035651106"),
        ("5002000010007", "Mukesh Sahani", "mukesh.sahani@ybl", "9871200007", 88000, "356938035651107"),
        ("5002000010008", "Jyoti Mishra", "jyoti.mishra@paytm", "9871200008", 70000, "356938035651108"),
    ]
    collectors = [
        ("5002000020001", "Ashok Verma", "ashok.verma@ybl", "9871200021", "356938035651201"),
        ("5002000020002", "Neha Singh", "neha.singh@ybl", "9871200022", "356938035651202"),
    ]
    layers = [
        ("5002000030001", "Faizan Alam", "faizan.alam@ybl", "9871200031", "356938035651211"),
        ("5002000030002", "Ritu Kumari", "ritu.kumari@ybl", "9871200032", "356938035651212"),
    ]
    admin = ("5002000000001", "Rohit Sinha", "rohit.sinha@okaxis", "9871200099", "356938035651299")
    banks = ["PNB", "SBI", "AXIS", "HDFC"]

    ledger = Ledger(banks)
    for idx, (acct, name, upi, phone, loss, imei) in enumerate(victims):
        target = collectors[idx % 2]
        ledger.push((acct, name, upi, banks[idx % 4]), (target[0], target[1], target[2], banks[1]),
                    loss, "recharge task payment", minute=7)

    incoming = ledger.incoming()
    for c in collectors:
        half = int(incoming[c[0]] * 0.45)
        ledger.push((c[0], c[1], c[2], banks[1]), (layers[0][0], layers[0][1], layers[0][2], banks[2]),
                    half, "upline transfer")
        ledger.push((c[0], c[1], c[2], banks[1]), (layers[1][0], layers[1][1], layers[1][2], banks[2]),
                    int(incoming[c[0]] * 0.9) - half, "upline transfer")

    incoming2 = ledger.incoming()
    for l in layers:
        ledger.push((l[0], l[1], l[2], banks[2]), (admin[0], admin[1], admin[2], banks[3]),
                    int(incoming2[l[0]] * 0.9), "consolidation to admin")

    for i in range(4):
        ledger.push(
            (f"500200005000{i}", "Society Club", f"club{i}@ybl", banks[0]),
            (f"500200005000{(i + 1) % 4}", "Society Club", f"club{(i + 1) % 4}@ybl", banks[0]),
            rng.randint(200, 700), "routine settle",
        )
    write_csv(case_dir / "02_transactions.csv", TXN_HEADER, ledger.rows)

    sessions: list[list[object]] = []
    for i, (acct, name, upi, phone, loss, imei) in enumerate(victims):
        sessions.append([f"S{i:04d}", ts(-300 + i * 6), imei, phone, f"157.32.44.{10 + i}",
                         "2.4.7", "23.34", "85.33"])
    for i, c in enumerate(collectors):
        sessions.append([f"S{i + 50:04d}", ts(-60 + i * 5), c[4], c[3], f"157.32.44.{60 + i}",
                         "2.4.7", "23.34", "85.33"])
    sessions.append(["S90", ts(40), admin[4], admin[3], "49.207.188.9", "2.4.7", "25.61", "85.14"])
    write_csv(case_dir / "05_device_sessions.csv",
              ["session_id", "ts", "imei", "msisdn", "ip_address", "app_version", "latitude", "longitude"],
              sessions)

    write_text(case_dir / "01_incident_notes.txt", """
INTELLIGENCE NOTE 01 - Ranchi Cyber Cell (fake earning app and task racket)

KEY FINDING: victims were added to a Telegram group promising daily investment returns against small recharge tasks.
Coach Rohit Sinha (9871200010) administers the group and pushes premium plan upgrades with assured profit.
Collector account 5002000020001 of Ashok Verma takes recharge payments from four victims.
Collector account 5002000020002 of Neha Singh takes recharge payments from the remaining victims.
Layer account 5002000030001 of Faizan Alam and layer account 5002000030002 of Ritu Kumari collect the pooled amount.
Admin account 5002000000001 of mastermind Rohit Sinha is where the consolidated amount lands.
Each collector keeps only a commission so the balance moves out the same day.
The group offers bonus credit on every completed task and later demands a recharge for the refund release.
App package com.quick.task.pro was installed from an external link, not from the play store.
""")

    write_text(case_dir / "06_victim_complaints.txt", """
VICTIM COMPLAINTS - consolidated (8 complaints, PS Kanke Road, Ranchi)

Victim Neeraj Chauhan (9871200001) paid Rs.55,000 towards a task recharge on 05/03/2024 and got nothing back.
Victim Pooja Kumari (9871200002) paid Rs.78,000 on 05/03/2024 after the coach promised daily investment returns.
Victim Aftab Alam (9871200003) paid Rs.1,20,000 on 06/03/2024 for a premium plan unlock.
Victim Sarita Gupta (9871200004) paid Rs.95,000 on 06/03/2024 chasing the task bonus.
Victim Devendra Mehta (9871200005) paid Rs.60,000 on 07/03/2024 for group entry renewal.
Victim Rina Tigga (9871200006) paid Rs.1,45,000 on 07/03/2024 after two small task payouts arrived first.
Victim Mukesh Sahani (9871200007) paid Rs.88,000 on 08/03/2024 for a guaranteed return package.
Victim Jyoti Mishra (9871200008) paid Rs.70,000 on 08/03/2024 when asked for a top-up to release profits.
""")

    write_text(case_dir / "07_accused_statements.txt", """
ACCUSED STATEMENTS - recorded on 12/03/2024

Accused Ashok Verma admits receiving the recharge amounts and keeping a commission before passing the balance.
Accused Neha Singh admits using her account for the task collections shown in the group.
Accused Faizan Alam admits receiving pooled amounts from both collectors.
Accused Rohit Sinha (PAN CNNPS8876L) denies admin access and claims the Telegram handle was stolen.
""")

    write_json(case_dir / "case.json", {
        "case_id": "ranchi_fake_task_app",
        "title": "Ranchi Fake Task App Investment Scam",
        "police_station": "PS Kanke Road, Ranchi",
        "district": "Ranchi",
        "state": "Jharkhand",
        "complainant": "8 victims (aggregated)",
        "occurred_on": "2024-03-05",
        "reported_on": "2024-03-09",
        "officer": "Investigating Officer, Cyber Crime Ranchi",
        "notes": "Mock dataset: fake task/investment app scam with collector and layer accounts.",
    })
    write_json(case_dir / "truth.json", {
        "case_id": "ranchi_fake_task_app",
        "expected_primary": ["TASK_INVESTMENT_SCAM"],
        "kingpins": [f"account:{admin[0]}"],
        "mules": [f"account:{c[0]}" for c in collectors] + [f"account:{l[0]}" for l in layers],
        "victims": [f"account:{v[0]}" for v in victims],
        "min_pattern_confidence": 0.45,
        "thresholds": {"kingpin_f1": 1.0, "mule_f1": 0.8, "victim_f1": 0.9},
    })
    return {"case_id": "ranchi_fake_task_app", "dir": case_dir}


def gen_kolkata(root: Path) -> dict:
    rng = random.Random(37)
    case_dir = root / "kolkata_vishing_blast"
    case_dir.mkdir(parents=True, exist_ok=True)

    victims = [
        ("5003000010001", "Sourav Banerjee", "sourav.banerjee@ybl", "9003100001", 64000, "356938035661101"),
        ("5003000010002", "Priya Das", "priya.das@okaxis", "9003100002", 47500, "356938035661102"),
        ("5003000010003", "Imran Sheikh", "imran.sheikh@ybl", "9003100003", 132000, "356938035661103"),
        ("5003000010004", "Rupa Ghosh", "rupa.ghosh@paytm", "9003100004", 38000, "356938035661104"),
        ("5003000010005", "Tanmay Roy", "tanmay.roy@ybl", "9003100005", 215000, "356938035661105"),
        ("5003000010006", "Nazia Khan", "nazia.khan@okaxis", "9003100006", 52000, "356938035661106"),
        ("5003000010007", "Arjun Dutta", "arjun.dutta@ybl", "9003100007", 89000, "356938035661107"),
        ("5003000010008", "Moumita Pal", "moumita.pal@paytm", "9003100008", 143000, "356938035661108"),
        ("5003000010009", "Rakesh Agarwal", "rakesh.agarwal@ybl", "9003100009", 76000, "356938035661109"),
    ]
    collectors = [
        ("5003000020001", "Bikash Mondal", "bikash.mondal@ybl", "9003100021", "356938035661201"),
        ("5003000020002", "Sneha Sarkar", "sneha.sarkar@ybl", "9003100022", "356938035661202"),
        ("5003000020003", "Javed Ansari", "javed.ansari@ybl", "9003100023", "356938035661203"),
    ]
    layer = ("5003000030001", "Deepak Roy", "deepak.roy@ybl", "9003100031", "356938035661211")
    cashout = ("5003000000001", "Anup Saha", "anup.saha@okaxis", "9003100099", "356938035661299")
    visher = "9003199999"
    banks = ["UCO", "SBI", "AXIS", "PNB"]

    ledger = Ledger(banks)
    for idx, (acct, name, upi, phone, loss, imei) in enumerate(victims):
        target = collectors[idx % 3]
        ledger.push((acct, name, upi, banks[idx % 4]), (target[0], target[1], target[2], banks[1]),
                    loss, "UPI debit after vishing call", minute=8)

    incoming = ledger.incoming()
    for c in collectors:
        ledger.push((c[0], c[1], c[2], banks[1]), (layer[0], layer[1], layer[2], banks[2]),
                    int(incoming[c[0]] * 0.9), "collector consolidation")

    incoming2 = ledger.incoming()
    ledger.push((layer[0], layer[1], layer[2], banks[2]), (cashout[0], cashout[1], cashout[2], banks[3]),
                int(incoming2[layer[0]] * 0.9), "layer to cashout")

    for i in range(3):
        ledger.push(
            (f"500300005000{i}", "Tea Stall", f"tea{i}@ybl", banks[0]),
            (f"500300005000{(i + 1) % 3}", "Tea Stall", f"tea{(i + 1) % 3}@ybl", banks[0]),
            rng.randint(150, 600), "routine settle",
        )
    write_csv(case_dir / "02_transactions.csv", TXN_HEADER, ledger.rows)

    cdrs: list[list[object]] = []
    cstep = 0

    def call(a: str, b: str, dur: int, imei_a: str = "", imei_b: str = "") -> None:
        nonlocal cstep
        cstep += 1
        cdrs.append([f"C{cstep:05d}", ts(cstep * 3), a, b, dur, f"CEL{rng.randint(100, 999)}", imei_a, imei_b])

    for idx, (acct, name, upi, phone, loss, imei) in enumerate(victims):
        call(visher, phone, rng.randint(25, 95), "", imei)
    for acc in collectors:
        call(acc[3], layer[3], rng.randint(20, 50), acc[4], layer[4])
    write_csv(case_dir / "03_call_logs.csv",
              ["call_id", "ts", "msisdn_a", "msisdn_b", "duration_sec", "cell_id", "imei_a", "imei_b"],
              cdrs)

    sessions: list[list[object]] = []
    for i, (acct, name, upi, phone, loss, imei) in enumerate(victims):
        sessions.append([f"S{i:04d}", ts(-320 + i * 5), imei, phone, f"103.60.12.{10 + i}",
                         "5.1.0", "22.57", "88.36"])
    for i, c in enumerate(collectors):
        sessions.append([f"S{i + 60:04d}", ts(-40 + i * 4), c[4], c[3], f"103.60.12.{60 + i}",
                         "5.1.0", "22.57", "88.36"])
    sessions.append(["S95", ts(55), cashout[4], cashout[3], "49.36.221.7", "5.1.0", "22.57", "88.36"])
    write_csv(case_dir / "05_device_sessions.csv",
              ["session_id", "ts", "imei", "msisdn", "ip_address", "app_version", "latitude", "longitude"],
              sessions)

    write_text(case_dir / "01_incident_notes.txt", """
INTELLIGENCE NOTE 01 - Kolkata Cyber Cell (spoofed bank customer care vishing blast)

KEY FINDING: a vishing campaign is running from VoIP number 9003199999 which blasts a fake bank customer care message carrying a KYC verification link.
The phishing page harvests the OTP and the credentials are used for immediate UPI transfers.
Broadcast number 9003199999 contacted nine victims without any inbound call to that number.
Beneficiary account 5003000020001 of Bikash Mondal is a mule account receiving the first layer of debits.
Beneficiary account 5003000020002 of Sneha Sarkar and beneficiary account 5003000020003 of Javed Ansari share the remaining debits.
Layer account 5003000030001 of Deepak Roy consolidates all three beneficiary accounts.
Cashout account 5003000000001 of mastermind Anup Saha is the terminal holder of the fraud proceeds.
Call recordings confirm the script used fake bank customer care lines and account blocked warnings.
""")

    write_text(case_dir / "06_victim_complaints.txt", """
VICTIM COMPLAINTS - consolidated (9 complaints, Kolkata city, received 06/03/2024)

Victim Sourav Banerjee (9003100001) lost Rs.64,000 on 06/03/2024 after entering the OTP on a fake verification page.
Victim Priya Das (9003100002) lost Rs.47,500 on 06/03/2024 after the caller warned her account blocked.
Victim Imran Sheikh (9003100003) lost Rs.1,32,000 on 06/03/2024 after clicking the KYC link received over SMS.
Victim Rupa Ghosh (9003100004) lost Rs.38,000 on 06/03/2024 after sharing the OTP with a customer care caller.
Victim Tanmay Roy (9003100005) lost Rs.2,15,000 on 07/03/2024 after completing the video verification fraud step.
Victim Nazia Khan (9003100006) lost Rs.52,000 on 07/03/2024 after the caller claimed pending refund approval.
Victim Arjun Dutta (9003100007) lost Rs.89,000 on 07/03/2024 after the fake helpline call.
Victim Moumita Pal (9003100008) lost Rs.1,43,000 on 08/03/2024 after entering card details on the phishing page.
Victim Rakesh Agarwal (9003100009) lost Rs.76,000 on 08/03/2024 after the verification call turned into a transfer request.
""")

    write_text(case_dir / "07_accused_statements.txt", """
ACCUSED STATEMENTS - recorded on 11/03/2024

Accused Bikash Mondal admits allowing his account to receive the first layer of credits for a commission.
Accused Sneha Sarkar admits receiving debits routed from the vishing campaign.
Accused Deepak Roy admits consolidating amounts before passing them onward.
Accused Anup Saha (PAN ABBPS2291F) denies operating the cashout account and blames a stolen cheque book.
""")

    write_json(case_dir / "case.json", {
        "case_id": "kolkata_vishing_blast",
        "title": "Kolkata Spoofed Customer Care Vishing Blast",
        "police_station": "Cyber Crime Cell, Kolkata Police",
        "district": "Kolkata",
        "state": "West Bengal",
        "complainant": "9 victims (aggregated)",
        "occurred_on": "2024-03-06",
        "reported_on": "2024-03-06",
        "officer": "Investigating Officer, Cyber Crime Cell Kolkata",
        "notes": "Mock dataset: vishing blast with broadcast caller, beneficiary mules and cashout.",
    })
    write_json(case_dir / "truth.json", {
        "case_id": "kolkata_vishing_blast",
        "expected_primary": ["PHISH_VISH"],
        "kingpins": [f"account:{cashout[0]}"],
        "mules": [f"account:{c[0]}" for c in collectors] + [f"account:{layer[0]}"],
        "victims": [f"account:{v[0]}" for v in victims],
        "min_pattern_confidence": 0.5,
        "thresholds": {"kingpin_f1": 1.0, "mule_f1": 0.8, "victim_f1": 0.9},
    })
    return {"case_id": "kolkata_vishing_blast", "dir": case_dir}


def generate_all(root: Path | None = None) -> list[dict]:
    from cfna.datagen import gen_jamtara

    target = root or DATA_ROOT
    target.mkdir(parents=True, exist_ok=True)
    results = []
    jamtara = gen_jamtara(target)
    write_jamtara_texts(jamtara["dir"])
    results.append(jamtara)
    results.append(gen_ranchi(target))
    results.append(gen_kolkata(target))
    return results


def main() -> None:
    for result in generate_all():
        print(f"generated {result['case_id']} -> {result['dir']}")


if __name__ == "__main__":
    main()

