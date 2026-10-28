import unittest

import fitz

from caption_engine import analyze_pdf, apply_captions, format_caption, parse_observation


def make_sample_pdf():
    doc = fitz.open()
    detail = doc.new_page(width=595, height=842)
    detail.insert_text((30, 100), "Special Inspection Report #42")
    detail.insert_text((30, 140), "E. Non-Conformance Observation 42.NC.3")
    photos = doc.new_page(width=595, height=842)
    photos.insert_text((30, 90), "Photographs:")
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 640, 480), 0)
    pix.clear_with(0xD0D0D0)
    photos.insert_image(fitz.Rect(40, 120, 300, 315), pixmap=pix)
    photos.insert_text((40, 328), "Existing condition caption", fontsize=10.5)
    return doc.tobytes()


class CaptionEngineTests(unittest.TestCase):
    def test_format_caption_uses_requested_prefix(self):
        self.assertEqual(
            format_caption("65", "NCR", "2", 3, "Thermal shim missing"),
            "65.NCR.2-PHOTO 3: Thermal shim missing",
        )
        self.assertEqual(
            format_caption("65", "GO", "1", 1, "Work in progress"),
            "65.GO.1-PHOTO 1: Work in progress",
        )

    def test_parse_observation_detail_headings(self):
        self.assertEqual(parse_observation("E. Non-Conformance Observation 65.NC.1"), ("NCR", "1"))
        self.assertEqual(parse_observation("F. General Observation # 1"), ("GO", "1"))
        self.assertIsNone(parse_observation("Non-conformance Observations:"))

    def test_detect_and_apply_caption_only_to_photo_page(self):
        source = make_sample_pdf()
        report_no, jobs, notes = analyze_pdf(source)
        self.assertEqual(report_no, "42")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].observation_type, "NCR")
        self.assertEqual(jobs[0].observation_number, "3")
        self.assertEqual(jobs[0].caption, "Existing condition caption")

        output, warnings = apply_captions(source, jobs, report_no)
        self.assertFalse(warnings)
        result = fitz.open(stream=output, filetype="pdf")
        self.assertEqual(len(result), 2)
        self.assertIn("42.NCR.3-PHOTO 1: Existing condition caption", result[1].get_text())
        self.assertNotIn("42.NCR.3-PHOTO", result[0].get_text())
        self.assertEqual(len(result[1].get_images(full=True)), 1)
        result.close()


if __name__ == "__main__":
    unittest.main()
