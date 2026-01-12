# API Documentation

## Base URL
`/api/data`

## Endpoints

### 1. Get Summary Statistics
**URL**: `/summary`
**Method**: `GET`
**Description**: Returns aggregated totals for enrolment, demographic updates, and biometric updates across the entire dataset.
**Response**:
```json
{
  "total_enrolment": 1500000,
  "total_demographic_updates": 500000,
  "total_biometric_updates": 200000,
  "states_count": 28,
  "districts_count": 700
}
```

### 2. Get Idea Analysis Data
**URL**: `/idea/<idea_id>`
**Method**: `GET`
**Params**:
- `idea_id` (int): 1 to 10
- `state_filter` (optional, string): Filter by state Name
- `district_filter` (optional, string): Filter by district Name
**Description**: Returns specific data required to render the chart for a given idea.
**Response (Example for Idea 1)**:
```json
{
  "idea_id": 1,
  "title": "District-Level Activity",
  "data": {
    "labels": ["District A", "District B", "District C"],
    "datasets": [
      {
        "label": "Total Activity",
        "data": [5000, 3000, 1000]
      }
    ]
  },
  "insight": "District A has the highest activity."
}
```

### 3. Export Report
**URL**: `/export`
**Method**: `GET`
**Params**:
- `format` (string): 'csv' or 'pdf'
**Description**: Generates and downloads a report containing analysis of all 10 ideas.
