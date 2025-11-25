# VVS Connections Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A custom integration for **Verkehrs- und Tarifverbund Stuttgart (VVS)**. It provides real-time connection data between two stations using the EFA API.

This integration is designed to work with the **[VVS Card](https://github.com/sigathi/ha_vvs_card)**.

## Installation

### Option 1: HACS (Recommended)
1.  Ensure [HACS](https://hacs.xyz/) is installed.
2.  Go to **HACS** > **Integrations**.
3.  Click the **3 dots** (top right) > **Custom repositories**.
4.  Add the URL of this repository: `https://github.com/sigathi/ha_vvs`
5.  Select Category: **Integration**.
6.  Click **Install**.
7.  **Restart Home Assistant**.

### Option 2: Manual Installation
1.  Download the `custom_components/vvs` folder from this repository.
2.  Copy the `vvs` folder into your Home Assistant's `config/custom_components/` directory.
3.  Restart Home Assistant.

## Configuration

This integration is configured entirely via the Home Assistant UI. You do not need to edit `configuration.yaml`.

1.  Go to **Settings** > **Devices & Services**.
2.  Click **+ ADD INTEGRATION** (bottom right).
3.  Search for **VVS**.
4.  **Step 1 (Search):** Enter the names of your Start and Destination stations (e.g., "Stuttgart", "Esslingen").
5.  **Step 2 (Select):** Choose the specific station from the dropdown list to ensure the correct ID is used.
6.  **Step 3 (Options):**
    * **Offset:** Minutes to look into the future (default: 0).
    * **Max Connections:** How many upcoming trips to fetch (default: 3).
    * **Route Type:** Optimize for Time, Interchanges, or Walking.

> [!TIP]
> **Handling Duplicate Station Names**
> If multiple stations share the same name, the search result will only show one.
> 
> **Solution:** > 1. Browse the [full station list here](./custom_components/vvs/vvspy/enums/stations.py).
> 2. Find the specific station you need.
> 3. Copy the **exact ID** (e.g., `Station_Name_1`) and paste it into the search field.

## Entities

The integration creates one sensor per route:
* **Entity ID:** `sensor.vvs_start_station_to_destination_station`
* **State:** The departure time of the *next* connection (HH:MM).
* **Attributes:** Contains a JSON list `trips` with details for the card (Departure, Arrival, Delay, Transports, Via).

## Recommended Frontend Card

To visualize this data, use the custom **VVS Card**:

[**Go to VVS Card Repository**](https://github.com/sigathi/ha_vvs_card)

## Credits
Powered by the [**vvspy**](https://github.com/zaanposni/vvspy) library.
