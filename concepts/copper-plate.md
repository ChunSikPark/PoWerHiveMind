---
type: concept
domain: cross-cutting
topic: power-flow
aliases: [copper-plate, copperplate, copper-plate-model, network-collapse, unconstrained-dispatch]
tags: [copper-plate, dispatch, transmission, network, slack-bus, power-flow, technique, cross-cutting]
---

# Copper-Plate Model

## Abstract
Collapse the entire transmission network — strip all branches, loads, and shunts, then add a single slack bus — so generators dispatch to serve total system load **without any transmission constraints**. Every generator sees infinite capacity between itself and every other bus; hence "copper plate" (ideal conductor). Used in a weather-driven copper-plate study to let weather-driven renewable output dispatch freely, isolating the weather → MW signal from network topology artifacts. The build sequence (delete Branch/Load/Shunt → add slack bus 999999 → large slack gen) is documented under Build steps below.

## Connections
- **Up:** [Home](../index.md)
- **Used in:** a weather-driven copper-plate study (renewable dispatch without network limits — exact build steps under Build steps below)
- **💡 Could apply to (idea transfer):** renewable resource/potential assessment · max-generation studies · isolating a weather → MW signal from any network study
- **Across:** [timestep-simulation](timestep-simulation.md) (copper-plate runs are typically time-step simulations over a weather period)

## Content

### What it does and why

A full power-flow model enforces transmission constraints: a wind farm may be curtailed because a nearby line is at thermal limit, even if the wind is blowing. For studies that ask "how much energy could these generators produce given this weather?" — not "how much does the network allow?" — those constraints are noise. Copper-plate removes them.

With all branches deleted:
- No line flow limits to violate.
- No voltage constraints (no shunts, no reactive power coupling).
- Total generation = total load, balanced by the slack bus.
- Each generator dispatches to its weather-driven maximum (wind speed → MW, solar irradiance → MW).

The slack bus absorbs any imbalance (positive or negative), so the power balance always closes regardless of the renewable dispatch profile.

### Build steps (from a weather-driven copper-plate study)

Starting from a full PowerWorld case:
1. **Delete Branch objects** — removes all transmission lines and transformers, eliminating all flow constraints.
2. **Delete Load objects** — removes all bus loads (load is represented as a net system-wide value, served by the slack).
3. **Delete Shunt objects** — removes all capacitors/reactors (no reactive power devices needed in a copper-plate model).
4. **Add slack bus 999999** — a synthetic bus that acts as the infinite balancing node.
5. **Add large slack generator at bus 999999** — set to AGC/slack mode with very large MW limits (e.g., ±99999 MW) so it can absorb any imbalance.

The result is a star topology: every original generator bus connects to the slack, and the slack sets system frequency/voltage reference.

### Use in a weather-driven copper-plate study

The PowerFlow Weather (PFW) copper-plate model drives weather-dependent renewable generators (wind, solar) through a time-step simulation over a historical weather period. Because the network is gone, the MW output of each generator in each time step is determined purely by the weather at its location — wind speed for wind, GHI/DNI for solar. This isolates the **weather → MW** relationship and produces a clean time series of potential (unconstrained) renewable generation.

Downstream studies can then take this unconstrained generation signal and apply network constraints separately — a decomposition that keeps the weather modeling and the network modeling cleanly separated.

### 💡 Idea-transfer targets

- **Renewable resource/potential assessment:** "How much energy could all the wind and solar in a region produce over a 20-year climate?" Copper-plate gives you the unconstrained answer; the gap between copper-plate and network-constrained output quantifies curtailment potential.
- **Max-generation studies:** "What is the theoretical maximum MW this fleet could produce on any hour?" Strip the network, dispatch everything to maximum, read the total.
- **Weather → MW signal isolation for dynamic line rating:** DLR studies need to know how wind-driven generation affects line loading. A copper-plate pre-pass isolates the weather → generation relationship before layering in network effects.
- **Benchmarking network congestion:** the difference between copper-plate dispatch and constrained dispatch quantifies how much transmission is limiting renewable utilization — a useful metric for transmission planning.

### What copper-plate does NOT give you

- **Voltage profiles** — no branches means no voltage drops, no reactive coupling.
- **Line loading** — by construction there are no lines.
- **Congestion signals** — the whole point is to remove them.
- **Locational marginal prices** — no network, no transmission component to the LMP.

If you need any of these, you need the full network model. Copper-plate is specifically for studies where the question is about energy potential, not delivery constraints.

### Relationship to timestep simulation

Copper-plate models are almost always run as time-step simulations: the weather input changes each time step, the renewable dispatch updates, and the slack absorbs the balance. The [timestep-simulation](timestep-simulation.md) framework is the computational engine; the copper-plate topology is the network configuration. They compose naturally.
