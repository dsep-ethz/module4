# get_data.R
# Downloads the raw data once and saves small, lower-resolution layers in data/.
# Run once from the project folder:  source("get_data.R")
# Instructors: run this yourself and share data/, so students start from 00_layers.qmd.
# Each step is skipped if its file already exists (delete the file to redo it).

# ---- packages ---------------------------------------------------------------
pkgs <- c("terra", "sf", "dplyr", "rnaturalearth", "rnaturalearthdata", "geodata", "duckdbfs", "osmdata",
          # used by the activities
          "tidyverse", "dagitty", "fixest", "rdrobust", "MatchIt",
          "cobalt", "sensemakr")
missing <- setdiff(pkgs, rownames(installed.packages()))
if (length(missing)) install.packages(missing)

library(terra)
library(sf)
library(dplyr)

dir.create("data", showWarnings = FALSE)
setGDALconfig(c("GDAL_HTTP_TIMEOUT=60", "GDAL_HTTP_MAX_RETRY=3", "GDAL_HTTP_RETRY_DELAY=2"))

# ---- 1. Belize outline ----------------------------------------------------------
belize <- rnaturalearth::ne_countries(scale = "medium", country = "Belize", returnclass = "sf")
st_write(belize, "data/belize.gpkg", delete_dsn = TRUE, quiet = TRUE)
win <- ext(vect(belize))

# ---- 2. protected areas: polygons, simplified to ~100 m --------------------------
# WDPA (June 2026) GeoParquet from the Boettiger lab. This is the slow step: the
# global file is scanned for Belize's rows. Mirror if slow:
# https://minio.carlboettiger.info/public-wdpa/wdpa.parquet
f_pa <- "data/pa_belize.gpkg"
if (!file.exists(f_pa)) {
  message("Protected areas (slow, once) ...")
  pa <- duckdbfs::open_dataset("https://s3-west.nrp-nautilus.io/public-wdpa/wdpa.parquet") |>
    filter(ISO3 == "BLZ", STATUS == "Designated", STATUS_YR > 0,
           GIS_M_AREA < 0.5 * GIS_AREA) |>                    # drop mostly-marine PAs
    select(SITE_ID, NAME_ENG, DESIG_ENG, IUCN_CAT, STATUS_YR, geom = SHAPE) |>
    duckdbfs::to_sf(crs = 4326) |>
    st_make_valid() |>
    st_transform(32616) |>                                     # UTM 16N, metres
    st_simplify(dTolerance = 100) |>
    st_transform(4326)
  st_write(pa, f_pa, delete_dsn = TRUE, quiet = TRUE)
}

# ---- 3. forest: Hansen GFC v1.11, 30 m -> ~300 m -----------------------------------
# Belize is inside one 10-degree tile (20N_090W). Only the Belize window is read.
url <- "/vsicurl/https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/Hansen_GFC-2023-v1.11_%s_20N_090W.tif"
f_forest <- "data/forest2000_300m.tif"
f_loss   <- "data/forest_loss_300m.tif"
if (!all(file.exists(c(f_forest, f_loss)))) {
  message("Forest loss (once) ...")
  lossyear  <- crop(rast(sprintf(url, "lossyear")), win)
  treecover <- crop(rast(sprintf(url, "treecover2000")), win)
  forest    <- treecover >= 30

  # share of each ~300 m cell that was forest in 2000
  writeRaster(aggregate(forest, 10, mean), f_forest, overwrite = TRUE)

  # 23 layers: share of each cell's area that lost forest in 2001, ..., 2023
  loss <- rast(lapply(1:23, \(y) aggregate(forest & lossyear == y, 10, mean)))
  names(loss) <- paste0("loss_", 2001:2023)
  writeRaster(loss, f_loss, overwrite = TRUE)
}

# ---- 4. elevation (~1 km) ----------------------------------------------------------
f_elev <- "data/elevation_1km.tif"
if (!file.exists(f_elev)) {
  elev <- geodata::elevation_30s("BLZ", path = tempdir())
  writeRaster(crop(elev, win), f_elev, overwrite = TRUE)
}

# ---- 5. major roads ----------------------------------------------------------------------
f_roads <- "data/roads_belize.gpkg"
if (!file.exists(f_roads)) {
  message("Roads ...")
  servers <- c("https://overpass-api.de/api/interpreter",
               "https://overpass.kumi.systems/api/interpreter",
               "https://maps.mail.ru/osm/tools/overpass/api/interpreter")
  roads <- NULL
  for (s in servers) {
    roads <- tryCatch({
      osmdata::set_overpass_url(s)
      osm <- osmdata::opq(bbox = st_bbox(belize), timeout = 180) |>
        osmdata::add_osm_feature("highway", c("motorway", "trunk", "primary", "secondary")) |>
        osmdata::osmdata_sf()
      osm$osm_lines[, c("osm_id", "highway")]
    }, error = function(e) { message("  ", s, " failed: ", conditionMessage(e)); NULL })
    if (!is.null(roads)) break
  }
  if (is.null(roads)) {
    message("  Overpass unavailable: using Natural Earth roads instead")
    roads <- rnaturalearth::ne_download(scale = 10, type = "roads", category = "cultural",
                                        returnclass = "sf") |>
      st_make_valid() |>
      st_crop(st_bbox(belize)) |>
      select(type)
  }
  st_write(roads, f_roads, delete_dsn = TRUE, quiet = TRUE)
}

# ---- 6. population 2000 (WorldPop, 1 km, Belize only) ----------------------------------
f_pop <- "data/population_2000.tif"
if (!file.exists(f_pop)) {
  message("Population ...")
  wp <- "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2000/BLZ/blz_ppp_2000_1km_Aggregated_UNadj.tif"
  ok <- tryCatch({ download.file(wp, f_pop, mode = "wb", quiet = TRUE); TRUE }, error = function(e) FALSE)
  if (!ok) {
    message("  WorldPop unavailable: using GPWv4 (geodata, ~5 km) instead")
    gpw <- geodata::population(year = 2000, res = 2.5, path = tempdir())
    writeRaster(crop(gpw, win), f_pop, overwrite = TRUE)
  }
}

# ---- 7. districts (GADM level 1) -------------------------------------------------------
f_dist <- "data/districts.gpkg"
if (!file.exists(f_dist)) {
  districts <- geodata::gadm("BLZ", level = 1, path = tempdir()) |> st_as_sf()
  st_write(districts[, "NAME_1"], f_dist, delete_dsn = TRUE, quiet = TRUE)
}

message("Done. Layers in data/: ", paste(list.files("data"), collapse = ", "))

