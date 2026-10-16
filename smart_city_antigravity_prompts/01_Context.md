# Context — Smart City: Where Should We Fix First?

> **Use this file as the product and dataset context for Antigravity.** Read this together with `02_Solution.md` and `03_Ideal_Tech_Stack.md`. Treat the CSV files and this specification as the source of truth. Do not invent columns, labels, or facts that are not present in the source data.

## 1. Product context

Build **Smart City — Where Should We Fix First?**, an explainable civic-infrastructure prioritization and intervention-support product. Its central question is:

**Given the location attributes, historic incidents, and public complaints in the supplied datasets, which locations should a city team review first, and why?**

The product should help a user explore patterns, compare locations and zones, understand the evidence behind a priority score, and consider suitable next-step interventions. It is a decision-support prototype, not an automated decision maker.

### Critical limitation

The accompanying `README.txt` explicitly describes this as a **synthetic educational dataset created for a DATATHON**. Coordinates and timestamps are simulated; these records are not official civic reports and must not be used to make actual public-safety decisions. Preserve that distinction throughout the product. Include a visible, persistent disclaimer on the dashboard, map, exports, and relevant detail views:

> **Synthetic demo data:** locations, coordinates, incidents, complaints, and timestamps are simulated. Priorities are illustrative and are not suitable for real-world public-safety decisions.

Do not infer or display a real city name. Do not claim that coordinates identify actual intersections, schools, hospitals, or events. The `near_school` and `near_hospital` fields are synthetic binary context flags.

## 2. Source files and join key

The supplied folder contains these three CSV datasets and `README.txt`:

| File | Rows | Purpose | Primary identifier | Join key |
|---|---:|---|---|---|
| `locations.csv` | 1,000 | One row per location, with zone, road, exposure, and simulated coordinates | `location_id` | `location_id` |
| `incidents.csv` | 10,000 | One row per recorded incident | `incident_id` | `location_id` |
| `public_complaints.csv` | 8,000 | One row per public complaint | `complaint_id` | `location_id` |
| `README.txt` | 5 lines | Dataset provenance, join key, and limitations | — | — |

**Join rule:** use `location_id` to connect each incident and complaint to exactly one location. Do not join incidents directly to complaints, which would create a many-to-many row explosion. Aggregate incidents and complaints independently to location level first, then join those aggregates to `locations.csv`.

## 3. Exact data dictionary

### `locations.csv` — 10 columns

- `location_id` — unique synthetic location identifier, e.g. `L0001`.
- `zone` — synthetic zone label, e.g. `ZONE_19`; there are 20 zones.
- `road_type` — one of `Local`, `Collector`, `Residential`, `Arterial`, `Highway`.
- `road_condition` — one of `Good`, `Fair`, `Poor`, `Critical`.
- `population_density_per_km2` — numeric population-density measure; do not reinterpret its units.
- `near_school` — binary flag (`0` or `1`).
- `near_hospital` — binary flag (`0` or `1`).
- `pedestrian_activity` — one of `Low`, `Medium`, `High`.
- `latitude` — simulated latitude.
- `longitude` — simulated longitude.

Observed location-data profile:

- 1,000 unique location IDs; no missing values were found in the supplied file.
- Zone sizes vary from 43 to 65 locations. When comparing zones, normalize by location count or show both totals and per-location measures. Do not rank zones by raw totals alone.
- Road condition counts: `Good` 230, `Fair` 383, `Poor` 309, `Critical` 78.
- `near_school = 1` for 286 locations; `near_hospital = 1` for 155 locations.
- Pedestrian activity: `Low` 316, `Medium` 431, `High` 253.
- `population_density_per_km2` ranges from 507 to 24,983; median is about 12,699.
- Simulated coordinate bounds are approximately latitude 16.186–16.707 and longitude 80.248–80.819. These bounds are **not evidence of real location accuracy**.

### `incidents.csv` — 9 columns

- `incident_id` — unique synthetic incident identifier, e.g. `I000001`.
- `location_id` — location reference.
- `timestamp` — synthetic incident timestamp, covering calendar year 2025.
- `incident_type` — one of `Streetlight outage`, `Signal failure`, `Pothole`, `Blocked drain`, `Collision`, `Flooding`.
- `severity` — one of `Low`, `Medium`, `High`, `Critical`.
- `injuries` — integer injury count for the incident.
- `reported_by` — one of `Citizen`, `Authority`, `Police`, `Sensor`.
- `resolved` — binary flag (`1` resolved, `0` unresolved).
- `resolution_hours` — numeric duration field supplied for every row.

Observed incident-data profile:

- 10,000 rows; 10,000 unique incident IDs; no missing values found.
- All 1,000 location IDs appear in the incident data; no unmatched location IDs found.
- Date range is 2025-01-01 through 2025-12-31.
- Incident types are fairly evenly represented: Streetlight outage 1,726; Signal failure 1,699; Pothole 1,685; Blocked drain 1,651; Collision 1,641; Flooding 1,598.
- Severity counts: `Low` 3,819; `Medium` 3,726; `High` 1,985; `Critical` 470.
- `resolved = 1` for 7,126 rows (71.3%) and `resolved = 0` for 2,874 rows (28.7%).
- 2,179 incident rows report at least one injury; `injuries` sums to 2,475 in this synthetic sample.
- `resolution_hours` has a median of 27.1 and mean of about 32.2 across all rows. Because the field is populated even for rows whose `resolved` flag is 0, do **not** treat every value as proof that a resolution was completed. For a completed-resolution KPI, filter to `resolved = 1` and label the metric clearly.
- `timestamp` is not unique (timestamps repeat); use `incident_id` as the event key.

### `public_complaints.csv` — 7 columns

- `complaint_id` — unique synthetic complaint identifier, e.g. `C000001`.
- `location_id` — location reference.
- `created_at` — synthetic complaint timestamp, covering calendar year 2025.
- `category` — one of `Road damage`, `Traffic`, `Lighting`, `Waste`, `Pedestrian safety`, `Drainage`.
- `priority_reported` — one of `Low`, `Normal`, `High`. The supplied data does **not** contain an `Urgent` value.
- `status` — one of `Resolved`, `In progress`, `Closed`, `Assigned`, `Open`.
- `days_to_resolution` — numeric duration field supplied for every row.

Observed complaint-data profile:

- 8,000 rows; 8,000 unique complaint IDs; no missing values found.
- All 1,000 location IDs appear; no unmatched location IDs found.
- Date range is 2025-01-01 through 2025-12-31.
- Categories are fairly evenly represented: Road damage 1,361; Traffic 1,357; Lighting 1,343; Waste 1,330; Pedestrian safety 1,319; Drainage 1,290.
- Reported priorities: `Normal` 4,469; `Low` 1,943; `High` 1,588.
- Status counts: `Resolved` 3,258; `In progress` 1,440; `Closed` 1,304; `Assigned` 1,062; `Open` 936.
- For a simple active-work queue, classify `Open`, `Assigned`, and `In progress` as active/non-terminal statuses. That is an explicit product assumption, not a new source field. Under this rule, 3,438 complaints (43.0%) are active/non-terminal. Treat `Resolved` and `Closed` as terminal for queue counts, but preserve and show their distinct source status labels.
- `days_to_resolution` is populated even for active/non-terminal statuses. Do not interpret those rows as confirmed completed turnaround durations. If reporting completed-resolution duration, filter to `Resolved` and/or `Closed`, state the filter, and keep raw values unchanged.
- `created_at` is not unique; use `complaint_id` as the key.

## 4. Data checks already performed

The supplied files were inspected for row counts, schema, missing values, unique IDs, value distributions, date ranges, and referential integrity. These checks found:

- No null/missing values across the provided columns.
- No duplicate `location_id`, `incident_id`, or `complaint_id` keys.
- No incident or complaint records whose `location_id` is absent from `locations.csv`.
- All 1,000 location IDs are represented in both the incident and complaint datasets.
- Repeated event timestamps exist, so timestamp must not be treated as a primary key.
- No need to fabricate, impute, or silently clean the supplied rows to get a basic joined dataset working.

Even so, implement runtime validation. Fail clearly or produce an explicit validation report if the actual files differ from these expected counts/schemas. Preserve raw files and never silently rewrite source data.

## 5. Exploratory findings to inform the product

These are simple descriptive aggregates from this synthetic sample. They are not causal claims or final risk rankings, and the product must compute them from the CSVs instead of hardcoding them.

- Each location has between 2 and 23 incident rows (mean 10; median 10) and between 1 and 17 complaint rows (mean 8; median 8).
- `ZONE_11` has the largest raw incident total (644), followed by `ZONE_05` (636) and `ZONE_16` (587). Zone sizes differ, so these raw counts alone should not determine the zone priority order.
- On a per-location basis, `ZONE_10` has the highest observed incident count average (about 10.77 incidents/location), followed by `ZONE_03` (10.45), `ZONE_15` (10.40), `ZONE_18` (10.35), and `ZONE_05` (10.26).
- `ZONE_01` has the highest observed average count of `Critical` incidents per location (0.70), followed by `ZONE_10` (0.66) and `ZONE_02` (0.65).
- `ZONE_18` has the highest observed average `High` incident count per location (about 2.39).
- `ZONE_01` has the highest summed-injury average per location (about 3.08).
- `ZONE_04` has the highest active/non-terminal complaint average per location (about 3.78 under the stated status rule).
- `ZONE_13` has the largest share of locations with `Poor` or `Critical` road condition (about 57%).
- At location level, the incident record with the highest raw incident count is `L0362` (23 records in the supplied data). It has 4 `Critical` and 4 `High` incidents, 7 summed injuries, and a `Poor` road condition. Use this only as a sanity check that aggregation works; do not make it a predetermined winner in a scoring model.

## 6. Product principles

1. **Explain every priority.** Show the score, component contributions, and source evidence behind each recommended location.
2. **No black-box ML by default.** These synthetic files do not supply a defensible labeled target for training a predictive risk model. Use a transparent, deterministic scoring method that is easy to test and tune.
3. **Separate observations from recommendations.** A score is a heuristic for review, not a forecast, causal statement, or declaration that harm will occur.
4. **Normalize fair comparisons.** Zone comparisons should account for the number of locations in each zone; time comparisons should use the selected time window and show the sample size.
5. **Keep traceability.** Every aggregate should be traceable to source records and `location_id`. Keep original category names and IDs intact.
6. **Be explicit about limitations.** The records are synthetic; no real dispatch, work orders, public alerts, or automatic interventions should be triggered.
