"""
Service Monitor GUI - Main application window
"""

import customtkinter as ctk
from tkinter import ttk
import threading
import asyncio
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from service_monitor import ServiceMonitor, ServiceStatus
from alert_manager import AlertManager, AlertType


# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ServiceMonitorGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Service Monitor")
        self.window.geometry("1200x800")
        
        # Initialize monitoring
        self.monitor = ServiceMonitor()
        self.alert_manager = AlertManager(self.monitor.config)
        
        # Register status change callback
        self.monitor.register_callback(self.on_status_change)
        
        # UI components
        self.status_indicators = {}
        self.selected_service = None
        
        # Create UI
        self._create_ui()
        
        # Start monitoring in background thread
        self.monitor_thread = threading.Thread(target=self._run_monitor, daemon=True)
        self.monitor_thread.start()
        
        # Start UI update loop
        self.window.after(1000, self._update_ui)
    
    def _create_ui(self):
        """Create the user interface"""
        # Create notebook (tabs)
        self.notebook = ctk.CTkTabview(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.notebook.add("Dashboard")
        self.notebook.add("Details")
        
        # Create dashboard tab
        self._create_dashboard_tab()
        
        # Create details tab
        self._create_details_tab()
    
    def _create_dashboard_tab(self):
        """Create dashboard with status indicators"""
        dashboard = self.notebook.tab("Dashboard")
        
        # Title
        title = ctk.CTkLabel(
            dashboard,
            text="Service Status Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # Legend
        legend_frame = ctk.CTkFrame(dashboard)
        legend_frame.pack(pady=10)
        
        ctk.CTkLabel(
            legend_frame,
            text="Status Legend:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)
        
        # Green indicator
        green_canvas = ctk.CTkCanvas(legend_frame, width=20, height=20, bg="#2b2b2b", highlightthickness=0)
        green_canvas.pack(side="left", padx=5)
        green_canvas.create_oval(2, 2, 18, 18, fill="#00ff00", outline="")
        ctk.CTkLabel(
            legend_frame,
            text="Operational",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 15))
        
        # Yellow indicator
        yellow_canvas = ctk.CTkCanvas(legend_frame, width=20, height=20, bg="#2b2b2b", highlightthickness=0)
        yellow_canvas.pack(side="left", padx=5)
        yellow_canvas.create_oval(2, 2, 18, 18, fill="#ffff00", outline="")
        ctk.CTkLabel(
            legend_frame,
            text="Degraded (>1s)",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 15))
        
        # Red indicator
        red_canvas = ctk.CTkCanvas(legend_frame, width=20, height=20, bg="#2b2b2b", highlightthickness=0)
        red_canvas.pack(side="left", padx=5)
        red_canvas.create_oval(2, 2, 18, 18, fill="#ff0000", outline="")
        ctk.CTkLabel(
            legend_frame,
            text="Down/Failed",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))
        
        # Status indicators container
        self.indicators_frame = ctk.CTkScrollableFrame(dashboard)
        self.indicators_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create status indicators for each service
        services = self.monitor.config.get('services', [])
        for idx, service_config in enumerate(services):
            self._create_status_indicator(service_config['name'], idx)
    
    def _create_status_indicator(self, service_name: str, row: int):
        """Create a status indicator for a service"""
        frame = ctk.CTkFrame(self.indicators_frame)
        frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
        self.indicators_frame.grid_columnconfigure(0, weight=1)
        
        # Service name
        name_label = ctk.CTkLabel(
            frame,
            text=service_name,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        name_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Status light
        status_canvas = ctk.CTkCanvas(frame, width=50, height=50, bg="#2b2b2b", highlightthickness=0)
        status_canvas.grid(row=0, column=1, padx=20, pady=10)
        circle = status_canvas.create_oval(5, 5, 45, 45, fill="gray", outline="")
        
        # Status text
        status_label = ctk.CTkLabel(
            frame,
            text="Checking...",
            font=ctk.CTkFont(size=14)
        )
        status_label.grid(row=0, column=2, padx=20, pady=10, sticky="w")
        
        # Response time
        response_label = ctk.CTkLabel(
            frame,
            text="-- ms",
            font=ctk.CTkFont(size=12)
        )
        response_label.grid(row=0, column=3, padx=20, pady=10, sticky="w")
        
        # Last check time
        time_label = ctk.CTkLabel(
            frame,
            text="Never",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        time_label.grid(row=0, column=4, padx=20, pady=10, sticky="e")
        
        # View details button
        details_btn = ctk.CTkButton(
            frame,
            text="View Details",
            command=lambda: self._show_service_details(service_name),
            width=100
        )
        details_btn.grid(row=0, column=5, padx=20, pady=10)
        
        # Store references
        self.status_indicators[service_name] = {
            'canvas': status_canvas,
            'circle': circle,
            'status_label': status_label,
            'response_label': response_label,
            'time_label': time_label
        }
    
    def _create_details_tab(self):
        """Create details tab with graphs"""
        details = self.notebook.tab("Details")
        
        # Service selector
        selector_frame = ctk.CTkFrame(details)
        selector_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            selector_frame,
            text="Select Service:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=10)
        
        service_names = [s['name'] for s in self.monitor.config.get('services', [])]
        self.service_selector = ctk.CTkComboBox(
            selector_frame,
            values=service_names,
            command=self._on_service_selected,
            width=300
        )
        self.service_selector.pack(side="left", padx=10)
        
        if service_names:
            self.service_selector.set(service_names[0])
        
        # Graph container
        self.graph_frame = ctk.CTkFrame(details)
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create initial graph
        if service_names:
            self._show_service_details(service_names[0])
    
    def _on_service_selected(self, service_name: str):
        """Handle service selection"""
        self._show_service_details(service_name)
    
    def _show_service_details(self, service_name: str):
        """Show detailed graph for a service"""
        self.selected_service = service_name
        self.notebook.set("Details")
        self.service_selector.set(service_name)
        self._update_graph()
    
    def _update_graph(self):
        """Update the service detail graph"""
        if not self.selected_service:
            return
        
        # Clear existing graph
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        # Get service data
        service_data = self.monitor.get_service_data(self.selected_service)
        if not service_data or not service_data.history:
            # Show "waiting for data" message
            info_frame = ctk.CTkFrame(self.graph_frame)
            info_frame.pack(expand=True)
            
            ctk.CTkLabel(
                info_frame,
                text=f"Waiting for data from {self.selected_service}...",
                font=ctk.CTkFont(size=16)
            ).pack(pady=10)
            
            if service_data and service_data.last_check > 0:
                last_check = datetime.fromtimestamp(service_data.last_check)
                ctk.CTkLabel(
                    info_frame,
                    text=f"Last check: {last_check.strftime('%I:%M:%S %p')}",
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                ).pack()
            else:
                ctk.CTkLabel(
                    info_frame,
                    text="Monitoring will begin shortly...",
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                ).pack()
            return
        
        # Create matplotlib figure
        fig = Figure(figsize=(10, 6), facecolor='#2b2b2b')
        ax = fig.add_subplot(111)
        
        # Extract data
        timestamps = [datetime.fromtimestamp(check.timestamp) for check in service_data.history]
        response_times = [check.response_time * 1000 for check in service_data.history]  # Convert to ms
        statuses = [check.status for check in service_data.history]
        
        # Plot response time
        ax.plot(timestamps, response_times, color='#1f77b4', linewidth=2, label='Response Time')
        
        # Color background by status
        for i in range(len(timestamps) - 1):
            if statuses[i] == ServiceStatus.RED:
                ax.axvspan(timestamps[i], timestamps[i + 1], alpha=0.3, color='red')
            elif statuses[i] == ServiceStatus.YELLOW:
                ax.axvspan(timestamps[i], timestamps[i + 1], alpha=0.3, color='yellow')
        
        # Format plot with larger fonts
        ax.set_xlabel('Time', color='white', fontsize=16, weight='bold')
        ax.set_ylabel('Response Time (ms)', color='white', fontsize=16, weight='bold')
        ax.set_title(f'{self.selected_service} - 24 Hour History', color='white', fontsize=18, weight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=14, loc='upper left')
        
        # Format axes with larger tick labels
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.tick_params(colors='white', labelsize=14)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_color('#2b2b2b')
        ax.spines['right'].set_color('#2b2b2b')
        
        # Increase spine width for better visibility
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)
        
        fig.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def _update_ui(self):
        """Update UI with current service status"""
        for service_name, indicators in self.status_indicators.items():
            service_data = self.monitor.get_service_data(service_name)
            
            if service_data:
                # Update status light
                color_map = {
                    ServiceStatus.GREEN: "#00ff00",
                    ServiceStatus.YELLOW: "#ffff00",
                    ServiceStatus.RED: "#ff0000"
                }
                color = color_map.get(service_data.current_status, "gray")
                indicators['canvas'].itemconfig(indicators['circle'], fill=color)
                
                # Update status text
                indicators['status_label'].configure(
                    text=service_data.current_status.value.upper()
                )
                
                # Update response time
                if service_data.response_time > 0:
                    indicators['response_label'].configure(
                        text=f"{service_data.response_time * 1000:.0f} ms"
                    )
                
                # Update last check time
                if service_data.last_check > 0:
                    last_check = datetime.fromtimestamp(service_data.last_check)
                    time_ago = datetime.now() - last_check
                    if time_ago.seconds < 60:
                        time_str = f"{time_ago.seconds}s ago"
                    else:
                        time_str = f"{time_ago.seconds // 60}m ago"
                    indicators['time_label'].configure(text=time_str)
        
        # Only update graph every 5 seconds and if tab is active
        current_time = datetime.now()
        if not hasattr(self, '_last_graph_update'):
            self._last_graph_update = current_time
        
        if self.notebook.get() == "Details" and self.selected_service:
            if (current_time - self._last_graph_update).total_seconds() >= 5:
                self._update_graph()
                self._last_graph_update = current_time
        
        # Schedule next update
        self.window.after(1000, self._update_ui)
    
    def on_status_change(self, service_name: str, old_status: ServiceStatus, new_status: ServiceStatus):
        """Handle service status changes"""
        if new_status == ServiceStatus.RED:
            self.alert_manager.alert_service_down(service_name)
        elif new_status == ServiceStatus.YELLOW:
            self.alert_manager.alert_service_degraded(service_name)
        elif old_status in [ServiceStatus.RED, ServiceStatus.YELLOW] and new_status == ServiceStatus.GREEN:
            self.alert_manager.alert_service_restored(service_name)
    
    def _run_monitor(self):
        """Run the monitor in a background thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.monitor.monitor_loop())
    
    def run(self):
        """Start the GUI application"""
        self.window.mainloop()
    
    def cleanup(self):
        """Cleanup on exit"""
        self.monitor.stop()


if __name__ == "__main__":
    app = ServiceMonitorGUI()
    
    try:
        app.run()
    finally:
        app.cleanup()
