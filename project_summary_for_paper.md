# Smart Cleanliness System - Project Summary for Research Paper

This document contains a comprehensive overview of the "Smart Cleanliness System," a full-stack platform consisting of a mobile application designed to bridge the gap between citizens, municipal authorities, volunteers, and administrators to maintain urban cleanliness efficiently. 

You can use this document as context to generate a research paper, abstract, introduction, methodology, or architecture section for the project.

## 1. Introduction & Motivation
The Smart Cleanliness System addresses the persistent issue of urban waste management by crowdsourcing waste reporting and gamifying the cleanup process. It provides real-time waste tracking, automated escalation of unresolved issues, and a volunteer-driven resolution mechanism.

## 2. Project Architecture & Technologies
The platform is built using a modern, scalable full-stack architecture:

### Backend 
- **Framework**: Python environment using **Flask** (A lightweight WSGI web application framework).
- **Database**: **MySQL** (Relational Database) accessed via `Flask-MySQLdb`.
- **API Architecture**: RESTful APIs designed with Flask Blueprints (e.g., Auth, Complaints, Volunteer, Awareness, Authority, Emergency, Locate, Admin).
- **Additional Libraries**: `Werkzeug` (for secure file uploads and password hashing), `Flask-CORS` (for cross-origin resource sharing).

### Frontend (Mobile Application)
- **Framework**: **React Native** (using **Expo** framework) for cross-platform (iOS/Android) mobile app development.
- **Navigation**: React Navigation (`@react-navigation/native-stack`).
- **Maps & Geolocation**: `react-native-maps` and `expo-location` to capture precise GPS coordinates of waste and render them on interactive maps.
- **Camera & Media**: `expo-image-picker` for capturing real-time evidence of unmanaged waste.
- **UI & Styling**: `react-native-paper` for Material Design components and `lucide-react-native` for modern icons.
- **Network Requests**: `axios` for communicating with the Flask REST APIs.

## 3. Core Modules & Features

### 3.1. Role-Based Access Control (RBAC) System
The system is tailored for 4 distinct user roles:
1. **Citizen**: Can report waste, track the status of reports, and view neighborhood waste on maps.
2. **Authority**: Review and validate reported waste, marking decisions (Agree/Disagree) based on severity or area jurisdiction.
3. **Volunteer**: Individuals who voluntarily participate in clean-up drives. They can register, join events, assign vehicles, and earn points on a leaderboard to gamify the process.
4. **Administrator**: Oversees the entire system. Escalates unresolved complaints from authorities, manages volunteer events, and assigns logistics (vehicles/volunteers).

### 3.2. Geo-Tagged Waste Reporting (Citizen Module)
- Citizens capture a photo of the waste using the mobile app.
- The app automatically attaches GPS coordinates (Latitude/Longitude) to the complaint.
- Citizens can input severity and a descriptive summary.
- Image duplication/AI validation is considered in the backend design (`test_ai.py`, `test_duplicate.py`).

### 3.3. Multi-tier Escalation Workflow
- **Level 1**: Complaints go to the local 'Authority' for validation.
- **Level 2**: If the authority determines an issue requires extra resources or remains unresolved, it is escalated to the 'Admin'.
- **Level 3**: The Admin evaluates the requirement and pushes the task to the **Volunteer Hub**.

### 3.4. Volunteer Hub & Gamification
- Admin creates "Events" based on escalated major waste sites.
- Citizens can switch roles or act as Volunteers, joining these events.
- **Logistics Registration**: Volunteers can register their vehicles (e.g., trucks/vans) for transporting waste.
- **Leaderboard**: To encourage continuous participation, volunteers gain points for completing events, ranked on a public leaderboard.

### 3.5. Smart Mapping & Analytics (Locate Module)
- Real-time mapping module that plots unresolved reported waste across the city map.
- Helps municipal groups strategically identify hotspots of garbage dumping.

### 3.6. Emergency & Awareness Management
- **Emergency Reporting**: A specialized fast-track flow for hazardous waste or emergencies requiring immediate attention.
- **Awareness Portal**: A dedicated section to promote hygiene campaigns, including a **Donation system** where individuals can fund the clean-up efforts.

## 4. Conclusion / Potential Paper Highlights
- **Innovation**: The integration of crowdsourced geo-tagged reporting with a verified, multi-tiered escalation process.
- **Community Engagement**: Turning a logistical problem into a community-driven solution through gamification and volunteer hubs.
- **Transparency**: End-to-end visibility for the Citizen, tracking their report from submission to clean-up resolution.
