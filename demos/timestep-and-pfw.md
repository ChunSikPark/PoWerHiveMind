---
type: method
domain: weather
topic: timestep
aliases: [demo-timestep, pfw-demo, weather-to-mw-demo, timestep-demo]
tags: [demo, timestep, pfw, pww, weather, renewables, esapp, worked-example]
---

# Demo: Weather to megawatts — PFW models and TimeStep

## Abstract

Turning a weather file into hourly wind and solar output. Covers the check that decides
whether the case can do this at all — **do its renewable units carry PFW model
strings?** — verified on a real case where 9 of 45 generators do. Getting that check
wrong is why TimeStep runs "successfully" and produces nothing.

## Connections

- **Up:** [Home](../index.md) · [index](../index.md)
- **Across:** [timestep-workflow](../concepts/timestep-workflow.md) · [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md) · [pww-data](../concepts/pww-data.md) · [how-to-analyze-results](../methods/how-to-analyze-results.md)

## Content

### The user's prompts

> *"Can this case do a weather simulation?"*
> *"Get February 2021 weather and tell me how much wind and solar these units produce."*

### Step 1 — can this case do it at all?

Ask before setting anything up. TimeStep does not convert weather to power — **each
generator's embedded PFW model does**. A unit without one produces nothing, and nothing
warns you.

```python
from esapp import PowerWorld
from esapp.components import Gen

pw = PowerWorld(r"C:\path\to\Synth40_with_PFW.pwb")

g = pw[Gen, ["GenFuelType", "GenMW", "GenMWMax", "TSPFWModelString"]]
ft = g["GenFuelType"].astype(str).str.strip()
print(ft.value_counts().to_dict())

ren = g[ft.str.contains("WND|SUN", na=False)]
has_pfw = g["TSPFWModelString"].astype(str).str.len() > 2
print(f"renewable units: {len(ren)}   with a PFW model: {has_pfw.sum()}")
```

```
fuel types: {'DFO (Distillate Fuel Oil)': 23, 'OBL (Other Biomass Liquids)': 12,
             'SUN (Solar)': 6, 'WND (Wind)': 3, 'BIT (Bituminous Coal)': 1}
renewable units: 9
with a PFW model: 9
```

9 renewables — 6 solar, 3 wind — and all 9 carry a PFW model. This case is ready.

**If that second number were 0**, stop and say so. Do not run TimeStep and report zero
output as a finding; report that the case has no weather models. Those are completely
different answers, and only one of them is true.

Note the two case files here. The base `Synth40.pwb` and
`Synth40_with_PFW.pwb` differ precisely in this: the `_with_PFW` variant has the
models. Check which one you were handed.

### PWW is not PFW

The single most expensive confusion in this workflow:

| | What it is | Where it lives |
|---|---|---|
| **PWW** | PowerWorld **Weather** data — measurements at stations over time | A `.pww` file you load |
| **PFW** | Power **Flow Weather** — the model converting weather to MW for one unit | A string inside each generator |

One letter apart. You load a PWW; a PFW is already in the case. If output is zero, the
question is which of the two is missing — and the answer is usually PFW.

### Step 2 — get the weather

```python
from TeamOverbyeWeather import WeatherClient

client = WeatherClient()
files = client.download("era5", "2021-02", region="TX", dest="./weather")
```

Crop at download time, not after. See [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md) for regions, ISO
footprints, bounding boxes, and the `RegionTooLargeError` recovery.

Match the weather footprint to the case. Loading Texas weather against the Synth40 case
produces a run with no matching stations — and it will not tell you.

### Step 3 — run TimeStep

```python
pw.esa.RunScriptCommand(rf'TimeStepLoadPWWRangeLatLon("{pww}", ...)')
pw.esa.RunScriptCommand('TimeStepSaveFieldsSet(GEN, [GenMW])')
pw.esa.RunScriptCommand('TimeStepDoSinglePoint')        # debug ONE point first
pw.esa.RunScriptCommand('TimeStepDoRun')
pw.esa.RunScriptCommand(rf'TimeStepSaveResultsByTypeCSV("{out}", GEN)')
```

Four things worth internalising:

1. **`TimeStepDoSinglePoint` before `TimeStepDoRun`.** One timestamp fails in seconds; a
   full run fails after a long wait, with the same error.
2. **Fields not named in `TimeStepSaveFieldsSet` are simply absent** from the output. No
   warning.
3. **Only selected units produce output.** Select the renewables explicitly.
4. **Work on a copy of the case.** The run mutates it.

Full sequence and field lists: [timestep-simulation-setup](../methods/timestep-simulation-setup.md).

### Step 4 — read the output

The exported CSV is **not** a plain table. Expect **8 metadata header rows** before the
data. Read past them or every column parses as text and your first plot is empty.

Timestamps commonly need a timezone conversion, and the natural last step is splitting
solar from wind. See [how-to-analyze-results](../methods/how-to-analyze-results.md).

### When output is zero

Walk this in order — it is almost never the weather file:

| Check | If it fails |
|---|---|
| Do the units have PFW models? | The case cannot do this. Say so |
| Are the renewables actually selected? | Only selected units produce output |
| Does the weather footprint cover the case? | Texas weather, the Synth40 case — no matching stations |
| Was `GenMW` in `TimeStepSaveFieldsSet`? | The column is absent, not zero |
| Did `TimeStepDoSinglePoint` work? | Fix that before running the whole series |

Zero output is a setup failure until proven otherwise. Reporting "these units generate
nothing" when the real answer is "this case has no weather models" is exactly the
confident wrong answer this kit exists to prevent.

### What to report back

> The `_with_PFW` case has 9 renewable units — 6 solar, 3 wind — and **all 9 carry PFW
> model strings**, so it is set up for a weather simulation. The base case is not; make
> sure you are pointing me at the `_with_PFW` variant.
>
> Note the weather footprint has to match the case. This is the Synth40 system, so Texas
> ERA5 data will produce a run with no matching stations.
>
> Pages used: `concepts/timestep-workflow.md`, `methods/timestep-simulation-setup.md`,
> `methods/teamoverbyeweather-client.md`.
