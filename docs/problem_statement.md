# UIDAI Data Hackathon 2026 - Dashboard

## Problem Statement
The UIDAI Data Hackathon 2026 challenge involves analyzing Aadhaar-related datasets to derive actionable insights for the government. The goal is to process enrollment, demographic update, and biometric update data to identify patterns, improve service delivery, and enhance system integrity.

## Scope
The project scope includes:
- **Data Normalization**: Cleaning and standardizing three datasets: Aadhaar Enrolment, Demographic Updates, and Biometric Updates.
- **Data Analysis**: Implementing 10 specific analytical ideas ranging from district-level activity tracking to disaster relief planning.
- **Dashboard Development**: Creating a user-friendly, animated web dashboard using Flask and Chart.js to visualize the analysis state-wise and district-wise.
- **Reporting**: Generating exportable reports (CSV, PDF) for government use.
- **Recommendations**: Providing specific problem-solving suggestions based on data trends.

## Data Sources
Three primary CSV datasets provided:
1.  **Aadhaar Enrolment**: `date, state, district, pincode, age_0_5, age_5_17, age_18_above`
2.  **Aadhaar Demographic Update**: `date, state, district, pincode, age_5_17, age_18_above` (Headers in file: `demo_age_5_17`, `demo_age_17_`)
3.  **Aadhaar Biometric Update**: `date, state, district, pincode, age_5_17, age_18_above` (Headers in file: `bio_age_5_17`, `bio_age_17_`)

## Methodology
1.  **Backend (Python/Flask)**: 
    - Load and parse CSVs.
    - normalize column names.
    - Aggregate data by State and District.
    - Implement specific logic for each of the 10 ideas.
    - Expose APIs for the frontend.
2.  **Frontend (HTML/JS)**:
    - Responsive dashboard using Bootstrap/Tailwind (CSS).
    - Interactive charts using Chart.js.
    - filters for State/District selection.
3.  **Analysis Logic**:
    - *Idea 1 (District Activity)*: Sum of all operations per district.
    - *Idea 2 (Biometric Camps)*: Identify districts with low biometric updates relative to demographic updates or enrollment.
    - *Idea 3 (Age Verifier)*: Highlight districts with high 18+ enrollment/update activity (potential first-time voters).
    - *Idea 4 (Ghost Child)*: Analyze 0-5 enrollment trends; low numbers vs expected benchmarks (if available) or anomalies.
    - *Idea 5 (Integrity)*: Placeholder for duplicate detection logic (simulation based on same-day spikes).
    - *Idea 6 (Financial)*: Placeholder (as per user note).
    - *Idea 7 (Language)*: Map states to languages and recommend support.
    - *Idea 8 (Health Monitor)*: Identify centers ( Pincodes) with zero activity or high rejection proxy (simulated).
    - *Idea 9 (Disaster)*: Track demographic update spikes in specific regions over time.
    - *Idea 10 (City Life)*: Identify high-traffic pincodes in urban districts.

## Deliverables
- Fully functional Flask Application.
- Interactive Dashboard.
- API Documentation.
- Analytical Reports.
