# TerminalTelemetry

A modern, cyberpunk-inspired terminal emulator with integrated network device monitoring capabilities. This application combines terminal functionality with real-time network telemetry in a highly customizable interface.

## Core Features

### Terminal Interface
- Multi-tabbed terminal sessions
- Session management and persistence
- Secure credential storage with master password protection
- YAML-based session configuration

### Network Telemetry
- Real-time device monitoring dashboard
- Automatic device discovery and type detection
- Interface utilization graphs
- Route table visualization
- LLDP/CDP neighbor discovery
- ARP table monitoring

### User Interface
- Split-pane design with adjustable widths
- Session navigator with tree-based organization
- Real-time graphs and statistics
- Themed HUD-style frames with corner decorations

## Design Architecture

### Theme System
The application features a comprehensive theming system with several built-in themes:
- Cyberpunk (default)
- Retro Green
- Retro Amber
- Neon Blue
- Light Mode

Each theme includes carefully designed color schemes for:
- Text and backgrounds
- Borders and decorations
- Charts and graphs
- Status indicators
- UI element highlights

### Component Structure

1. **Main Window (`TermtelWindow`)**
   - Manages the overall application layout
   - Handles theme switching
   - Controls the FastAPI backend server

2. **Session Navigator (`SessionNavigator`)**
   - Tree-based session management
   - Credential handling
   - Quick-connect functionality

3. **Terminal Tabs (`TerminalTabWidget`)**
   - Multiple terminal session management
   - Session persistence
   - Custom terminal emulation

4. **Device Dashboard (`DeviceDashboardWidget`)**
   - Real-time device monitoring
   - Interface statistics
   - Network topology information
   - Routing table visualization

5. **HUD Frame System (`LayeredHUDFrame`)**
   - Cyberpunk-inspired frame design
   - Dynamic corner decorations
   - Theme-aware styling
   - Customizable borders and effects

### Security Features

- Encrypted credential storage
- Master password protection
- Secure session handling
- Protected device authentication

## Technical Implementation

### Backend Integration
- FastAPI server for terminal communication
- Device monitoring via NAPALM
- Asynchronous data collection
- Real-time updates

### Frontend Framework
- Built with PyQt6
- SVG-based icons and decorations
- Custom widget styling
- Dynamic theme management

### Data Visualization
- Real-time graphing capabilities
- Network topology visualization
- Interface utilization monitoring
- Custom chart theming

## Configuration

The application supports:
- Custom session configurations via YAML
- Theme customization
- Terminal preferences
- Layout persistence

## Development Features

- Modular design for easy extension
- Comprehensive theme support
- Event-driven architecture
- Detailed logging system
- Error handling and recovery

## Requirements
- Python 3.x
- PyQt6
- NAPALM
- FastAPI
- Additional dependencies in requirements.txt

Would you like me to expand on any particular aspect of the documentation?