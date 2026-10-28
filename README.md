# TT Site Visit Photo Captioner

A repo-ready Streamlit application that adds observation-linked captions to photos in post-processed TT site visit report PDFs. It does not overwrite the source PDF.

## Caption format

- Non-conformance: `REPORT.NCR.OBSERVATION-PHOTO N: Existing photo caption`
- General observation: `REPORT.GO.OBSERVATION-PHOTO N: Existing photo caption`

The report number is read from `Special Inspection Report #…`. The app recognizes observation detail headings such as `Non-Conformance Observation 65.NC.1` and `General Observation #1`. Photos are detected only on pages containing a `Photographs:` heading. Photo number increments within each observation.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Upload a PDF, verify the detected observation and existing caption for every photo, correct any values, select **Apply captions**, then download the new PDF. Captions are left-aligned below photos. The engine tries progressively smaller font sizes (10.5 pt down to 5.5 pt) to fit the space before the next photo row. If it cannot fit safely, the original caption is left unchanged and a warning is shown.

## Git workflow

1. Create a private GitHub repository for the app.
2. From this folder, run:

   ```bash
   git init
   git add app.py caption_engine.py tests requirements.txt README.md .gitignore .github .streamlit/config.toml
   git commit -m "Add TT site visit photo captioner"
   git branch -M main
   git remote add origin <your-private-repository-url>
   git push -u origin main
   ```

3. GitHub Actions runs `pytest` for pushes and pull requests.
4. For a private deployment, use an approved internal Streamlit host. If using Streamlit Community Cloud, connect the repository, select `app.py`, and confirm that the report data handling meets TT's information-security requirements before deploying. PDFs are excluded by `.gitignore`; never commit project reports.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Current detection limits

- Input must be a text-based PDF with selectable observation headings and embedded photo images.
- The photo page must include the `Photographs:` heading.
- Observation association is based on document order: a detected observation detail page applies to subsequent photo pages until another detail heading is found.
- Always review the detected labels and preview before exporting. OCR-only/scanned reports, unusual layouts, and photos without existing captions may need manual correction.
