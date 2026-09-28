from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "data" / "cases"
BASE = datetime(2024, 3, 18, 9, 5, 0)


def ts(minute_step: int, start: datetime | None = None) -> str:
    moment = (start or BASE) + timedelta(minutes=minute_step)
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def iccid(prefix: str, index: int) -> str:
    return f"89{prefix}{index:016d}"[:20]


TXN_HEADER = [
    "txn_id", "ts", "from_upi", "from_account", "from_bank", "to_upi", "to_account",
    "to_bank", "amount_inr", "channel", "remarks", "from_name", "to_name",
]


class Ledger:
    def __init__(self, banks: list[str]) -> None:
        self.rows: list[list[object]] = []
        self.step = 0
        self.banks = banks

    def push(self, src, dst, amount: int, remark: str, minute: int = 6) -> None:
        self.step += 1
        self.rows.append([
            f"TXN{self.step:05d}", ts(self.step * minute), src[2], src[0], src[3],
            dst[2], dst[0], dst[3], amount, "UPI", remark, src[1], dst[1],
        ])

    def incoming(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        for row in self.rows:
            totals[row[6]] = totals.get(row[6], 0) + int(row[8])
        return totals


def gen_jamtara(root: Path) -> dict:
    rng = random.Random(11)
    case_dir = root / "jamtara_sim_swap"
    case_dir.mkdir(parents=True, exist_ok=True)

    victims = [
        ("5001000010001", "Ramesh Kumar Sahu", "ramesh.sahu@ybl", "9431100001", 145000, "356938035643101"),
        ("5001000010002", "Sunita Devi", "sunita.devi@okaxis", "9431100002", 89500, "356938035643102"),
        ("5001000010003", "Mohammed Irfan Ansari", "irfan.ansari@ybl", "9431100003", 210000, "356938035643103"),
        ("5001000010004", "Kavita Mahato", "kavita.mahato@paytm", "9431100004", 67500, "356938035643104"),
        ("5001000010005", "Prakash Oraon", "prakash.oraon@ybl", "9431100005", 320000, "356938035643105"),
        ("5001000010006", "Asha Lakra", "asha.lakra@okaxis", "9431100006", 118000, "356938035643106"),
    ]
    t3 = [
        ("5001000020001", "Deepak Mahato", "deepak.mahato@ybl", "9431100031", "356938035643201"),
        ("5001000020002", "Vikas Mandal", "vikas.mandal@ybl", "9431100032", "356938035643202"),
        ("5001000020003", "Sunil Kumar Raut", "sunil.raut@paytm", "9431100033", "356938035643203"),
        ("5001000020004", "Pintu Sah", "pintu.sah@okaxis", "9431100034", "356938035643204"),
    ]
    t2 = [
        ("5001000030001", "Manoj Gupta", "manoj.gupta@ybl", "9431100041", "356938035643211"),
        ("5001000030002", "Ravi Yadav", "ravi.yadav@ybl", "9431100042", "356938035643212"),
        ("5001000030003", "Amit Sinha", "amit.sinha@paytm", "9431100043", "356938035643213"),
    ]
    t1 = [
        ("5001000040001", "Sanjay Prasad", "sanjay.prasad@okaxis", "9431100051", "356938035643221"),
        ("5001000040002", "Harpender Singh", "harpender.singh@ybl", "9431100052", "356938035643222"),
    ]
    kingpin = ("5001000000001", "Bhola Ram Rai", "bhola.rai@okaxis", "9431100099", "356938035643299")
    recruiter = ("Suraj Ekka", "9431100010", "356938035643210")
    operators = [
        ("Bittu Mahto", "9431100021", ["356938035643801", "356938035643802"]),
        ("Kalu Haldar", "9431100022", ["356938035643803", "356938035643804"]),
    ]
    merchants = ["5001000050001", "5001000050002", "5001000050003"]
    banks = ["PNB", "SBI", "BOB", "UCO", "AXIS", "HDFC"]

    ledger = Ledger(banks)
    for idx, (acct, name, upi, phone, loss, imei) in enumerate(victims):
        target = t3[idx % len(t3)]
        parts = 2 if loss > 150000 else 1
        remaining = loss
        for part in range(parts):
            amount = int(remaining * 0.6) if parts == 2 and part == 0 else remaining
            remaining -= amount
            ledger.push(
                (acct, name, upi, banks[idx % len(banks)]),
                (target[0], target[1], target[2], banks[(idx + 2) % len(banks)]),
                amount, "victim debit layer-0",
            )

    incoming = ledger.incoming()
    fwd_plan = {t3[0][0]: t2[0], t3[1][0]: t2[0], t3[2][0]: t2[1], t3[3][0]: t2[2]}
    for acc in t3:
        amount = int(incoming[acc[0]] * 0.92)
        nxt = fwd_plan[acc[0]]
        ledger.push((acc[0], acc[1], acc[2], banks[1]), (nxt[0], nxt[1], nxt[2], banks[2]),
                    amount, "layer-1 consolidation")

    incoming2 = ledger.incoming()
    fwd2 = {t2[0][0]: t1[0], t2[1][0]: t1[0], t2[2][0]: t1[1]}
    for acc in t2:
        amount = int(incoming2[acc[0]] * 0.9)
        nxt = fwd2[acc[0]]
        ledger.push((acc[0], acc[1], acc[2], banks[2]), (nxt[0], nxt[1], nxt[2], banks[3]),
                    amount, "layer-2 consolidation")

    incoming1 = ledger.incoming()
    for acc in t1:
        amount = int(incoming1[acc[0]] * 0.9)
        ledger.push((acc[0], acc[1], acc[2], banks[3]),
                    (kingpin[0], kingpin[1], kingpin[2], banks[4]),
                    amount, "final layer to master account")

    for i in range(4):
        ledger.push(
            (merchants[i % 3], "Kirana Merchant", f"shop{i % 3}@ybl", banks[5]),
            (merchants[(i + 1) % 3], "Kirana Merchant", f"shop{(i + 1) % 3}@ybl", banks[5]),
            rng.randint(300, 900), "routine merchant settle",
        )
    write_csv(case_dir / "02_transactions.csv", TXN_HEADER, ledger.rows)

    cdrs: list[list[object]] = []
    cstep = 0

    def call(a: str, b: str, dur: int, imei_a: str = "", imei_b: str = "") -> None:
        nonlocal cstep
        cstep += 1
        cdrs.append([f"C{cstep:05d}", ts(cstep * 2), a, b, dur, f"CEL{rng.randint(100, 999)}", imei_a, imei_b])

    call(operators[0][1], recruiter[1], 84, operators[0][2][0], recruiter[2])
    call(recruiter[1], operators[0][1], 41, recruiter[2], operators[0][2][0])
    call(operators[1][1], recruiter[1], 66, operators[1][2][0], recruiter[2])
    for acc in t3:
        call(recruiter[1], acc[3], rng.randint(30, 90), recruiter[2], acc[4])
    for acc in t3[:3]:
        call(acc[3], t2[0][3], rng.randint(20, 60), acc[4], t2[0][4])
    call(t2[2][3], t1[1][3], 55, t2[2][4], t1[1][4])
    for idx, (acct, name, upi, phone, loss, imei) in enumerate(victims):
        op = operators[idx % 2]
        call(op[1], phone, rng.randint(35, 110), op[2][idx % 2], imei)
        if idx % 2 == 0:
            call(phone, op[1], rng.randint(8, 25), imei, op[2][idx % 2])
    write_csv(case_dir / "03_call_logs.csv",
              ["call_id", "ts", "msisdn_a", "msisdn_b", "duration_sec", "cell_id", "imei_a", "imei_b"],
              cdrs)

    sims: list[list[object]] = []
    for idx, (acct, name, upi, phone, loss, imei) in enumerate(victims):
        sims.append([phone, iccid("9141", idx + 1), imei, "2021-07-02", "DEACTIVATED", "Jio", "Jamtara",
                     name, "original victim SIM"])
        op = operators[idx % 2]
        sims.append([phone, iccid("9142", idx + 1), op[2][idx % 2], ts(25 + idx * 3), "ACTIVE", "Airtel",
                     "Jamtara", name, "victim SIM reissued after spoofed KYC update"])
    for oi, (name, phone, imeis) in enumerate(operators):
        for si, imei in enumerate(imeis):
            sims.append([phone, iccid("9143", oi * 4 + si + 1), imei, "2024-02-11", "ACTIVE", "Airtel",
                         "Jamtara", name, "operator SIM used for port requests"])
    for i, acc in enumerate(t3):
        sims.append([acc[3], iccid("9144", i + 1), acc[4], "2023-11-05", "ACTIVE", "Jio", "Dumka",
                     acc[1], "money mule SIM linked to rented account"])
    for i, acc in enumerate(t2):
        sims.append([acc[3], iccid("9145", i + 1), acc[4], "2023-12-01", "ACTIVE", "Jio", "Dumka",
                     acc[1], "money mule SIM of second layer"])
    for i, acc in enumerate(t1):
        sims.append([acc[3], iccid("9146", i + 1), acc[4], "2024-01-04", "ACTIVE", "Vodafone", "Deoghar",
                     acc[1], "money mule SIM of final layer"])
    sims.append([recruiter[1], iccid("9147", 1), recruiter[2], "2023-10-19", "ACTIVE", "Jio", "Jamtara",
                 recruiter[0], "recruited account holder"])
    sims.append([kingpin[3], iccid("9147", 2), kingpin[4], "2023-09-08", "ACTIVE", "Airtel", "Ranchi",
                 kingpin[1], "kingpin handset SIM"])
    write_csv(case_dir / "04_sim_device_registry.csv",
              ["msisdn", "iccid", "imei", "activation_date", "status", "provider", "district",
               "owner_name", "remarks"], sims)

    sessions: list[list[object]] = []
    for i, (acct, name, upi, phone, loss, imei) in enumerate(victims):
        sessions.append([f"S{i:04d}", ts(-240 + i * 9), imei, phone, f"49.36.185.{20 + i}", "8.2.1", "23.98", "86.22"])
        op = operators[i % 2]
        sessions.append([f"S{i + 100:04d}", ts(26 + i * 4), op[2][i % 2], phone, f"103.21.58.{10 + i}",
                         "8.2.1", "23.94", "86.11"])
    for i, acc in enumerate(t3):
        sessions.append([f"S{i + 200:04d}", ts(-100 + i * 7), acc[4], acc[3], f"157.32.9.{30 + i}",
                         "7.9.4", "23.88", "86.98"])
    sessions.append(["S300", ts(10), operators[0][2][0], operators[0][1], "103.21.58.4", "8.2.1", "23.94", "86.11"])
    write_csv(case_dir / "05_device_sessions.csv",
              ["session_id", "ts", "imei", "msisdn", "ip_address", "app_version", "latitude", "longitude"],
              sessions)

    write_json(case_dir / "case.json", {
        "case_id": "jamtara_sim_swap",
        "title": "Jamtara SIM-Swap & UPI Mule Network",
        "police_station": "Cyber Crime Police Station, Jamtara",
        "district": "Jamtara",
        "state": "Jharkhand",
        "complainant": "Ramesh Kumar Sahu and 5 other victims",
        "occurred_on": "2024-03-18",
        "reported_on": "2024-03-19",
        "officer": "Investigating Officer, Cyber Crime PS Jamtara",
        "notes": "Mock dataset: Jamtara SIM-swap pattern with 6 victims and 4 mule layers.",
    })
    write_json(case_dir / "truth.json", {
        "case_id": "jamtara_sim_swap",
        "expected_primary": ["SIM_SWAP_OTP"],
        "kingpins": [f"account:{kingpin[0]}"],
        "mules": [f"account:{a[0]}" for a in (t3 + t2 + t1)],
        "victims": [f"account:{v[0]}" for v in victims],
        "min_pattern_confidence": 0.5,
        "thresholds": {"kingpin_f1": 1.0, "mule_f1": 0.8, "victim_f1": 0.9},
    })
    return {"case_id": "jamtara_sim_swap", "dir": case_dir}


def main() -> None:
    from cfna.datagen_cases import generate_all

    for result in generate_all():
        print(f"generated {result['case_id']} -> {result['dir']}")


if __name__ == "__main__":
    main()

