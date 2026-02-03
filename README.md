# gNMI Collector

A Python-based gNMI (gRPC Network Management Interface) telemetry collector for network devices. This collector supports async subscriptions to streaming telemetry data from multiple platforms including Arista cEOS and SONiC.

## Features

- **Async Subscriptions**: Efficient asynchronous collection from multiple devices simultaneously
- **Multi-Platform Support**: Pre-configured paths for cEOS and SONiC platforms
- **Configurable Telemetry**: Collect interface statistics, LLDP neighbor data, and ARP/neighbor information
- **YAML Configuration**: Easy-to-manage device and path configurations
- **Insecure Mode**: Simplified setup for lab environments without certificate management

## Project Structure

```
gnmi-collector/
├── collector.py              # Main collector implementation
├── configs/                  # Configuration directory
│   ├── devices.yaml         # Device configuration
│   ├── paths_ceos.yaml      # Arista cEOS telemetry paths
│   └── paths_sonic.yaml     # SONiC telemetry paths
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.7 or higher
- Network devices with gNMI enabled (cEOS, SONiC, or other compatible devices)
- Network connectivity to target devices

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install pygnmi PyYAML
```

## Configuration

### 1. Configure Devices

Edit `configs/devices.yaml` to add your network devices:

```yaml
devices:
  - name: my-ceos-switch
    host: 192.168.1.10
    port: 6030
    username: admin
    password: admin
    platform: ceos
    insecure: true
    skip_verify: true

  - name: my-sonic-switch
    host: 192.168.1.20
    port: 8080
    username: admin
    password: password
    platform: sonic
    insecure: true
    skip_verify: true

subscription:
  mode: STREAM
  encoding: JSON_IETF
  sample_interval: 10  # seconds
```

### 2. Configure Telemetry Paths

The collector includes pre-configured paths for:

- **Interface metrics**: Counters, operational status, admin status, MTU
- **LLDP data**: Neighbor information, LLDP interface states
- **ARP/Neighbor data**: IPv4 and IPv6 neighbor tables

Paths are platform-specific and located in:
- `configs/paths_ceos.yaml` - For Arista cEOS devices
- `configs/paths_sonic.yaml` - For SONiC devices

You can customize these files to add or remove specific telemetry paths based on your needs.

## Usage

### Run the Collector

```bash
python collector.py
```

Or make it executable and run directly:

```bash
chmod +x collector.py
./collector.py
```

### Stop the Collector

Press `Ctrl+C` to gracefully stop the collector.

## Lab Setup Notes

This collector is configured for **insecure gNMI** connections, which is ideal for lab environments:

- **No certificate validation**: `skip_verify: true`
- **Insecure transport**: `insecure: true`
- **Simple authentication**: Username/password only

⚠️ **Warning**: Do not use insecure mode in production environments. For production, configure proper TLS certificates and secure authentication.

## Output

The collector logs telemetry data to the console with timestamps. Example output:

```
2024-01-01 12:00:00 - __main__ - INFO - Starting gNMI Collector
2024-01-01 12:00:00 - __main__ - INFO - Loaded 2 device(s) from configuration
2024-01-01 12:00:00 - __main__ - INFO - Starting subscription for device: my-ceos-switch
2024-01-01 12:00:01 - __main__ - INFO - [my-ceos-switch] Telemetry Update
2024-01-01 12:00:01 - __main__ - INFO - [my-ceos-switch] Path: /interfaces/interface/state/counters
2024-01-01 12:00:01 - __main__ - INFO - [my-ceos-switch] Data: {...}
```

## Extending the Collector

### Add Custom Data Processing

Modify the `handle_telemetry_update()` method in `collector.py` to:

- Store data in a time-series database (InfluxDB, Prometheus, etc.)
- Process and analyze telemetry data
- Generate alerts based on thresholds
- Export data to other systems

### Add New Platforms

1. Create a new path configuration file: `configs/paths_<platform>.yaml`
2. Define the telemetry paths for interface, LLDP, and ARP data
3. Add devices with the new platform name in `devices.yaml`

### Example: Custom Processing

```python
async def handle_telemetry_update(self, device_name: str, entry: Dict[str, Any]):
    # Store to database
    await self.store_to_influxdb(device_name, entry)
    
    # Check thresholds
    if self.check_threshold_violation(entry):
        await self.send_alert(device_name, entry)
```

## Troubleshooting

### Connection Issues

- Verify device IP and port are correct
- Check network connectivity: `ping <device-ip>`
- Verify gNMI is enabled on the device
- Check firewall rules allow gRPC/gNMI traffic

### Authentication Errors

- Verify username and password are correct
- Check device user has appropriate permissions for gNMI

### No Telemetry Data

- Verify paths in `paths_<platform>.yaml` are supported by your device
- Check device gNMI capabilities: some paths may not be available
- Review device logs for gNMI subscription errors

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions, please open an issue on the GitHub repository.