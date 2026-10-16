# Solution — Antigravity Build Prompt

> **Build instruction:** Use this file together with `01_Context.md` and `03_Ideal_Tech_Stack.md`. Implement the product end to end around the actual CSV schemas. Inspect the repository and available MCP tools before making changes. Work in small, verifiable steps, run the app and tests, and fix errors rather than stopping after scaffolding.

## Mission

Build **Smart City — Where Should We Fix First?**, an explainable prioritization and intervention-support system for a synthetic civic dataset. Help an analyst answer:

- Which locations appear to need review first?
- What evidence makes each location rank highly?
- Which issue types and open complaints are driving the score?
- How do locations and zones compare after normalizing for zone size?
- What broad next-step intervention should be considered, based on the recorded issue categories?

The frontend will be supplied by me through **Stitch MCP**. Do not independently invent or redesign the full UI. Prioritize the data pipeline, domain logic, backend/API, validation, scoring, tests, and integration contracts. When Stitch output is available, inspect and integrate it while preserving its visual design and component choices. Do not replace Stitch-generated screens with your own design system.

## 1. First inspect the workspace

1. Inspect the existing repository, runtime, current files, environment, and Stitch MCP output if available.
2. Find the provided files `locations.csv`, `incidents.csv`, `public_complaints.csv`, and `README.txt`. If their location differs, discover the actual path; do not create substitute datasets.
3. Read `01_Context.md` and `03_Ideal_Tech_Stack.md` before implementing.
4. Reuse the repository's existing project conventions and package manager where sensible. Do not create a duplicate frontend app or competing backend framework.
5. Write down a short implementation checklist in the repository, then execute it. Do not stop at a plan.

## 2. Data ingestion and canonical domain model

Create a robust, repeatable loading pipeline for the three CSV files.

- Preserve the supplied files as immutable source inputs.
- Validate required columns, expected value domains, numeric fields, timestamp parseability, unique primary keys, and `location_id` referential integrity.
- Convert `timestamp` and `created_at` to proper datetime types. Treat them as event timestamps, not unique keys.
- Validate `resolved`, `near_school`, and `near_hospital` as binary values; validate injuries and durations as numeric and non-negative. If validation fails, return actionable validation errors rather than silently dropping or changing data.
- Keep source categories and IDs exactly as provided. Do not invent an `Urgent` priority or missing categories.
- Aggregate incidents and complaints independently by `location_id`; only then join those per-location aggregates to locations. Avoid many-to-many joins.
- Ensure every metric has a clear denominator and definition. Expose the record counts used for it.
- Make the loader idempotent: running it twice must not duplicate persisted source records or aggregates.
- Support a clear local setup command and a clear data re-import command. Add a validation report or health endpoint that states loaded row counts and any problems.

### Required derived metrics per location

At minimum, calculate:

**Incident metrics**
- `incident_count`
- counts by incident type
- counts by severity (`Low`, `Medium`, `High`, `Critical`)
- `severity_weighted_burden`, using the configurable default weights `Low=1`, `Medium=2`, `High=4`, `Critical=7`
- `total_injuries` and `injury_incident_count` (count incidents with `injuries > 0`)
- `unresolved_incident_count` (`resolved = 0`)
- `resolved_incident_count` (`resolved = 1`)
- `incident_resolution_rate` = resolved count / incident count
- median recorded resolution hours for completed incidents only (`resolved = 1`); label this filter clearly
- latest incident date and incident counts by month/type/severity where useful

**Complaint metrics**
- `complaint_count`
- counts by complaint category and reported priority
- `high_priority_complaint_count` (`priority_reported = 'High'` only)
- `active_complaint_count` (`status` in `Open`, `Assigned`, `In progress`)
- counts by every source status, preserving the exact status labels
- median recorded days to resolution for terminal-status complaints only (`Resolved` or `Closed`), labelled with that filter
- latest complaint date and complaint counts by month/category/status where useful

**Location/context metrics**
- all original location fields
- `incident_count` and `complaint_count` density-normalized only where the denominator is explicit
- road-condition factor, exposure-context component, final score, ranking, tier, and score-component explanations

A location is one row in the combined location summary. Event-level detail must remain available for drill-down and traceability.

## 3. Explainable priority score

Implement a deterministic, documented, unit-tested **0–100 review-priority score**. This is an illustrative heuristic, not a validated safety model. Keep the formula and weights in one configuration file or typed configuration object, not scattered throughout the code. Show the exact component scores, weights, and evidence used for each location. Allow the default weights to be tuned later without rewriting the aggregation pipeline.

### Default component weights (sum = 100)

| Component | Weight | Definition |
|---|---:|---|
| Incident recurrence | 20 | Percentile rank of the location's incident count among all locations |
| Safety impact | 25 | Percentile rank of the location's severity-weighted burden plus injury burden; severity weights are configurable (`Low=1`, `Medium=2`, `High=4`, `Critical=7`) and the injury multiplier defaults to `2` |
| Unresolved incidents | 15 | Percentile rank of `unresolved_incident_count` |
| Complaint volume | 15 | Percentile rank of `complaint_count` |
| Active complaint backlog | 10 | Percentile rank of active complaints (`Open`, `Assigned`, `In progress`) |
| Road condition | 10 | Deterministic condition mapping: `Good=0.10`, `Fair=0.35`, `Poor=0.70`, `Critical=1.00` |
| Exposure context | 5 | Average of four values: percentile-ranked population density, pedestrian activity (`Low=0.25`, `Medium=0.60`, `High=1.00`), `near_school` flag, and `near_hospital` flag |

### Score calculation rules

- Convert percentile-ranked components to a 0–1 scale, with deterministic tie handling.
- For the `Safety impact` component, define the raw burden as `severity_weighted_burden + (injury_multiplier * total_injuries)`, then compute its percentile rank.
- Define `Exposure context` as the mean of the four normalized subcomponents above. `near_school` and `near_hospital` are binary inputs, not verified geographic facts.
- Calculate the score as the weighted sum of each 0–1 component multiplied by its weight. This yields a score between 0 and 100 before rounding.
- Handle ties deterministically. Include a stable secondary sort such as `location_id`; do not let record order affect results.
- Do not penalize a location because one dataset has a lower row count without checking the denominator. Explain that all scores are based on the supplied synthetic 2025 sample.
- Provide a `score_version` and return the component breakdown with every ranked record.
- Store thresholds for display tiers in configuration and label the tiers as illustrative. Suggested defaults: `80–100 = Very High`, `60–<80 = High`, `40–<60 = Moderate`, `<40 = Lower`. Explain that labels/weights are prototype defaults and not calibrated against real-world outcomes.
- Use the displayed score to order the ranked list. Make the tie-breaking order explicit.
- Include tests asserting that scores stay in `[0, 100]`, weights total 100, missing joins are rejected, repeatable inputs yield repeatable scores, and increasing an adverse feature with other features fixed does not reduce the score.

## 4. Suggested intervention logic

Create a transparent rule-based **suggested next-step** for analysts. This is guidance for review only, not an instruction to dispatch a crew, issue a fine, or initiate emergency response. Tie every suggestion to visible evidence and show the rule that triggered it.

Examples of mappings:

- High pothole incidents or `Road damage` complaints → consider a road-surface inspection and repair assessment.
- High `Blocked drain`, `Flooding`, or `Drainage` records → consider a drain inspection/clearing assessment.
- High `Streetlight outage` incidents or `Lighting` complaints → consider a streetlight audit and repair assessment.
- High `Signal failure`, `Traffic`, or `Collision` records → consider a signal/intersection and traffic-safety audit.
- Elevated `Pedestrian safety` complaints, high pedestrian activity, or `near_school = 1` → consider a pedestrian-crossing/walkway review.
- High `Waste` complaints → consider a waste-collection or cleanliness review.

When multiple issues are present, return the top one or two suggestions with their evidence, not an opaque generated paragraph. Keep the mapping editable in configuration. Use phrasing such as “Suggested review” or “Consider assessing”; do not claim the intervention will solve the problem or infer causality.

## 5. Product capabilities and expected user journeys

The frontend comes from Stitch MCP, so implement the APIs and data contracts needed for these flows without designing a replacement UI.

### A. Overview / dashboard

Provide a concise summary of the synthetic sample:
- number of locations, incidents, and complaints loaded
- share/count of incidents flagged resolved and unresolved
- severity breakdown, including Critical and High
- active complaint count and status breakdown
- locations by road condition
- incident and complaint trends by month across the selected date range
- top locations by review score, each with clear “why it ranks here” evidence

Use clear labels and units. Any chart must be generated from loaded data and react to date/zone/category filters where applicable.

### B. Priority worklist

Return a sortable, filterable location list with:
- rank and score / tier
- `location_id`, zone, road type, and road condition
- incident/complaint totals
- High/Critical incidents, total injuries, unresolved incidents, active complaints
- the top score drivers and a plain-language reason summary
- the suggested next-step review

Support filtering by zone, road type, road condition, pedestrian activity, near-school/hospital flags, issue type/category, severity, and priority tier where applicable. Support sorting and pagination. Return the active filter state and total result count in the API response.

### C. Location detail

For a selected `location_id`, provide:
- all source attributes from `locations.csv`
- total score and every weighted component
- a human-readable explanation generated from actual component values (do not use a canned reason that ignores the row)
- event and complaint counts by category/severity/status
- a chronological incident/complaint timeline, with sensible pagination and date filters
- relevant record identifiers, timestamps, and source attributes for auditability
- rule-based suggested review(s) with their triggering evidence

### D. Zone comparison

- Show counts plus **per-location averages/rates** for incidents, High/Critical incidents, injuries, unresolved incidents, complaints, and active complaints.
- Include zone location count as the denominator.
- Compare average priority score and road-condition mix.
- Clearly distinguish “raw totals” from “per-location” metrics. The zones have unequal numbers of locations (43–65 each), so raw totals are not a fair standalone ranking.

### E. Spatial exploration

- Prepare location records for a point map using `latitude` and `longitude` only as simulated coordinates.
- The map must display the synthetic-data disclaimer directly within the map experience. Do not display real street/intersection names inferred from the coordinates or imply that pins are real reports.
- Support selection of a point to open its location details. Allow switching between score, incident count, and active complaint count as the point metric if the supplied Stitch UI supports it.
- Do not call a geocoding service to enrich these synthetic points.

### F. Export and transparency

- Allow export of the current ranked location table and zone summary to CSV, including score components and a concise reason field.
- Include `score_version`, `generated_at`, selected filters, record counts, and the synthetic-data disclaimer in an export metadata sheet/file or documented companion metadata.
- Do not export private credentials, environment variables, or unfiltered event data when the user has selected a filtered view unless that behavior is clearly exposed.

## 6. API contract

Implement REST endpoints along these lines, adapting naming to the existing repository if needed. Document the final routes and response models.

- `GET /api/health` — service status, dataset readiness, loaded row counts, data/score version.
- `GET /api/overview` — dashboard KPIs and aggregate chart series; support date and zone filters.
- `GET /api/locations` — filtered, sortable, paginated location summary list; include total count and filters applied.
- `GET /api/locations/{location_id}` — full location detail, score explanation, and related records.
- `GET /api/zones` — zone totals and denominator-normalized metrics.
- `GET /api/trends` — monthly time series with selectable metric, record type, category/type, zone, and date range as feasible.
- `GET /api/filters` — valid zone, road type, condition, activity, issue type, severity, complaint category, status, and priority values sourced from data/configuration.
- `GET /api/exports/locations.csv` and `GET /api/exports/zones.csv` — filtered exports.

Use typed request validation and typed response models. Validate page sizes and date bounds; reject unknown sort keys instead of accepting arbitrary SQL or dataframe expressions. Return useful 4xx messages for invalid filters and a clear error when datasets are not loaded. Do not expose internal filesystem paths in production API errors.

## 7. Stitch MCP frontend integration

When the frontend arrives through Stitch MCP:

1. Inspect its component tree, routes, responsive behavior, styles, icons, design tokens, and expected input data.
2. Preserve Stitch's layout and visual direction. Bind its charts, cards, map, tables, and detail screens to the API responses rather than hardcoding demo metrics.
3. Create a small typed API client and explicit TypeScript types from the backend schema if the provided frontend is TypeScript-based.
4. Match loading, empty, validation-error, and server-error states to the existing visual system.
5. Avoid duplicate state for derived metrics. Keep the score computation server-side or in the single shared domain layer; never implement slightly different scoring logic in the frontend.
6. Do not silently replace available real Stitch assets with placeholders. Do not create a competing frontend, design system, or styling framework merely because integration is inconvenient.
7. If Stitch MCP output is not available yet, build the backend and contracts first and leave clearly documented integration points; do not block implementation by asking for a mockup.

## 8. Data visualizations and interaction quality

Where supported by the supplied interface, prepare data for:
- score-ranked location table
- incident severity and type distributions
- complaint category, priority, and status distributions
- monthly incidents vs complaints
- road-condition distribution
- normalized zone comparison
- map with score/issue overlays
- location-specific event timeline

Charts must use values computed from the source datasets, include axis labels/units and tooltips, handle empty result sets, and respect active filters. Do not fabricate trend points or extrapolate beyond the 2025 records. If a date filter has no rows, return an empty series with a meaningful empty-state message.

## 9. Non-functional requirements

- Deterministic, explainable, testable calculations.
- No ML claims, predictive certainty, or causal claims.
- Clean separation between ingestion, aggregation, scoring, intervention rules, persistence, and API handlers.
- No hardcoded dashboard totals or pre-decided winner location/zone.
- Reproducible installation and local run instructions.
- Useful logs and actionable validation errors; no secrets in logs.
- Sensible pagination for event lists and bounded query sizes.
- Accessible API data shape: stable names, explicit nullability, readable labels, and numeric values as numbers (not formatted strings) except display labels.
- Avoid unrelated product features such as user accounts, live dispatch, real-time sensors, payments, or notifications unless already present in the repository and explicitly required.

## 10. Definition of done

The work is complete only when:

- The app can load the three supplied CSVs without manually editing them.
- Validation confirms 1,000 locations, 10,000 incidents, and 8,000 complaints for the supplied versions, with no missing or unmatched location references.
- Aggregates are created without multiplying records through a many-to-many join.
- The priority score and explanation are deterministic, versioned, configurable, and covered by tests.
- Overview, worklist, location-detail, zone-comparison, trends, and export APIs work and are documented.
- Active complaint status logic and completed-resolution duration filters are explicit and tested.
- Synthetic-data limitations are visible in the API/docs and ready to be displayed by the Stitch frontend.
- Frontend integration respects the Stitch implementation when it is present.
- Tests pass, the backend launches locally, and README instructions explain setup, data location, import, test, run, and API access.
