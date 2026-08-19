# Viewer Engagement & Retention Analytics Platform

## SW2627 - Data Product - Subscription Statistics

A data analytics platform that identifies viewer engagement patterns associated with subscriber retention and presents actionable insights to support data-driven content acquisition decisions.

---

## 1. Project Overview

Subscription-based streaming platforms collect large amounts of viewer engagement data, including:

- Watch duration
- Pause frequency
- Episode completion
- Episodes watched
- Viewing frequency
- Subscription activity

However, content acquisition teams often lack a unified analytical system that connects these engagement behaviors with subscriber retention.

This project aims to bridge that gap by processing viewer activity data, engineering meaningful engagement metrics, analyzing their relationship with retention, and presenting the findings through an interactive dashboard.

### Core Question

> **Which viewer engagement patterns are associated with subscriber retention, and how can these insights help content acquisition teams make better decisions?**

---

## 2. Problem Statement

A subscription-based streaming platform captures watch duration, pause frequency, and episode completion data, but acquisition teams still greenlight content without understanding which viewer engagement patterns correlate with retention.

The platform may know how many people watched a piece of content, but raw view counts alone do not explain whether the content contributes to sustained subscriber engagement.

The project therefore focuses on connecting:

```text
Viewer Activity
       ↓
Engagement Metrics
       ↓
Viewer Segmentation
       ↓
Retention Analysis
       ↓
Content Insights
       ↓
Acquisition Decisions
```

---

## 3. Team Git & GitHub Workflow

To ensure smooth collaboration, quality control, and clean version history, our team follows a structured Git workflow.

### 1. Branch Naming Conventions

All new work should be developed on a dedicated branch created from `main`. Use descriptive branch names with appropriate prefixes:

| Prefix | Description | Example |
| :--- | :--- | :--- |
| `feat/` | New features, analysis modules, or pipelines | `feat/data-validation`, `feat/engagement-metrics` |
| `fix/` | Bug fixes and corrections | `fix/correct-data-processing`, `fix/missing-values` |
| `docs/` | Documentation additions or updates | `docs/update-readme`, `docs/team-workflow` |
| `setup/` | Environment, dependencies, or repository setup | `setup/dev-environment`, `setup/github-workflow` |
| `refactor/` | Code refactoring without changing functionality | `refactor/clean-pipeline` |

### 2. Feature Branch Workflow

Never commit directly to the `main` branch. Follow these steps for every task:

1. **Pull Latest Changes:** Always ensure your local `main` is up to date before starting:
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Create a Feature Branch:**
   ```bash
   git checkout -b feat/add-data-validation
   ```
3. **Work & Test Locally:** Make your changes and test them in your virtual environment.
4. **Stage and Commit Changes:** Make small, logical commits following conventional commit rules.

### 3. Conventional Commit Messages

We write clear, standardized commit messages in the format: `<type>: <short summary>`

Common types:
- `feat:` A new feature or functionality (e.g., `feat: add data validation`)
- `fix:` A bug fix or correction (e.g., `fix: correct data processing`)
- `docs:` Documentation changes only (e.g., `docs: update README`)
- `refactor:` Code refactoring without fixing a bug or adding a feature (e.g., `refactor: simplify metric calculation`)
- `chore:` Maintenance tasks or dependency updates (e.g., `chore: update dependencies`)

### 4. Pull Request (PR) & Code Review Workflow

1. **Push Feature Branch to GitHub:**
   ```bash
   git push -u origin feat/add-data-validation
   ```
2. **Open a Pull Request:**
   - Go to GitHub and open a Pull Request targeting `main`.
   - Provide a clear PR title and descriptive summary of changes made.
3. **Link Associated Issues:**
   - Connect the PR to its corresponding issue using keywords (e.g., `Closes #12` or `Resolves #45`).
4. **Peer Code Review:**
   - At least one teammate must review and approve the PR before merging.
   - Address any reviewer feedback or suggestions with additional commits on the branch.
5. **Merge to Main:**
   - Once approved, merge the PR into `main` and delete the feature branch.
