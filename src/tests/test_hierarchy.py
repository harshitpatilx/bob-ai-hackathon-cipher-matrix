import unittest
from pathlib import Path

from cfna.analysis.hierarchy import assign_roles, build_hierarchy, summarize_roles
from cfna.analysis.metrics import compute_metrics
from cfna.models import CaseGraph, EntityType
from cfna.models import ROLE_KINGPIN, ROLE_MULE, ROLE_RECRUITER, ROLE_VICTIM

DATA = Path(__file__).resolve().parents[1] / "data" / "cases"


def _chain_case() -> CaseGraph:
    case = CaseGraph()
    king = case.add_entity(EntityType.ACCOUNT, "5001000000001").id
    mid_a = case.add_entity(EntityType.ACCOUNT, "5001000020001").id
    mid_b = case.add_entity(EntityType.ACCOUNT, "5001000030001").id
    sink = case.add_entity(EntityType.ACCOUNT, "5001000010001").id
    case.add_relation(mid_a, king, "transfer", weight=1.0, amount=90000.0, ts="2024-03-06T10:00:00")
    case.add_relation(mid_b, mid_a, "transfer", weight=1.0, amount=95000.0, ts="2024-03-06T10:05:00")
    case.add_relation(sink, mid_b, "transfer", weight=1.0, amount=100000.0, ts="2024-03-06T10:10:00")
    return case


class TestRolesSynthetic(unittest.TestCase):
    def test_pass_through_chain(self) -> None:
        case = _chain_case()
        assessments = assign_roles(case, compute_metrics(case))
        self.assertEqual(assessments["account:5001000000001"].role, ROLE_KINGPIN)
        self.assertEqual(assessments["account:5001000020001"].role, ROLE_MULE)
        self.assertEqual(assessments["account:5001000030001"].role, ROLE_MULE)
        self.assertEqual(assessments["account:5001000010001"].role, ROLE_VICTIM)

    def test_victim_not_mule_despite_inflow_label(self) -> None:
        case = CaseGraph()
        account = case.add_entity(EntityType.ACCOUNT, "5001000020001")
        account.add_label("victim")
        case.add_relation("account:5001000010001", account.id, "transfer",
                          weight=1.0, amount=80000.0, ts="2024-03-06T10:00:00")
        case.add_relation(account.id, "account:5001000030001", "transfer",
                          weight=1.0, amount=74000.0, ts="2024-03-06T11:00:00")
        assessments = assign_roles(case, compute_metrics(case))
        self.assertEqual(assessments[account.id].role, ROLE_MULE)

    def test_hierarchy_layers(self) -> None:
        case = _chain_case()
        assessments = assign_roles(case, compute_metrics(case))
        hierarchy = build_hierarchy(case, assessments)
        self.assertEqual(hierarchy[ROLE_KINGPIN], ["account:5001000000001"])
        self.assertEqual(summarize_roles(assessments)[ROLE_MULE], 2)


@unittest.skipUnless(DATA.exists(), "trial data not generated")
class TestRolesTrialData(unittest.TestCase):
    def test_jamtara_roles(self) -> None:
        from cfna.pipeline import build_case, analyze

        case, _ = build_case(DATA / "jamtara_sim_swap")
        brief, _metrics, _ev = analyze(case)
        self.assertIn("account:5001000000001",
                      [n for n, a in brief.assessments.items() if a.role == ROLE_KINGPIN])
        mules = {n for n, a in brief.assessments.items() if a.role == ROLE_MULE}
        expected = {f"account:50010000{i:05d}" for i in range(20001, 20005)}
        expected |= {f"account:50010000{i:05d}" for i in range(30001, 30004)}
        expected |= {"account:5001000040001", "account:5001000040002"}
        self.assertEqual(mules & expected, expected)

    def test_recruiter_label_wins_for_non_money_node(self) -> None:
        case = CaseGraph()
        person = case.add_entity(EntityType.PERSON, "SURAJ EKKA")
        person.add_label("recruiter")
        case.add_entity(EntityType.ACCOUNT, "5001000010001")
        assessments = assign_roles(case, compute_metrics(case))
        self.assertEqual(assessments[person.id].role, ROLE_RECRUITER)


if __name__ == "__main__":
    unittest.main()
