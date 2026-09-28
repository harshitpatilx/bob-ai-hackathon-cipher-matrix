import unittest

from cfna.extract.entities import find_spans, line_labels
from cfna.models import CaseGraph, Document, EntityType
from cfna.extract import extract_from_text


class TestSpans(unittest.TestCase):
    def test_multi_entity_sentence(self) -> None:
        text = (
            "UPI id rakesh.kumar@ybl sent Rs.1,25,000 from account 5001000123456 "
            "to 9431100012 using IMEI 356938035643801 and SIM 89012345678901234567"
        )
        found = {(s.etype, s.norm) for s in find_spans(text)}
        self.assertIn((EntityType.UPI_ID, "rakesh.kumar@ybl"), found)
        self.assertIn((EntityType.ACCOUNT, "5001000123456"), found)
        self.assertIn((EntityType.PHONE, "9431100012"), found)
        self.assertIn((EntityType.DEVICE, "356938035643801"), found)
        self.assertIn((EntityType.SIM, "89012345678901234567"), found)

    def test_no_spurious_overlap(self) -> None:
        spans = find_spans("account 5001000123456 to 9431100012")
        types = sorted(s.etype for s in spans)
        self.assertEqual(types, sorted({EntityType.ACCOUNT, EntityType.PHONE}))
        self.assertLess(spans[0].end, spans[1].start)

    def test_ifsc_and_pan(self) -> None:
        found = {(s.etype, s.norm) for s in find_spans("IFSC PUNB0123456 PAN ABCDE1234F")}
        self.assertIn((EntityType.IFSC, "PUNB0123456"), found)
        self.assertIn((EntityType.PAN, "ABCDE1234F"), found)

    def test_non_identifier_digits_ignored(self) -> None:
        self.assertEqual(find_spans("order 12345 of Rs.450"), [])


class TestLabels(unittest.TestCase):
    def test_role_markers(self) -> None:
        self.assertIn("victim", line_labels("Victim Sourav Banerjee (9003100001) lost Rs.64,000"))
        self.assertIn("mule", line_labels("Mule account 5001000020001 of Bikash Mondal"))
        self.assertIn("kingpin", line_labels("mastermind Anup Saha is the terminal holder"))
        self.assertIn("operator", line_labels("Operator Bittu handles the sim swaps"))

    def test_person_names(self) -> None:
        case = CaseGraph()
        doc = Document(path="n.txt", kind="notes",
                       text="Recruiter Suraj Ekka sources fresh bank accounts",
                       lines=["Recruiter Suraj Ekka sources fresh bank accounts"])
        extract_from_text(case, doc)
        self.assertIn("person:SURAJ EKKA", case.entities)
        self.assertIn("recruiter", case.entities["person:SURAJ EKKA"].labels)


class TestTextRelations(unittest.TestCase):
    def test_transfer_sentence(self) -> None:
        from cfna.extract.relations import extract_text_relations

        case = CaseGraph()
        doc = Document(
            path="n.txt", kind="notes",
            text="Funds transferred Rs.50,000 from account 5001000999999 to account 5001000123456",
            lines=["Funds transferred Rs.50,000 from account 5001000999999 to account 5001000123456"],
        )
        extract_from_text(case, doc)
        extract_text_relations(case, [doc])
        transfers = [r for r in case.relation_list() if r.rtype == "transfer"]
        self.assertEqual(len(transfers), 1)
        self.assertEqual(transfers[0].amount, 50000.0)
        self.assertEqual(transfers[0].src, "account:5001000999999")
        self.assertEqual(transfers[0].dst, "account:5001000123456")


if __name__ == "__main__":
    unittest.main()
