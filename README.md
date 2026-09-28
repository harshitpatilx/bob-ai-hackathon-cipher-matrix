# 🚀 Cyber Fraud Network Analyser
---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Cipher Matrix |
| **Track** | [AI / DevOps / Sustainability / Open] |
| **Team Lead** | Preetansh Gohil — [email@ibm.com] |
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
  - 👑 Kingpin
  - 🔗 Facilitator
  - 💰 Mule
  -
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
| **Languages** | Python, Javascript |
| **Frameworks** | [e.g., FastAPI, React] |
| **IBM Technologies** | IBM Bob |
| **Databases** | [e.g., PostgreSQL, Redis] |
| **Other** | Git, Github |

---

## 📁 Repository Structure

```
├── src/                  # All source code
├── docs/                 # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                 # Demo artifacts
│   ├── screenshots/      # App screenshots
│   └── demo-video-link.txt  # Link to demo video
├── presentation/         # Slide deck
└── submission.yaml       # Structured submission metadata
```

---

## ⚡ How to Run

> **Copy these exact steps from your [`docs/setup-guide.md`](docs/setup-guide.md)**

```bash
# 1. Clone the repo
git clone https://github.com/harshitpatilx/bob-ai-hackathon-cipher-matrix.git
cd bob-ai-hackathon-cipher-matrix

# 2. Install dependencies
[your install command here]

# 3. Configure environment
cp .env.example .env
# Edit .env with your values

# 4. Run the project
[your run command here]
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

> Be honest — judges appreciate transparency over overclaiming.

- [Limitation 1: e.g., "Authentication is mocked — not production-ready"]
- [Limitation 2: e.g., "Only tested on Chrome"]
- [Limitation 3: e.g., "Feature X is scaffolded but not fully implemented"]

---

## 🏅 What We're Most Proud Of

[Tell the judges what part of your submission is strongest and worth paying close attention to.]

---
