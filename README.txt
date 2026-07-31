# Braille Translation & Layout Verifier

This tool validates the translation and layout formatting compliance of Braille documents (.pdf or .brf) against print source documents (.docx or .pdf).

## How to Run the App

1. **Extract** the contents of `validator_distribution.zip` to a folder on your computer.
2. Double-click the **`validator.exe`** file to launch the desktop application interface.

---

## How to Use the App

1. **Upload Print Document**: Click the first **"Browse..."** button and select the source print file (e.g. `english_sample.docx`).
2. **Upload Braille Document**: Click the second **"Browse..."** button and select the generated Braille file (e.g. `braille_sample.pdf`).
3. **Select Grade**: Choose the translation grade (Grade 1 or Grade 2) matching your Braille document.
4. **Verify Compliance**: Click **"Run Validation"**.
5. **View Interactive HTML Report**: Once complete, the application will automatically save an interactive HTML dashboard report next to your Braille file and open it in your web browser. This report highlights any translation errors (rendered in Unicode Braille dots), punctuation variances, line-width overflows, page-length discrepancies, and formatting alignment failures.

---

## Testing with Mock Files

You can test the application instantly using the pre-configured mock sample files located in the `mock_files` directory:
* **Source English File**: `mock_files/English (UEB) - basic-  Master File.docx`
* **Target Braille File**: `mock_files/English (UEB) - basic - Mistakes Highlighted in Red.pdf`
