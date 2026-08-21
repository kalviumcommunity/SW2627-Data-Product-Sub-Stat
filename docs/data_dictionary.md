# Data Dictionary & Business Context Mapping

## SW2627 - Viewer Engagement & Retention Analytics Platform

This document outlines the data dictionary, data types, business context, and operational definitions for all entities and features within the streaming analytics platform.

---

## 1. Business Context & Analytical Objectives

The core mission of this data product is to determine **how viewer behavioral patterns influence subscriber retention**, enabling content acquisition teams to make data-backed investment decisions.

The dataset models four core functional domains:
1. **User & Subscription Profile**: Viewer demographics, geographical presence, and subscription tier economics.
2. **Viewing Consumption**: Granular content consumption sessions, content catalog categorization, and duration metrics.
3. **Engagement Behaviors**: Micro-interaction behaviors (pausing, completion rates, viewing cadence) representing viewer satisfaction.
4. **Retention & Churn Dynamics**: Account lifecycle milestones, renewal patterns, and churn classifications.

```text
+-----------------------+     +-----------------------+
|  User & Subscription  | --> |  Viewing Consumption  |
+-----------------------+     +-----------------------+
            |                             |
            v                             v
+-----------------------+     +-----------------------+
|  Retention & Churn    | <-- |  Engagement Dynamics  |
+-----------------------+     +-----------------------+
```

---

## 2. Comprehensive Data Dictionary

### A. User & Subscription Fields

| Column Name | Data Type | Constraint / Allowed Values | Description & Meaning | Business Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `viewer_id` | `VARCHAR(32)` / `String` | Primary Key, Non-Null | Unique identifier assigned to each registered viewer account. | Enables distinct tracking of individual viewer journeys and cross-session aggregations. |
| `user_name` | `VARCHAR(100)` / `String` | Non-Null | Full name or display name of the account holder. | Account management and personalization. |
| `country` | `CHAR(2)` / `String` | ISO-3166-1 alpha-2 (e.g., `US`, `UK`, `CA`, `AU`, `IN`) | Two-letter country code of account registration. | Geographical segmentation, regional content preference analysis, and regional pricing optimization. |
| `signup_date` | `DATE` / `String (YYYY-MM-DD)` | Valid Date <= Current Date | Date when the user first created the subscription account. | Cohort analysis, tenure calculation, and onboarding lifecycle tracking. |
| `subscription_plan` | `VARCHAR(20)` / `Categorical` | `Basic`, `Standard`, `Premium` | Current active or most recent subscription tier. | Revenue tiering and assessing retention variance across subscription tiers. |
| `monthly_fee` | `DECIMAL(6,2)` / `Float` | >= 0.00 | Monthly recurring subscription charge in USD. | Computing Customer Lifetime Value (CLV) and Monthly Recurring Revenue (MRR). |
| `auto_renew` | `BOOLEAN` / `Integer (0/1)` | `True (1)`, `False (0)` | Indicates whether automatic monthly subscription billing is enabled. | Early indicator of churn propensity when disabled. |
| `payment_method` | `VARCHAR(30)` / `Categorical` | `Credit Card`, `Debit Card`, `PayPal`, `Direct Debit` | Primary payment instrument on file. | Payment failure analysis and churn correlation. |

---

### B. Viewing Consumption Fields

| Column Name | Data Type | Constraint / Allowed Values | Description & Meaning | Business Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `content_id` | `VARCHAR(32)` / `String` | Foreign Key, Non-Null | Unique identifier for a movie, series, or episode. | Catalog performance tracking and content valuation. |
| `content_title` | `VARCHAR(150)` / `String` | Non-Null | Official title of the streaming content asset. | Reporting and content team executive dashboards. |
| `genre` | `VARCHAR(50)` / `Categorical` | `Drama`, `Sci-Fi`, `Comedy`, `Action`, `Documentary`, `Thriller`, `Animation` | Primary catalog classification category. | Genre affinity analysis to guide licensing and content acquisition budgets. |
| `content_type` | `VARCHAR(20)` / `Categorical` | `Movie`, `Series_Episode`, `Documentary_Special` | Structural format of the media item. | Differentiating single-session vs. multi-session engagement dynamics. |
| `watch_date` | `DATE` / `String (YYYY-MM-DD)` | Valid Date | Date on which the viewing session took place. | Time-series trend analysis, seasonality detection, and day-of-week viewing habits. |
| `watch_duration_minutes` | `DECIMAL(7,2)` / `Float` | >= 0.00 | Total duration in minutes watched by the viewer during the session. | Core volume metric for audience interest and consumption depth. |
| `total_content_duration_minutes` | `DECIMAL(7,2)` / `Float` | > 0.00 | Total running runtime of the media asset. | Normalizing watch duration against total runtime to derive completion rates. |

---

### C. Engagement Dynamics Fields

| Column Name | Data Type | Constraint / Allowed Values | Description & Meaning | Business Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `completion_rate` | `DECIMAL(5,4)` / `Float` | 0.0000 to 1.0000 | Proportion of content watched (`watch_duration / total_duration`). | Key proxy for viewer satisfaction; high completion correlates strongly with retention. |
| `pause_frequency` | `INTEGER` / `Integer` | >= 0 | Number of times playback was paused during the viewing session. | Measures viewing friction; excessive pauses may indicate disinterest or external distraction. |
| `rewind_count` | `INTEGER` / `Integer` | >= 0 | Number of backward seek operations executed. | Indicates scene replay interest or dialogue comprehension difficulty. |
| `episodes_watched` | `INTEGER` / `Integer` | >= 0 | Cumulative count of episodes completed in a series. | Measures franchise momentum and episodic stickiness. |
| `viewing_frequency_per_week` | `INTEGER` / `Integer` | 0 to 7 | Distinct days per week the viewer streamed content. | Measures platform habituation and regular platform usage. |
| `binge_watching_flag` | `BOOLEAN` / `Integer (0/1)` | `True (1)`, `False (0)` | Flagged `1` if viewer watched 3 or more consecutive episodes in a single day. | High binge frequency indicates strong content hook and short-term retention stability. |
| `engagement_score` | `DECIMAL(5,2)` / `Float` | 0.00 to 100.00 | Composite weighted index of completion rate, watch duration, and frequency. | Provides a single unified metric for ranking content assets and viewer segments. |

---

### D. Retention & Churn Fields

| Column Name | Data Type | Constraint / Allowed Values | Description & Meaning | Business Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `subscription_status` | `VARCHAR(20)` / `Categorical` | `Active`, `Paused`, `Cancelled` | Current operational state of the user account. | Target variable for operational reporting and subscriber counts. |
| `tenure_months` | `INTEGER` / `Integer` | >= 0 | Total consecutive months the subscription has remained active. | Baseline for cohort longevity and survival analysis. |
| `churn` | `INTEGER` / `Binary (0/1)` | `0 (Retained)`, `1 (Churned)` | Binary indicator denoting whether the subscriber cancelled within the observation window. | Primary classification target for predictive retention modeling. |
| `cancellation_date` | `DATE` / `String (YYYY-MM-DD)` | Valid Date or `Null` | Date of cancellation if `churn == 1`. | Pinpoints the exact timing of churn events relative to content release dates. |
| `cancellation_reason` | `VARCHAR(100)` / `Categorical` | `Price`, `Lack of Content`, `Technical Issues`, `Competitor`, `Other`, `Null` | Self-reported or inferred reason for subscription termination. | Actionable feedback for product and content acquisition teams. |
| `retention_risk_tier` | `VARCHAR(20)` / `Categorical` | `Low`, `Medium`, `High`, `Critical` | Model-assigned risk rating based on recent drop-off in viewing frequency and completion rates. | Triggers proactive retention interventions and personalized content recommendations. |
| `customer_lifetime_value` | `DECIMAL(8,2)` / `Float` | >= 0.00 | Cumulative historical revenue generated by the subscriber. | ROI evaluation for marketing acquisition campaigns and licensing cost recovery. |

---

## 3. Entity Relationships & Domain Architecture

```text
+--------------------------------------------------------------------------------+
|                                 VIEWER / USER                                  |
|  PK: viewer_id | user_name | country | signup_date | subscription_plan | fee   |
+--------------------------------------------------------------------------------+
                                       |
                                       | 1 : N (One viewer has many sessions)
                                       v
+--------------------------------------------------------------------------------+
|                              VIEWING & ENGAGEMENT                              |
|  PK: session_id | FK: viewer_id | FK: content_id | watch_date | duration        |
|  completion_rate | pause_frequency | episodes_watched | binge_flag | score     |
+--------------------------------------------------------------------------------+
                                       |
                                       | N : 1 (Many sessions link to one content)
                                       v
+--------------------------------------------------------------------------------+
|                                 CONTENT ASSET                                  |
|  PK: content_id | content_title | genre | content_type | total_duration        |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                              RETENTION & LIFECYCLE                             |
|  FK: viewer_id | status | tenure_months | churn (0/1) | risk_tier | CLV        |
+--------------------------------------------------------------------------------+
```
