# QuickBooks API Integration Project Summary

## Project Context
Developer building automation tools for wife's bookkeeping workflow at a general contracting firm. Heavy reliance on Claude for coding assistance. Working in Python with desktop apps.

## Existing Applications

### App 1: Worker Payment Processing
- **Purpose**: Automate worker payment workflow
- **Current functionality**:
  - Downloads data from Google Sheets (worker invoice storage)
  - Retrieves URLs to handwritten invoice images
  - Filters and groups invoices by worker and date range
  - Provides GUI with table view + clickable image gallery
  - Combines selected invoices into PDF for QuickBooks manual entry
- **Next step**: Automate check writing via QuickBooks API

### App 2: Client Invoice Matching (Less Successful)
- **Purpose**: Match boss's email descriptions to work orders in Google Sheets
- **Current functionality**:
  - GUI for pasting email text from boss
  - Downloads/filters Google Sheets data for potential matches
  - Uses Claude API to suggest structured matches
- **Issue**: Wife prefers manual matching due to tribal knowledge and pride in accuracy
- **Reality**: She's faster/more accurate than current LLM matching

## Current Challenge: QuickBooks API Integration

### Setup Status
- QuickBooks Developer account created
- Sandbox credentials obtained
- Ready to begin API integration development

### Concern Raised
- Worried about complexity of setting up sandbox to mirror real-world client list
- Only 3-4 clients but seemed like significant manual work

### Solution Identified
- **Key insight**: Can create customers programmatically via API instead of manual setup
- Use `python-quickbooks` library for batch customer creation
- Takes ~5 minutes vs manual clicking through interface

## Recommended Development Approach

### Branch Strategy
```bash
git checkout -b quickbooks-integration
```

### Modular Integration
- Add `quickbooks_client.py` module to existing apps
- Maintain existing structure while adding QB connectivity
- Use sandbox flag pattern for safe development

### Setup Script Pattern
```python
def setup_sandbox_data(self):
    """One-time setup to mirror production client list"""
    if not self.sandbox:
        return
    
    # Auto-create real client list in sandbox
    # Batch create using python-quickbooks library
```

## Target Integrations

### Priority 1: Worker Payment App
- Create checks via QuickBooks API
- Attach PDF invoices to check records
- Link individual invoices in check notes

### Priority 2: Client Invoice Creation
- Create invoices with line items from Google Sheets data
- Upload invoice PDFs as attachments
- Tag work orders to invoices for markup tracking

## Key Technical Details
- Use `python-quickbooks` library for API interactions
- Leverage batch operations for efficiency
- Sandbox environment mirrors production API exactly
- Real data structure + sandbox company = safe testing
- Production deployment = credential swap only

## Business Context Notes
- Wife takes pride in tribal knowledge and manual matching accuracy
- Boss workflow needs restructuring (future pitch opportunity)
- Company trying to hide markup in invoice structure
- Manual processes currently waste significant time in QuickBooks data entry

## Next Immediate Steps
1. Set up basic authentication in sandbox
2. Create customer setup script for sandbox
3. Build invoice creation function using Google Sheets data
4. Add check creation for worker payment workflow
5. Test end-to-end with real data flows (sandbox QB company)

## Development Timeline Estimate
- Week 1: Basic auth + simple invoice creation in sandbox
- Week 2: Invoice creation with Google Sheets integration  
- Week 3: Check creation for worker payments
- Week 4: End-to-end testing + production readiness