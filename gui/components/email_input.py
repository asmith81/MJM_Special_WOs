# gui/components/email_input.py
"""
Email input component for Work Order Matcher
Large text area for pasting email billing text
"""

import tkinter as tk
from tkinter import ttk, scrolledtext


class EmailInputWidget:
    """Widget for email text input with validation and formatting"""
    
    def __init__(self, parent, on_change_callback=None):
        """
        Initialize email input widget
        
        Args:
            parent: Parent tkinter widget
            on_change_callback: Function to call when text changes
        """
        self.parent = parent
        self.on_change_callback = on_change_callback
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Email Billing Text", padding="10")
        
        # Create components
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all GUI components"""
        
        # Instructions label
        instructions = ttk.Label(
            self.frame, 
            text="Paste the email billing text below. Look for unit numbers, amounts, and job descriptions.",
            foreground="gray",
            wraplength=600
        )
        instructions.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Text area with scrollbar
        self.text_area = scrolledtext.ScrolledText(
            self.frame,
            width=80,
            height=15,
            wrap=tk.WORD,
            font=("Consolas", 10),
            borderwidth=2,
            relief="groove"
        )
        self.text_area.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Bind text change events
        if self.on_change_callback:
            self.text_area.bind('<KeyRelease>', self._on_text_change)
            self.text_area.bind('<Button-1>', self._on_text_change) 
            self.text_area.bind('<Control-v>', self._on_paste)
        
        # Character count label
        self.char_count_label = ttk.Label(self.frame, text="0 characters", foreground="gray")
        self.char_count_label.grid(row=2, column=0, sticky=tk.W)
        
        # Clear button
        self.clear_button = ttk.Button(
            self.frame, 
            text="Clear Text",
            command=self.clear_text
        )
        self.clear_button.grid(row=2, column=1, sticky=tk.E)
        
        # Configure grid weights
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
    
    def _on_text_change(self, event=None):
        """Handle text change events"""
        self._update_char_count()
        if self.on_change_callback:
            self.on_change_callback(self.get_text())
    
    def _on_paste(self, event=None):
        """Handle paste events (delay update for paste completion)"""
        self.frame.after(10, self._on_text_change)
    
    def _update_char_count(self):
        """Update character count display"""
        text_length = len(self.get_text())
        self.char_count_label.config(text=f"{text_length:,} characters")
        
        # Color coding for text length
        if text_length == 0:
            color = "gray"
        elif text_length < 100:
            color = "orange"  # Too short, probably incomplete
        elif text_length > 5000:
            color = "red"    # Very long, might hit token limits
        else:
            color = "green"   # Good length
            
        self.char_count_label.config(foreground=color)
    
    def get_text(self) -> str:
        """Get current text content"""
        return self.text_area.get("1.0", tk.END).strip()
    
    def set_text(self, text: str):
        """Set text content"""
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", text)
        self._update_char_count()
    
    def clear_text(self):
        """Clear all text"""
        self.set_text("")
        self.text_area.focus_set()
    
    def append_text(self, text: str):
        """Append text to existing content"""
        self.text_area.insert(tk.END, text)
        self._update_char_count()
    
    def is_empty(self) -> bool:
        """Check if text area is empty"""
        return len(self.get_text()) == 0
    
    def get_validation_status(self) -> dict:
        """Get validation status of current text"""
        text = self.get_text()
        
        # Basic validation checks
        has_amount = any(char in text for char in ['$', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])
        has_unit_reference = any(word in text.lower() for word in ['unit', 'building', 'apartment', 'apt'])
        has_work_description = any(word in text.lower() for word in ['repair', 'fix', 'replace', 'install', 'work', 'labor'])
        
        min_length = len(text) >= 50
        reasonable_length = len(text) <= 3000
        
        return {
            'valid': min_length and has_amount and reasonable_length,
            'has_amount': has_amount,
            'has_unit_reference': has_unit_reference, 
            'has_work_description': has_work_description,
            'min_length': min_length,
            'reasonable_length': reasonable_length,
            'character_count': len(text)
        }
    
    def set_sample_text(self):
        """Set sample email text for testing"""
        sample = """Our invoice for the work is as follows:
Unit 5966: The concrete sidewalk and drain area was cracked and needed repair
Materials and Labor: $ 3,987.00

Unit 5804: Drywall was repaired, plastered and painted due to a roof leak 
Materials and Labor: $ 350.00

Grand Total: $ 4,337.00

Thank you for your business."""
        
        self.set_text(sample)
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame"""
        self.frame.grid(**kwargs) 