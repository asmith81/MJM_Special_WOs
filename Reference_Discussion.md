# Work Order Matcher - Development Reference

## Project Overview
A tkinter-based desktop application that helps general contractors match email billing descriptions to Google Sheets work order entries using Anthropic's Claude API for intelligent fuzzy matching.

## Problem Context
- General contractor has "special" clients with separate contracts
- Work orders for special clients use alpha-numeric IDs (start with letter)
- Owner sends billing emails with job descriptions and amounts
- Need to match email line items to Google Sheets work order rows
- Goal: Compare subcontractor costs vs. client billing amounts to identify profit/loss

## Sample Data Examples

### Email Format Example 1 (Structured):
```
Our invoice for the work is as follows:
Unit 5966: The concrete sidewalk and drain area was cracked and needed repair...
Materials and Labor: $ 3,987.00
Unit 5804: Drywall was repaired, plastered and painted due to a roof leak 
Materials and Labor: $ 350.00
[continues with more units...]
Grand Total: $ 6,709.00
```

### Email Format Example 2 (Less Structured):
```
New Endeavor for Women: 
Our invoice for the work at 56Th st NE is as follows: 
Two (2) stoves were repaired, 
One needed new hooks for the oven door. 
One needed a new oven door handle. 
Materials and Labor:$ 477.00
```

### Google Sheets Row Example:
```csv
Invoice #,Approval Status,Invoice Status,Invoice Timestamp,Name,WO #,Invoice Link,Total,Job Completion Status,Picture of Completed Job,Location,Description,Picture of WO,MJM Invoiced Date,Marcelo Notes,Date WO Assigned,Perla Notes,Cristian Notes
1660,Aprobado,paid 03/06/2025,2/3/2025,Frank,P02022025,C[link],$450.00,Completed,[links],5878 Southern Ave SE. Washington DC 20019,Plumbing There is a back up in the unit 5910 2/3/2025 10:14:37
```

## File Structure
```
wo_matcher/
├── main.py                 # Entry point, launches GUI
├── gui/
│   ├── __init__.py
│   ├── main_window.py      # Main tkinter interface
│   └── components/
│       ├── __init__.py
│       ├── email_input.py  # Text area for email paste
│       ├── count_input.py  # Expected WO count field
│       └── results_display.py # Show matches/results
├── data/
│   ├── __init__.py
│   ├── sheets_client.py    # Google Sheets API integration
│   └── data_models.py      # Data structures for WO, matches
├── llm/
│   ├── __init__.py
│   ├── anthropic_client.py # Anthropic API wrapper
│   └── prompt_builder.py   # Construct prompts for matching
├── utils/
│   ├── __init__.py
│   ├── config.py          # API keys, sheet IDs, constants
│   └── validators.py      # Input validation helpers
├── requirements.txt       # Python dependencies
├── config.yaml           # Configuration file
├── .env.example          # Environment variables template
└── README.md             # Setup and usage instructions
```

## Technical Requirements

### Dependencies (requirements.txt):
```
anthropic>=0.18.0
google-api-python-client>=2.0.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=0.5.0
pandas>=1.5.0
pyyaml>=6.0
python-dotenv>=0.19.0
```

### Environment Variables (.env):
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/credentials.json
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_SHEET_RANGE=Sheet1!A:R
```

## Core Functionality

### User Workflow:
1. User opens tkinter application
2. Pastes email text into large text area
3. Enters expected number of work orders to find (integer input)
4. Clicks "Find Matches" button
5. App filters Google Sheets to alpha-numeric work orders only
6. App sends email text + candidate rows to Anthropic Claude API
7. Results display shows matches with confidence scores and evidence
8. User can export or save results

### Key Matching Criteria:
- **Unit numbers** (strongest signal when present)
- **Dollar amounts** (exact or close matches)
- **Job type keywords** (plumbing, drywall, HVAC, etc.)
- **Location/property context**
- **Date proximity**

### Expected API Output Format:
```
Match 1:
- Email Item: "Unit 5910: Kitchen drain line clogged... $450"
- WO#: A1234
- Confidence: 95%
- Evidence: "Exact unit number match (5910), job type match (plumbing/drain), exact amount match ($450)"

Match 2:
- Email Item: "Two stoves repaired... $477"
- WO#: C9876
- Confidence: 60%
- Evidence: "Property address partial match, appliance repair keywords, no unit specificity reduces confidence"
```

## Data Processing Notes

### Google Sheets Filtering:
- Total rows: ~2000
- Filter to work orders where WO# starts with a letter
- This creates a much smaller, manageable dataset for matching

### Confidence Score Guidelines:
- 90%+: Multiple strong signals align (unit #, amount, job type)
- 70-89%: Good match with some uncertainty
- 50-69%: Possible match, needs review
- <50%: Low confidence, likely needs manual intervention

## Implementation Priorities

### Phase 1 (MVP):
1. Basic tkinter GUI with input fields
2. Google Sheets API integration with filtering
3. Anthropic API integration with basic prompt
4. Simple results display

### Phase 2 (Enhancements):
1. Improved prompt engineering for better matching
2. Export functionality (CSV, Excel)
3. Configuration management
4. Error handling and validation

### Phase 3 (Polish):
1. Better UI/UX design
2. Logging and debugging features
3. Batch processing capabilities
4. Settings/preferences management

## Key Technical Considerations

### Google Sheets API:
- Need service account credentials or OAuth2 setup
- Filter rows where column F (WO #) starts with a letter
- Handle API rate limits gracefully

### Anthropic API:
- Use Claude Sonnet for cost-effectiveness
- Structure prompts to return JSON or structured text
- Handle API errors and timeouts

### GUI Design:
- Large text area for email input (scrollable)
- Clear labels and intuitive layout
- Progress indicators for API calls
- Resizable window with good defaults

### Error Handling:
- API connection failures
- Invalid input validation
- Malformed email text
- Missing configuration

## Security & Configuration

### API Key Management:
- Store in .env file (never commit)
- Validate keys on startup
- Clear error messages for missing/invalid keys

### Google Sheets Access:
- Read-only access sufficient
- Service account preferred over OAuth for automation
- Handle authentication errors gracefully

## Testing Strategy

### Test Cases:
- Various email formats (structured vs. unstructured)
- Different numbers of work orders in emails
- Edge cases (no matches, multiple possible matches)
- API failure scenarios
- Invalid user inputs

### Sample Data:
- Create test emails with known work orders
- Test Google Sheets with sample alpha-numeric work orders
- Verify matching accuracy with known good matches
