# StatsMatch

Local Flask app that searches API-Football and saves player profiles in
`data/players.csv`, created automatically on the first successful search.

## Search real players with a GET request

Add your API-Football (API-Sports) key to `.env` in the project root:

```dotenv
API_FOOTBALL_KEY=your-api-key
```

## Run in PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:5000. Press Ctrl+C to stop.


API client: `app/services/api_football.py`. GET route: `app/routes/api.py`.
Provider documentation: https://www.api-football.com/documentation-v3