# gui/main_window.py
"""
Main window for Work Order Matcher
Integrates all GUI components with the matching system
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.components.email_input import EmailInputWidget
from gui.components.count_input import CountInputWidget  
from gui.components.results_display import ResultsDisplayWidget
from data.sheets_client import SheetsClient
from llm.anthropic_client import AnthropicClient
from data.data_models import MatchingResult, WorkOrder


class WorkOrderMatcherApp:
    """Main application window for Work Order Matcher"""
    
    def __init__(self, root):
        """Initialize the main application"""
        self.root = root
        self.root.title("Work Order Matcher - AI-Powered Billing Analysis")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Initialize clients
        self.sheets_client = SheetsClient()
        self.anthropic_client = AnthropicClient()
        self.work_orders = []
        
        # GUI components
        self.email_input = None
        self.count_input = None
        self.results_display = None
        self.find_matches_button = None
        self.status_bar = None
        
        # State tracking
        self.matching_in_progress = False
        
        # Set up GUI
        self._setup_gui()
        
        # Load work orders in background
        self._load_work_orders_async()
    
    def _setup_gui(self):
        """Set up the main GUI layout"""
        
        # Configure root grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)  # Main content area expands
        
        # Title and status bar
        self._create_header()
        
        # Main content area
        self._create_main_content()
        
        # Status bar
        self._create_status_bar()
        
        # Menu bar
        self._create_menu_bar()
        
        # Configure window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_header(self):
        """Create application header"""
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="Work Order Matcher",
            font=("Segoe UI", 18, "bold")
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Subtitle
        subtitle_label = ttk.Label(
            header_frame,
            text="AI-powered matching of email billing to work order data",
            font=("Segoe UI", 11),
            foreground="gray"
        )
        subtitle_label.grid(row=1, column=0, sticky=tk.W)
        
        # System status
        self.system_status_label = ttk.Label(
            header_frame,
            text="🔄 Loading work orders...",
            font=("Segoe UI", 10),
            foreground="orange"
        )
        self.system_status_label.grid(row=0, column=1, rowspan=2, sticky=tk.E)
    
    def _create_main_content(self):
        """Create main content area"""
        # Main container with paned window for resizable sections
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=(0, 10))
        
        # Left panel - Input
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)
        
        # Right panel - Results  
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        # Set up left panel
        self._create_input_panel(left_frame)
        
        # Set up right panel
        self._create_results_panel(right_frame)
    
    def _create_input_panel(self, parent):
        """Create input panel with email and count widgets"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # Email input (takes most space)
        self.email_input = EmailInputWidget(
            parent, 
            on_change_callback=self._on_email_text_change
        )
        self.email_input.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Controls frame
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.grid_columnconfigure(0, weight=1)
        
        # Expected count input
        self.count_input = CountInputWidget(
            controls_frame,
            initial_value=5,
            on_change_callback=self._on_count_change
        )
        self.count_input.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Action buttons frame
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Find matches button (primary action)
        self.find_matches_button = ttk.Button(
            buttons_frame,
            text="🔍 Find Matches",
            command=self._find_matches,
            style="Accent.TButton"
        )
        self.find_matches_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Sample text button
        sample_button = ttk.Button(
            buttons_frame,
            text="📝 Load Sample",
            command=self._load_sample_email
        )
        sample_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_button = ttk.Button(
            buttons_frame,
            text="🗑️ Clear All",
            command=self._clear_all
        )
        clear_button.pack(side=tk.LEFT)
        
        # Progress bar (hidden initially)
        self.progress_bar = ttk.Progressbar(
            controls_frame,
            mode='indeterminate',
            style="success.Horizontal.TProgressbar"
        )
        self.progress_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        self.progress_bar.grid_remove()  # Hide initially
        
    def _create_results_panel(self, parent):
        """Create results panel"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # Results display widget
        self.results_display = ResultsDisplayWidget(parent)
        self.results_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def _create_status_bar(self):
        """Create status bar"""
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Work orders count
        self.wo_count_label = ttk.Label(
            status_frame,
            text="Work Orders: Loading...",
            font=("Segoe UI", 9)
        )
        self.wo_count_label.grid(row=0, column=0, padx=(10, 20))
        
        # Status message (expandable)
        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Version info
        version_label = ttk.Label(
            status_frame,
            text="v1.0 | Claude 3.5 Sonnet",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        version_label.grid(row=0, column=2, padx=(20, 10))
        
    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Sample Email", command=self._load_sample_email)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Reload Work Orders", command=self._reload_work_orders)
        tools_menu.add_command(label="Test Connections", command=self._test_connections)
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear All Data", command=self._clear_all)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _load_work_orders_async(self):
        """Load work orders in background thread"""
        def load_work_orders():
            try:
                self._update_status("Connecting to Google Sheets...")
                
                # Authenticate and load work orders
                if not self.sheets_client.authenticate():
                    self._update_status("❌ Google Sheets authentication failed", "red")
                    self._update_system_status("❌ Authentication failed", "red")
                    return
                
                self._update_status("Loading work orders...")
                self.work_orders = self.sheets_client.load_alpha_numeric_work_orders()
                
                # Update UI on main thread
                self.root.after(0, self._on_work_orders_loaded)
                
            except Exception as e:
                self.root.after(0, lambda: self._on_work_orders_error(str(e)))
        
        # Start background thread
        thread = threading.Thread(target=load_work_orders, daemon=True)
        thread.start()
    
    def _on_work_orders_loaded(self):
        """Handle successful work orders loading"""
        count = len(self.work_orders)
        self._update_wo_count(f"Work Orders: {count} alpha-numeric loaded")
        self._update_status(f"✅ Ready - {count} work orders available", "green")
        self._update_system_status("✅ System ready", "green")
        
        # Enable find matches button
        self.find_matches_button.config(state="normal")
    
    def _on_work_orders_error(self, error):
        """Handle work orders loading error"""
        self._update_wo_count("Work Orders: Error loading")
        self._update_status(f"❌ Error loading work orders: {error}", "red")
        self._update_system_status("❌ System error", "red")
        
        # Keep button disabled
        self.find_matches_button.config(state="disabled")
    
    def _find_matches(self):
        """Main matching function"""
        if self.matching_in_progress:
            return
            
        # Validate inputs
        email_text = self.email_input.get_text()
        if not email_text or len(email_text.strip()) < 20:
            messagebox.showwarning("Input Required", "Please paste email billing text first.")
            self.email_input.focus()
            return
        
        if not self.work_orders:
            messagebox.showerror("No Data", "No work orders are loaded. Please check your Google Sheets connection.")
            return
        
        expected_count = self.count_input.get_count()
        
        # Start matching in background
        self._start_matching_async(email_text, expected_count)
    
    def _start_matching_async(self, email_text, expected_count):
        """Start matching process in background thread"""
        def run_matching():
            try:
                # Update UI
                self.root.after(0, self._on_matching_started)
                
                # Run matching - convert WorkOrder objects to dict format
                work_orders_dict = []
                for wo in self.work_orders:
                    wo_dict = {
                        'WO #': wo.wo_id,
                        'Total': wo.total,
                        'Location': wo.location,
                        'Description': wo.description
                    }
                    work_orders_dict.append(wo_dict)
                
                result = self.anthropic_client.find_matches(
                    email_text=email_text,
                    work_orders=work_orders_dict,
                    expected_count=expected_count
                )
                
                # Convert to MatchingResult object
                matching_result = MatchingResult.from_api_response(result, self.work_orders)
                
                # Update UI on main thread
                self.root.after(0, lambda: self._on_matching_completed(matching_result))
                
            except Exception as e:
                self.root.after(0, lambda: self._on_matching_error(str(e)))
        
        # Start background thread
        thread = threading.Thread(target=run_matching, daemon=True)
        thread.start()
    
    def _on_matching_started(self):
        """Handle matching process start"""
        self.matching_in_progress = True
        self.find_matches_button.config(state="disabled", text="🔍 Analyzing...")
        self.progress_bar.grid()  # Show progress bar
        self.progress_bar.start(10)  # Start animation
        self._update_status("🤖 Analyzing email with Claude AI...", "blue")
    
    def _on_matching_completed(self, result: MatchingResult):
        """Handle successful matching completion"""
        self.matching_in_progress = False
        self.find_matches_button.config(state="normal", text="🔍 Find Matches")
        self.progress_bar.stop()
        self.progress_bar.grid_remove()  # Hide progress bar
        
        if result.success:
            # Display results
            self.results_display.display_results(result)
            
            # Update status
            status_msg = f"✅ Analysis complete: {result.total_match_count} matches found"
            if result.unmatched_count > 0:
                status_msg += f", {result.unmatched_count} unmatched"
            self._update_status(status_msg, "green")
            
        else:
            self._update_status(f"❌ Analysis failed: {result.error}", "red")
            messagebox.showerror("Analysis Failed", f"Matching analysis failed:\n\n{result.error}")
    
    def _on_matching_error(self, error):
        """Handle matching process error"""
        self.matching_in_progress = False
        self.find_matches_button.config(state="normal", text="🔍 Find Matches")
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        
        self._update_status(f"❌ Error during analysis: {error}", "red")
        messagebox.showerror("Analysis Error", f"An error occurred during analysis:\n\n{error}")
    
    def _load_sample_email(self):
        """Load sample email text"""
        if self.matching_in_progress:
            return
            
        self.email_input.set_sample_text()
        self.count_input.set_count(2)  # Sample has 2 work orders
        self._update_status("Sample email loaded", "blue")
    
    def _clear_all(self):
        """Clear all input and results"""
        if self.matching_in_progress:
            return
            
        self.email_input.clear_text()
        self.count_input.reset_to_default()
        self.results_display._clear_results()
        self._update_status("All data cleared", "gray")
    
    def _reload_work_orders(self):
        """Reload work orders from Google Sheets"""
        if self.matching_in_progress:
            return
            
        self._update_system_status("🔄 Reloading...", "orange")
        self.find_matches_button.config(state="disabled")
        self._load_work_orders_async()
    
    def _test_connections(self):
        """Test all system connections"""
        if self.matching_in_progress:
            return
            
        def test_all():
            try:
                self.root.after(0, lambda: self._update_status("Testing connections...", "blue"))
                
                # Test Google Sheets
                sheets_ok = self.sheets_client.test_connection()
                
                # Test Anthropic
                anthropic_result = self.anthropic_client.test_connection()
                anthropic_ok = anthropic_result.get('success', False)
                
                # Report results
                status = "✅ All connections working" if sheets_ok and anthropic_ok else "⚠️ Some connections failed"
                color = "green" if sheets_ok and anthropic_ok else "orange"
                
                details = f"Google Sheets: {'✅' if sheets_ok else '❌'}\n"
                details += f"Anthropic API: {'✅' if anthropic_ok else '❌'}"
                
                self.root.after(0, lambda: self._update_status(status, color))
                self.root.after(0, lambda: messagebox.showinfo("Connection Test", details))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Connection Test Failed", str(e)))
        
        thread = threading.Thread(target=test_all, daemon=True)
        thread.start()
    
    def _show_about(self):
        """Show about dialog"""
        about_text = """Work Order Matcher v1.0

AI-powered tool for matching email billing descriptions 
to Google Sheets work order data.

Features:
• Blended confidence scoring
• Intelligent fuzzy matching
• Export capabilities
• Real-time analysis

Powered by:
• Claude 3.5 Sonnet (Anthropic)
• Google Sheets API
• Python + tkinter"""

        messagebox.showinfo("About Work Order Matcher", about_text)
    
    def _on_email_text_change(self, text):
        """Handle email text changes"""
        # Update button state based on content
        has_content = bool(text and len(text.strip()) > 20)
        has_work_orders = bool(self.work_orders)
        not_processing = not self.matching_in_progress
        
        button_enabled = has_content and has_work_orders and not_processing
        self.find_matches_button.config(state="normal" if button_enabled else "disabled")
    
    def _on_count_change(self, count):
        """Handle count input changes"""
        # Could add validation or other logic here
        pass
    
    def _update_status(self, message, color="gray"):
        """Update status bar message"""
        self.status_label.config(text=message, foreground=color)
    
    def _update_system_status(self, message, color="gray"):
        """Update system status in header"""
        self.system_status_label.config(text=message, foreground=color)
    
    def _update_wo_count(self, message):
        """Update work orders count"""
        self.wo_count_label.config(text=message)
    
    def _on_closing(self):
        """Handle application closing"""
        if self.matching_in_progress:
            if not messagebox.askokcancel("Exit", "Matching is in progress. Exit anyway?"):
                return
        
        print("Work Order Matcher closing...")
        self.root.quit()
        self.root.destroy()


def create_application():
    """Create and configure the main application"""
    # Create root window
    root = tk.Tk()
    
    # Configure styles
    style = ttk.Style()
    
    try:
        # Try to use modern Windows theme
        style.theme_use('winnative')
    except:
        # Fallback to default
        style.theme_use('default')
    
    # Create application
    app = WorkOrderMatcherApp(root)
    
    return app, root


if __name__ == "__main__":
    app, root = create_application()
    root.mainloop() 