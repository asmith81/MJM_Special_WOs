# data/sheets_client.py
"""
Google Sheets client wrapper for Work Order Matcher
Provides clean interface to Google Sheets data with WorkOrder objects
"""

from typing import List, Optional
import time
from auth.google_auth import GoogleAuth
from data.data_models import WorkOrder
from utils.logging_config import get_logger
from utils.config import Config
import pandas as pd

logger = get_logger('sheets_client')


class SheetsClient:
    """Clean interface to Google Sheets data"""
    
    def __init__(self):
        """Initialize with Google authentication and logging"""
        logger.debug("Initializing SheetsClient")
        self.auth = GoogleAuth()
        self._authenticated = False
        logger.debug("SheetsClient initialized")
    
    def authenticate(self) -> bool:
        """Authenticate with Google Sheets with enhanced logging"""
        try:
            logger.info("Starting Google Sheets authentication")
            start_time = time.time()
            
            self.auth.authenticate()
            self._authenticated = True
            
            auth_duration = time.time() - start_time
            logger.info(f"✅ Google Sheets authentication successful in {auth_duration:.2f}s")
            
            return True
        except Exception as e:
            logger.error(f"❌ Google Sheets authentication failed: {e}")
            self._authenticated = False
            return False
    
    def test_connection(self) -> bool:
        """Test connection to Google Sheets with logging"""
        try:
            if not self._authenticated:
                logger.warning("Cannot test connection - not authenticated")
                return False
            
            logger.info("Testing Google Sheets connection")
            result = self.auth.test_connection()
            
            if result:
                logger.info("✅ Google Sheets connection test passed")
            else:
                logger.error("❌ Google Sheets connection test failed")
            
            return result
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def load_all_work_orders(self) -> List[WorkOrder]:
        """Load all work orders from Google Sheets with enhanced logging and error handling"""
        try:
            if not self._authenticated:
                raise Exception("Not authenticated - call authenticate() first")
            
            logger.info("Loading work orders from Google Sheets")
            start_time = time.time()
            
            # Get raw data from auth client
            raw_data = self.auth.load_work_orders()
            data_load_duration = time.time() - start_time
            
            # Convert to WorkOrder objects
            work_orders = []
            skipped_count = 0
            conversion_start = time.time()
            
            for i, row in enumerate(raw_data):
                try:
                    wo = WorkOrder.from_sheets_row(row)
                    work_orders.append(wo)
                except Exception as e:
                    # Skip malformed rows but continue processing
                    skipped_count += 1
                    logger.warning(f"Skipping malformed work order row {i+1}: {e}")
                    continue
            
            conversion_duration = time.time() - conversion_start
            total_duration = time.time() - start_time
            
            logger.info(f"✅ Loaded {len(work_orders)} work orders ({skipped_count} skipped) in {total_duration:.2f}s")
            
            if Config.ENABLE_PERFORMANCE_LOGGING:
                logger.info(f"Work orders loading performance - Data: {data_load_duration:.2f}s, Conversion: {conversion_duration:.2f}s")
            
            return work_orders
            
        except Exception as e:
            logger.error(f"❌ Failed to load work orders: {e}")
            return []
    
    def load_alpha_numeric_work_orders(self) -> List[WorkOrder]:
        """Load only alpha-numeric work orders (special clients)"""
        all_work_orders = self.load_all_work_orders()
        return [wo for wo in all_work_orders if wo.is_alpha_numeric()]
    
    def get_work_order_by_id(self, wo_id: str) -> Optional[WorkOrder]:
        """Get specific work order by ID"""
        work_orders = self.load_alpha_numeric_work_orders()
        return next((wo for wo in work_orders if wo.wo_id == wo_id), None)
    
    def get_work_orders_by_location(self, location_hint: str) -> List[WorkOrder]:
        """Get work orders matching location hint"""
        work_orders = self.load_alpha_numeric_work_orders()
        location_lower = location_hint.lower()
        return [
            wo for wo in work_orders 
            if location_lower in wo.location.lower() or location_lower in wo.description.lower()
        ]
    
    def get_work_orders_by_amount_range(self, target_amount: float, tolerance_percent: float = 15.0) -> List[WorkOrder]:
        """Get work orders within amount tolerance"""
        work_orders = self.load_alpha_numeric_work_orders()
        matching_wos = []
        
        for wo in work_orders:
            wo_amount = wo.get_clean_amount()
            if wo_amount > 0:
                diff_percent = abs(wo_amount - target_amount) / target_amount * 100
                if diff_percent <= tolerance_percent:
                    matching_wos.append(wo)
        
        return matching_wos
    
    def get_summary_statistics(self) -> dict:
        """Get summary statistics about work orders"""
        work_orders = self.load_all_work_orders()
        alpha_numeric_wos = [wo for wo in work_orders if wo.is_alpha_numeric()]
        
        total_amounts = [wo.get_clean_amount() for wo in alpha_numeric_wos if wo.get_clean_amount() > 0]
        
        return {
            'total_work_orders': len(work_orders),
            'alpha_numeric_work_orders': len(alpha_numeric_wos),
            'total_value': sum(total_amounts) if total_amounts else 0,
            'average_value': sum(total_amounts) / len(total_amounts) if total_amounts else 0,
            'min_value': min(total_amounts) if total_amounts else 0,
            'max_value': max(total_amounts) if total_amounts else 0
        }
    
    def export_work_orders_to_csv(self, filename: str, work_orders: Optional[List[WorkOrder]] = None):
        """Export work orders to CSV file"""
        if work_orders is None:
            work_orders = self.load_alpha_numeric_work_orders()
        
        if not work_orders:
            print("⚠️ No work orders to export")
            return
        
        try:
            # Convert to pandas DataFrame
            data = []
            for wo in work_orders:
                data.append({
                    'WO_ID': wo.wo_id,
                    'Total': wo.total,
                    'Clean_Amount': wo.get_clean_amount(),
                    'Location': wo.location,
                    'Description': wo.description
                })
            
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"✅ Exported {len(work_orders)} work orders to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def search_work_orders(self, search_term: str) -> List[WorkOrder]:
        """Search work orders by term (location, description, or WO ID)"""
        work_orders = self.load_alpha_numeric_work_orders()
        search_lower = search_term.lower()
        
        matching_wos = []
        for wo in work_orders:
            if (search_lower in wo.wo_id.lower() or 
                search_lower in wo.location.lower() or 
                search_lower in wo.description.lower()):
                matching_wos.append(wo)
        
        return matching_wos
    
    def get_status(self) -> dict:
        """Get client status information"""
        return {
            'authenticated': self._authenticated,
            'credentials_status': self.auth.get_credentials_status() if self._authenticated else 'Not authenticated',
            'can_connect': self.test_connection() if self._authenticated else False
        } 