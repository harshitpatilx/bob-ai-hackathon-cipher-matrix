from __future__ import annotations

import re

# Local input form (`cfna serve`). The report nav links to it, so keep the port in sync
# with the `serve` sub-command defaults in cli.py.
INPUT_UI_HOST = "127.0.0.1"
INPUT_UI_PORT = 8765
INPUT_UI_URL = f"http://{INPUT_UI_HOST}:{INPUT_UI_PORT}/"

UPI_RE = re.compile(r"(?<![\w@+.-])([a-z0-9][a-z0-9._-]{1,63}@[a-z]{2,32})(?![\w@])", re.I)
EMAIL_RE = re.compile(r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,})\b")
HANDLE_RE = re.compile(r"(?<![\w@])@([a-z0-9_]{4,40})\b", re.I)
PHONE_RE = re.compile(r"(?:(?:\+|00)91[-\s]?)?(?<!\d)([6-9]\d{9})(?!\d)")
IMEI_RE = re.compile(r"(?<!\d)(\d{15})(?!\d)")
ICCID_RE = re.compile(r"(?<!\d)(89\d{16,20})(?!\d)")
IFSC_RE = re.compile(r"\b([A-Z]{4}0[A-Z0-9]{6})\b")
PAN_RE = re.compile(r"\b([A-Z]{5}\d{4}[A-Z])\b")
AADHAAR_RE = re.compile(r"(?<!\d)(\d{4}[\s-]\d{4}[\s-]\d{4})(?!\d)")
IPV4_RE = re.compile(r"\b((?:\d{1,3}\.){3}\d{1,3})\b")
CARD_RE = re.compile(r"(?<!\d)([456]\d{15})(?!\d)")
ACCOUNT_RE = re.compile(r"(?<!\d)(\d{9,18})(?!\d)")
MONEY_RE = re.compile(r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.I)
MONEY_WORD_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*(crores?|cr|lakhs?|lacs?|lac)\b", re.I)
DATE_RE = re.compile(r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2})\b")
TIME_RE = re.compile(r"\b([01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\b")
NAME_AFTER_RE = re.compile(
    r"\b(?i:accused|kingpin|mastermind|complainant|victim|recruiter|operator|mule|coach|"
    r"name\s*(?:of)?|a/n|s/o|d/o|r/o|w/o|shri|smt|mrs|mr|ms)\s*:?\s*"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})"
)
NAME_FIELD_RE = re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})$")
DISTRICT_RE = re.compile(
    r"\b(?i:r/o|vill\.?|village|located at|based in|district|dist\.)\s+"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"
)

UPI_PSP = {
    "ybl", "okaxis", "okicici", "oksbi", "okhdfcbank", "okaxis", "ibbl", "icici", "sbi",
    "axis", "hdfc", "kotak", "pnb", "bob", "cnrb", "ubin", "indianbank", "federal", "idbi",
    "csb", "airtel", "freecharge", "mobikwik", "amazonpay", "paytm", "jio", "yesb", "dcb",
    "tjsb", "ratnakar", "indus", "unionbank", "canara", "iob", "apl", "bl", "jd", "axl",
    "upi", "ok", "tjx", "apl", "kmb", "tmob", "payz", "ybl", "ib", "pnb", "airpay",
    "aiou", "jd", "apl", "svcl", "tsl", "ijp", "apl",
}

NAME_STOPWORDS = {
    "the", "of", "and", "for", "accused", "named", "fraud", "cyber", "police", "station",
    "district", "bank", "account", "phone", "sim", "card", "upi", "amount", "rupees",
    "mr", "mrs", "ms", "shri", "smt", "case", "file", "fir", "number", "from", "this",
    "that", "with", "complaint", "reported", "offence", "offense", "village", "ward",
    "road", "nagar", "colony", "block", "ps", "sho", "io", "nobody", "unknown",
}

ROLE_MARKERS: dict[str, list[str]] = {
    "kingpin": [
        "kingpin", "mastermind", "master mind", "brain behind", "ringleader",
        "ring leader", "syndicate head", "top of the syndicate", "king pin",
        "master account", "mastermind's", "controlling account", "hawala main",
    ],
    "operator": [
        "sim swap operator", "swapper", "technical operator", "handles the sim",
        "handled the sim", "device operator", "otp relay", "executes the swap",
        "swap technician", "tech guy", "operator ", "operators ",
    ],
    "recruiter": [
        "recruited", "recruiter", "procured the bank", "procured bank accounts",
        "onboarded", "arranged mules", "supplies accounts", "account supplier",
        "brought in mules", "hired mules",
    ],
    "mule": [
        "mule", "money mule", "rented account", "rent account", "on rent",
        "benami account", "leased the account", "let out the account",
        "used his account for passing", "pass-through",
    ],
    "victim": [
        "victim", "complainant", "defrauded", "duped", "cheated of", "lost ₹",
        "lost rs", "lost inr", "suffered a loss", "first information report by",
    ],
    "accused": ["accused", "suspect", "named person", "co-accused"],
}

TRANSFER_VERBS = r"(?:transferred|paid|credited|debited|sent|moved|deposit(?:ed)?|withdrawn|withdraw|paid out)"
LOSS_VERBS = (
    r"(?:lost|losing|lose|defrauded(?:\s+of)?|cheated\s+(?:of|out\s+of)?|duped(?:\s+of)?|"
    r"swindled(?:\s+of)?|siphoned(?:\s+from)?|misappropriated|scammed(?:\s+of)?|"
    r"suffered\s+a\s+loss(?:\s+of)?|fraudulently\s+withdrawn)"
)
ROLE_LABEL_SET = {"kingpin", "operator", "recruiter", "mule", "victim"}
SENTENCE_SPLIT = re.compile(r"(?<=[.!?\n])\s+")

TEXT_LINK_PATTERNS: list[tuple[re.Pattern[str], str, float]] = [
    (re.compile(r"imei\s+(\d{15})\s+(?:was\s+)?(?:linked|mapped|used)\s+(?:with|to)\s+(?:the\s+)?sim\s+([\d]{18,22})", re.I), "device_sim", 2.0),
    (re.compile(r"same\s+device\s+(?:was\s+)?(?:used|seen)\s+for\s+(.+)", re.I), "same_device", 1.2),
    (re.compile(r"([\d]{18,22})\s+(?:was\s+)?(?:ported|activated|reissued|swapped)", re.I), "sim_swap", 1.5),
    (re.compile(r"(?:belongs to|belonging to|owned by|in the name of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.I), "owned_by", 1.4),
    (re.compile(r"(?:operated by|controlled by|handled by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.I), "controlled_by", 1.4),
]

SIM_SWAP_KW = ["sim swap", "sim swap fraud", "sim port", "ported", "reissued sim", "reissued", "replacement sim", "otp", "one time password", "sim blocked", "network went off", "no signal", "kyc update", "sim hijack", "hijacked sim", "duplicate sim", "sim cloned"]
TASK_KW = ["task", "investment", "returns", "profit", "recharge", "group", "coach", "premium plan", "refund of", "click work", "earning app", "bonus"]
PHISH_KW = ["phishing", "vishing", "verification", "kyc", "update your", "customer care", "helpline", "fake link", "otp", "blocked account", "refund pending", "branch office"]
LOAN_KW = ["loan app", "instant loan", "interest", "blackmail", "obscene", "morphed", "contact list", "extortion", "recover the amount"]
IDENTITY_KW = ["kyc", "aadhaar", "pan card", "video kyc", "identity", "forged", "fake id", "documents submitted", "in the name of another"]
CARD_KW = ["skimmer", "cloned card", "atm", "pos machine", "cvv", "magstripe", "card details", "swiped"]
SEXTORTION_KW = ["video call", "obscene", "blackmail", "morphed video", "explicit", "telegram"]
ROMANCE_KW = ["lover", "dating", "matrimony", "girlfriend", "boyfriend", "nude", "honeytrap"]

LEGAL_COMMON = [
    "IT Act 2000, s.66C - identity theft (personation using electronic signature/password)",
    "IT Act 2000, s.66D - cheating by personation using computer resource",
    "IT Act 2000, s.43 - unauthorised access / damage to computer system (read with s.66)",
    "BNS 2023, s.318(4) - cheating by personation [IPC 419]; s.318 - cheating [IPC 420]",
    "BNS 2023, s.61 - criminal conspiracy [IPC 120B]",
]

LEGAL_BY_PATTERN: dict[str, list[str]] = {
    "SIM_SWAP_OTP": [
        "BNS 2023, s.318(4) - cheating by impersonation [IPC 419/420]",
        "IT Act 2000, s.66C - identity theft (OTP/SIM credentials)",
        "IT Act 2000, s.66D - cheating by personation using computer resource",
        "BNS 2023, s.61 - criminal conspiracy [IPC 120B]",
        "Indian Telegraph Act 1885, s.4 / TRAI regulations - unauthorised SIM acquisition (as applicable)",
        "PMLA 2002, s.3 & s.4 - laundering of fraud proceeds (if cross-state fund layering proved)",
    ],
    "MULE_CHAIN": [
        "BNS 2023, s.318 - cheating [IPC 420]",
        "IT Act 2000, s.66D - cheating by personation using computer resource",
        "BNS 2023, s.61 - criminal conspiracy [IPC 120B]",
        "PMLA 2002, s.3 & s.4 - money laundering (bank accounts used for layering)",
        "BNS 2023, s.316(4) - criminal breach of trust by banker/agent [IPC 409] (account holders)",
    ],
    "TASK_INVESTMENT_SCAM": [
        "BNS 2023, s.318 - cheating [IPC 420]",
        "BNS 2023, s.61 - criminal conspiracy [IPC 120B]",
        "IT Act 2000, s.66D - cheating by personation using computer resource",
        "IT Act 2000, s.67 - publishing misleading material (app/group content)",
        "PMLA 2002, s.3 & s.4 - proceeds of crime",
    ],
    "PHISH_VISH": [
        "BNS 2023, s.318(4) - cheating by personation [IPC 419/420]",
        "IT Act 2000, s.66C - identity theft",
        "IT Act 2000, s.66D - cheating by personation using computer resource",
        "IT Act 2000, s.67 - false/misleading digital publication",
        "BNS 2023, s.61 - criminal conspiracy [IPC 120B]",
    ],
    "LOAN_APP_EXTORTION": [
        "BNS 2023, s.308/309 - extortion / extortion with threat [IPC 383/384]",
        "IT Act 2000, s.66D - cheating by personation using computer resource",
        "IT Act 2000, s.67 - publication of obscene/morphed material in electronic form",
        "BNS 2023, s.351 - criminal intimidation [IPC 503/506]",
        "PMLA 2002, s.3 & s.4 - proceeds of crime",
    ],
    "IDENTITY_KYC_FRAUD": [
        "IT Act 2000, s.66C - identity theft",
        "IT Act 2000, s.66D - cheating by personation",
        "BNS 2023, s.318(4) - cheating by personation [IPC 419]",
        "BNS 2023, s.336/338 - forgery [IPC 465/468]",
        "BNS 2023, s.340 - using forged document [IPC 471]",
    ],
    "CARD_CLONING": [
        "IT Act 2000, s.66C - identity theft (card credentials)",
        "BNS 2023, s.303 - theft [IPC 379]",
        "BNS 2023, s.318 - cheating [IPC 420]",
        "BNS 2023, s.61 - criminal conspiracy [IPC 120B]",
    ],
    "SEXTORTION": [
        "IT Act 2000, s.67 - obscene material in electronic form",
        "BNS 2023, s.351 - criminal intimidation [IPC 503/506]",
        "BNS 2023, s.96-99 - outrage of modesty (where applicable) [IPC 354A]",
        "BNS 2023, s.61 - criminal conspiracy [IPC 120B]",
    ],
    "ROMANCE_HONEYTRAP": [
        "BNS 2023, s.318 - cheating [IPC 420]",
        "BNS 2023, s.61 - criminal conspiracy [IPC 120B]",
        "IT Act 2000, s.66D - cheating by personation",
        "PMLA 2002, s.3 & s.4 - proceeds of crime",
    ],
}

ACTIONS_COMMON = [
    "Freeze all identified bank accounts / UPI handles of accused and issue notice u/s 91 BNSS (03) 2023 to banks for KYC, IP and device logs.",
    "Obtain NPCI mapping (UPI handle -> bank account -> IFSC) and full statement of accounts for last 12 months.",
    "Get certified CDRs (call detail records) and IPDR data for accused MSISDNs from telecom operators for the offence period.",
    "Flag IMEIs on CEIR/CENTRAL Equipment Identity Register for blocking/recovery; verify IMEI-swap history with operator HLR.",
    "Register the complaint on cybercrime.gov.in / NCRP and inform I4C, MHA; report to CERT-In within 6 hours under the CERT-In Directions, 2022.",
    "Identify and verify beneficiaries of every withdrawal; obtain ATM/branch CCTV footage and UPI QR/cash-out points.",
    "Prepare a seizure memo for devices recovered; extract digital evidence with a certified examiner (ITA s.65B admissibility).",
]

ACTIONS_BY_PATTERN: dict[str, list[str]] = {
    "SIM_SWAP_OTP": [
        "Obtain SIM swap/port activation logs, HLR/KYC dump and the porting request records from the operator for each victim MSISDN.",
        "Establish time gap between SIM swap timestamp and first fraudulent UPI debit; this is the core causation link for the FIR.",
        "Map each re-issued SIM (ICCID) to the operator device (IMEI) used at the time of swap and to the cell tower/CDR location.",
        "Question telecom dealer / retailer who processed the port request; verify KYC photo and address submitted at swap.",
    ],
    "MULE_CHAIN": [
        "Lay down hop-by-hop fund flow chart (victim -> Tier-3 -> Tier-2 -> Tier-1 -> cash-out) as an annexure to the FIR.",
        "Attach the pass-through analysis: ratio of inflow immediately re-transferred, to establish knowledge under PMLA s.3.",
        "Interrogate Tier-1 mules first (closest to cash-out) and offer collaborator status to lower tiers.",
    ],
    "TASK_INVESTMENT_SCAM": [
        "Preserve group/app data (Telegram/WhatsApp group membership, recharge wallet IDs) from victim devices.",
        "Trace recharge wallet top-ups to the exchange/crypto rails; issue freezing request to virtual-asset service providers.",
        "Identify the 'coach/admin' handles controlling the group and map them to payout accounts.",
    ],
    "PHISH_VISH": [
        "Trace the broadcast caller ID/SMS sender to VoIP/SMPP route; obtain the originating gateway records.",
        "Capture the phishing page/domain WHOIS and hosting records; request takedown through CERT-In.",
        "Correlate OTP window (5-10 minutes) with debits for every victim to prove OTP relay.",
    ],
    "LOAN_APP_EXTORTION": [
        "Seize victim handsets and recover app APKs, contact list uploads and loan-agreement screenshots.",
        "Extract money collection accounts from the app config and freeze them; report app on NCRP.",
        "Record statements on morphed-pornography blackmail; register separate offence for extortion calls.",
    ],
    "IDENTITY_KYC_FRAUD": [
        "Compare KYC documents submitted against bank records; obtain genuine document holders' statement.",
        "Check whether one Aadhaar/PAN/photograph is mapped to multiple accounts across banks (mule KYC cloning).",
    ],
    "CARD_CLONING": [
        "Obtain ATM/POS CCTV and transaction logs; match card numbers to skimming incidents.",
        "Coordinate with acquiring bank for chargeback and card-block confirmation.",
    ],
    "SEXTORTION": [
        "Preserve chat/transaction records from victim device; obtain Telegram handle ownership records.",
        "Do not publish victim identity; follow victim-sensitive procedure under CrPC/BNSS victim protocol.",
    ],
    "ROMANCE_HONEYTRAP": [
        "Map all profiles/photographs used by the accused; obtain platform account creation IP logs.",
        "Trace 'processing fee' / 'custom duty' payments to beneficiary accounts and freeze.",
    ],
}

PATTERN_SUMMARY: dict[str, str] = {
    "SIM_SWAP_OTP": "SIM-swap / OTP-relay fraud: telecom identity is hijacked, victim SIM is re-issued to the syndicate, OTPs are read on their device and UPI debits are executed.",
    "MULE_CHAIN": "Layered money-mule network: funds hop through serial pass-through accounts with near-full forwarding before cash-out.",
    "TASK_INVESTMENT_SCAM": "Fake task/investment work scam: many victims are induced to 'recharge' for task bonuses into a small set of collector accounts.",
    "PHISH_VISH": "Phishing/vishing campaign: a small set of broadcast caller IDs or fake links harvest credentials which are used against many victims.",
    "LOAN_APP_EXTORTION": "Instant-loan-app extortion: small disbursals are followed by morphed-image blackmail and recovery calls.",
    "IDENTITY_KYC_FRAUD": "Identity/KYC fraud: forged or stolen Aadhaar/PAN/video-KYC is used to open mule accounts or impersonate victims.",
    "CARD_CLONING": "Card cloning / ATM-POS skimming: cloned credentials are used at ATM/POS endpoints.",
    "SEXTORTION": "Sextortion: explicit video/chat leverage used to extract money through UPI.",
    "ROMANCE_HONEYTRAP": "Romance/honeytrap fraud: fake relationships used to extract 'fees', 'duty' or 'medical' money.",
}

PATTERN_ORDER = [
    "SIM_SWAP_OTP",
    "MULE_CHAIN",
    "TASK_INVESTMENT_SCAM",
    "PHISH_VISH",
    "LOAN_APP_EXTORTION",
    "IDENTITY_KYC_FRAUD",
    "CARD_CLONING",
    "SEXTORTION",
    "ROMANCE_HONEYTRAP",
]


def money_to_float(value: str) -> float:
    value = value.replace(",", "").strip()
    try:
        return float(value)
    except ValueError:
        return 0.0


def scale_money(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit.startswith("cro") or unit == "cr":
        return value * 10_000_000
    if unit.startswith("lak") or unit == "lac":
        return value * 100_000
    return value


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def normalize_upi(value: str) -> str:
    return value.strip().lower().rstrip(".")


def normalize_handle(value: str) -> str:
    return value.strip().lstrip("@").lower()


def normalize_account(value: str) -> str:
    return re.sub(r"\D", "", value)


def normalize_ifsc(value: str) -> str:
    return value.strip().upper()
