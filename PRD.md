# Product Requirements Document: Work Order Matcher

## 1. Executive Summary

### 1.1 Product Overview
The Work Order Matcher is a desktop application that helps general contractors automatically match email billing descriptions to Google Sheets work order entries using AI-powered analysis, and now includes complete invoice automation through QuickBooks Online integration. The tool addresses profit margin visibility issues by connecting subcontractor invoices with client billing amounts and automates the entire invoice creation and documentation workflow.

### 1.2 Business Problem
- General contractor works with "special" clients under separate contracts
- Owner sends billing emails with job descriptions and amounts to charge clients
- Middle management lacks visibility into profit margins on these jobs
- Manual matching of email descriptions to work order data is time-intensive and error-prone
- Manual QuickBooks invoice creation and PDF processing creates additional administrative overhead
- Significant money being lost due to owner billing clients at discounts without cost visibility

### 1.3 Success Metrics
- Reduce manual matching time from hours to minutes
- Achieve 80%+ accuracy in automatic work order matching
- Provide clear profit/loss visibility for special client jobs
- Enable proactive cost analysis before client billing decisions
- Automate invoice creation and PDF documentation workflow
- Eliminate manual QuickBooks data entry for matched work orders

## 2. Product Goals

### 2.1 Primary Goals
- Automate matching of email billing items to Google Sheets work order rows
- Provide confidence scores and evidence for each match
- Display profit/loss analysis comparing subcontractor costs vs client billing
- Enable quick identification of unprofitable jobs

### 2.2 Secondary Goals
- Reduce administrative overhead for middle management
- Improve decision-making data for owner billing decisions
- Create audit trail for billing reconciliation
- Support export of analysis results

## 3. User Stories

### 3.1 Primary User: Middle Management
**As a** middle manager at the contracting firm  
**I want to** quickly match owner billing emails to our work order data  
**So that** I can identify which jobs are losing money and provide cost visibility

**As a** middle manager  
**I want to** see confidence scores for each match  
**So that** I can review uncertain matches manually before making business decisions

**As a** middle manager  
**I want to** export matched data  
**So that** I can share profit/loss analysis with leadership

### 3.2 Secondary User: Owner
**As the** business owner  
**I want to** access cost data before billing clients  
**So that** I can make informed pricing decisions and protect profit margins

## 4. Functional Requirements

### 4.1 Core Features

#### 4.1.1 Email Processing
- Accept email text input via copy/paste interface
- Parse multiple work order line items from unstructured email text
- Extract job descriptions, amounts, and location/unit identifiers
- Handle various email formats (structured and unstructured)

#### 4.1.2 Google Sheets Integration
- Connect to existing Google Sheets work order tracking system
- Filter to alpha-numeric work order numbers (special clients only)
- Retrieve work order details: WO#, description, amount, location, date
- Handle authentication and API rate limiting

#### 4.1.3 AI-Powered Matching
- Send email data and candidate work orders to Anthropic Claude API
- Receive structured matching results with confidence scores
- Support fuzzy matching on descriptions, amounts, locations, unit numbers
- Handle partial matches and multiple potential candidates

#### 4.1.4 Results Display
- Show matched work order numbers with confidence percentages
- Display matching evidence/reasoning for each result
- Highlight unmatched email items requiring manual review
- Calculate and display profit/loss for each matched pair

#### 4.1.5 User Input Controls
- Large text area for email content input
- Numeric input for expected work order count
- "Find Matches" action button
- Clear/reset functionality

### 4.2 Data Requirements

#### 4.2.1 Input Data
- Raw email text containing billing line items
- Expected number of work orders (user-provided count)
- Google Sheets work order data (filtered to alpha-numeric WO#s)

#### 4.2.2 Output Data
- Work order number matches
- Confidence scores (0-100%)
- Matching evidence descriptions
- Profit/loss calculations
- Unmatched items flagged for review

### 4.3 Business Logic

#### 4.3.1 Matching Criteria Priority
1. **High Priority**: Unit numbers, exact amount matches
2. **Medium Priority**: Job type keywords, location context
3. **Low Priority**: Date proximity, contractor names

#### 4.3.2 Confidence Score Ranges
- **90-100%**: Multiple strong signals align (unit #, amount, job type)
- **70-89%**: Good match with minor uncertainty
- **50-69%**: Possible match requiring manual review
- **0-49%**: Low confidence, likely incorrect match

## 5. Technical Requirements

### 5.1 Platform
- Desktop application using Python and tkinter
- Windows compatibility required
- Local processing (no cloud data storage)

### 5.2 External Dependencies
- Google Sheets API for work order data access
- Anthropic Claude API for intelligent matching
- Internet connection required for API access

### 5.3 Performance Requirements
- Process emails with up to 20 line items
- Complete matching analysis within 30 seconds
- Handle Google Sheets with 2000+ rows (filtered to ~100-200 relevant rows)
- Maintain responsive UI during processing

### 5.4 Security Requirements
- OAuth2 authentication for Google Sheets API (preferred over service account)
- Automatic token refresh handling for long-term use
- Secure storage of Anthropic API key in environment variables
- No logging of sensitive customer data
- Local-only data processing
- Read-only access to Google Sheets
- Startup credential validation with clear error messaging

## 6. User Interface Requirements

### 6.1 Main Window Layout
- Application title and branding
- Large, scrollable text area for email input
- Numeric input field for expected work order count
- "Find Matches" primary action button
- Results display area with scrollable table/list

### 6.2 Results Display
- Tabular format showing: Email Item | WO# | Confidence | Evidence
- Color coding for confidence levels (green/yellow/red)
- Expandable details for matching evidence
- Export button for results

### 6.3 User Experience
- Clear, intuitive interface requiring minimal training
- Progress indicators during API processing
- Informative error messages
- Responsive design that works on standard business monitors

## 7. Integration Requirements

### 7.1 Google Sheets API
- **OAuth2 authentication** (recommended based on reference implementation)
  - One-time user authentication with Google account
  - Automatic token storage and refresh in local `token.json`
  - Familiar Google login flow for better user experience
  - No IT involvement required for credential setup
- Read access to specified spreadsheet and range
- Filter capability for alpha-numeric work order numbers
- Error handling for API limits and connectivity issues
- Graceful handling of expired tokens and network issues

### 7.2 Anthropic Claude API
- Claude Sonnet 4 model for cost-effectiveness
- Simple API key storage in environment variables
- Structured prompt engineering for consistent output format
- JSON or structured text response parsing
- Rate limiting and error handling

### 7.3 Credential Management Strategy
- **Hybrid approach**: OAuth2 for Google Sheets + API key for Anthropic
- **Auto-refresh tokens**: Minimize user re-authentication
- **Startup validation**: Check all credentials before launching main interface
- **Clear error dialogs**: Guide users through setup process with specific instructions

## 8. Credential Management Implementation

### 8.1 Reference Project Analysis
Based on analysis of the firm's existing successful application, the following patterns have been validated:

#### 8.1.1 OAuth2 Token Management (Proven Pattern)
```python
# Auto-generated token.json structure:
{
  "token": "ya29.a0AS3H6NzJ...",           # Short-lived access token
  "refresh_token": "1//05i0z-Ik2FHE...",    # Long-lived refresh token  
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "1042497359356-...",          # OAuth client ID
  "client_secret": "GOCSPX-cTM45CTD...",     # OAuth client secret
  "expiry": "2025-07-22T01:49:17.797280Z"   # Auto-refresh when expired
}
```

#### 8.1.2 Startup Validation Flow (Copy This Pattern)
```python
def check_credentials():
    """Pre-flight validation before launching main GUI"""
    # 1. Check if Anthropic API key exists in environment
    # 2. Validate OAuth client credentials are configured
    # 3. Test Google Sheets access with sample call
    # 4. Show specific error dialogs with setup instructions
    # 5. Only launch main app if all validations pass
```

#### 8.1.3 Authentication Benefits Observed
- **✅ Zero IT involvement**: Users authenticate with personal Google accounts
- **✅ One-time setup**: Authentication persists across app restarts
- **✅ Auto-recovery**: Expired tokens refresh automatically 
- **✅ Familiar UX**: Standard Google login flow (no custom auth screens)
- **✅ Cross-platform**: Works identically on Windows/Mac/Linux
- **✅ Secure**: User-level permissions, no shared service accounts

### 8.2 Implementation Requirements
- Copy OAuth2 client configuration pattern from reference project
- Implement identical startup validation flow
- Use same token storage location and format
- Apply same error handling and user messaging patterns
- Maintain same hybrid approach: OAuth2 + environment variables

## 9. Data Examples

### 9.1 Sample Email Format (Structured)
```
Our invoice for the work is as follows:
Unit 5966: The concrete sidewalk and drain area was cracked and needed repair...
Materials and Labor: $ 3,987.00
Unit 5804: Drywall was repaired, plastered and painted due to a roof leak 
Materials and Labor: $ 350.00
Grand Total: $ 6,709.00
```

### 9.2 Sample Email Format (Unstructured)
```
New Endeavor for Women: 
Our invoice for the work at 56Th st NE is as follows: 
Two (2) stoves were repaired, 
One needed new hooks for the oven door. 
Materials and Labor:$ 477.00
```

### 9.3 Google Sheets Data Structure
**Headers**: Invoice #, Approval Status, Invoice Status, Invoice Timestamp, Name, WO #, Invoice Link, Total, Job Completion Status, Picture of Completed Job, Location, Description, Picture of WO, MJM Invoiced Date, Marcelo Notes, Date WO Assigned, Perla Notes, Cristian Notes

## 10. Implementation Phases

### 10.1 Phase 1: MVP (2-3 weeks)
- **Authentication foundation** (based on reference project patterns)
  - OAuth2 flow for Google Sheets with auto-refresh tokens
  - Startup credential validation with helpful error dialogs
  - Environment-based Anthropic API key management
- Basic tkinter GUI with input fields
- Google Sheets API integration and alpha-numeric filtering
- Anthropic API integration with basic matching
- Simple results display with confidence scores

### 10.2 Phase 2: Enhancement (1-2 weeks)
- Improved prompt engineering for better accuracy
- Export functionality (CSV format)
- **Enhanced error handling** (learned from reference implementation)
  - Network connectivity issues
  - API rate limiting
  - Invalid sheet permissions
  - Token refresh failures
- UI polish and user experience improvements

### 10.3 Phase 3: Advanced Features (1 week)
- Profit/loss calculations and display
- Batch processing capabilities
- Configuration management interface
- Logging and audit trail features

### 10.4 File Structure (Based on Reference Project Success)
```
wo_matcher/
├── main.py                     # Entry point with startup validation
├── .env.example                # Template for API keys
├── auth/
│   ├── google_auth.py         # OAuth2 flow (based on reference pattern)
│   └── token.json             # Auto-generated OAuth tokens (gitignored)
├── config/
│   ├── credentials.py         # OAuth client config + constants
│   └── sheets_config.py       # Sheet IDs, ranges, filters
├── gui/
│   ├── main_window.py         # Main tkinter interface
│   ├── startup_validation.py  # Pre-flight credential checks
│   └── components/            # UI components
├── data/
│   ├── sheets_client.py       # Google Sheets integration
│   └── data_models.py         # Data structures
├── llm/
│   ├── anthropic_client.py    # Anthropic API wrapper
│   └── prompt_builder.py      # Prompt construction
└── utils/
    ├── config.py              # Configuration management
    └── validators.py          # Input validation
```

## 11. Acceptance Criteria

### 11.1 Core Functionality
- [ ] User can paste email text and specify expected work order count
- [ ] Application successfully connects to Google Sheets and filters alpha-numeric WOs
- [ ] AI matching returns results with confidence scores ≥50% accuracy
- [ ] Results display clearly shows matches and evidence
- [ ] Application handles common error scenarios gracefully

### 11.2 Performance
- [ ] Processing completes within 30 seconds for typical emails
- [ ] UI remains responsive during API calls
- [ ] Application handles 20+ line item emails without failure

### 11.3 Usability
- [ ] Non-technical users can operate without training
- [ ] Error messages are clear and actionable
- [ ] Results are easy to interpret and act upon

## 12. Risks and Mitigations

### 12.1 Technical Risks
- **API Rate Limits**: Implement proper rate limiting and error handling
- **Token Expiration**: Use OAuth2 auto-refresh pattern (proven in reference project)
- **Matching Accuracy**: Develop comprehensive prompt engineering and testing
- **Data Quality**: Handle inconsistent email formats and sheet data
- **Authentication Setup**: Implement startup validation with clear error dialogs (reference project success pattern)

### 12.2 Business Risks
- **User Adoption**: Design intuitive interface and provide clear value demonstration
- **Cost Management**: Monitor API usage and optimize calls
- **Data Security**: Use proven OAuth2 pattern + local processing (no cloud storage)

### 12.3 Lessons Learned from Reference Implementation
- **✅ OAuth2 Success Factors**: Auto-refresh tokens, clear setup flow, familiar Google login
- **✅ Error Handling**: Comprehensive startup validation prevents runtime issues
- **✅ User Experience**: Self-service authentication (no IT involvement required)
- **⚠️ Avoid**: Service account complexity, manual token management, unclear error messages

## 13. Success Criteria

### 13.1 Quantitative Metrics
- 80%+ matching accuracy for structured emails
- 60%+ matching accuracy for unstructured emails
- <30 second processing time for typical emails
- 90%+ user satisfaction in initial testing

### 13.2 Qualitative Metrics
- Users report significant time savings vs manual matching
- Middle management gains actionable insights into job profitability
- Owner receives cost data to support pricing decisions
- Improved visibility leads to better profit margin management

## 14. QuickBooks Integration & Invoice Automation

### 14.1 Overview
Extended functionality that takes the work order matching results and creates a complete invoice automation pipeline from match acceptance through final PDF documentation in Google Drive.

### 14.2 Business Context
- Special work orders only go to approximately 3 regular clients
- Current manual QuickBooks invoice creation is time-intensive
- PDF documentation and Google Drive storage is currently manual
- Invoice tracking in Google Sheets requires manual link updates

### 14.3 Enhanced Workflow
1. **Existing**: Email paste → LLM matching → Match suggestions
2. **New**: User accepts matches → Stage for invoicing  
3. **New**: Batch staged items → Create QB invoice via API
4. **New**: User reviews/approves in QB interface → User saves invoice as PDF within QB
5. **New**: Manual "Process Invoice PDF" button → File picker → Google Drive upload → Sheet update with link

### 14.4 New Functional Requirements

#### 14.4.1 Match Staging System
- Accept/reject individual match suggestions from LLM analysis
- Stage accepted matches for batch invoice creation
- Session-based staging (no persistent storage required)
- Support batching multiple work orders into single invoice
- Clear staging after successful invoice processing

#### 14.4.2 Client Management
- Simple dictionary-based client configuration
- Store basic client information: name, QuickBooks customer ID, email
- Support for ~3 regular clients (no GUI configuration needed)
- Integration with QuickBooks customer records

#### 14.4.3 QuickBooks Online Integration
- API authentication using python-quickbooks library
- Sandbox environment for development and testing
- Customer creation/management via API
- Invoice creation with line items from staged work orders
- Standard invoice format (no custom templates required)

#### 14.4.4 PDF Processing Workflow
- Manual "Process Invoice PDF" button after QB invoice creation
- File picker dialog for PDF selection (no automatic file monitoring)
- Support for PDFs saved from QuickBooks interface
- Upload to Google Drive with organized folder structure
- Generate shareable links for Google Sheets updates

#### 14.4.5 Google Drive Integration
- Expand existing Google authentication to include Drive API scopes
- Upload invoice PDFs to designated Drive folders
- Generate shareable links for easy access
- Maintain file organization by client/date (optional)

#### 14.4.6 Google Sheets Updates
- Update work order rows with invoice PDF links
- Mark processed work orders with completion status
- Track invoice creation dates and QB invoice numbers
- Maintain audit trail of processed items

### 14.5 Technical Architecture Extensions

#### 14.5.1 New Modules
```
quickbooks/
├── __init__.py
├── qb_client.py          # QB API wrapper using python-quickbooks
├── invoice_builder.py    # Convert staged matches to QB invoice format
└── customer_manager.py   # Handle client dictionary management

staging/
├── __init__.py
├── match_staging.py      # Session-based staging of accepted matches
└── invoice_session.py    # Batch management for invoice creation

drive/
├── __init__.py
├── drive_client.py       # PDF upload and link generation
└── pdf_processor.py      # File picker and processing workflow
```

#### 14.5.2 Authentication Extensions
- Expand Google OAuth2 scopes to include Drive API access
- QuickBooks OAuth2 integration for API access
- Sandbox credentials for development
- Production credential management

#### 14.5.3 Updated Google Scopes
```python
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',     # Existing
    'https://www.googleapis.com/auth/drive.file'        # New for PDF upload
]
```

### 14.6 User Interface Extensions

#### 14.6.1 Match Review Interface
- Accept/reject buttons for each LLM match suggestion
- Staging area showing accepted matches
- Batch processing controls for invoice creation
- Clear staging functionality

#### 14.6.2 Invoice Processing Panel
```
┌─ Invoice Processing ─────────────┐
│ Staged Items: 5 work orders      │
│ Client: ABC Construction         │
│                                  │
│ [Create QB Invoice]              │
│                                  │
│ ✅ Invoice #12345 created in QB  │
│ [Process Invoice PDF]            │
└──────────────────────────────────┘
```

#### 14.6.3 Progress Tracking
- Visual indicators for workflow stages
- Success/error messaging for each step
- Processing status updates during API calls

### 14.7 Implementation Phases

#### 14.7.1 Phase 1: Basic QB Integration (Week 1)
- QuickBooks authentication and sandbox setup
- Basic customer creation via API
- Simple invoice creation from staged matches
- Client dictionary configuration

#### 14.7.2 Phase 2: Staging & Workflow (Week 2)  
- Match acceptance/staging interface
- Batch invoice creation functionality
- Enhanced error handling and user feedback
- End-to-end invoice creation workflow

#### 14.7.3 Phase 3: PDF & Drive Integration (Week 3)
- Google Drive authentication expansion
- File picker for PDF selection
- Drive upload and link generation
- Google Sheets update with PDF links

#### 14.7.4 Phase 4: Testing & Polish (Week 4)
- End-to-end workflow testing
- Error handling refinement
- User experience optimization
- Production readiness validation

### 14.8 Configuration Requirements

#### 14.8.1 Client Configuration
```python
CLIENTS = {
    "client_1": {
        "name": "ABC Construction", 
        "qb_customer_id": "123",
        "email": "billing@abc.com"
    },
    "client_2": {
        "name": "XYZ Development",
        "qb_customer_id": "456", 
        "email": "accounting@xyz.com"
    },
    "client_3": {
        "name": "DEF Properties",
        "qb_customer_id": "789",
        "email": "invoices@def.com"
    }
}
```

#### 14.8.2 QuickBooks Configuration
- Sandbox app credentials for development
- Production app credentials for deployment
- API endpoint configurations
- Customer ID mappings

#### 14.8.3 Google Drive Configuration
- Target folder IDs for PDF storage
- File naming conventions
- Sharing permissions for generated links

### 14.9 Data Flow Integration

#### 14.9.1 Extended Data Pipeline
```
Email Input → LLM Matching → User Review → Match Staging → 
QB Invoice Creation → User PDF Save → PDF Processing → 
Drive Upload → Sheets Update → Workflow Complete
```

#### 14.9.2 State Management
- Session-based staging with cleanup after processing
- Error recovery at each workflow stage
- Rollback capabilities for failed operations
- Audit logging for troubleshooting

### 14.10 Security Considerations

#### 14.10.1 API Security
- OAuth2 for both Google and QuickBooks APIs
- Secure token storage and refresh handling
- Sandbox isolation for development
- Production credential separation

#### 14.10.2 Data Handling
- No persistent storage of sensitive invoice data
- Local-only processing of financial information
- Secure file handling during PDF processing
- Proper cleanup of temporary files

### 14.11 Success Criteria for QB Integration

#### 14.11.1 Functional Success
- [ ] Users can accept/reject match suggestions and stage for invoicing
- [ ] Staged matches successfully create QuickBooks invoices via API
- [ ] PDF processing workflow handles user-selected files correctly
- [ ] Google Drive upload and link generation works reliably
- [ ] Google Sheets updates with PDF links automatically

#### 14.11.2 Performance Success
- [ ] Invoice creation completes within 60 seconds
- [ ] PDF upload and processing under 30 seconds
- [ ] End-to-end workflow from staging to documentation under 5 minutes
- [ ] Error recovery handles common failure scenarios

#### 14.11.3 Business Success
- [ ] Eliminates manual QuickBooks invoice data entry
- [ ] Reduces PDF documentation time by 80%+
- [ ] Provides complete audit trail from email to final invoice
- [ ] Maintains accuracy while improving efficiency