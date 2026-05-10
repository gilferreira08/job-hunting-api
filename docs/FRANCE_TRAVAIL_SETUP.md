# France Travail Connector Setup

This guide explains how to enable the `FranceTravailConnector` used by `POST /search-jobs`.

## 1) Required credentials

You need two environment variables:

- `FRANCE_TRAVAIL_CLIENT_ID`
- `FRANCE_TRAVAIL_CLIENT_SECRET`

These credentials are used to request an OAuth access token before querying the France Travail offers API.

## 2) Where to place credentials

Add them to your local `.env` file (never commit `.env`):

```env
FRANCE_TRAVAIL_CLIENT_ID=your_client_id_here
FRANCE_TRAVAIL_CLIENT_SECRET=your_client_secret_here
```

The `.env.example` file already includes these keys as placeholders.

## 3) How to verify `/search-jobs` is returning real France Travail jobs

Call:

```http
POST /search-jobs
```

with payload like:

```json
{
  "query": "Treasury Manager",
  "location": "France",
  "limit_per_source": 10
}
```

Then check backend logs for France Travail diagnostics printed by the endpoint.

## 4) Expected diagnostic messages

### A) Credentials missing / not configured

```text
[search-jobs] France Travail: 0 raw jobs | France Travail credentials missing. Set FRANCE_TRAVAIL_CLIENT_ID and FRANCE_TRAVAIL_CLIENT_SECRET.
```

### B) Token/API request failure

```text
[search-jobs] France Travail: 0 raw jobs | France Travail token request failed: ...
```

or

```text
[search-jobs] France Travail: 0 raw jobs | France Travail search request failed: ...
```

### C) Real jobs returned

```text
[search-jobs] France Travail: 7 raw jobs | France Travail returned 7 jobs
```

If you see a value greater than 0, the connector is live and returning data.

## 5) Example search queries

Use these examples in `POST /search-jobs`:

- `Treasury Manager France`
- `Funding Manager France`
- `Project Finance Manager France`
- `Risk Management Finance France`
