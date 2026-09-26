# Pakistan Carbon Emissions — a monitoring readout

A small, self-contained dashboard of Pakistan's CO₂ emissions from 1960 to 2024, built to
understand what national emissions data can and cannot tell you about a city.

**Live:** https://<your-username>.github.io/pakistan-carbon-emissions/

## The data

[Our World in Data — CO₂ and Greenhouse Gas Emissions](https://github.com/owid/co2-data),
which packages the Global Carbon Budget into a single tidy CSV (CC BY). Figures are
**production-based** CO₂: emissions counted where the fuel is burned. They exclude land-use
change and non-CO₂ greenhouse gases, both of which matter and neither of which is in scope here.

`prepare_data.py` reads the 14 MB source file and writes a 10 KB `data.json` holding only the
four views the page draws, so the dashboard loads in kilobytes rather than parsing a CSV in the
browser.

## What the four charts show

**National total against emissions per person.** Pakistan's total has roughly tripled since 1990,
while emissions per person have stayed under one tonne. The two lines separate because population
growth sits between them — a reminder that a rising national total is not by itself evidence that
individual consumption is rising.

**Regional comparison, per person.** On the same axis as India, Bangladesh and Iran, Pakistan sits
near the bottom. Iran's line makes the scale honest: a single regional neighbour emits more than
ten times as much per person.

**Source breakdown.** Oil, gas and coal each carry a comparable share, with cement a persistent
fourth. The five sources reconstruct the published national total to within 0.002 Mt, which is the
check the script prints on every run.

**Growth against emissions.** GDP per person and CO₂ per person plotted as a path through time.
Pakistan moves right and up together, then reverses sharply after 2021 — emissions per person fell
from 1.02 t to 0.72 t by 2024. That is not decoupling; it tracks an economic contraction, and it
is exactly the kind of ambiguity annual national data cannot resolve on its own.

## What would need to be monitored instead

The honest conclusion of this exercise is that annual, national, production-based figures are the
wrong instrument for urban policy:

- **Spatial resolution.** Policy acts on corridors and neighbourhoods. That needs a gridded
  inventory — satellite NO₂ and CO column measurements, or a bottom-up inventory assembled from
  traffic counts, fuel sales and industrial registers.
- **Temporal resolution.** One value per year cannot attribute a change to a policy rather than to
  a fuel-price shock or a winter inversion. Daily or hourly series can.
- **Accounting basis.** Production-based figures assign emissions to where fuel is burned.
  Consumption-based accounting assigns them to where goods are used, and gives a different answer
  about responsibility.

## Running it

```bash
curl -L -o owid-co2-data.csv \
  https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv
pip install pandas
python prepare_data.py          # writes data.json
python -m http.server           # then open http://localhost:8000
```

Serve the folder rather than opening `index.html` directly — browsers block `fetch()` on
`file://` URLs, so the page will report that it cannot load `data.json`.

## Built with

Python and pandas for the aggregation; plain HTML, CSS and JavaScript with
[Chart.js](https://www.chartjs.org/) for the page. No build step and no framework — the whole
thing is three files and deploys to GitHub Pages as-is.

---

Built by Mariyam · BS Data Science, FAST-NUCES Lahore ·
[github.com/imsbrb](https://github.com/imsbrb)
