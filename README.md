# Digital Signboard Project

A digital signboard application that displays information cards and updates from email notifications.

## Project Structure

```
project_root/
├── app/                    # Application code
├── assets/                 # Asset files
│   ├── branding/          # Corporate/marketing assets
│   └── cards/             # Card-specific images
├── data/                  # Content storage
├── static/                # Web assets
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
├── templates/             # HTML templates
└── tests/                 # Test files
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate    # Windows
   ```

2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure email settings in config.py

4. Run the application:
   ```bash
   python -m app.signboard
   ```

## Development

- Place marketing assets in `assets/branding/`
- Place card images in `assets/cards/`
- Update site content in `data/updates.xml`