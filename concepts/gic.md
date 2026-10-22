---
type: concept
domain: tooling
topic: power-flow
aliases: [gic, geomagnetically-induced-current, gmd, geomagnetic-disturbance]
tags: [gic, gmd, powerworld, esapp, transformer, solar-storm]
---

# Concept: GIC — geomagnetically induced current

## Abstract

Geomagnetically induced currents are quasi-DC currents driven into the grid during a
geomagnetic disturbance, flowing through long transmission lines and transformer
neutrals. They cause half-cycle transformer saturation, harmonics, reactive-power
absorption, and in severe cases thermal damage. PowerWorld models GIC natively, and
`esapp` exposes it through `esapp.utils.GIC`. Verified against esapp 0.1.3.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](esapp.md) · [powerworld-simauto](powerworld-simauto.md) · [glossary](glossary.md)
- **Deeper:** [aux-script-commands](../references/aux-script-commands.md) for the underlying `GIC*` SCRIPT actions

## Content

### The physics, briefly

A changing geomagnetic field induces a geoelectric field at the earth's surface. That
field drives quasi-DC current through any long conductor grounded at both ends, which
describes a transmission line with grounded-wye transformers at each end.

The current is quasi-DC relative to 60 Hz, so it biases the transformer core into
half-cycle saturation. Consequences, in the order they usually matter:

- **Reactive power absorption** rises sharply, depressing voltage
- **Harmonics** appear and can trip protective relays
- **Transformer heating**, which is the damage mechanism in a severe storm

### The API, and the mistake to avoid

**There is no `pw.gic`.** GIC lives in `esapp.utils` as a class you construct with the
`PowerWorld` object:

```python
from esapp import PowerWorld
from esapp.utils import GIC

pw = PowerWorld(r"C:\path\to\case.pwb")
g = GIC(pw)
```

Then:

```python
g.configure(pf_include=True, ts_include=False, calc_mode="SnapShot")
g.storm(maxfield=100.0, direction=90.0, solvepf=True)   # V/km, degrees
g.model()                                               # build the GIC model
G = g.gmatrix(sparse=True)                              # conductance matrix
```

Verified signatures:

| Call | Signature |
|---|---|
| `GIC(pw)` | `__init__(self, pw=None)` |
| `configure` | `(pf_include: bool = True, ts_include: bool = False, calc_mode: str = 'SnapShot') -> None` |
| `storm` | `(maxfield: float, direction: float, solvepf: bool = True) -> None` |
| `model` | `() -> GIC` |
| `gmatrix` | `(sparse: bool = True) -> csr_matrix | ndarray` |

### Other settings on the object

The `GIC` object exposes the modelling knobs as attributes rather than arguments:

| Attribute | Controls |
|---|---|
| `efield_mag`, `efield_angle` | The geoelectric field magnitude and direction |
| `min_kv` | Voltage floor below which branches are excluded |
| `skip_low_r_lines`, `skip_equiv_lines` | Exclude low-resistance or equivalenced branches |
| `segment_length_km` | Line segmentation length for the field integral |
| `hotspot_include` | Include transformer hot-spot heating |
| `pf_include`, `ts_include` | Couple GIC into the power flow and/or transient stability |
| `calc_mode` | `SnapShot` and related calculation modes |
| `zeta`, `eff`, `Px` | Model coefficients |
| `bus_no_sub` | Buses without an assigned substation |
| `update_line_volts` | Whether induced line voltages are refreshed |
| `timevary_csv`, `loadb3d` | Time-varying field input and B3D field data |
| `calc_max_direction` | Solve for the worst-case field direction |
| `A`, `G`, `H` | The assembled model matrices |
| `cleargic` | Clear GIC results |

### Substation grounding is the input that matters most

GIC results are dominated by substation grounding resistance and transformer winding
configuration. A case that has never been prepared for GIC study will have placeholder
grounding data, and it will still produce plausible-looking, meaningless numbers.

Before trusting any GIC result, confirm the case actually carries substation grounding
resistances and correct transformer configurations. Nothing errors; the answer is just
not about your system.

### Direction matters, and the worst case is not obvious

GIC magnitude depends on the angle between the geoelectric field and each line. The
worst direction for one transformer is rarely the worst for another, so a single
assumed direction under-reports system risk. Use `calc_max_direction` rather than
guessing, or sweep the direction and keep the envelope.

### Script-level access

Everything above maps to PowerWorld `GIC*` SCRIPT actions: `GICCalculate`,
`GICTimeVaryingCalculate`, `GICSaveGMatrix`, and the PTI/PSLF exchange actions. See
[aux-script-commands](../references/aux-script-commands.md). Reach for those only when the `esapp.utils.GIC` surface does
not cover what you need.

### Scope

This page covers **driving PowerWorld's GIC feature**. It does not teach geomagnetic
hazard assessment, earth-conductivity modelling, or how to choose a storm scenario. For
those, go to the GMD literature and the relevant NERC standards.
