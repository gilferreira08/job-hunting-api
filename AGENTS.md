# AGENTS.md

## Project Name
Job Hunt Dashboard — Treasury & Strategic Finance CRM

## Project Purpose
Build a personal job-search CRM/dashboard for a senior finance professional targeting Treasury, Funding, Liquidity, Project Finance, Debt Structuring, Financial Risk Management, Treasury Transformation and Strategic Finance roles.

The app must help track verified job opportunities, avoid duplicates, manage applications, store board analyses, tailor CV/cover letter strategy and monitor follow-up actions.

## Candidate Positioning
The candidate is positioned as:

Treasury Manager | Funding & Liquidity | Treasury Transformation | Risk Management

Core strengths:
- Treasury Front Office
- Funding & Liquidity
- Debt Structuring
- Refinancing
- FX & Interest Rate Hedging
- Project Finance
- Infrastructure Finance
- Financial Modelling
- DSCR / IRR / CFADS
- Treasury Transformation
- TMS Implementation
- Strategic Finance Analysis
- High analytical/problem-solving roles

## Target Roles
Prioritize:
- Treasury Manager
- Treasury Front Office Manager
- Corporate Treasury
- Funding Manager
- Liquidity Manager
- ALM / Liquidity Manager
- Hedging / Risk Manager
- Project Finance Manager
- Infrastructure Finance
- Structured Finance
- Debt Advisory
- Treasury Transformation
- Strategic FP&A only if highly analytical and strategic

Avoid:
- Junior roles
- Accounting-only roles
- Audit-only roles
- AP/AR roles
- Back-office-only roles
- Tax-heavy treasury roles
- German-only roles
- Compliance-only risk roles
- Low analytical finance operations

## Priority Countries
1. France
2. Portugal
3. Switzerland
4. Luxembourg
5. Remote Europe
6. Brazil

## Approved Job Sources
Only use or track jobs from:

### Job Platforms
- LinkedIn
- eFinancialCareers
- Hellowork
- Welcome to the Jungle
- Glassdoor
- Indeed

### Company Career Sites
- Top French companies
- Top Portuguese companies
- Financial services companies
- Consultancies
- Fintech companies
- Infrastructure / energy / project finance companies

Do not rely on random aggregators, scraped pages, expired mirrors or unclear redirect links.

## Verification Rules
A job must NOT be added as a recommended opportunity unless:

1. The application link works.
2. The job page opens correctly.
3. The job title is visible on the page.
4. The role appears active/open.
5. The role is strategically aligned with the candidate profile.
6. The role is not a duplicate.
7. The role is not already applied, closed, excluded or out of scope.
8. The role was published within the last 14 days, unless the company career page clearly shows it is still active.

If any of these conditions fail, mark the role as:
- Closed
- Link Invalid
- Out of Scope
- Already Applied
- Duplicate
- Not Verified

Do not present unverified roles as recommendations.

## Application Statuses
Use only these statuses:

- Open
- In Preparation
- Applied
- Interview
- Final Round
- Offer
- Rejected
- On Hold
- Closed
- Link Invalid
- Out of Scope
- Duplicate
- Excluded

## Recruitment Board
Every job analysis must include feedback from the following board:

1. HR Director
2. CFO
3. Head of Treasury
4. Hiring Manager
5. FP&A Manager
6. Financial Risk Manager
7. Project Finance Director

Each board member should provide:
- Score from 0 to 100
- Strengths
- Concerns
- Feedback

Then calculate:
- Overall Board Score
- Recommendation: Apply Now / Consider / Skip

## Scoring Methodology
Use this weighted scoring model:

- Treasury / Hedging Relevance: 30%
- Project Finance Exposure: 20%
- Debt / Funding / Refinancing: 15%
- Seniority Match: 15%
- Tools & Systems: 10%
- Location Fit: 10%

## Recommendation Logic
Use:

### Apply Now
Score >= 80 and role is verified active.

### Consider
Score 70–79 or role is strategically useful but not ideal.

### Skip
Score < 70, out of scope, weak strategic fit, junior, accounting-heavy, audit-heavy or not verified.

## Existing Applications / Exclusions
The app must track and prevent duplicates.

Known applied roles:
- Soitec — Responsable Trésorerie Groupe
- Neoen — Project Finance Manager
- Pernod Ricard — Treasury Front Office Manager
- Stripe — Treasury Manager Luxembourg / BBSA-related treasury position
- Circle — Manager Treasury France
- Revolut — Treasury Manager / Liquidity or Capital
- Morgan Philips — Head Treasury & Investments
- SIPLEC — Directeur Trésorerie
- Bank of China — Treasury-related role
- Kering — BPO SAP Cash & Treasury Project Manager

Known excluded or unavailable:
- BIL — closed/unavailable
- DZ PRIVATBANK — German-heavy/out of scope
- Sensirion — tax-heavy/out of scope
- Axxès — unavailable
- Expectra — unavailable
- Technique Solaire — unavailable
- Omya — invalid/broken link
- QIMA — unavailable
- Wabtec — unavailable
- Wise — unavailable
- KPMG page previously tested as invalid
- BM&A — incorrect link
- Lawrence Harvey — incorrect link

## Data Model
The app should store each job with:

- id
- company
- positionTitle
- location
- country
- source
- applicationLink
- publicationDate
- verificationStatus
- status
- boardScore
- recommendation
- priority
- appliedDate
- lastCheckedDate
- nextActionDate
- cvVersion
- coverLetterVersion
- hiringContact
- notes
- duplicateKey

Duplicate key should be based on:
company + normalized title + country/location

## Dashboard Requirements
The dashboard should show:

- Total jobs tracked
- Open verified roles
- Applied roles
- Interviews
- Follow-ups due
- Closed/unavailable roles
- Average board score
- Top priority roles

## Main Views
Build these pages:

1. Dashboard
2. Jobs Table
3. Add Job
4. Job Detail
5. Board Analysis
6. CV / Cover Letter Tracker
7. Exclusions / Already Applied List

## Jobs Table Filters
Include filters for:
- Status
- Country
- Source
- Board score
- Recommendation
- Priority
- Verification status
- Application status

## CV Tailoring Logic
For each role, generate CV tailoring notes based on category:

### Treasury / Liquidity
Emphasize:
- Liquidity forecasting
- Cash management
- Funding strategy
- Treasury operations
- Treasury transformation
- TMS implementation

### Project Finance
Emphasize:
- DSCR / IRR / CFADS
- Debt sizing
- Refinancing
- Infrastructure finance
- Bankability analysis
- Financial modelling

### Fintech Treasury
Emphasize:
- Treasury scalability
- Automation
- Liquidity optimization
- Risk frameworks
- Fast-growth environment
- Cross-functional collaboration

### Treasury Advisory
Emphasize:
- TMS implementation
- Treasury process improvement
- Treasury governance
- Hedging advisory
- Stakeholder management

## UI Style
Use a clean executive finance style:
- Minimal
- Professional
- Dense but readable
- Dashboard/table-first
- Neutral colors
- No flashy consumer UI
- Prioritize clarity and speed

## Tech Stack
Preferred stack:
- Next.js
- TypeScript
- Tailwind CSS
- Prisma
- SQLite for local MVP
- Later migration possible to PostgreSQL / Supabase

## Development Rules
- Keep the first version simple.
- Do not over-engineer.
- Build MVP first.
- Use mock data initially if needed.
- Prioritize working tables, filters and forms.
- Add automation later.
- Do not scrape websites in MVP.
- Manual entry is acceptable for version 1.
- Avoid authentication in MVP unless requested.

## MVP Features
Version 1 must include:
- Jobs table
- Add/edit/delete job
- Status tracking
- Duplicate warning
- Board score fields
- Application link field
- Notes field
- Basic dashboard metrics

## Later Features
Add later:
- CSV import/export
- Follow-up reminders
- CV version upload/linking
- Cover letter version upload/linking
- AI-assisted board analysis
- Company target list monitoring
- Search history
- Application timeline

## Quality Standards
Before finishing any coding task:
- Run linting if available.
- Run type checks if available.
- Run tests if available.
- Start the app locally if possible.
- Fix visible errors.
- Keep code readable and maintainable.

## Communication Style
When explaining work:
- Be concise.
- Explain what changed.
- Mention files modified.
- Mention how to test.
- Mention limitations.
- Do not invent completed features.
