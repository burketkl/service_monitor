# Service Monitor

A real-time service monitoring application with a GUI that tracks internet service health, displays trends, and alerts on outages.

## Features

- 🎯 **Real-time Monitoring**: Continuously checks service health via HTTP/API endpoints
- 📊 **Visual Dashboard**: Red/Yellow/Green status indicators for quick overview
- 📈 **Trend Graphs**: 24-hour historical data visualization per service
- 🔔 **Multi-channel Alerts**:
  - Desktop notifications
  - System sound alerts
  - SMS alerts (via Twilio - optional)
- 💾 **Data Persistence**: Historical data saved to disk
- 🎨 **Modern GUI**: Built with CustomTkinter (dark theme)

## Screenshots

### Dashboard View
Quick status overview with color-coded indicators (Green = Operational, Yellow = Degraded, Red = Down)

### Details View
24-hour trend graphs showing response times and status changes

## Installation

### Prerequisites

- Python 3.8 or higher
- Windows, macOS, or Linux

### Setup

1. **Clone the repository**
   ```bash
   cd service_monitor
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your services**
   ```bash
   # Copy the example config
   copy config.example.yaml config.yaml
   
   # Edit config.yaml and add your services
   ```

## Configuration

Edit `config.yaml` to customize:

### Monitoring Settings
```yaml
monitoring:
  check_interval: 60  # seconds between checks
  timeout: 10  # seconds before marking service as down
  history_duration: 24  # hours of data to keep
```

### Services
Add any HTTP/HTTPS endpoint or API:

```yaml
services:
  - name: "My API"
    url: "https://api.example.com/health"
    type: "api"
    method: "GET"
    expected_status: 200
    
  - name: "My Website"
    url: "https://www.example.com"
    type: "http"
    method: "GET"
    expected_status: 200
```

### Alert Settings
```yaml
alerts:
  sound_enabled: true
  desktop_notifications: true
  
  # SMS (optional - requires Twilio account)
  sms_enabled: false
  twilio_account_sid: "YOUR_ACCOUNT_SID"
  twilio_auth_token: "YOUR_AUTH_TOKEN"
  twilio_from_number: "+1234567890"
  twilio_to_numbers:
    - "+1234567890"
```

### Thresholds
```yaml
thresholds:
  yellow_response_time: 2.0  # seconds - warning threshold
  red_consecutive_failures: 3  # failures before marking as down
```

## Usage

### Run the application

```bash
python main.py
```

### Using the GUI

1. **Dashboard Tab**: View all services at a glance
   - Green light = Service operational
   - Yellow light = Service degraded (slow response)
   - Red light = Service down
   - Click "View Details" to see trends

2. **Details Tab**: View detailed graphs
   - Select a service from dropdown
   - View 24-hour response time history
   - Color-coded background shows status periods

### SMS Alerts (Optional)

To enable SMS alerts:

1. Sign up for a [Twilio account](https://www.twilio.com/)
2. Get your Account SID and Auth Token
3. Get a Twilio phone number
4. Update `config.yaml` with your Twilio credentials
5. Set `sms_enabled: true`

## Service Examples

Here are some popular services you can monitor:

```yaml
services:
  # GitHub
  - name: "GitHub"
    url: "https://api.github.com/status"
    type: "api"
    method: "GET"
    expected_status: 200
  
  # Google
  - name: "Google"
    url: "https://www.google.com"
    type: "http"
    method: "GET"
    expected_status: 200
  
  # AWS Status
  - name: "AWS"
    url: "https://status.aws.amazon.com"
    type: "http"
    method: "GET"
    expected_status: 200
  
  # Cloudflare
  - name: "Cloudflare"
    url: "https://www.cloudflarestatus.com"
    type: "http"
    method: "GET"
    expected_status: 200
  
  # Your Custom API
  - name: "My API"
    url: "https://api.yourservice.com/health"
    type: "api"
    method: "GET"
    expected_status: 200
```

## Data Storage

- Configuration: `config.yaml`
- Historical data: `data/service_data.json`
- Data is automatically cleaned up based on `history_duration` setting

## Troubleshooting

### Import errors
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### No config file
Copy `config.example.yaml` to `config.yaml` and customize it

### Desktop notifications not working
- **Windows**: Should work out of the box
- **macOS**: May need to grant terminal permissions
- **Linux**: May need to install notification daemon

### SMS not working
- Verify Twilio credentials are correct
- Check Twilio account balance
- Ensure phone numbers include country code (e.g., +1 for US)

## Development

### Project Structure
```
service_monitor/
├── main.py                    # Application entry point
├── src/
│   ├── __init__.py
│   ├── service_monitor.py     # Core monitoring engine
│   ├── alert_manager.py       # Alert handling
│   └── gui.py                 # GUI application
├── config.yaml                # Your configuration
├── config.example.yaml        # Example configuration
├── requirements.txt           # Python dependencies
├── data/                      # Historical data (auto-created)
└── README.md
```

### Adding New Features

The codebase is modular:
- **service_monitor.py**: Add new check types or status logic
- **alert_manager.py**: Add new alert channels
- **gui.py**: Add new visualizations or UI components

## License

MIT License - feel free to use and modify

## Contributing

Pull requests welcome! Please ensure:
- Code follows existing style
- Add tests for new features
- Update documentation

## Future Enhancements

Potential features to add:
- [ ] Email alerts
- [ ] Slack/Discord webhooks
- [ ] Custom check scripts
- [ ] Multi-region checks
- [ ] Export data to CSV
- [ ] Web dashboard
- [ ] Docker container

## Support

For issues or questions, please open an issue on GitHub.
