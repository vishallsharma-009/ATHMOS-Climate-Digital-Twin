# Implementation Log

## YYYY-MM-DD
- **Decision**: Separated IMD and INSAT Rainfall channels.
- **Context**: The official ISRO problem statement implies keeping different observation sources distinct. A single 'Rainfall' metric was being logically merged in the frontend visualization.
- **Action Taken**: 
  - Verified that `isro_vars` in the backend correctly maps to the 6 required separate channels: `imd_rainfall_mm`, `tmax_c`, `tmin_c`, `lst_c`, `sst_c`, `insat_rainfall_mm`.
  - Updated `Forecast.jsx` to explicitly display both IMD Rain and INSAT Rain separately in the daily cards.
  - Updated `ClimateCharts.jsx` to split the `Rain (mm)` bar chart into two separate bar charts: `IMD Rain (mm)` and `INSAT Rain (mm)`, ensuring complete visual separation aligned with the backend tensor's source separation.
  - Verified backend pipeline logic to guarantee no overlapping mappings or silent averaging occurs during the dataset fusion phase.
