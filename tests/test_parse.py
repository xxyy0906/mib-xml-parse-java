from __future__ import annotations

import sys
import unittest
from pathlib import Path

PARSER_ROOT = Path(__file__).resolve().parents[1]
if str(PARSER_ROOT) not in sys.path:
    sys.path.insert(0, str(PARSER_ROOT))

from mibxml.pipeline import list_mib_xml_files, parse_mib_xml


class ParseMibXmlTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Path(__file__).parent / "fixtures" / "mini-mib.xml"
        self.out = Path(__file__).parent / "out-mini"
        if self.out.exists():
            import shutil
            shutil.rmtree(self.out)

    def test_generic_input_writes_parse_xml_and_entities(self):
        result = parse_mib_xml(self.fixture, self.out)
        parse_xml = result["parse_xml"]
        self.assertTrue(parse_xml.is_file())
        self.assertEqual(parse_xml.name, "mini-mib-parse.xml")

        text = parse_xml.read_text(encoding="utf-8")
        self.assertNotIn("desc=", text)
        self.assertNotIn("full=", text)
        self.assertIn('oid="1.3.6.1.4.1.1206.4.2.1.1.2.1.2"', text)
        self.assertIn("phaseWalk", text)
        self.assertIn('indexes="splitNumber, splitPhase"', text)

        walk = result["entities"] / "PhaseEntry.java"
        self.assertTrue(walk.is_file(), walk)
        java = walk.read_text(encoding="utf-8")
        self.assertIn("AUTO-GENERATED FILE. Do not modify.", java)
        self.assertIn("Generated at:", java)
        self.assertTrue(java.lstrip().startswith("/*"))
        self.assertIn('oid = "1.3.6.1.4.1.1206.4.2.1.1.2.1.2"', java)
        self.assertIn("byte[] phaseConcurrency", java)

        phase = result["entities"] / "NtcipPhase.java"
        self.assertTrue(phase.is_file(), phase)
        self.assertFalse((result["entities"] / "Phase.java").exists())
        self.assertIn("class NtcipPhase", phase.read_text(encoding="utf-8"))
        self.assertTrue((result["entities"] / "NtcipCoord.java").is_file())

        self.assertIsNone(result["itms"])
        self.assertFalse((self.out / "entities" / "itms-model-temp").exists())

        split = result["entities"] / "SplitEntry.java"
        self.assertIn('indexes = {"splitNumber", "splitPhase"}', split.read_text(encoding="utf-8"))

        ann = result["annotations"] / "NtcipColumn.java"
        self.assertTrue(ann.is_file(), ann)
        self.assertEqual(result["annotations"], self.out / "entities" / "ann")
        self.assertFalse((result["entities"] / "ann").exists())
        self.assertFalse((result["entities"] / "com").exists())

    def test_itms_opt_in_writes_group_files_with_inner_entries(self):
        result = parse_mib_xml(self.fixture, self.out, gen_itms=True)
        itms_dir = result["itms"]
        self.assertIsNotNone(itms_dir)
        itms_phase = itms_dir / "NtcipPhase.java"
        self.assertTrue(itms_phase.is_file(), itms_phase)
        itms_text = itms_phase.read_text(encoding="utf-8")
        self.assertIn("extends GBT2017Packet<NtcipPhase>", itms_text)
        self.assertIn("@Label(Object = 1, Modify = false)", itms_text)
        self.assertNotIn("ITMS type =", itms_text)
        self.assertIn("public static class PhaseEntry", itms_text)
        self.assertIn("@Label(Object = 2, Attribute = 1, Modify = false)", itms_text)
        self.assertIn("@Label(Object = 2, Attribute = 2, Modify = true)", itms_text)
        self.assertFalse((itms_dir / "PhaseEntry.java").exists())
        self.assertFalse((itms_dir / "SplitEntry.java").exists())
        itms_coord = (itms_dir / "NtcipCoord.java").read_text(encoding="utf-8")
        self.assertIn("public static class SplitEntry", itms_coord)
        self.assertTrue((itms_dir / "NtcipAsc.java").is_file())
        self.assertTrue((itms_dir / "README.md").is_file())

    def test_list_mib_xml_skips_parse_xml(self):
        folder = Path(__file__).parent / "fixtures"
        names = {p.name for p in list_mib_xml_files(folder)}
        self.assertIn("mini-mib.xml", names)
        self.assertTrue(all(not n.endswith("-parse.xml") for n in names))


if __name__ == "__main__":
    unittest.main()
