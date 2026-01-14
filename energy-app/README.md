# Energy Management System

A microservices based energy management system built with FastAPI, React, and Python.


## System Architecture

### Microservices
- **Auth Service** (Port 8001): User authentication, JWT tokens
- **Users Service** (Port 8002): Admin user management interface, CRUD proxies to auth
- **Devices Service** (Port 8003): Device CRUD and user-device assignments
- **Monitoring Service** (Port 8004): Stores and aggregates device measurements, computes hourly consumption
- **Customer Support Service** (Port 8005): Rule-based chatbot with 10+ rules + Gemini AI fallback; forwards to admin only on explicit request
- **WebSocket Service** (Port 8006): Real-time notifications (overconsumption alerts) and chat messaging
- **Load Balancer Service**: Distributes device data messages to monitoring replicas (round-robin or consistent hashing)
- **Gateway** (Port 8000): API Gateway with JWT validation and request routing
- **Frontend** (Port 3000): React based admin and client dashboards

### Infrastructure
- **RabbitMQ**: Event bus for service synchronization (fanout exchange for user/device events)
- **Traefik**: Reverse proxy (Port 80, 8080)
- **PostgreSQL**: Database with separate DBs per service
- **Docker Compose**: Local development containerization
- **Docker Swarm**: Production deployment with load balancing

## Assignment 3: WebSockets and Load Balancing

### New Features Implemented

#### 1. Real-Time Overconsumption Notifications
- Monitoring service detects when device consumption exceeds max_consumption threshold
- Publishes alerts to RabbitMQ fanout exchange `overconsumption_notifications`
- WebSocket service consumes notifications and broadcasts to affected users via WebSocket

#### 2. Customer Support Chat System
- **Rule-based Chatbot**: 10+ rules for common questions (device management, energy usage, billing, etc.)
- **AI-Driven Support (Gemini)**: Unmatched messages answered via Gemini API
- **Admin Escalation**: Only when user explicitly requests admin/support (rule match)
- **WebSocket Integration**: Real-time chat between clients and admins

#### 3. Load Balancing for Monitoring Service
- **Load Balancer Service**: Single consumer on `device_data_queue`
- Distributes messages to per-replica ingest queues (`ingest_queue_1`, `ingest_queue_2`, `ingest_queue_3`)
- Supports two strategies:
  - **Round-robin**: Balanced distribution across replicas
  - **Consistent-hash**: Device-based routing for session affinity
- Monitoring service reads from `INGEST_QUEUE` env var (enables per-replica queues in swarm)

### WebSocket Endpoints

#### `/ws/notifications?token=<JWT>`
- Authenticate with JWT token
- Receive real-time overconsumption alerts for user's devices
- Keep-alive with ping/pong

#### `/ws/chat?token=<JWT>`
- Two-way communication for customer support
- Clients send messages → chatbot responds or forwards to admin
- Admins receive user messages and can reply in real-time

## Event Driven Synchronization

Services communicate user and device changes using RabbitMQ with a fanout exchange. Each service has its own queue bound to this exchange, ensuring all receive every event. This keeps user/device data in sync across all microservices.

- User registration, update, and device assignment events are broadcast to all services.
- Each service consumes from its own queue, so no events are missed.


## Device Simulator

The `device_simulator` sends periodic device readings to RabbitMQ. This simulates real device data for testing and development.

**Usage:**

1. Open a terminal in the `device_simulator` directory.
2. Run:
	```powershell
	python simulator.py --device-id <DEVICE_ID> [--interval <SECONDS>] [--rabbitmq-host <HOST>] [--rabbitmq-port <PORT>] [--rabbitmq-user <USER>] [--rabbitmq-pass <PASS>]
	```
	Example:
	```powershell
	python simulator.py --device-id dev123 --interval 600
	```
3. The simulator will send readings to the `device_data_queue` in RabbitMQ at the specified interval.



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
- Real-time overconsumption alerts via WebSocket
- Customer support chat

### Customer Support
- 10+ rule-based responses for common questions
- Automatic escalation to admin for complex queries
- Real-time chat via WebSocket

## Technology Stack

**Backend:**
- FastAPI (Python)
- SQLAlchemy ORM
- PostgreSQL
- JWT authentication
- Passlib + bcrypt
- WebSockets
- RabbitMQ (pika)

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

### Local Development with Docker Compose

1. **Clone the repository**
	```powershell
	git clone <repository-url>
	cd energy-app
	```

2. **Create .env file** with required environment variables:
	```
	POSTGRES_PASSWORD=yourpassword
	JWT_SECRET=your-secret-key
	JWT_EXPIRES_MIN=120
	RABBITMQ_USER=guest
	RABBITMQ_PASS=guest
	```

3. **Build and start all services**:
	```powershell
	docker-compose up --build
	```

4. **Access the application**:
	- Frontend: http://localhost:3000
	- API Gateway: http://localhost:8000
	- Traefik Dashboard: http://localhost:8080
	- RabbitMQ Management: http://localhost:15672





### Load Balancing Configuration

The load balancer distributes device data messages across monitoring replicas:

- **Strategy**: Set via `LOAD_STRATEGY` environment variable
  - `round-robin` (default): Evenly distributes messages
  - `consistent-hash`: Routes same device_id to same replica
  
- **Replica Count**: Set via `NUM_REPLICAS` environment variable (default: 3)

- **Queue Naming**: Monitoring replicas consume from `ingest_queue_1`, `ingest_queue_2`, etc.

### Testing the System

1. **Register an admin user** via frontend at http://localhost:3000

2. **Create devices** via admin dashboard

3. **Run device simulator**:
	```powershell
	cd device_simulator
	pip install -r requirements.txt
	python simulator.py --device-id <device-id> --interval 600
	```

4. **Test overconsumption alerts**:
	- Set a low max_consumption on a device
	- Run simulator to generate data exceeding the limit
	- Check WebSocket notifications endpoint

5. **Test customer support**:
	- Connect to `/ws/chat` endpoint
	- Send test messages matching chatbot rules
	- Send unmatched messages to trigger admin forwarding

### Monitoring and Debugging

**RabbitMQ Queues:**
- `device_data_queue`: Device simulator publishes here
- `ingest_queue_1`, `ingest_queue_2`, `ingest_queue_3`: Per-replica monitoring queues
- `overconsumption_notifications`: Fanout exchange for alerts
- `admin_chat_queue`: Unhandled support messages
- `sync_events`: Device/user synchronization



**Service Logs:**
```powershell

docker-compose logs -f monitoring
docker-compose logs -f websocket
docker-compose logs -f support
docker-compose logs -f load_balancer


```

1. **If running locally without Docker**
	```powershell
	pip install -r requirements.txt
	cd frontend
	npm install
	```

2. **If using Docker**
	```powershell
	docker compose up -d --build
	```



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
- Displays chart of consumption over time for each device

### Logout
- Click "Logout" button (top-right) from any dashboard
- Redirects to login page
- Clears authentication token
