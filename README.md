# 🚀 Cyber Fraud Network Analyser
---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Cipher Matrix |
| **Track** | Cyber Forensics |
| **Team Lead** | Preetansh Gohil — preetanshmgohil@gmail.com |
| **Members** | Jwalan, Harshit, Vaibhav |

---

## 🎯 Problem Statement

- Cyber-fraud investigations involve **large amounts of fragmented intelligence** such as:
  - Bank transaction records
  - Call logs
  - Phone numbers
  - Device IDs
  - Suspect/accused information
  - Victim details

- These data sources are often **disconnected**, making it difficult to identify relationships between individuals, accounts, devices, and transactions.

- Investigators may need to manually correlate this information to determine:
  - **Who is connected to whom**
  - **How money moved through the network**
  - **Which individuals played which roles**
  - **How the fraud operation was organized**
  - **What fraud pattern was used**

- Important relationships can remain hidden when intelligence is examined **individually rather than as a connected network**.

- There is a need for an intelligent investigation tool that can **automatically correlate fragmented intelligence, uncover hidden relationships, identify fraud patterns, reconstruct the criminal hierarchy, and convert the findings into an actionable case summary**.

---

## 💡 Solution

- **Cyber Fraud Network Analyser** is a Bob-powered AI investigation tool that converts fragmented cyber-fraud intelligence into a **connected and explainable investigation network**.

- The system accepts mock intelligence such as:
  - Transaction records
  - Call logs
  - Device IDs
  - Phone numbers
  - Accused/suspect profiles
  - Victim information

- **Extracts entities** from the provided intelligence, including:
  - Persons
  - Bank accounts
  - Phone numbers
  - Devices
  - Transactions
  - Locations
  - Organizations

- **Discovers relationships** between entities by correlating information across different datasets.

- **Builds an interactive network graph** that allows investigators to visualize:
  - Money movement
  - Communication links
  - Shared devices
  - Account relationships
  - Connections between suspects and victims

- **Identifies potential fraud patterns**, such as:
  - Multi-layer fund transfers
  - Mule-account networks
  - SIM-related fraud
  - Coordinated victim targeting

- **Reconstructs the probable network hierarchy**, identifying roles such as:
  -  👑 Kingpin
  -  🔗 Facilitator
  -  💰 Mule
  -  🎯 Operator
  -  🧑 Victim
 
---

## ✨ Key Features

- **Feature 1:** **Multi-Source Intelligence Extraction** -Processes mock transaction records, call logs, device identifiers, phone numbers, and suspect profiles to extract relevant entities and evidence.
- **Feature 2:** **Automated Relationship Discovery** - Correlates entities across different datasets to uncover hidden connections such as shared devices, repeated communication, common accounts, and money transfers.
- **Feature 3:** **Interactive Fraud Network Graph** — Visualizes the complete investigation as a relationship graph, allowing investigators to trace connections and follow the flow of money, communication, and digital identities.
- **Feature 4:** **Fraud Pattern & Role Detection** — Identifies suspicious network structures and classifies probable roles such as Kingpin, Mule, Facilitator, and Victim, helping reconstruct the hierarchy of the fraud operation.
- **Feature 5:** **FIR-Ready Investigation Brief** — Converts the analyzed intelligence into a structured case brief containing the incident summary, key entities, evidence relationships, suspected roles, fraud pattern, and recommended investigative actions.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python |
| **Frameworks** | Python stdlib only (no pip dependencies), vis.js via CDN for the report graph |
| **IBM Technologies** | IBM Bob |
| **Other** | Git, GitHub |

---

## 📁 Repository Structure

```
├── src/                  # All source code
│   ├── cfna/             # Core package (pipeline, extraction, analysis, report)
│   ├── tests/            # 47-test unittest suite
│   ├── data/cases/       # Generated trial cases with truth.json
│   ├── output/           # Generated reports (HTML, FIR brief, JSON)
│   └── README.md         # Developer / technical documentation
├── demo/                 # Demo artifacts
│   ├── screenshots/      # App screenshots
│   └── demo-video-link.txt
├── presentation/         # Slide deck
└── submission.yaml       # Structured submission metadata
```

---

## ⚡ How to Run

```bash
# 1. Clone the repo
git clone https://github.com/harshitpatilx/bob-ai-hackathon-cipher-matrix.git
cd bob-ai-hackathon-cipher-matrix

# 2. Install the package (adds cfna to PATH)
pip install -e src/

# --- OR skip install and run everything from the src/ directory ---
cd src

# 3. Generate mock trial cases
python -m cfna.datagen

# 4. Run a case
python -m cfna run data/cases/jamtara_sim_swap -o output

# 5. Open the report
start output/jamtara_sim_swap/report.html

# Alternatively: double-click start_cfna.bat (src/) to open the browser input form
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/slides.pdf](presentation/) |

---

## ⚠️ Known Limitations

- All intelligence input is mock / synthetic — not connected to live banking or telecom APIs.
- IBM Bob API endpoint is wired but not active; all analysis runs on local deterministic heuristics (0 external API calls, 0 bob-coin spend).
- The vis-network graph in `report.html` requires a CDN fetch (unpkg.com) — no network means no graph.

---

## 🏅 What We're Most Proud Of

The fully self-contained, FIR-ready investigation pipeline — from raw CSVs and free-text to
an interactive HTML network report, a 12-section FIR brief, and a risk-ranked entity graph —
all in pure Python stdlib with zero dependencies and a 76-test suite that passes 3/3 trial cases
with perfect kingpin, mule, and victim F1 scores.

---