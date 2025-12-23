#!/usr/bin/env python3
"""
Cloud Pricing Monitor - Python Desktop UI

A tkinter-based desktop application for monitoring cloud GPU/CPU pricing
across top 10 cloud providers. Allows setting price thresholds and
launching instances when prices drop below target.

Usage:
    python pricing_monitor_ui.py
"""

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Dict, List, Optional, Any

from cloud_pricing_monitor import (
    CloudPricingMonitor,
    InstanceType,
    CloudProvider,
    PriceThreshold,
    InstancePrice
)


class PricingMonitorApp:
    """Desktop UI for Cloud Pricing Monitor"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("☁️ Cloud Pricing Monitor")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Set dark theme colors
        self.colors = {
            "bg": "#1a1a2e",
            "fg": "#e0e0e0",
            "accent": "#00d9ff",
            "success": "#00ff88",
            "warning": "#ffaa00",
            "danger": "#ff4444",
            "card_bg": "#16213e",
            "entry_bg": "#0f0f1a",
            "border": "#333355"
        }
        
        self.root.configure(bg=self.colors["bg"])
        
        # Initialize monitor
        self.monitor = CloudPricingMonitor(check_interval=30)
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.async_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Activity log
        self.activity_log: List[str] = []
        
        # Build UI
        self._setup_styles()
        self._build_ui()
        
        # Initial price fetch
        self._refresh_prices()
    
    def _setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure colors
        style.configure(".", 
                       background=self.colors["bg"],
                       foreground=self.colors["fg"],
                       fieldbackground=self.colors["entry_bg"])
        
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["card_bg"])
        
        style.configure("TLabel", 
                       background=self.colors["bg"],
                       foreground=self.colors["fg"],
                       font=("Helvetica", 10))
        
        style.configure("Title.TLabel",
                       font=("Helvetica", 24, "bold"),
                       foreground=self.colors["accent"])
        
        style.configure("Subtitle.TLabel",
                       font=("Helvetica", 12),
                       foreground="#888888")
        
        style.configure("Header.TLabel",
                       font=("Helvetica", 14, "bold"),
                       foreground=self.colors["accent"])
        
        style.configure("Price.TLabel",
                       font=("Helvetica", 16, "bold"),
                       foreground=self.colors["success"])
        
        style.configure("Provider.TLabel",
                       font=("Helvetica", 11, "bold"),
                       foreground=self.colors["fg"])
        
        style.configure("Specs.TLabel",
                       font=("Helvetica", 9),
                       foreground="#888888")
        
        style.configure("Status.TLabel",
                       font=("Helvetica", 10))
        
        # Button styles
        style.configure("TButton",
                       font=("Helvetica", 10, "bold"),
                       padding=(15, 8))
        
        style.configure("Primary.TButton",
                       background=self.colors["accent"],
                       foreground="#000000")
        
        style.configure("Success.TButton",
                       background=self.colors["success"],
                       foreground="#000000")
        
        style.configure("Danger.TButton",
                       background=self.colors["danger"],
                       foreground="#ffffff")
        
        # Entry style
        style.configure("TEntry",
                       fieldbackground=self.colors["entry_bg"],
                       foreground=self.colors["fg"],
                       insertcolor=self.colors["fg"])
        
        # Notebook (tabs) style
        style.configure("TNotebook",
                       background=self.colors["bg"],
                       borderwidth=0)
        
        style.configure("TNotebook.Tab",
                       background=self.colors["card_bg"],
                       foreground=self.colors["fg"],
                       padding=(20, 10),
                       font=("Helvetica", 10, "bold"))
        
        style.map("TNotebook.Tab",
                 background=[("selected", self.colors["accent"])],
                 foreground=[("selected", "#000000")])
    
    def _build_ui(self):
        """Build the main UI components"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self._build_header(main_frame)
        
        # Status bar
        self._build_status_bar(main_frame)
        
        # Threshold controls
        self._build_threshold_section(main_frame)
        
        # Price display tabs
        self._build_price_tabs(main_frame)
        
        # Activity log
        self._build_activity_log(main_frame)
    
    def _build_header(self, parent):
        """Build header section"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, 
                 text="☁️ Cloud Pricing Monitor",
                 style="Title.TLabel").pack(side=tk.LEFT)
        
        ttk.Label(header_frame,
                 text="Monitor GPU & CPU pricing across top 10 cloud providers",
                 style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(20, 0))
    
    def _build_status_bar(self, parent):
        """Build status bar with controls"""
        status_frame = ttk.Frame(parent, style="Card.TFrame", padding=15)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status indicator
        status_left = ttk.Frame(status_frame, style="Card.TFrame")
        status_left.pack(side=tk.LEFT)
        
        self.status_canvas = tk.Canvas(status_left, width=12, height=12,
                                       bg=self.colors["card_bg"], highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=(0, 8))
        self.status_dot = self.status_canvas.create_oval(2, 2, 10, 10, 
                                                         fill=self.colors["danger"])
        
        self.status_label = ttk.Label(status_left, text="Monitor Stopped",
                                      style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        # Stats
        stats_frame = ttk.Frame(status_frame, style="Card.TFrame")
        stats_frame.pack(side=tk.LEFT, padx=40)
        
        ttk.Label(stats_frame, text="Last Check:", 
                 style="Status.TLabel").pack(side=tk.LEFT)
        self.last_check_label = ttk.Label(stats_frame, text="Never",
                                          foreground=self.colors["accent"],
                                          style="Status.TLabel")
        self.last_check_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(stats_frame, text="Total Checks:",
                 style="Status.TLabel").pack(side=tk.LEFT)
        self.total_checks_label = ttk.Label(stats_frame, text="0",
                                            foreground=self.colors["accent"],
                                            style="Status.TLabel")
        self.total_checks_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(stats_frame, text="Launches:",
                 style="Status.TLabel").pack(side=tk.LEFT)
        self.launches_label = ttk.Label(stats_frame, text="0",
                                        foreground=self.colors["accent"],
                                        style="Status.TLabel")
        self.launches_label.pack(side=tk.LEFT)
        
        # Control buttons
        btn_frame = ttk.Frame(status_frame, style="Card.TFrame")
        btn_frame.pack(side=tk.RIGHT)
        
        self.start_btn = tk.Button(btn_frame, text="▶ Start Monitor",
                                   command=self._start_monitor,
                                   bg=self.colors["success"],
                                   fg="#000000",
                                   font=("Helvetica", 10, "bold"),
                                   padx=15, pady=5, relief=tk.FLAT)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⬛ Stop Monitor",
                                  command=self._stop_monitor,
                                  bg=self.colors["danger"],
                                  fg="#ffffff",
                                  font=("Helvetica", 10, "bold"),
                                  padx=15, pady=5, relief=tk.FLAT,
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = tk.Button(btn_frame, text="🔄 Refresh",
                                     command=self._refresh_prices,
                                     bg=self.colors["accent"],
                                     fg="#000000",
                                     font=("Helvetica", 10, "bold"),
                                     padx=15, pady=5, relief=tk.FLAT)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
    
    def _build_threshold_section(self, parent):
        """Build threshold configuration section"""
        threshold_frame = ttk.Frame(parent)
        threshold_frame.pack(fill=tk.X, pady=(0, 20))
        
        # GPU threshold
        gpu_frame = ttk.Frame(threshold_frame, style="Card.TFrame", padding=20)
        gpu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(gpu_frame, text="🎮 GPU Instance Threshold",
                 style="Header.TLabel").pack(anchor=tk.W)
        
        ttk.Label(gpu_frame, text="Maximum Price ($/hour):",
                 style="Status.TLabel").pack(anchor=tk.W, pady=(15, 5))
        
        self.gpu_threshold_var = tk.StringVar(value="2.00")
        gpu_entry = ttk.Entry(gpu_frame, textvariable=self.gpu_threshold_var,
                             font=("Helvetica", 12), width=15)
        gpu_entry.pack(anchor=tk.W)
        
        self.gpu_auto_var = tk.BooleanVar(value=False)
        gpu_auto_cb = tk.Checkbutton(gpu_frame, 
                                     text="Auto-launch when price drops below threshold",
                                     variable=self.gpu_auto_var,
                                     bg=self.colors["card_bg"],
                                     fg=self.colors["fg"],
                                     selectcolor=self.colors["entry_bg"],
                                     activebackground=self.colors["card_bg"],
                                     activeforeground=self.colors["fg"],
                                     font=("Helvetica", 9))
        gpu_auto_cb.pack(anchor=tk.W, pady=(10, 10))
        
        tk.Button(gpu_frame, text="Set GPU Threshold",
                 command=lambda: self._set_threshold("gpu"),
                 bg=self.colors["accent"],
                 fg="#000000",
                 font=("Helvetica", 10, "bold"),
                 padx=15, pady=5, relief=tk.FLAT).pack(anchor=tk.W)
        
        self.gpu_cheapest_label = ttk.Label(gpu_frame, text="$--.--",
                                            style="Price.TLabel")
        self.gpu_cheapest_label.pack(anchor=tk.W, pady=(15, 0))
        ttk.Label(gpu_frame, text="$/hr cheapest",
                 style="Specs.TLabel").pack(anchor=tk.W)
        
        # CPU threshold
        cpu_frame = ttk.Frame(threshold_frame, style="Card.TFrame", padding=20)
        cpu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        ttk.Label(cpu_frame, text="💻 CPU Instance Threshold",
                 style="Header.TLabel").pack(anchor=tk.W)
        
        ttk.Label(cpu_frame, text="Maximum Price ($/hour):",
                 style="Status.TLabel").pack(anchor=tk.W, pady=(15, 5))
        
        self.cpu_threshold_var = tk.StringVar(value="0.30")
        cpu_entry = ttk.Entry(cpu_frame, textvariable=self.cpu_threshold_var,
                             font=("Helvetica", 12), width=15)
        cpu_entry.pack(anchor=tk.W)
        
        self.cpu_auto_var = tk.BooleanVar(value=False)
        cpu_auto_cb = tk.Checkbutton(cpu_frame,
                                     text="Auto-launch when price drops below threshold",
                                     variable=self.cpu_auto_var,
                                     bg=self.colors["card_bg"],
                                     fg=self.colors["fg"],
                                     selectcolor=self.colors["entry_bg"],
                                     activebackground=self.colors["card_bg"],
                                     activeforeground=self.colors["fg"],
                                     font=("Helvetica", 9))
        cpu_auto_cb.pack(anchor=tk.W, pady=(10, 10))
        
        tk.Button(cpu_frame, text="Set CPU Threshold",
                 command=lambda: self._set_threshold("cpu"),
                 bg=self.colors["accent"],
                 fg="#000000",
                 font=("Helvetica", 10, "bold"),
                 padx=15, pady=5, relief=tk.FLAT).pack(anchor=tk.W)
        
        self.cpu_cheapest_label = ttk.Label(cpu_frame, text="$--.--",
                                            style="Price.TLabel")
        self.cpu_cheapest_label.pack(anchor=tk.W, pady=(15, 0))
        ttk.Label(cpu_frame, text="$/hr cheapest",
                 style="Specs.TLabel").pack(anchor=tk.W)
    
    def _build_price_tabs(self, parent):
        """Build tabbed price display"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # GPU prices tab
        self.gpu_frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.gpu_frame, text="  GPU Instances  ")
        
        # Scrollable frame for GPU prices
        self.gpu_canvas = tk.Canvas(self.gpu_frame, bg=self.colors["bg"],
                                   highlightthickness=0)
        gpu_scrollbar = ttk.Scrollbar(self.gpu_frame, orient=tk.VERTICAL,
                                      command=self.gpu_canvas.yview)
        self.gpu_scroll_frame = ttk.Frame(self.gpu_canvas)
        
        self.gpu_scroll_frame.bind("<Configure>",
            lambda e: self.gpu_canvas.configure(scrollregion=self.gpu_canvas.bbox("all")))
        
        self.gpu_canvas.create_window((0, 0), window=self.gpu_scroll_frame, anchor=tk.NW)
        self.gpu_canvas.configure(yscrollcommand=gpu_scrollbar.set)
        
        self.gpu_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        gpu_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # CPU prices tab
        self.cpu_frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.cpu_frame, text="  CPU Instances  ")
        
        # Scrollable frame for CPU prices
        self.cpu_canvas = tk.Canvas(self.cpu_frame, bg=self.colors["bg"],
                                   highlightthickness=0)
        cpu_scrollbar = ttk.Scrollbar(self.cpu_frame, orient=tk.VERTICAL,
                                      command=self.cpu_canvas.yview)
        self.cpu_scroll_frame = ttk.Frame(self.cpu_canvas)
        
        self.cpu_scroll_frame.bind("<Configure>",
            lambda e: self.cpu_canvas.configure(scrollregion=self.cpu_canvas.bbox("all")))
        
        self.cpu_canvas.create_window((0, 0), window=self.cpu_scroll_frame, anchor=tk.NW)
        self.cpu_canvas.configure(yscrollcommand=cpu_scrollbar.set)
        
        self.cpu_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cpu_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _build_activity_log(self, parent):
        """Build activity log section"""
        log_frame = ttk.Frame(parent, style="Card.TFrame", padding=15)
        log_frame.pack(fill=tk.X)
        
        ttk.Label(log_frame, text="📋 Activity Log",
                 style="Header.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.log_text = tk.Text(log_frame, height=6, 
                               bg=self.colors["entry_bg"],
                               fg=self.colors["fg"],
                               font=("Courier", 9),
                               relief=tk.FLAT,
                               state=tk.DISABLED)
        self.log_text.pack(fill=tk.X)
        
        self._add_log("Cloud Pricing Monitor UI loaded")
    
    def _add_log(self, message: str, level: str = "info"):
        """Add a message to the activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "info": self.colors["fg"],
            "success": self.colors["success"],
            "warning": self.colors["warning"],
            "error": self.colors["danger"]
        }
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert("1.0", f"[{timestamp}] {message}\n")
        self.log_text.configure(state=tk.DISABLED)
    
    def _refresh_prices(self):
        """Refresh prices from monitor"""
        def fetch():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.monitor.fetch_all_prices())
            loop.close()
            self.root.after(0, self._update_price_display)
        
        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()
        self._add_log("Refreshing prices...")
    
    def _update_price_display(self):
        """Update the price display with current prices"""
        # Clear existing price cards
        for widget in self.gpu_scroll_frame.winfo_children():
            widget.destroy()
        for widget in self.cpu_scroll_frame.winfo_children():
            widget.destroy()
        
        # Get threshold values
        try:
            gpu_threshold = float(self.gpu_threshold_var.get())
        except ValueError:
            gpu_threshold = None
        
        try:
            cpu_threshold = float(self.cpu_threshold_var.get())
        except ValueError:
            cpu_threshold = None
        
        # Get prices sorted by cost
        gpu_prices = sorted(
            self.monitor.get_prices_by_type(InstanceType.GPU),
            key=lambda p: p.price_per_hour
        )
        cpu_prices = sorted(
            self.monitor.get_prices_by_type(InstanceType.CPU),
            key=lambda p: p.price_per_hour
        )
        
        # Update cheapest labels
        if gpu_prices:
            self.gpu_cheapest_label.configure(
                text=f"${gpu_prices[0].price_per_hour:.4f}"
            )
        if cpu_prices:
            self.cpu_cheapest_label.configure(
                text=f"${cpu_prices[0].price_per_hour:.4f}"
            )
        
        # Create price cards
        self._create_price_cards(self.gpu_scroll_frame, gpu_prices, 
                                gpu_threshold, is_cheapest_first=True)
        self._create_price_cards(self.cpu_scroll_frame, cpu_prices,
                                cpu_threshold, is_cheapest_first=True)
        
        # Update status
        status = self.monitor.get_status()
        self.total_checks_label.configure(text=str(status["total_checks"]))
        self.launches_label.configure(text=str(status["launches_triggered"]))
        
        if status["last_check"]:
            self.last_check_label.configure(
                text=datetime.fromisoformat(status["last_check"]).strftime("%H:%M:%S")
            )
        
        self._add_log("Prices updated", "success")
    
    def _create_price_cards(self, parent, prices: List[InstancePrice], 
                           threshold: Optional[float], is_cheapest_first: bool):
        """Create price cards for a list of prices"""
        # Create a grid frame
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        for i, price in enumerate(prices):
            row = i // 4
            col = i % 4
            
            is_cheapest = (i == 0 and is_cheapest_first)
            is_below_threshold = (threshold is not None and 
                                 price.price_per_hour <= threshold)
            
            card = self._create_price_card(grid_frame, price, 
                                          is_cheapest, is_below_threshold)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Configure grid weights
        for col in range(4):
            grid_frame.columnconfigure(col, weight=1)
    
    def _create_price_card(self, parent, price: InstancePrice,
                          is_cheapest: bool, is_below_threshold: bool) -> ttk.Frame:
        """Create a single price card"""
        # Determine border color
        if is_cheapest:
            border_color = self.colors["success"]
        elif is_below_threshold:
            border_color = self.colors["warning"]
        else:
            border_color = self.colors["border"]
        
        # Card frame with border
        card_outer = tk.Frame(parent, bg=border_color, padx=2, pady=2)
        card = tk.Frame(card_outer, bg=self.colors["card_bg"], padx=15, pady=12)
        card.pack(fill=tk.BOTH, expand=True)
        
        # Header with provider and badge
        header = tk.Frame(card, bg=self.colors["card_bg"])
        header.pack(fill=tk.X)
        
        provider_label = tk.Label(header, text=price.provider.value.upper(),
                                 bg=self.colors["card_bg"],
                                 fg=self.colors["fg"],
                                 font=("Helvetica", 11, "bold"))
        provider_label.pack(side=tk.LEFT)
        
        if is_cheapest:
            badge = tk.Label(header, text="CHEAPEST",
                           bg=self.colors["success"],
                           fg="#000000",
                           font=("Helvetica", 8, "bold"),
                           padx=5, pady=2)
            badge.pack(side=tk.RIGHT)
        elif is_below_threshold:
            badge = tk.Label(header, text="BELOW THRESHOLD",
                           bg=self.colors["warning"],
                           fg="#000000",
                           font=("Helvetica", 8, "bold"),
                           padx=5, pady=2)
            badge.pack(side=tk.RIGHT)
        
        # Instance name
        tk.Label(card, text=price.instance_name,
                bg=self.colors["card_bg"],
                fg="#888888",
                font=("Helvetica", 9)).pack(anchor=tk.W, pady=(5, 0))
        
        # Price
        tk.Label(card, text=f"${price.price_per_hour:.4f}/hr",
                bg=self.colors["card_bg"],
                fg=self.colors["accent"],
                font=("Helvetica", 16, "bold")).pack(anchor=tk.W, pady=(5, 0))
        
        # Specs
        specs_frame = tk.Frame(card, bg=self.colors["card_bg"])
        specs_frame.pack(fill=tk.X, pady=(8, 0))
        
        specs = price.specs
        if specs.get("gpu"):
            tk.Label(specs_frame, text=specs["gpu"],
                    bg="#2a2a4a", fg="#888888",
                    font=("Helvetica", 8),
                    padx=5, pady=2).pack(side=tk.LEFT, padx=(0, 5))
        if specs.get("vcpu"):
            tk.Label(specs_frame, text=f"{specs['vcpu']} vCPU",
                    bg="#2a2a4a", fg="#888888",
                    font=("Helvetica", 8),
                    padx=5, pady=2).pack(side=tk.LEFT, padx=(0, 5))
        if specs.get("ram_gb"):
            tk.Label(specs_frame, text=f"{specs['ram_gb']} GB RAM",
                    bg="#2a2a4a", fg="#888888",
                    font=("Helvetica", 8),
                    padx=5, pady=2).pack(side=tk.LEFT)
        
        # Launch button
        launch_btn = tk.Button(card, text="🚀 Launch Instance",
                              command=lambda p=price: self._launch_instance(p),
                              bg=self.colors["accent"],
                              fg="#000000",
                              font=("Helvetica", 9, "bold"),
                              padx=10, pady=5,
                              relief=tk.FLAT)
        launch_btn.pack(fill=tk.X, pady=(10, 0))
        
        return card_outer
    
    def _set_threshold(self, instance_type: str):
        """Set price threshold for instance type"""
        try:
            if instance_type == "gpu":
                max_price = float(self.gpu_threshold_var.get())
                auto_launch = self.gpu_auto_var.get()
                it = InstanceType.GPU
            else:
                max_price = float(self.cpu_threshold_var.get())
                auto_launch = self.cpu_auto_var.get()
                it = InstanceType.CPU
            
            threshold = PriceThreshold(
                instance_type=it,
                max_price=max_price,
                auto_launch=auto_launch
            )
            self.monitor.set_threshold(threshold)
            
            self._add_log(
                f"{instance_type.upper()} threshold set to ${max_price}/hr"
                f"{' (auto-launch enabled)' if auto_launch else ''}",
                "success"
            )
            
            # Refresh display to show threshold badges
            self._update_price_display()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid price value")
    
    def _launch_instance(self, price: InstancePrice):
        """Launch an instance"""
        if not messagebox.askyesno("Confirm Launch",
            f"Launch {price.instance_type.value.upper()} instance on "
            f"{price.provider.value.upper()}?\n\n"
            f"Instance: {price.instance_name}\n"
            f"Price: ${price.price_per_hour:.4f}/hr"):
            return
        
        def launch():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.monitor.launch_instance(price))
            loop.close()
            
            self.root.after(0, lambda: self._handle_launch_result(result))
        
        thread = threading.Thread(target=launch, daemon=True)
        thread.start()
        self._add_log(f"Launching {price.provider.value} {price.instance_name}...")
    
    def _handle_launch_result(self, result: Dict[str, Any]):
        """Handle launch result"""
        if result.get("success"):
            self._add_log(
                f"✅ Instance launched: {result['instance_id']} on {result['provider']}",
                "success"
            )
            messagebox.showinfo("Launch Successful",
                f"Instance launched successfully!\n\n"
                f"Instance ID: {result['instance_id']}\n"
                f"Provider: {result['provider']}\n"
                f"Price: ${result['price_per_hour']:.4f}/hr")
        else:
            self._add_log(f"❌ Launch failed: {result.get('error', 'Unknown error')}", "error")
            messagebox.showerror("Launch Failed", result.get("error", "Unknown error"))
        
        # Update stats
        self.launches_label.configure(text=str(self.monitor.status.launches_triggered))
    
    def _start_monitor(self):
        """Start the pricing monitor"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.status_canvas.itemconfig(self.status_dot, fill=self.colors["success"])
        self.status_label.configure(text="Monitor Running")
        
        def run_monitor():
            self.async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.async_loop)
            
            async def monitor_loop():
                self.monitor.status.is_running = True
                while self.is_monitoring:
                    await self.monitor.fetch_all_prices()
                    self.monitor.status.last_check = datetime.utcnow()
                    self.monitor.status.total_checks += 1
                    
                    # Update UI
                    self.root.after(0, self._update_price_display)
                    
                    # Check thresholds for auto-launch
                    matches = self.monitor.check_thresholds()
                    for price in matches:
                        threshold = self.monitor.thresholds.get(price.instance_type)
                        if threshold and threshold.auto_launch:
                            result = await self.monitor.launch_instance(price)
                            threshold.auto_launch = False
                            self.root.after(0, lambda r=result: self._handle_launch_result(r))
                    
                    await asyncio.sleep(self.monitor.check_interval)
            
            self.async_loop.run_until_complete(monitor_loop())
        
        self.monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        self.monitor_thread.start()
        
        self._add_log("Monitor started (checking every 30 seconds)", "success")
    
    def _stop_monitor(self):
        """Stop the pricing monitor"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.monitor.status.is_running = False
        
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_canvas.itemconfig(self.status_dot, fill=self.colors["danger"])
        self.status_label.configure(text="Monitor Stopped")
        
        self._add_log("Monitor stopped", "warning")
    
    def on_closing(self):
        """Handle window close"""
        self._stop_monitor()
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = PricingMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
