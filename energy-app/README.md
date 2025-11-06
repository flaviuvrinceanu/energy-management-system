# Energy Management System

A microservices based energy management system built with FastAPI, React, and Python.

## System Architecture

### Microservices
- **Auth Service** (Port 8001): User authentication, JWT tokens
- **Users Service** (Port 8002): Admin user management interface, CRUD proxies to auth
- **Devices Service** (Port 8003): Device CRUD and user-device assignments
- **Gateway** (Port 8000): API Gateway with JWT validation and request routing
- **Frontend** (Port 3000): React based admin and client dashboards

### Infrastructure
- **Traefik**: Reverse proxy (Port 80, 8080)
- **PostgreSQL**: Database with separate DBs per service
- **Docker Compose**: Containerization

## Features

### Authentication & Authorization
- User registration and login
- JWT-based authentication
- Role-based access control (Admin/Client)
- Password hashing with bcrypt

### User Management (Admin)
- Create users with roles
- Update usernames
- Delete users
- View all users

### Device Management (Admin)
- CRUD operations on devices
- Update device name and max consumption
- Assign/unassign devices to users
- View all devices with assignments

### Client Dashboard
- View assigned devices
- See device details (name, max consumption)

## Technology Stack

**Backend:**
- FastAPI (Python)
- SQLAlchemy ORM
- PostgreSQL
- JWT authentication
- Passlib + bcrypt

**Frontend:**
- React 
- Axios


**Infrastructure:**
- Docker
- Traefik reverse proxy


## Prerequisites

- Docker Desktop
- Git

## Installation & Setup 

1. **If running locally without Docker**

pip install -r requirements.txt
cd frontend
npm install

2. **If using Docker**

docker compose up -d --build



## Navigating the Application

### Login & Registration
1. **Access App**: Open http://localhost:3000
2. **New User**: Click "Register" → Enter username, password, select role → Submit
3. **Existing User**: Enter credentials → Click "Login"
4. **Auto-Redirect**: Dashboard opens based on your role (Admin/Client)

### Admin Dashboard

**Main Navigation Tabs:**
- **User Management**: Manage system users
- **Device Management**: Manage devices and assignments

**User Management Tab:**
- View all users in a table (Username, Role)
- **Create**: Fill form above table → Click "Create User"
- **Edit**: Click "Edit" button → Modify username → "Save"
- **Delete**: Click "Delete" button → Confirm

**Device Management Tab:**
- View all devices (Name, Max Consumption, Assigned User)
- **Create**: Fill form above table → Click "Create Device"
- **Edit**: Click "Edit" → Modify fields → "Save"
- **Assign**: Select user from dropdown → Auto-assigns
- **Unassign**: Click "Unassign" for assigned devices
- **Delete**: Click "Delete" → Confirm

### Client Dashboard

**My Devices View:**
- Displays table of your assigned devices
- Shows: Device Name, Max Consumption
- Read-only view (no edit/delete options)
- Refreshes automatically

### Logout
- Click "Logout" button (top-right) from any dashboard
- Redirects to login page
- Clears authentication token
