from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cfna.cli import main
from cfna.intake import (
    Intake,
    case_dir_for,
    ensure_case,
    slugify,
    sniff_table,
    table_to_csv,
    wizard,
    write_case,
    write_template,
)
from cfna.ingest.loaders import load_case_dir
from cfna.pipeline import run_case

NOTES = (
    "Kingpin Anup Saha holds account 5001000000001 which is the terminal beneficiary. "
    "The victim SIM was reissued after a spoofed KYC update and OTPs were read. "
    "Victim Ramesh Kumar (9431100001) lost Rs.64000 on 06/03/2024."
)


class TestHelpers(unittest.TestCase):
    def test_slugify(self) -> None:
        self.assertEqual(slugify("SIM-Swap & UPI Mule"), "sim_swap_upi_mule")
        self.assertEqual(slugify("   "), "case")
        self.assertEqual(slugify("", "fallback"), "fallback")

    def test_sniff_table_comma_and_tab(self) -> None:
        header, rows = sniff_table("amount_inr,txn_id\n64000,T1\n")
        self.assertEqual(header, ["amount_inr", "txn_id"])
        self.assertEqual(rows, [["64000", "T1"]])
        header, rows = sniff_table("msisdn\tduration\n9431100001\t48\n")
        self.assertEqual(header, ["msisdn", "duration"])
        self.assertEqual(rows, [["9431100001", "48"]])

    def test_table_roundtrip(self) -> None:
        csv_text = table_to_csv(["a", "b"], [["1", "2"]])
        header, rows = sniff_table(csv_text)
        self.assertEqual((header, rows), (["a", "b"], [["1", "2"]]))


class TestWriteCase(unittest.TestCase):
    def test_write_case_then_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "demo"
            write_case(
                case_dir,
                {"case_id": "demo", "title": "Demo", "district": "Ranchi"},
                [("user_notes", NOTES)],
                [("records.csv", "amount_inr,txn_id,from_account,to_account\n64000,T1,5001000123456,5001000987654\n")],
                [],
            )
            meta, docs, records = load_case_dir(case_dir)
            self.assertEqual(meta.title, "Demo")
            self.assertEqual(meta.district, "Ranchi")
            narratives = [d for d in docs if d.kind != "structured"]
            self.assertEqual(len(narratives), 1)
            self.assertTrue(any("Kingpin" in line for line in narratives[0].lines))
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["__kind"], "transactions")
            self.assertEqual(sorted(p.name for p in case_dir.iterdir()),
                             ["01_user_notes.txt", "02_records.csv", "case.json"])

    def test_existing_dir_refused_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "demo"
            write_case(case_dir, {"title": "Demo"}, [("notes", NOTES)], [], [])
            with self.assertRaises(FileExistsError):
                write_case(case_dir, {"title": "Demo"}, [("notes", "more text")], [], [])
            write_case(case_dir, {"title": "Demo"}, [("extra", "more text")], [], [], force=True)

    def test_case_dir_for_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            first = case_dir_for({"title": "A Case"}, dest)
            first.mkdir()
            (first / "case.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                case_dir_for({"title": "A Case"}, dest)
            self.assertEqual(case_dir_for({"title": "A Case"}, dest, force=True).name, first.name)

    def test_ensure_case_from_single_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "my_notes.txt"
            note.write_text(NOTES, encoding="utf-8")
            case_dir = ensure_case(note)
            self.assertTrue(case_dir.is_dir())
            self.assertNotEqual(case_dir, note)
            meta, docs, _ = load_case_dir(case_dir)
            self.assertTrue(docs)
            self.assertEqual(meta.case_id, "my_notes")
            # a directory passes straight through
            self.assertEqual(ensure_case(case_dir), case_dir)


class TestWizard(unittest.TestCase):
    def test_wizard_collects_meta_and_notes(self) -> None:
        answers = iter([
            "Pasted Case", "pasted_case",   # title, id
            "PS Cyber", "", "", "Ramesh Kumar", "2024-03-06", "", "", "",  # 8 meta fields
            "",                             # intel files (skip)
            "Victim Ramesh Kumar lost Rs.64000 after the OTP was read.", ".",
            "",                             # table paste skipped
        ])

        def fake_prompt(_text: str = "") -> str:
            try:
                return next(answers)
            except StopIteration:
                raise EOFError from None

        with patch("builtins.print"):
            intake = wizard(fake_prompt)

        self.assertEqual(intake.meta["title"], "Pasted Case")
        self.assertEqual(intake.meta["police_station"], "PS Cyber")
        self.assertEqual(intake.meta["complainant"], "Ramesh Kumar")
        self.assertEqual(len(intake.texts), 1)
        self.assertIn("64000", intake.texts[0][1])
        self.assertEqual(intake.tables, [])
        self.assertTrue(intake.has_input())

    def test_wizard_handles_eof(self) -> None:
        def eof_prompt(_text: str = "") -> str:
            raise EOFError from None

        with patch("builtins.print"):
            intake = wizard(eof_prompt)
        self.assertFalse(intake.has_input())


class TestNewCommand(unittest.TestCase):
    def test_new_from_text_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("builtins.print"):
                rc = main([
                    "new", "--id", "cli_text_case", "--title", "CLI Text Case",
                    "--district", "Jamtara", "--text", NOTES,
                    "--dest", tmp, "--no-run",
                ])
            self.assertEqual(rc, 0)
            case_dir = Path(tmp) / "cli_text_case"
            self.assertTrue((case_dir / "case.json").exists())
            meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["district"], "Jamtara")
            self.assertTrue(list(case_dir.glob("*.txt")))

    def test_new_from_text_file_and_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "note.md"
            note.write_text(NOTES, encoding="utf-8")
            table = Path(tmp) / "txns.csv"
            table.write_text(
                "timestamp,txn_id,from_account,to_account,amount_inr,channel\n"
                "2024-03-06T10:05:00,T1,5001000123456,5001000987654,64000,UPI\n",
                encoding="utf-8",
            )
            out = Path(tmp) / "out"
            with patch("builtins.print"):
                rc = main([
                    "new", "--id", "cli_file_case", "--title", "CLI File Case",
                    "--text-file", str(note), "--file", str(table),
                    "--dest", tmp, "--out", str(out),
                ])
            self.assertEqual(rc, 0)
            case_dir = Path(tmp) / "cli_file_case"
            self.assertTrue((case_dir / "01_note.md").exists())
            _, docs, records = load_case_dir(case_dir)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["__kind"], "transactions")
            self.assertTrue((out / "cli_file_case" / "report.html").exists())
            self.assertTrue((out / "cli_file_case" / "fir_brief.md").exists())

    def test_new_piped_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stdin = io.StringIO(NOTES)
            with patch.object(sys, "stdin", stdin), patch("builtins.print"):
                rc = main([
                    "new", "--id", "piped_case", "--title", "Piped",
                    "--dest", tmp, "--no-run",
                ])
            self.assertEqual(rc, 0)
            files = [p.name for p in (Path(tmp) / "piped_case").iterdir()]
            self.assertTrue(any(name.endswith(".txt") for name in files))

    def test_new_piped_stdin_csv_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stdin = io.StringIO("amount_inr,txn_id\n64000,T9\n")
            with patch.object(sys, "stdin", stdin), patch("builtins.print"):
                rc = main([
                    "new", "--id", "piped_csv", "--title", "Piped CSV",
                    "--stdin-format", "csv", "--dest", tmp, "--no-run",
                ])
            self.assertEqual(rc, 0)
            _, _, records = load_case_dir(Path(tmp) / "piped_csv")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["__kind"], "transactions")

    def test_new_without_input_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stdin = io.StringIO("")
            with patch.object(sys, "stdin", stdin), patch("sys.stderr", new=io.StringIO()):
                rc = main(["new", "--title", "Nothing", "--dest", tmp, "--no-run"])
            self.assertEqual(rc, 2)

    def test_new_refuses_existing_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            args = ["new", "--id", "dupe", "--title", "Dupe", "--text", NOTES,
                    "--dest", tmp, "--no-run"]
            with patch("builtins.print"):
                self.assertEqual(main(args), 0)
            with patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(main(args), 2)

    def test_new_end_to_end_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            with patch("builtins.print"):
                rc = main([
                    "new", "--id", "full_case", "--title", "Full Case",
                    "--text", NOTES, "--dest", tmp, "--out", str(out),
                ])
            self.assertEqual(rc, 0)
            report = (out / "full_case" / "report.html").read_text(encoding="utf-8")
            self.assertIn("Full Case", report)
            brief = (out / "full_case" / "fir_brief.md").read_text(encoding="utf-8")
            self.assertTrue(brief.strip())


class TestRunSingleFile(unittest.TestCase):
    def test_run_accepts_a_bare_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "complaint.txt"
            note.write_text(NOTES, encoding="utf-8")
            out = Path(tmp) / "out"
            with patch("builtins.print"):
                rc = main(["run", str(note), "--out", str(out)])
            self.assertEqual(rc, 0)
            produced = list(out.rglob("report.html"))
            self.assertEqual(len(produced), 1)

    def test_run_missing_path(self) -> None:
        with patch("sys.stderr", new=io.StringIO()):
            rc = main(["run", str(Path("does_not_exist_zz"))])
        self.assertEqual(rc, 2)


class TestTemplateCommand(unittest.TestCase):
    def test_template_writes_loadable_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("builtins.print"):
                rc = main(["template", tmp])
            self.assertEqual(rc, 0)
            target = Path(tmp) / "cfna_input_template"
            names = sorted(p.name for p in target.iterdir())
            self.assertIn("transactions.csv", names)
            self.assertIn("incident_notes.txt", names)
            self.assertIn("README.txt", names)
            meta, docs, records = load_case_dir(target)
            self.assertEqual(meta.case_id, "sample_case")
            self.assertTrue(any(d.kind != "structured" for d in docs))
            kinds = {r["__kind"] for r in records}
            self.assertIn("transactions", kinds)

    def test_template_files_roundtrip_through_new(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = write_template(Path(tmp) / "tpl")
            out = Path(tmp) / "out"
            with patch("builtins.print"):
                rc = main([
                    "new", "--id", "from_template", "--title", "From Template",
                    "--file", str(target / "incident_notes.txt"),
                    "--file", str(target / "transactions.csv"),
                    "--dest", tmp, "--out", str(out),
                ])
            self.assertEqual(rc, 0)
            result = run_case(Path(tmp) / "from_template", out)
            self.assertTrue(Path(result["outputs"]["report.html"]).exists())


class TestIntakeObject(unittest.TestCase):
    def test_intake_merge(self) -> None:
        base = Intake(meta={"title": "A"}, texts=[("n", "body")])
        extra = Intake(meta={"title": "B", "district": "X"}, files=[Path("somewhere")])
        merged = base.merge(extra)
        self.assertEqual(merged.meta["title"], "B")
        self.assertEqual(merged.meta["district"], "X")
        self.assertEqual(len(merged.texts), 1)
        self.assertEqual(len(merged.files), 1)


if __name__ == "__main__":
    unittest.main()
