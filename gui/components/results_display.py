# gui/components/results_display.py
"""
Results display component for Work Order Matcher
Shows matches with confidence scores, evidence, and export options
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional
import csv
from datetime import datetime

from data.data_models import MatchingResult, Match


class ResultsDisplayWidget:
    """Widget for displaying matching results with detailed information"""
    
    def __init__(self, parent):
        """Initialize results display widget"""
        self.parent = parent
        self.current_results: Optional[MatchingResult] = None
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Matching Results", padding="10")
        
        # Create components
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all GUI components"""
        
        # Results summary frame
        summary_frame = ttk.Frame(self.frame)
        summary_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Summary labels
        self.summary_label = ttk.Label(
            summary_frame, 
            text="No analysis run yet",
            font=("Segoe UI", 10, "bold")
        )
        self.summary_label.pack(side=tk.LEFT)
        
        # Export button
        self.export_button = ttk.Button(
            summary_frame,
            text="Export Results",
            command=self._export_results,
            state="disabled"
        )
        self.export_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Clear button  
        self.clear_button = ttk.Button(
            summary_frame,
            text="Clear Results", 
            command=self._clear_results,
            state="disabled"
        )
        self.clear_button.pack(side=tk.RIGHT)
        
        # Main results area with notebook for different views
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Matches tab
        self._create_matches_tab()
        
        # Unmatched tab
        self._create_unmatched_tab()
        
        # Details tab
        self._create_details_tab()
        
        # Configure grid weights
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        
    def _create_matches_tab(self):
        """Create the matches display tab"""
        matches_frame = ttk.Frame(self.notebook)
        self.notebook.add(matches_frame, text="Matches")
        
        # Treeview for matches
        columns = ("Confidence", "Work Order", "Email Item", "Amount Diff", "Evidence")
        self.matches_tree = ttk.Treeview(matches_frame, columns=columns, show="headings", height=10)
        
        # Configure columns
        self.matches_tree.heading("Confidence", text="Confidence")
        self.matches_tree.heading("Work Order", text="Work Order")  
        self.matches_tree.heading("Email Item", text="Email Item")
        self.matches_tree.heading("Amount Diff", text="Amount Diff")
        self.matches_tree.heading("Evidence", text="Evidence")
        
        self.matches_tree.column("Confidence", width=100, anchor=tk.CENTER)
        self.matches_tree.column("Work Order", width=100, anchor=tk.CENTER)
        self.matches_tree.column("Email Item", width=300, anchor=tk.W)
        self.matches_tree.column("Amount Diff", width=100, anchor=tk.CENTER) 
        self.matches_tree.column("Evidence", width=200, anchor=tk.W)
        
        # Scrollbar for matches tree
        matches_scrollbar = ttk.Scrollbar(matches_frame, orient=tk.VERTICAL, command=self.matches_tree.yview)
        self.matches_tree.configure(yscrollcommand=matches_scrollbar.set)
        
        # Grid the matches tree and scrollbar
        self.matches_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        matches_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights for matches frame
        matches_frame.grid_columnconfigure(0, weight=1)
        matches_frame.grid_rowconfigure(0, weight=1)
        
        # Bind double-click for details
        self.matches_tree.bind("<Double-1>", self._on_match_double_click)
        
    def _create_unmatched_tab(self):
        """Create the unmatched items tab"""
        unmatched_frame = ttk.Frame(self.notebook)
        self.notebook.add(unmatched_frame, text="Unmatched")
        
        # Label
        ttk.Label(
            unmatched_frame, 
            text="Items that could not be matched with sufficient confidence:",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(0, 10))
        
        # Listbox for unmatched items
        self.unmatched_listbox = tk.Listbox(
            unmatched_frame,
            height=10,
            font=("Segoe UI", 10),
            selectmode=tk.EXTENDED
        )
        
        # Scrollbar for unmatched listbox
        unmatched_scrollbar = ttk.Scrollbar(unmatched_frame, orient=tk.VERTICAL, command=self.unmatched_listbox.yview)
        self.unmatched_listbox.configure(yscrollcommand=unmatched_scrollbar.set)
        
        # Pack unmatched components
        self.unmatched_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        unmatched_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _create_details_tab(self):
        """Create the detailed analysis tab"""
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="Analysis Details")
        
        # Text area for detailed information
        self.details_text = tk.Text(
            details_frame,
            height=15,
            width=80,
            font=("Consolas", 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        
        # Scrollbar for details
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        # Grid details components
        self.details_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        details_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_rowconfigure(0, weight=1)
        
    def display_results(self, results: MatchingResult):
        """Display matching results"""
        self.current_results = results
        
        # Update summary
        if results.success:
            summary_text = f"{results.total_match_count} matches found, {results.unmatched_count} unmatched"
            if results.high_confidence_matches:
                summary_text += f" • {len(results.high_confidence_matches)} high confidence"
            if results.medium_confidence_matches:
                summary_text += f" • {len(results.medium_confidence_matches)} need review"
        else:
            summary_text = f"Analysis failed: {results.error}"
            
        self.summary_label.config(text=summary_text)
        
        # Populate matches
        self._populate_matches_tree(results.matches)
        
        # Populate unmatched items
        self._populate_unmatched_list(results.unmatched_items)
        
        # Populate analysis details
        self._populate_details_text(results)
        
        # Enable buttons
        self.export_button.config(state="normal" if results.success else "disabled")
        self.clear_button.config(state="normal")
        
    def _populate_matches_tree(self, matches: List[Match]):
        """Populate the matches treeview"""
        # Clear existing items
        for item in self.matches_tree.get_children():
            self.matches_tree.delete(item)
            
        # Add matches
        for match in matches:
            # Format confidence with level indicator
            confidence_text = f"{match.confidence}% ({match.confidence_level})"
            
            # Format amount difference
            if match.amount_comparison.is_exact_match:
                amount_diff = "Exact"
            else:
                diff = match.amount_comparison.difference
                percent = match.amount_comparison.percentage_difference
                amount_diff = f"${abs(diff):.2f} ({percent:.1f}%)"
            
            # Truncate evidence for display
            evidence = match.evidence.score_breakdown[:50] + "..." if len(match.evidence.score_breakdown) > 50 else match.evidence.score_breakdown
            
            # Truncate email item for display
            email_item = match.email_item[:60] + "..." if len(match.email_item) > 60 else match.email_item
            
            # Insert item
            item_id = self.matches_tree.insert("", tk.END, values=(
                confidence_text,
                match.work_order_id,
                email_item,
                amount_diff,
                evidence
            ))
            
            # Set row color based on confidence
            self.matches_tree.set(item_id, "Confidence", confidence_text)
            
            # Color coding based on confidence level
            if match.confidence >= 85:
                self.matches_tree.item(item_id, tags=("high_confidence",))
            elif match.confidence >= 70:
                self.matches_tree.item(item_id, tags=("good_confidence",))
            elif match.confidence >= 50:
                self.matches_tree.item(item_id, tags=("medium_confidence",))
            else:
                self.matches_tree.item(item_id, tags=("low_confidence",))
        
        # Configure row colors
        self.matches_tree.tag_configure("high_confidence", background="#e8f5e8")
        self.matches_tree.tag_configure("good_confidence", background="#f0f8f0") 
        self.matches_tree.tag_configure("medium_confidence", background="#fff8dc")
        self.matches_tree.tag_configure("low_confidence", background="#ffe4e1")
        
    def _populate_unmatched_list(self, unmatched_items: List[str]):
        """Populate the unmatched items listbox"""
        # Clear existing items
        self.unmatched_listbox.delete(0, tk.END)
        
        # Add unmatched items
        for item in unmatched_items:
            # Truncate long items
            display_item = item[:100] + "..." if len(item) > 100 else item
            self.unmatched_listbox.insert(tk.END, display_item)
    
    def _populate_details_text(self, results: MatchingResult):
        """Populate the detailed analysis text"""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        
        # Analysis summary
        details = f"WORK ORDER MATCHING ANALYSIS\n"
        details += f"{'=' * 40}\n\n"
        
        if results.success:
            details += f"Status: ✅ Analysis Successful\n"
            details += f"Summary: {results.summary}\n\n"
            
            details += f"MATCH BREAKDOWN:\n"
            details += f"• Total matches: {results.total_match_count}\n"
            details += f"• High confidence (≥70%): {len(results.high_confidence_matches)}\n"
            details += f"• Medium confidence (50-69%): {len(results.medium_confidence_matches)}\n"
            details += f"• Unmatched items: {results.unmatched_count}\n\n"
            
            # Detailed match information
            details += f"DETAILED MATCHES:\n"
            details += f"{'-' * 20}\n\n"
            
            for i, match in enumerate(results.matches, 1):
                details += f"Match #{i}: {match.work_order_id}\n"
                details += f"Confidence: {match.confidence}% ({match.confidence_level})\n"
                details += f"Email Item: {match.email_item[:100]}...\n" if len(match.email_item) > 100 else f"Email Item: {match.email_item}\n"
                details += f"Evidence: {match.evidence.score_breakdown}\n"
                
                if match.evidence.primary_signals:
                    details += f"Primary signals: {', '.join(match.evidence.primary_signals)}\n"
                if match.evidence.supporting_signals:
                    details += f"Supporting signals: {', '.join(match.evidence.supporting_signals)}\n"
                
                details += f"Amount comparison: ${match.amount_comparison.email_amount} vs ${match.amount_comparison.wo_amount}\n"
                details += f"\n"
                
        else:
            details += f"Status: ❌ Analysis Failed\n"
            details += f"Error: {results.error}\n\n"
            
            if results.raw_response:
                details += f"RAW RESPONSE:\n"
                details += f"{'-' * 15}\n"
                details += f"{results.raw_response[:500]}...\n\n" if len(results.raw_response) > 500 else f"{results.raw_response}\n\n"
        
        self.details_text.insert("1.0", details)
        self.details_text.config(state=tk.DISABLED)
        
    def _on_match_double_click(self, event):
        """Handle double-click on match item"""
        selection = self.matches_tree.selection()
        if not selection or not self.current_results:
            return
            
        # Get selected match
        item_index = self.matches_tree.index(selection[0])
        if item_index < len(self.current_results.matches):
            match = self.current_results.matches[item_index]
            self._show_match_details(match)
    
    def _show_match_details(self, match: Match):
        """Show detailed information for a specific match"""
        details = f"Match Details: {match.work_order_id}\n"
        details += f"{'=' * 40}\n\n"
        details += f"Confidence: {match.confidence}% ({match.confidence_level})\n"
        details += f"Work Order ID: {match.work_order_id}\n\n"
        details += f"Email Item:\n{match.email_item}\n\n"
        details += f"Evidence Breakdown:\n{match.evidence.score_breakdown}\n\n"
        
        if match.evidence.primary_signals:
            details += f"Primary Signals:\n"
            for signal in match.evidence.primary_signals:
                details += f"  • {signal}\n"
            details += "\n"
            
        if match.evidence.supporting_signals:
            details += f"Supporting Signals:\n"
            for signal in match.evidence.supporting_signals:
                details += f"  • {signal}\n"
            details += "\n"
        
        details += f"Amount Analysis:\n"
        details += f"  Email Amount: ${match.amount_comparison.email_amount:.2f}\n"
        details += f"  Work Order Amount: ${match.amount_comparison.wo_amount:.2f}\n"
        details += f"  Difference: ${match.amount_comparison.difference:.2f}\n"
        details += f"  Percentage Diff: {match.amount_comparison.percentage_difference:.1f}%\n"
        details += f"  Match Type: {'Exact' if match.amount_comparison.is_exact_match else 'Close' if match.amount_comparison.is_close_match else 'Different'}\n"
        
        if match.work_order:
            details += f"\nWork Order Details:\n"
            details += f"  Location: {match.work_order.location}\n"
            details += f"  Description: {match.work_order.description}\n"
        
        # Show in message dialog
        messagebox.showinfo("Match Details", details)
    
    def _export_results(self):
        """Export results to CSV file"""
        if not self.current_results or not self.current_results.success:
            messagebox.showwarning("Export Error", "No successful results to export")
            return
            
        # Get filename from user
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"wo_matching_results_{timestamp}.csv"
        
        filename = filedialog.asksaveasfilename(
            title="Export Matching Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialname=default_filename
        )
        
        if not filename:
            return
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    "Work_Order_ID", "Confidence_Percent", "Confidence_Level",
                    "Email_Item", "Email_Amount", "WO_Amount", "Amount_Difference",
                    "Score_Breakdown", "Primary_Signals", "Supporting_Signals"
                ])
                
                # Write matches
                for match in self.current_results.matches:
                    writer.writerow([
                        match.work_order_id,
                        match.confidence,
                        match.confidence_level,
                        match.email_item,
                        match.amount_comparison.email_amount,
                        match.amount_comparison.wo_amount,
                        match.amount_comparison.difference,
                        match.evidence.score_breakdown,
                        "; ".join(match.evidence.primary_signals),
                        "; ".join(match.evidence.supporting_signals)
                    ])
                
                # Write unmatched items section
                if self.current_results.unmatched_items:
                    writer.writerow([])  # Empty row
                    writer.writerow(["UNMATCHED_ITEMS"])
                    for item in self.current_results.unmatched_items:
                        writer.writerow([item])
            
            messagebox.showinfo("Export Complete", f"Results exported to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")
    
    def _clear_results(self):
        """Clear all results"""
        self.current_results = None
        
        # Clear summary
        self.summary_label.config(text="No analysis run yet")
        
        # Clear matches tree
        for item in self.matches_tree.get_children():
            self.matches_tree.delete(item)
        
        # Clear unmatched list
        self.unmatched_listbox.delete(0, tk.END)
        
        # Clear details
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        self.details_text.config(state=tk.DISABLED)
        
        # Disable buttons
        self.export_button.config(state="disabled")
        self.clear_button.config(state="disabled")
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame"""
        self.frame.grid(**kwargs) 