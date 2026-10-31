# CornProfit Connect

A student-friendly Streamlit + SQLite prototype for Philippine corn farmers. It runs locally and works offline for manual records and calculations.

## Included
- Farm cycle records, expenses, harvest income, profit/loss, filters, CSV export
- CornCost budget plans, planned-vs-actual category comparisons, break-even and revenue estimates
- CornPrice Watch manual price reports, filters, unit-price display, target alerts, CSV import
- CornBulk Connect farmer listings, connection requests, buyer offers, saved/contacted offers, transport estimates, offer comparison, group-selling cost allocations
- Profile/settings, local SQLite storage, password hashing, tests

## Requirements
Python 3.10+ recommended. Live government price feeds, online maps/routes, cloud backup, external messaging, and remote multi-user synchronization are not connected. Price and buyer data are manually entered and must be confirmed directly. The prototype's verification status is a user-entered label, not third-party verification.

## Install and run
1. Install Python from https://www.python.org/downloads/ (Windows: tick "Add Python to PATH").
2. Open a terminal in this folder.
3. Create a virtual environment:
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies: `python -m pip install -r requirements.txt`
5. Initialize the database (optional; app also initializes it automatically): `python -c "from database import init_db; init_db()"`
6. Start the app: `streamlit run app.py`
7. Open the URL printed by Streamlit, usually http://localhost:8501.
8. Register a local account. Use Settings to load clearly labelled sample data if desired.
9. Run tests: `pytest -q`

## Data and privacy
The SQLite database is stored in `data/cornprofit.db`. Back it up by copying that file while the app is closed. Passwords are PBKDF2 hashes, not plain text. This local prototype is not a security-audited commercial service; do not expose it publicly or store sensitive data until professional security, authorization, backup, and privacy reviews are complete.

## Sample data
Use **Settings → Load demonstration data**. All seeded price and buyer records are labelled as sample/unverified. The option adds records for the current account and can be run more than once; avoid repeatedly loading it if duplicate demo rows are unwanted. "Clear my demonstration data" removes only records marked with the demo naming conventions / sample notes where supported; review before using.

## Main calculation notes
- Expense amount = quantity × unit price when both are entered; otherwise enter a direct amount.
- Profit/loss = recorded income (gross sales + other income) − recorded expenses.
- Break-even = total budget cost ÷ expected saleable kg; zero quantity yields no break-even price.
- Fuel = round-trip km × L/km × fuel price/L.
- Net buyer proceeds = gross revenue − transport − stated fixed and percentage deductions. Unclear deductions are not auto-calculated.
- Group shared cost allocations are validated to add up to the entered total.

## Troubleshooting
- `streamlit: command not found`: activate the virtual environment and run `python -m streamlit run app.py`.
- SQLite permission error: place the project in a folder your account can write to.
- Port occupied: run `streamlit run app.py --server.port 8502`.
- Dependency errors: update pip with `python -m pip install --upgrade pip`, then reinstall requirements.
- Forgot local password: this prototype has no password recovery flow. For a demo, register another account; do not manually edit hashes unless you understand the database.

## Production-readiness gaps
A real deployment needs HTTPS, threat modelling, role/ownership authorization tests, rate limiting, secure password-reset, privacy/consent flows, database migrations, automated backups, audit logs, formal testing, and a proper hosting/database architecture. Online sync needs stable IDs, timestamps, conflict-resolution rules, and duplicate handling.
