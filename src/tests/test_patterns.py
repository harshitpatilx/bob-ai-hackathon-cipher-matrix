import unittest

from cfna.analysis.metrics import compute_metrics
from cfna.analysis.patterns import classify_patterns
from cfna.models import CaseGraph, Document, EntityType
from cfna.extract import extract_from_text
from cfna.extract.relations import extract_text_relations


def _case_with(lines: list[str]) -> CaseGraph:
    case = CaseGraph()
    doc = Document(path="n.txt", kind="notes", text="\n".join(lines), lines=lines)
    case.documents.append(doc)
    extract_from_text(case, doc)
    extract_text_relations(case, [doc])
    return case


class TestPatternKeywords(unittest.TestCase):
    def test_sim_swap_keywords(self) -> None:
        case = _case_with([
            "The SIM swap fraud began when the victim SIM was reissued after a spoofed KYC update.",
            "The ported SIM was used to read OTPs on the swapper handset.",
        ])
        matches = classify_patterns(case, compute_metrics(case))
        self.assertEqual(matches[0].id, "SIM_SWAP_OTP")
        self.assertGreaterEqual(matches[0].score, 0.35)

    def test_vishing_keywords(self) -> None:
        case = _case_with([
            "Phishing link was sent over SMS and the vishing caller pretended to be bank customer care.",
            "The victim was asked to update KYC verification details on a fake page.",
        ])
        matches = classify_patterns(case, compute_metrics(case))
        self.assertEqual(matches[0].id, "PHISH_VISH")

    def test_task_scam_keywords(self) -> None:
        case = _case_with([
            "The task investment scam promised daily profit returns for recharge in a telegram group.",
            "Victims paid recharge amounts believing they would get commission on task completion.",
        ])
        matches = classify_patterns(case, compute_metrics(case))
        self.assertEqual(matches[0].id, "TASK_INVESTMENT_SCAM")


class TestStructuralDetectors(unittest.TestCase):
    def test_many_to_few_structure(self) -> None:
        case = CaseGraph()
        for i in range(4):
            src = case.add_entity(EntityType.ACCOUNT, f"500100001000{i}").id
            case.add_relation(src, "account:5001000020001", "transfer", weight=1.0, amount=9000.0, ts="2024-03-06T10:00:00")
        matches = classify_patterns(case, compute_metrics(case))
        ids = {m.id for m in matches}
        self.assertTrue({"TASK_INVESTMENT_SCAM", "MULE_CHAIN"} & ids)

    def test_mule_chain_structure(self) -> None:
        case = CaseGraph()
        prev = case.add_entity(EntityType.ACCOUNT, "5001000010001").id
        for n in range(1, 4):
            node = case.add_entity(EntityType.ACCOUNT, f"50010000{n:04d}1").id
            case.add_relation(prev, node, "transfer", weight=1.0, amount=100000.0, ts="2024-03-06T10:00:00")
            prev = node
        matches = classify_patterns(case, compute_metrics(case))
        self.assertEqual(matches[0].id, "MULE_CHAIN")

    def test_all_patterns_registered(self) -> None:
        from cfna.config import PATTERN_ORDER
        from cfna.analysis.patterns import KEYWORDS, WEIGHTS, STRUCTURAL

        self.assertEqual(sorted(KEYWORDS), sorted(PATTERN_ORDER))
        self.assertEqual(sorted(WEIGHTS), sorted(PATTERN_ORDER))
        self.assertEqual(sorted(STRUCTURAL), sorted(PATTERN_ORDER))


if __name__ == "__main__":
    unittest.main()
