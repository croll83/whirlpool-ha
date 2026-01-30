# Whirlpool Home Assistant Integration (Extended)

Custom integration for Whirlpool appliances with extended support for W9 series ovens and microwaves.

## Features

- **Oven W9**: State, Cook mode, Temperature, Target temperature, Total cycles, Light, Door, Time remaining
- **Microwave W9**: State, Temperature, Target temperature, Power level, Total cycles, Light, Door, Time remaining
- Washer/Dryer support (from original integration)

## Requirements

This integration requires a patched version of `whirlpool-sixth-sense` library:
```bash
pip install git+https://github.com/croll83/whirlpool-sixth-sense.git --force-reinstall
```

For HAOS, run inside the container:
```bash
docker exec homeassistant pip install git+https://github.com/croll83/whirlpool-sixth-sense.git --force-reinstall
```

## Installation

1. Clone this repo into your `custom_components` folder:
```bash
cd /config/custom_components
git clone https://github.com/croll83/whirlpool-ha.git whirlpool
```

2. Restart Home Assistant

3. Add the Whirlpool integration via UI (Settings → Devices & Services → Add Integration)

## Supported Data Models

- `ddm_cooking_bio_self_clean_steam_tourmaline_v2` - Oven W9
- `ddm_cooking_bi_mwo_self_clean_steam_tourmaline_v2` - Microwave W9

## Credits

- Original integration: [home-assistant/core](https://github.com/home-assistant/core)
- Oven PR: [#142993](https://github.com/home-assistant/core/pull/142993)
- Library: [abmantis/whirlpool-sixth-sense](https://github.com/abmantis/whirlpool-sixth-sense)
