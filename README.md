# Connect My Pool — Home Assistant Integration

A custom Home Assistant integration for controlling AstralPool pool and spa systems through the [ConnectMyPool](https://www.connectmypool.com.au) cloud API.

## Supported Pool Systems

This integration works with pool and spa systems that meet the following requirements:

- **Astral Internet Gateway** installed and connected
- **Astral Touch Screen** controller
- **Astral Connect 10** or **Astral Connect Lite** device
- Pool registered and communicating with the ConnectMyPool website
- **Home Automation API access approved** by Astral Pool

## Prerequisites

1. Log in to [ConnectMyPool](https://www.connectmypool.com.au) via a desktop browser.
2. Navigate to **Settings → Home Automation**.
3. Fill in the "Reason for request" field and click **Request Home Automation Access**.
4. Wait for approval via email.
5. Once approved, return to the Home Automation page to retrieve your **Pool API Code**.

> **Security Note:** Your Pool API Code grants full control of your pool system. Treat it like a password — do not share it publicly or commit it to source control.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant.
2. Click the **⋮** menu → **Custom repositories**.
3. Add `https://github.com/christianf7/HA-Astra-Integration` with category **Integration**.
4. Search for **Connect My Pool** and install it.
5. Restart Home Assistant.

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/christianf7/HA-Astra-Integration/releases).
2. Copy the `custom_components/connect_my_pool` folder to your Home Assistant `custom_components/` directory.
3. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & services → Add Integration**.
2. Search for **Connect My Pool**.
3. Enter your **Pool API Code** when prompted.
4. The integration will validate your code, discover your pool equipment, and create entities automatically.

## Supported Entities

Entities are created dynamically based on the equipment discovered in your pool system.

| Feature | Platform | Description |
|---------|----------|-------------|
| Water Temperature | `sensor` | Current pool water temperature |
| Heaters | `climate` | On/Off/Heat/Cool control with target temperature |
| Solar Heaters (mode) | `select` | Off / Auto / On mode selection |
| Solar Heaters (temp) | `number` | Target temperature slider (10–40 °C) |
| Channels (multi-mode) | `select` | Channels with Off/Auto/On modes (e.g. filter pumps) |
| Channels (on/off) | `switch` | Simple on/off channels (e.g. spa jets, blowers) |
| Valves | `select` | Off / Auto / On mode selection |
| Lighting Zones | `light` | On/Off control with named colour programs as effects |
| Lighting Sync | `button` | Re-sync lighting colour after a power cycle |
| Pool / Spa Mode | `select` | Switch between Pool and Spa mode |
| Favourites | `select` | Activate a configured favourite |

### Lighting Colour Programs

Colour-enabled lighting zones expose available colour programs as **effects** in the Home Assistant light entity. The available programs are determined by your installed lighting hardware and reported by the ConnectMyPool API.

### Channel Cycling

The ConnectMyPool API does not provide a direct "set channel mode" action — it only supports **cycling** through modes. This integration calculates the number of cycles needed to reach the desired mode and includes safety limits to prevent runaway cycling.

## Polling & Throttling

The ConnectMyPool API enforces a **60-second throttle** on status requests. This integration polls every **61 seconds** to respect this limit.

After sending a control command, the API lifts the throttle for approximately 5 minutes, allowing faster state updates. The integration requests a coordinator refresh after each action to reflect the latest state promptly.

If you see `Time Throttle Exceeded` warnings, the integration handles them gracefully and retries on the next polling cycle.

## Troubleshooting

### Enable Debug Logging

Add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.connect_my_pool: debug
```

Restart Home Assistant and check the logs for detailed API communication info.

### Common Issues

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| "Invalid Pool API Code" during setup | Wrong API code | Double-check your code on the ConnectMyPool website |
| "API Not Enabled" | Access not yet approved | Request access via ConnectMyPool Settings → Home Automation |
| "Pool Not Connected" | Pool gateway offline | Check your pool's internet connection |
| "Cannot Connect" | Network issue | Verify Home Assistant can reach `connectmypool.com.au` |
| Entities show "Unavailable" | Temporary API outage | Entities recover automatically when the API is reachable again |
| Channel doesn't reach desired mode | Unexpected cycle order | The cycling sequence may differ for your specific hardware — please report |

### Diagnostics

This integration supports Home Assistant diagnostics. Go to **Settings → Devices & services → Connect My Pool → ⋮ → Download diagnostics** to generate a diagnostic report. All sensitive information (API codes) is automatically redacted.

## Known Limitations

- **Cloud dependency:** All communication goes through the ConnectMyPool cloud service. If their servers are down, the integration cannot function.
- **Polling only:** The API is polling-based with a 60-second minimum interval. State changes from the physical controls or mobile app may take up to 61 seconds to appear in Home Assistant.
- **Channel cycling:** The API only supports cycling through channel modes, not setting them directly. The integration calculates the required cycles, but unusual hardware configurations may behave unexpectedly.
- **No RGB lighting:** Lighting programs are named presets, not arbitrary RGB colours. They are exposed as Home Assistant light effects.
- **Temperature range:** Heater and solar temperatures are constrained to 10–40 °C by the API.

## Contributing

Issues and pull requests are welcome at [GitHub](https://github.com/christianf7/HA-Astra-Integration).

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
