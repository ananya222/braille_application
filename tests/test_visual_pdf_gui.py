import glob
import os
import unittest

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QColor, QImage
    from main_gui import VisualResultsPage, compose_pdf_page_on_white
except Exception:
    QApplication = None
    VisualResultsPage = None
    compose_pdf_page_on_white = None


@unittest.skipIf(QApplication is None, "PySide6 is unavailable")
class VisualPdfGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.pdf_path = glob.glob(os.path.join("testfiles", "Document 1", "*.pdf"))[0]

    def test_render_navigation_zoom_and_issue_selection(self):
        page = VisualResultsPage()
        page.resize(1000, 700)
        page.show()
        page.set_data(self.pdf_path, [{
            "kind": "replacement",
            "page": 1,
            "expected": "⠁",
            "actual": "⠃",
            "context": "test",
            "confidence": "high_confidence",
            "provenance_cells": [{
                "page": 1, "x0": 10, "x1": 20, "top": 30, "bottom": 42,
                "unicode_cell": "⠃",
            }],
        }])
        self.app.processEvents()
        self.assertEqual(page.document.pageCount(), 9)
        self.assertGreater(page.canvas.width(), 0)
        self.assertGreater(page.canvas.height(), 0)
        self.assertAlmostEqual(page.canvas._page_size.width(), 595.32, places=1)
        self.assertAlmostEqual(page.canvas._page_size.height(), 841.92, places=1)

        page.show_page(3)
        page._set_manual_zoom(1.4)
        self.app.processEvents()
        self.assertEqual(page.current_page, 3)
        self.assertAlmostEqual(page.zoom_factor, 1.4)

        page.select_issue(1)
        self.app.processEvents()
        self.assertEqual(page.current_page, 1)
        self.assertEqual(page.selected_issue_id, 1)
        page.close()

    def test_transparent_pdf_render_is_composited_onto_white(self):
        transparent = QImage(4, 4, QImage.Format_ARGB32)
        transparent.fill(QColor(0, 0, 0, 0))
        white = compose_pdf_page_on_white(transparent)
        self.assertEqual(white.pixelColor(0, 0).getRgb(), (255, 255, 255, 255))


if __name__ == "__main__":
    unittest.main()
