---
type: method
domain: weather
topic: timestep
aliases: [teamoverbyeweather, team-overbye-weather, weather-client, weather-sdk, TeamOverbyeWeather]
tags: [weather, pww, era5, hrrr, noaa, python, client, download]
---

# Method: Getting weather data with the TeamOverbyeWeather client

## Abstract

`TeamOverbyeWeather` is a pip-installable Python client for the Team Overbye weather
portal. One call downloads a weather dataset, crops it to a region, and crops it to a
time window, returning `.pww` files ready for PowerWorld's TimeStep feature. It is the
**one part of the kit that needs no PowerWorld licence**: the client, the PWW reader, and
the cropping tools are pure Python. Verified against version 0.4.0; the `bbox` order and the `download()`
signature were re-checked against 0.4.2's installed source on 2026-10-19.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [pww-data](../concepts/pww-data.md) · [timestep-workflow](../concepts/timestep-workflow.md)
- **Next:** [timestep-simulation-setup](timestep-simulation-setup.md) to feed the downloaded PWW into PowerWorld

## Content

### Install

```bash
pip install TeamOverbyeWeather
```

Depends only on `numpy`, `requests`, and `tqdm`. No PowerWorld, no Windows requirement.

### The whole thing in five lines

```python
from TeamOverbyeWeather import WeatherClient

client = WeatherClient()
files = client.download("era5", "2021-02", region="TX", dest="./weather")
print(files)   # [PosixPath('weather/era5_texas_2021-02.pww')]
```

`download()` fetches, crops to the region, and crops to the time window server- or
client-side as appropriate, then writes `.pww`.

### What data is available

Do not guess source or type names. Ask the server:

```python
client.sources()          # ['era5', 'extreme', 'hrrr', 'noaa']
client.types("era5")      # ['historical', 'na', 'north_america', 'texas', 'tx']
client.types("hrrr")      # ['archive', 'current', 'forecast', 'history',
                          #  'hourly_archive', 'hourly_current']
client.types("noaa")      # ['archive', 'forecast', 'recent']
client.types("extreme")   # ['events']
client.catalog()          # everything, as a dict
client.status()           # server health
```

The four sources, and when to reach for each:

| Source | What it is | Use it for |
|---|---|---|
| `era5` | ECMWF reanalysis, hourly, ~0.25° | Long historical records. The default for screening a whole year |
| `hrrr` | NOAA High-Resolution Rapid Refresh, ~3 km, sub-hourly | Refining a specific event once screening has found it |
| `noaa` | NOAA GFS forecasts and archive | Forward-looking studies |
| `extreme` | The portal's curated extreme-event catalogue | Jumping straight to a known event without hunting for its dates |

Screen wide with `era5`, then refine a specific window with `hrrr`. Downloading HRRR for
a full year is neither necessary nor kind to the server.

### Selecting a region

Four mutually exclusive ways, in increasing order of precision:

```python
client.download("era5", "2021-02", region="TX")                       # a state
client.download("era5", "2021-02", iso="<ISO>")                        # an ISO footprint
client.download("era5", "2021-02", bbox=(36.5, -106.7, 25.8, -93.5))  # lat/lon box: N, W, S, E
client.download("era5", "2021-02")                                    # everything, usually too much
```

Discover valid identifiers rather than guessing:

```python
client.regions()                    # every layer the server knows
client.region_ids("states")         # ['AL', 'AK', 'AZ', 'AR', 'CA', ...]
```

`bbox` is `(lat_max, lon_min, lat_min, lon_max)`: **north, west, south, east**, in client
0.4.2. West longitudes are negative. Most libraries use min-then-max order instead, and
getting it wrong fails two different ways:

- `download()` checks the order and raises `ValueError: bbox (...) is inverted`.
- `pww_io.crop_to_bbox` and `localcrop.crop_file` take the same order but **do not check
  it**. A south-first box slices zero latitude rows and returns an empty crop with no error.
  Check the station count of a cropped file before you load it.

**A too-large request raises `RegionTooLargeError` rather than silently truncating.**
That is the server protecting itself; narrow the region or shorten the window.

### Selecting a time window

`dates` accepts a single date, a month string, or a list. For sub-day precision, add
`time_start` and `time_end`:

```python
files = client.download(
    "era5",
    "2021-02",
    region="TX",
    time_start="2021-02-14T00:00:00Z",
    time_end="2021-02-19T23:00:00Z",
    dest="./winter_storm_uri",
)
```

### The full signature

```python
client.download(
    source,                # 'era5' | 'hrrr' | 'noaa' | 'extreme'
    dates,                 # date, month string, or list
    type=None,             # from client.types(source)
    *,                     # everything below is keyword-only
    region=None,           # state/region id
    iso=None,              # ISO footprint
    bbox=None,             # (lat_max, lon_min, lat_min, lon_max) = N, W, S, E
    time_start=None,
    time_end=None,
    dest=".",              # output directory
    show_progress=None,    # overrides the client-level setting
    local_crop=True,       # crop client-side after download
    keep_raw=False,        # keep the uncropped download too
) -> list[Path]
```

Two flags:

- `local_crop=True` (the default) crops on your machine after downloading. Set it
  `False` only if you want exactly what the server sent.
- `keep_raw=True` keeps the uncropped file alongside the cropped one. Useful when you
  expect to re-crop the same download several ways; wasteful otherwise.

### Errors it raises

| Exception | Meaning | What to do |
|---|---|---|
| `RegionTooLargeError` | The requested region × time window exceeds the server's limit | Narrow the region, or split the time window and concatenate |
| `ServerBusyError` | The portal is under load | Back off and retry. Do not hammer it in a loop |
| `WeatherAPIError` | Anything else from the API | Read the message; usually a bad source/type/region name. Call `client.sources()` and `client.types()` to check |

```python
from TeamOverbyeWeather import RegionTooLargeError, ServerBusyError, WeatherAPIError
```

### Working with PWW files locally, without PowerWorld

The package reads and writes the PWW format directly. This is how you inspect weather
data on a machine with no PowerWorld licence.

```python
from TeamOverbyeWeather import pww_io

header, stations, arr = pww_io.read_pww_file("weather/era5_texas_2021-02.pww")
print(header)              # metadata: fields, time base, counts
print(len(stations))       # weather stations in the file
print(arr.shape)           # (time, field, lat, lon) uint8 grid, 0.25-degree cells
```

Crop, concatenate, and write back:

```python
from TeamOverbyeWeather import pww_io, localcrop

# crop an existing file on disk in one call
localcrop.crop_file("big.pww", "texas_only.pww",
                    bbox=(36.5, -106.7, 25.8, -93.5))   # N, W, S, E

# or work in memory
header, stations, arr = pww_io.crop_to_bbox(header, stations, arr,
                                            (36.5, -106.7, 25.8, -93.5))
assert stations, "empty crop: bbox order is (lat_max, lon_min, lat_min, lon_max)"
header, arr = pww_io.crop_to_timerange(header, arr, t_start, t_end)

# stitch several downloads into one continuous series
header, stations, arr = pww_io.concat_time([piece1, piece2, piece3])

open("combined.pww", "wb").write(pww_io.write_pww(header, stations, arr))
```

`concat_time` is the client-side answer to a region-too-large or window-too-long
rejection: download the pieces separately, then join them.

### Handing the result to PowerWorld

The `.pww` file this produces is the input to PowerWorld's TimeStep simulation. Continue
at [timestep-simulation-setup](timestep-simulation-setup.md), which loads it with `TimeStepLoadPWWRangeLatLon` and
runs the weather-to-MW conversion.

Crop before loading, not after. PowerWorld will happily ingest a continental PWW and
then spend a long time on stations you do not care about.

### What this client is not

It serves the Team Overbye portal only. For raw upstream access, go to the ERA5, HRRR or
NOAA services directly. What it saves you is the region crop, the time crop, and the PWW
conversion, which are normally the tedious part.
