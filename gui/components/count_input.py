# gui/components/count_input.py
"""
Count input component for Work Order Matcher
Simple integer input for expected work order count
"""

import tkinter as tk
from tkinter import ttk


class CountInputWidget:
    """Widget for expected work order count input"""
    
    def __init__(self, parent, initial_value=5, on_change_callback=None):
        """
        Initialize count input widget
        
        Args:
            parent: Parent tkinter widget
            initial_value: Default count value
            on_change_callback: Function to call when count changes
        """
        self.parent = parent
        self.on_change_callback = on_change_callback
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Create components
        self._create_widgets(initial_value)
        
    def _create_widgets(self, initial_value):
        """Create all GUI components"""
        
        # Label
        self.label = ttk.Label(
            self.frame, 
            text="Expected Work Orders:",
            font=("Segoe UI", 10, "bold")
        )
        self.label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # Spinbox for count input
        self.count_var = tk.StringVar(value=str(initial_value))
        self.count_spinbox = ttk.Spinbox(
            self.frame,
            from_=1,
            to=20,
            width=5,
            textvariable=self.count_var,
            command=self._on_value_change,
            validate="key",
            validatecommand=(self.parent.register(self._validate_input), '%P')
        )
        self.count_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # Bind additional events
        self.count_var.trace('w', self._on_variable_change)
        
        # Help text
        help_text = ttk.Label(
            self.frame,
            text="(How many work orders do you expect to find in the email?)",
            foreground="gray",
            font=("Segoe UI", 9)
        )
        help_text.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # Preset buttons frame
        presets_frame = ttk.Frame(self.frame)
        presets_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(presets_frame, text="Quick set:", foreground="gray").pack(side=tk.LEFT, padx=(0, 5))
        
        # Common preset values
        preset_values = [1, 2, 3, 5, 10]
        for value in preset_values:
            btn = ttk.Button(
                presets_frame,
                text=str(value),
                width=3,
                command=lambda v=value: self.set_count(v)
            )
            btn.pack(side=tk.LEFT, padx=(0, 2))
    
    def _validate_input(self, value):
        """Validate that input is a positive integer"""
        if value == "":
            return True  # Allow empty for editing
        try:
            int_value = int(value)
            return 1 <= int_value <= 99  # Reasonable range
        except ValueError:
            return False
    
    def _on_value_change(self):
        """Handle spinbox value change"""
        self._trigger_callback()
    
    def _on_variable_change(self, *args):
        """Handle variable trace change"""
        self._trigger_callback()
    
    def _trigger_callback(self):
        """Trigger the change callback if set"""
        if self.on_change_callback:
            try:
                count = self.get_count()
                self.on_change_callback(count)
            except ValueError:
                # Invalid value, don't trigger callback
                pass
    
    def get_count(self) -> int:
        """Get current count value with robust error handling"""
        try:
            value = self.count_var.get()
            if not value or not isinstance(value, str):
                return 5  # Default if empty or wrong type
            
            value = value.strip()
            if not value:
                return 5  # Default if empty after strip
                
            count = int(value)
            return max(1, min(99, count))  # Clamp to reasonable range
        except (ValueError, AttributeError, TypeError):
            return 5  # Default if invalid
    
    def set_count(self, count: int):
        """Set count value"""
        if 1 <= count <= 99:
            self.count_var.set(str(count))
    
    def is_valid(self) -> bool:
        """Check if current value is valid"""
        try:
            count = self.get_count()
            return 1 <= count <= 99
        except (ValueError, TypeError):
            return False
    
    def get_validation_status(self) -> dict:
        """Get validation status"""
        try:
            count = self.get_count()
            return {
                'valid': 1 <= count <= 99,
                'value': count,
                'in_range': 1 <= count <= 99,
                'message': f"Will search for {count} work order{'s' if count != 1 else ''}"
            }
        except (ValueError, TypeError):
            return {
                'valid': False,
                'value': None,
                'in_range': False,
                'message': "Please enter a valid number"
            }
    
    def reset_to_default(self):
        """Reset to default value"""
        self.set_count(5)
    
    def focus(self):
        """Set focus to the input field"""
        self.count_spinbox.focus_set()
        self.count_spinbox.select_range(0, tk.END)
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame"""
        self.frame.grid(**kwargs) 