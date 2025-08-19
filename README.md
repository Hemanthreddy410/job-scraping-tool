# Job Scraping and Export Tool

A comprehensive Python tool for scraping AI Engineer, Data Engineer, and Data Scientist job postings from major job boards (Greenhouse and Lever), exporting results to Excel, and automatically sharing via OneDrive.

## 🎯 Features

- **Multi-Platform Scraping**: Scrapes jobs from Greenhouse and Lever APIs
- **Intelligent Filtering**: Filters for AI/ML, Data Engineering, and Data Science roles in the USA
- **Excel Export**: Creates formatted Excel files with job data and summary statistics
- **OneDrive Integration**: Automatically uploads results to OneDrive and shares with team members
- **Duplicate Detection**: Removes duplicate job postings across platforms
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Rate Limiting**: Respectful API usage with built-in delays

## 📋 Target Job Roles

The tool specifically searches for these roles:
- AI Engineer / Artificial Intelligence Engineer
- Machine Learning Engineer / ML Engineer
- Data Engineer (all levels: Senior, Principal, Staff, Lead)
- Data Scientist (all levels: Senior, Principal, Staff, Lead, Applied)

## 🏢 Supported Companies

### Greenhouse Companies
- Airbnb, Stripe, Figma, Databricks, Coinbase, Instacart, Robinhood
- And more (configurable in `config.py`)

### Lever Companies  
- Netflix, Atlassian, Spotify
- And more (configurable in `config.py`)

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Setup

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip install requests pandas openpyxl python-dotenv
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.template .env
   ```
   
   Edit `.env` with your credentials:
   ```env
   # Microsoft Graph API credentials for OneDrive integration
   MICROSOFT_CLIENT_ID=your_client_id_here
   MICROSOFT_CLIENT_SECRET=your_client_secret_here
   MICROSOFT_TENANT_ID=your_tenant_id_here
   
   # Optional: Gmail credentials (if using email features)
   GMAIL_EMAIL=your_email@example.com
   GMAIL_APP_PASSWORD=your_app_password
   ```

## 🚀 Usage

### Basic Usage
```bash
python job_scraper.py
```

### What the tool does:
1. Scrapes job postings from configured companies on Greenhouse and Lever
2. Filters for target roles in USA locations
3. Removes duplicates
4. Creates an Excel file with results
5. Uploads to OneDrive (if configured)
6. Shares with specified team members

### Output Files
- **Excel File**: `job_scraping_results_YYYYMMDD_HHMMSS.xlsx`
  - Main sheet with all job data
  - Summary sheet with statistics
- **Log File**: `job_scraper.log` with detailed execution logs

## ⚙️ Configuration

### Modifying Target Companies
Edit `config.py` to add/remove companies:

```python
GREENHOUSE_COMPANIES = [
    'airbnb', 'stripe', 'your-company-name'
]

LEVER_COMPANIES = [
    'netflix', 'spotify', 'your-company-name'
]
```

### Modifying Job Roles
Edit the `TARGET_ROLES` list in `config.py`:

```python
TARGET_ROLES = [
    'AI Engineer',
    'Your Custom Role'
]
```

### Modifying Locations
Edit the `USA_LOCATIONS` list in `config.py` to change location filtering.

### OneDrive Sharing
Modify the `SHARE_USERS` list in `config.py`:

```python
SHARE_USERS = [
    'user1@company.com',
    'user2@company.com'
]
```

## 🔧 Microsoft Graph API Setup

To enable OneDrive integration, you need to set up a Microsoft App:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "App registrations"
3. Create a new registration
4. Note down:
   - Application (client) ID
   - Directory (tenant) ID
5. Go to "Certificates & secrets"
6. Create a new client secret
7. Add these values to your `.env` file

### Required API Permissions
- `Files.ReadWrite.All`
- `Sites.ReadWrite.All`

## 📊 Excel Output Structure

The generated Excel file contains:

### Main Sheet: "Job Scraping Results"
| Column | Description |
|--------|-------------|
| Company | Company name |
| Job Title | Full job title |
| Location | Job location |
| Job URL | Direct link to job posting |
| Posted Date | When the job was posted |
| Source | Greenhouse or Lever |
| Job ID | Unique identifier |
| Job Description | Full job description |

### Summary Sheet
- Total jobs found
- Breakdown by source (Greenhouse vs Lever)
- Breakdown by role type
- Scraping timestamp

## 📝 Logging

The tool creates detailed logs in `job_scraper.log`:
- API requests and responses
- Jobs found per company
- Errors and warnings
- Upload status

### Log Levels
- `INFO`: Normal operation updates
- `WARNING`: Non-critical issues (e.g., company not found)
- `ERROR`: Critical errors that need attention

## 🚨 Troubleshooting

### Common Issues

#### "Company not found" warnings
- Some companies may have changed their API endpoints
- Check if the company name is correct in the configuration
- Some companies might have switched platforms

#### OneDrive upload failures
- Verify your Microsoft Graph API credentials
- Check that your app has the required permissions
- Ensure your access token hasn't expired

#### Rate limiting errors
- The tool includes built-in delays
- If you encounter rate limits, increase `REQUEST_DELAY` in `config.py`

#### No jobs found
- Check if the target roles are spelled correctly
- Verify location filtering isn't too restrictive
- Some companies may not have current openings

### Debug Mode
For more detailed debugging, modify the logging level in `job_scraper.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Notes

- Keep your `.env` file secure and never commit it to version control
- The `.gitignore` file is configured to exclude sensitive files
- Rotate your API credentials regularly
- Use app-specific passwords for Gmail integration

## 📈 Extending the Tool

### Adding New Job Boards
1. Create a new scraping method in the `JobScraper` class
2. Follow the pattern of existing methods
3. Add the results to `self.jobs_data`

### Adding New Data Fields
1. Modify the job dictionary structure in scraping methods
2. Update the Excel creation logic in `create_excel_file()`
3. Adjust column headers accordingly

### Custom Filtering
Modify the `is_target_role()` and `is_usa_location()` methods to implement custom filtering logic.