# TalentMetrics — Recruitment Operations Analytics

A free, **static and interactive** GitHub Pages portfolio dashboard. The main demo uses HTML, CSS and vanilla JavaScript and requires **no Python runtime, API keys, or external libraries**. A separate `streamlit_app.py` preserves the original Python/Streamlit prototype.

## Publish on GitHub Pages
1. Create a public GitHub repository (for example `talentmetrics`).
2. Upload `index.html`, `styles.css`, `app.js`, `README.md` (and optionally `streamlit_app.py` and `requirements.txt`) to the repository root.
3. Open repository **Settings → Pages → Build and deployment**.
4. Choose **Deploy from a branch**, branch **main**, folder **/(root)**, then **Save**.
5. Wait for the published URL to appear in Pages settings. Usually `https://YOUR-USERNAME.github.io/talentmetrics/`.

To test locally, open `index.html` in a browser. No build step is required.

## Features
- Six dynamic recruitment KPIs, current pipeline stages, weekly application volume, university distribution.
- Recruiter workload, configurable operational attention queue, simulated stage-age diagnostics.
- Position, university, recruiter and application-date filters; CSV export.
- Responsive interface for desktop and mobile; synthetic data notice and transparent methodology.

## Metric definitions
- **Interview reach rate**: applicants with an interview date or interview/later stage ÷ applicants in filtered cohort.
- **Interview → offer**: applicants with offer evidence ÷ applicants with interview evidence.
- **Offer → hire**: applicants in Hired stage ÷ applicants with offer evidence; this is **not** a true offer acceptance rate.
- **Median interview lead time**: median calendar days from interview invitation to interview date, not the time taken to coordinate a booking.
- **Overdue follow-ups**: active candidates with due date before 2027-05-31 and incomplete task.
- **Stage age**: simulated snapshot days in stage, not historical stage duration.

## Data integrity
All 240 candidate records are deterministically generated, synthetic, and never sent to a server. Metrics are snapshot indicators, **not** actual AlphaSights data, actual recruitment performance, mature-cohort conversion, or a validated statistical model. No real applicant information is included. This project is not affiliated with AlphaSights.

## Python version
The `streamlit_app.py` is an independent Python implementation of a similar fictional recruitment dashboard, not the backend for GitHub Pages. To run it separately:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The two versions generate separate synthetic cohorts, so numbers may differ. The JavaScript edition is not executing Python.

## Suggested resume description (after testing and deployment)
**TalentMetrics — Recruitment Operations Analytics | JavaScript, Python, Streamlit** — Built a static interactive recruitment analytics dashboard using simulated applicant data to explore hiring-stage progression, interview lead times, recruiter workload and overdue follow-ups; published a recruiter-accessible demo through GitHub Pages.
