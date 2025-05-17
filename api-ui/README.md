# Resinkit Task Management UI

A web user interface for managing tasks in Resinkit.

## Features

- View and filter task lists
- Submit new tasks (JSON or YAML format)
- View task details, logs, and results
- Cancel running tasks

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. Clone the repository
2. Install dependencies:

```bash
npm install
```

### Configuration

By default, the application connects to the Resinkit API at `http://localhost:8602`.
To change this, set the `NEXT_PUBLIC_API_URL` environment variable:

```bash
export NEXT_PUBLIC_API_URL=http://your-api-server:8602
```

Or add it to a `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://your-api-server:8602
```

### Development

To start the development server:

```bash
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
```

### Running in Production

After building the application:

```bash
npm run start
```

## UI Design Considerations

This implementation follows these UI design considerations:

- **Clear Feedback:** Visual feedback for all user actions including loading states, success messages, and error messages.
- **Error Handling:** User-friendly display of API errors with guidance when possible.
- **Responsiveness:** Adaptive layout for various screen sizes.
- **Consistency:** Consistent visual style and interaction patterns throughout the application.
- **State Management:** Accurate reflection of task states with periodic refreshing of task data.

## API Endpoints

The application uses the following Resinkit API endpoints:

- `GET /api/v1/agent/tasks` - List tasks with optional filtering
- `POST /api/v1/agent/tasks` - Submit a new task (JSON)
- `POST /api/v1/agent/tasks/yaml` - Submit a new task (YAML)
- `GET /api/v1/agent/tasks/{task_id}` - Get task details
- `GET /api/v1/agent/tasks/{task_id}/logs` - Get task logs
- `GET /api/v1/agent/tasks/{task_id}/results` - Get task results
- `POST /api/v1/agent/tasks/{task_id}/cancel` - Cancel a task
