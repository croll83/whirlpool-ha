# Whirlpool Appliances (croll83)

Custom version of the Home Assistant `whirlpool` integration.

- Based on the official integration of Home Assistant 2026.10.4.
- Bundles the `whirlpool-sixth-sense` library (`wp/`) with HTTP API support for
  built-in microwaves such as the W9 MWO (`ddm_cooking_bi_mwo_*`), proposed
  upstream in abmantis/whirlpool-sixth-sense#227.
- Adds microwave entities: state, door, light, time remaining, power,
  temperature, total cycles and a stop button.

Install by copying this folder to `config/custom_components/whirlpool` and
restarting Home Assistant. Once the library upstream ships HTTP microwaves and
Home Assistant exposes microwave entities, remove this custom component.
