# Causal inference for conservation: do protected areas reduce deforestation?

Five units, each a lecture and a hands-on activity, all using one dataset: protected areas and forest loss in Belize, 2001–2023.

## Quick start

1. Open `causal-inference-pa.Rproj` in RStudio (or set the working directory to this folder).
2. Install the packages once (see Requirements below).
3. The data are already in `data/`, so there is nothing to download. `get_data.R` is only a record of how the data were made; it can take a long time to run and you do not need it.
4. Work through `00_layers.qmd`: load and map the layers, put them on a grid, and build `data/cells.rds`. This runs in seconds.
5. Open the unit notebooks in order.

## Contents

| File | What it is |
|---|---|
| `get_data.R` | Reference only: how the raw data were downloaded and saved in `data/` (slow; instructors) |
| `00_layers.qmd` | Unit 0 \| Working with the layers: load, map, rasterize, build the cell table |
| `01_dags.qmd` | Unit 1 \| DAGs: write the DAG in code, test its claims, good and bad controls |
| `02_rd.qmd` | Unit 2 \| Regression discontinuity at park boundaries (**the main focus**) |
| `03_matching.qmd` | Unit 3 \| Matching: balance, methods, sensitivity |
| `04_did.qmd` | Unit 4 \| Difference-in-differences: an open problem, no worked solution |

**Focus on regression discontinuity.** Work through the units in numerical order (DAGs, RD, matching, then DiD). Spend most of your time on the RD unit; matching is shorter, and DiD is an open problem for you to design if you have time!

**Why 2005?** Forest loss is observed from 2001, but most parks are from well before that. Units 1–3 treat parks designated by 2005 as protected and measure loss over 2006–2023; Unit 4 (DiD) is left open: the few parks designated after 2005 are the only ones with a before and an after. See `00_layers.qmd`.

## Files in `data/`

| File | Made in | Contents |
|---|---|---|
| `belize.gpkg` | `get_data.R` | Country outline (Natural Earth) |
| `pa_belize.gpkg` | `get_data.R` | Designated, mostly terrestrial protected areas, simplified to ~100 m, with designation year (WDPA) |
| `forest2000_300m.tif` | `get_data.R` | Share of each ~300 m cell with ≥ 30% tree cover in 2000 (Hansen) |
| `forest_loss_300m.tif` | `get_data.R` | 23 layers: share of each cell that lost forest in 2001 … 2023 (Hansen) |
| `elevation_1km.tif` | `get_data.R` | Elevation |
| `roads_belize.gpkg` | `get_data.R` | primary and secondary roads (OpenStreetMap, current) |
| `population_2000.tif` | `get_data.R` | People per ~1 km cell, 2000 (WorldPop) |
| `districts.gpkg` | `get_data.R` | Belize's six districts (GADM level 1) |
| `grid.tif` | `00_layers.qmd` | ~800 m grid: forest 2000, yearly loss, PA year, elevation, slope, road distance, population, district, remoteness |
| `cells.rds` | `00_layers.qmd` | One row per forested cell (every unit reads this in) |

Columns in `cells.rds`:

| Column | Meaning |
|---|---|
| `x`, `y` | Cell centre (lon/lat), ~800 m cells |
| `forest2000` | Share of the cell with ≥ 30% tree cover in 2000 |
| `loss_2001` … `loss_2023` | Share of the cell's 2000 forest lost that year |
| `pre_loss` | Share lost 2001–2005 |
| `loss` | Share of 2005 forest lost 2006–2023 (outcome for Units 1–3; Unit 4 uses the yearly `loss_*` columns) |
| `pa_year` | Designation year of the cell's earliest PA (`NA` = never protected) |
| `treated` | 1 if in a PA designated by 2005 |
| `late` | In a PA designated after 2005 (dropped in cross-sectional units) |
| `dist_frontier` | km to land already cleared in 2000 (remoteness) |
| `elev` | Elevation (m) |
| `slope` | Slope (degrees) |
| `dist_road` | km to the nearest major road (current OSM) |
| `pop` | People per km², 2000 |
| `district` | District name |
| `dist_edge` | Signed km to the edge of a PA designated by 2005 (+ inside, − outside) |

## Data sources

- **Forest change:** Hansen, M. C. et al. (2013) *Science* 342: 850–853. Global Forest Change v1.11 (2000–2023), read directly from Google Cloud Storage.
- **Protected areas:** UNEP-WCMC & IUCN, World Database on Protected Areas (June 2026), via the Boettiger lab's GeoParquet copy at `s3-west.nrp-nautilus.io/public-wdpa/wdpa.parquet`, simplified to ~100 m.
- **Elevation:** SRTM-derived 30″ elevation via the `geodata` package.
- **Roads:** OpenStreetMap contributors, via `osmdata` (Overpass API).
- **Population:** WorldPop 2000, 1 km UN-adjusted (`data.worldpop.org`); falls back to GPWv4 2000 via `geodata`.
- **Districts:** GADM v4.1 via `geodata`.
- **Boundaries:** Natural Earth via `rnaturalearth`.

## Troubleshooting

- **Few treated cells for DiD (Unit 4):** only about 100 cells are in parks designated after 2005, so expect a small, noisy sample. Widen the designation window you use.
- **`rdrobust` finds too few cells (Unit 2):** widen the 10 km window.
- **Model code uses the wrong `pop` or `elev`:** if a raster from Unit 0 with the same name is in your session, it can be picked up instead of the column. Restart R, or see the note in `03_matching.qmd`.

### Re-creating the data (instructors only)

Run `source("get_data.R")` from the project folder. It installs missing packages, downloads the data once, and saves small layers in `data/`. Each step is skipped if its file already exists, so delete a file to fetch it again.

- **Protected areas are slow:** the script scans the global WDPA file once for Belize's rows; after that `data/pa_belize.gpkg` is reused. If the server stalls, swap `s3-west.nrp-nautilus.io` for the mirror `minio.carlboettiger.info`.
- **Hansen read is slow:** download the two `20N_090W` tiles once with `download.file(..., mode = "wb")` and point `rast()` in `get_data.R` at the local files.
- **Roads download times out:** the Overpass API is sometimes busy; re-run `get_data.R` later (finished steps are skipped).

## Requirements

 Install the packages used by the notebooks:

```r
install.packages(c("tidyverse", "terra", "sf", "dagitty", "fixest", "rdrobust",
                   "MatchIt", "cobalt", "sensemakr"))
```

Only `get_data.R` also needs rnaturalearth, rnaturalearthdata, geodata, duckdbfs and osmdata.
