# Health Metric Calculator & Tracker

A comprehensive, desktop-based health tracking application built with Python and Tkinter. This application allows users to track BMI, daily steps, and water intake with persistent storage and data visualization.

Featuring a fully responsive Dark Mode, animated UI elements, and interactive graphs.

 Key Features

User Profiles: Create, edit, and manage multiple user profiles with persistent storage using SQLite.

BMI Calculator: Automatic calculation of BMI and Weight Status (Underweight, Normal, Obese, etc.) with support for both Metric (kg/cm) and Imperial (lb/ft) units.

Daily Tracking: Log your daily water intake (ml) and step counts via an intuitive calendar interface.

Data Visualization: View your progress over time with dynamic line graphs generated via matplotlib.

Smart Recommendations: Get personalized health tips based on your BMI and tracking history.

Theme Engine: A custom-built, animated Dark/Light mode toggle that themes every element of the UI, including graphs and popups.

 Release History & Changelog

v1.0.0 - The "Dark Mode" Update (Current)

Stable Release - November 25 2025

This release focuses on UI consistency, visual polish, and fixing critical bugs found in the v0.8 Beta regarding Dark Mode visibility.

 Dark Mode Text Fixes:

Fixed a critical bug where input fields (Entry widgets) would display white text on a white background or remain bright white in Dark Mode.

Migrated specific inputs from ttk.Entry to standard tk.Entry to allow full control over background and insertion cursor colors.

 Themed Popups:

Replaced system-default dialogs (which couldn't be themed) with custom Toplevel windows.

"Load Profile," "New Profile," and "Calendar" popups now respect the active theme (Dark/Light).
Dark Mode Graphs:

Implemented matplotlib styling contexts. Graphs now dynamically change their background, axes, and font colors to match the application theme (e.g., dark background with white text for Dark Mode).

Bug Fixes:

Fixed cursor visibility issues in text fields.

Resolved layout padding inconsistencies on the "About" tab.

v0.8.0 - Beta Phase

Feature Complete - November 24 2025

Added: Dark Mode toggle with smooth animation logic.

Added: matplotlib integration for visualizing Steps and Water history.

Added: "Insights" tab that generates text-based health advice based on database statistics.

Added: Imperial Unit support (ft/in and lbs) with automatic conversion logic.

Improvement: Added Notebook tabs for better navigation (BMI, Steps, Water, Insights).

v0.5.0 - Alpha / Proof of Concept

Initial Build - November 23 2025

Core: Basic Tkinter window structure.

Database: Implemented sqlite3 connection and table structure (profiles, steps, water_logs).

Functionality: Basic Create/Read/Update/Delete (CRUD) operations for profiles.

Math: Basic BMI calculation logic implemented.

 Installation

Clone the repository:

git clone (https://github.com/BredWuzHere/Health-Metric-Calculator.git)
cd health-metric-tracker


Install dependencies:
This app uses standard Python libraries, but requires matplotlib for graphing.

pip install matplotlib


(Note: tkinter, sqlite3, datetime, and os are included with standard Python installations.)

Run the application:

python health_app.py


Technical Stack

Language: Python 3.14

GUI Framework: Tkinter (with extensive use of ttk for modern styling).

Database: SQLite3 (Local file profiles.db).

Visualization: Matplotlib.

Algorithms: Custom interpolation logic for color transitions (Dark/Light mode fading).

 Usage Guide

Select Directory: On first launch, click "Open Directory" to choose where your database file (profiles.db) will be saved.

Create Profile: Click "New Profile," enter your name, height, and weight.

Track Data: Go to the Steps or Water tabs, select a date using the calendar icon, and input your data.

Visualize: Click "Show Graph" on the respective tabs to see your trends.

Toggle Theme: Use the toggle switch in the top right to switch between Light and Dark modes.

License

This project is open source and available under the MIT License.

Created for CS121 Advanced Computer Programming, BSU.
