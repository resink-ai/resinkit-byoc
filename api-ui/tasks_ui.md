
# Resinkit Task Management UI Design


**Overall UI Structure:**

* **Main Navigation:** A persistent sidebar or top bar for navigating key sections (likely just "Tasks" based on this API).
* **Primary View: Task Dashboard/List View:** This will be the central hub for viewing, filtering, and initiating actions on tasks.
* **Secondary View/Modal: Task Submission Form:** For creating new tasks.
* **Tertiary View/Page: Task Details Page:** For in-depth information about a specific task, including logs and results.

---

**UI Design & User Flows by API Endpoint Grouping:**

**1. Task Listing & Filtering (`GET /api/v1/agent/tasks`)**

* **UI Elements (Task Dashboard/List View):**
    * **Task Table:**
        * Columns: Task ID (clickable), Task Name (if inferable or user-settable outside this API), Task Type, Status, Creation Date, Last Updated (if available), Tags.
        * Each row represents a task.
    * **Action Bar above Table:**
        * **"Submit New Task" Button:** Primary action button to open the task submission form.
    * **Filtering Panel (collapsible or sidebar):**
        * **Task Type:** Dropdown menu (populated with distinct task types if known, otherwise free text).
        * **Status:** Dropdown menu (e.g., "Pending", "Running", "Success", "Failed", "Canceled").
        * **Task Name Contains:** Text input field.
        * **Tags Include Any:** Text input field (supports comma-separated values or a tag-input component).
        * **Created After:** Date picker.
        * **Created Before:** Date picker.
        * **"Apply Filters" Button.**
        * **"Clear Filters" Button.**
    * **Sorting Controls:**
        * Integrated into table headers (clickable headers for Task ID, Creation Date, etc.).
        * Optional explicit dropdowns for "Sort By" (e.g., "Created At", "Task Name") and "Sort Order" ("Ascending", "Descending").
    * **Pagination Controls:**
        * "Previous" / "Next" buttons.
        * Page number indicator/input.
        * Items per page selector (maps to `limit`, e.g., 10, 20, 50, 100).
    * **Quick Action Icons per Row (visible on hover/selection):**
        * "View Details" icon/button.
        * "Cancel Task" icon/button (enabled/disabled based on task status).

* **User Flow (Viewing and Filtering Tasks):**
    1.  User lands on the Task Dashboard.
    2.  The UI fetches and displays an initial list of tasks using default parameters (e.g., `limit=20`, `sort_by=created_at`, `sort_order=desc`).
    3.  User interacts with filter inputs (e.g., selects a "Status", enters a "Task Name Contains" keyword).
    4.  User clicks "Apply Filters".
    5.  The UI re-fetches the task list using the specified query parameters.
    6.  User can sort the list by clicking column headers or using sort dropdowns.
    7.  User navigates through pages using pagination.
    8.  User clicks on a Task ID or "View Details" icon to see more information.

---

**2. Task Submission (`POST /api/v1/agent/tasks` and `POST /api/v1/agent/tasks/yaml`)**

* **UI Elements (Task Submission Form - likely a Modal or Separate Page):**
    * **Input Method Selector:** Tabs or radio buttons: "JSON" and "YAML".
    * **JSON Input Section (if "JSON" selected):**
        * **Dynamic Key-Value Editor:** Given `additionalProperties: true`, a flexible interface is needed.
            * Fields for "Key" and "Value".
            * Buttons to "Add Field" / "Remove Field".
            * Support for basic value types (text, number, boolean).
            * *Advanced:* Support for nested objects/arrays, or a raw JSON text area with validation and syntax highlighting.
    * **YAML Input Section (if "YAML" selected):**
        * **YAML Editor:** A multi-line text area with syntax highlighting and real-time validation for YAML.
    * **Action Buttons:**
        * **"Submit Task" Button.**
        * **"Cancel" or "Close" Button.**
    * **Feedback Area:** For displaying success messages (e.g., "Task submitted with ID: `XYZ`") or validation error details (from `HTTPValidationError`).

* **User Flow (Submitting a New Task):**
    1.  User clicks the "Submit New Task" button on the Task Dashboard.
    2.  The Task Submission Form appears.
    3.  User selects the input method ("JSON" or "YAML").
    4.  User provides the task payload:
        * **JSON:** Enters key-value pairs or raw JSON.
        * **YAML:** Pastes or writes YAML into the editor.
    5.  User clicks "Submit Task".
    6.  The UI sends a POST request to the appropriate endpoint (`/api/v1/agent/tasks` or `/api/v1/agent/tasks/yaml`).
    7.  The UI displays a success or error message. On success, the form may close, and the Task Dashboard may refresh to show the new task.

---

**3. Task Details, Logs, and Results (`GET /api/v1/agent/tasks/{task_id}`, `GET /api/v1/agent/tasks/{task_id}/logs`, `GET /api/v1/agent/tasks/{task_id}/results`)**

* **UI Elements (Task Details Page):**
    * **Header Section:**
        * **Task ID:** Prominently displayed.
        * **Task Name (if available).**
        * **Current Status:** Clearly shown (e.g., with a colored badge).
        * **"Cancel Task" Button:** (Conditional, based on task status).
        * **"Refresh Details" Button.**
    * **Tabbed Interface:**
        * **"Overview" Tab (`GET /api/v1/agent/tasks/{task_id}`):**
            * A structured display of all properties returned by the API for the task.
            * Fields like Creation Date, Last Modified, Task Type, and any other dynamic properties.
        * **"Logs" Tab (`GET /api/v1/agent/tasks/{task_id}/logs`):**
            * **Log Level Filter:** Dropdown (INFO, WARN, ERROR, DEBUG) defaulting to INFO.
            * **Log Display Area:** A scrollable, formatted view of log entries (timestamp, level, message).
            * Option for auto-refresh or a manual "Refresh Logs" button.
            * Search/filter within displayed logs.
        * **"Results" Tab (`GET /api/v1/agent/tasks/{task_id}/results`):**
            * Display area for task results. The presentation will depend on the nature of the results (e.g., formatted JSON, plain text, link to download a file).
            * "Download Results" button if applicable.

* **User Flow (Viewing Task Details):**
    1.  User clicks on a Task ID or "View Details" icon from the Task Dashboard.
    2.  The UI navigates to the Task Details page for the specific `task_id`.
    3.  The UI fetches and displays data for the "Overview" tab.
    4.  User clicks the "Logs" tab:
        * UI fetches logs with the default level (INFO).
        * User can change the log level, triggering a re-fetch of logs with the new level.
    5.  User clicks the "Results" tab:
        * UI fetches and displays task results.
    6.  User can click "Refresh Details" to get the latest information for the current tab or the entire task.

---

**4. Cancel Task (`POST /api/v1/agent/tasks/{task_id}/cancel`)**

* **UI Elements:**
    * **"Cancel Task" Button:** (As described in Task List and Task Details sections).
    * **Confirmation Modal:**
        * Title: "Confirm Task Cancellation".
        * Message: "Are you sure you want to cancel Task `[task_id]`?"
        * **"Force Cancel" Checkbox:** (Maps to `force` query parameter). Label: "Attempt to forcefully cancel the task."
        * **"Confirm" Button.**
        * **"Cancel" (or "Keep Task") Button.**
    * **Notifications/Toasts:** For indicating the outcome (e.g., "Task cancellation initiated," "Failed to cancel task").

* **User Flow (Canceling a Task):**
    1.  User clicks a "Cancel Task" button (from the list or details page).
    2.  The Confirmation Modal appears.
    3.  User may check the "Force Cancel" checkbox.
    4.  User clicks "Confirm".
    5.  The UI sends a POST request to `/api/v1/agent/tasks/{task_id}/cancel` (with `force` parameter if checked).
    6.  The UI shows a notification.
    7.  The task's status in the UI (list and details) should update accordingly (e.g., to "Canceling" or "Canceled"), potentially after a refresh or if real-time updates are implemented.

---

**General UI Considerations:**

* **Clear Feedback:** Provide immediate visual feedback for all user actions (loading states, success messages, error messages).
* **Error Handling:** Display API errors (`ErrorResponse`, `HTTPValidationError`) in a user-friendly way, guiding the user if possible.
* **Responsiveness:** Ensure the layout adapts to various screen sizes.
* **Consistency:** Maintain a consistent visual style and interaction patterns throughout the application.
* **State Management:** The UI should accurately reflect the current state of tasks. This might involve polling for updates or, ideally, using WebSockets if the backend supports real-time updates (though not specified in this API).


# Task Management API specs
```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Resinkit Task API",
    "description": "Service for managing tasks with Resinkit",
    "contact": {
      "name": "Resinkit Tasks",
      "url": "http://localhost:8602/",
      "email": "support@resink.ai"
    },
    "version": "0.1.0"
  },
  "paths": {
    "/api/v1/agent/tasks": {
      "post": {
        "tags": [
          "agent"
        ],
        "summary": "Submit Task",
        "operationId": "submit_task_api_v1_agent_tasks_post",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": true,
                "title": "Payload"
              }
            }
          }
        },
        "responses": {
          "202": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      },
      "get": {
        "tags": [
          "agent"
        ],
        "summary": "List Tasks",
        "operationId": "list_tasks_api_v1_agent_tasks_get",
        "parameters": [
          {
            "name": "task_type",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Task Type"
            }
          },
          {
            "name": "status",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Status"
            }
          },
          {
            "name": "task_name_contains",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Task Name Contains"
            }
          },
          {
            "name": "tags_include_any",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Tags Include Any"
            }
          },
          {
            "name": "created_after",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Created After"
            }
          },
          {
            "name": "created_before",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Created Before"
            }
          },
          {
            "name": "limit",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "integer",
                  "maximum": 100,
                  "minimum": 1
                },
                {
                  "type": "null"
                }
              ],
              "default": 20,
              "title": "Limit"
            }
          },
          {
            "name": "page_token",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Page Token"
            }
          },
          {
            "name": "sort_by",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": "created_at",
              "title": "Sort By"
            }
          },
          {
            "name": "sort_order",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": "desc",
              "title": "Sort Order"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/agent/tasks/yaml": {
      "post": {
        "tags": [
          "agent"
        ],
        "summary": "Submit Task Yaml",
        "operationId": "submit_task_yaml_api_v1_agent_tasks_yaml_post",
        "requestBody": {
          "content": {
            "text/plain": {
              "schema": {
                "type": "string",
                "title": "Yaml Payload"
              }
            }
          },
          "required": true
        },
        "responses": {
          "202": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/agent/tasks/{task_id}": {
      "get": {
        "tags": [
          "agent"
        ],
        "summary": "Get Task Details",
        "operationId": "get_task_details_api_v1_agent_tasks__task_id__get",
        "parameters": [
          {
            "name": "task_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Task Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/agent/tasks/{task_id}/cancel": {
      "post": {
        "tags": [
          "agent"
        ],
        "summary": "Cancel Task",
        "operationId": "cancel_task_api_v1_agent_tasks__task_id__cancel_post",
        "parameters": [
          {
            "name": "task_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Task Id"
            }
          },
          {
            "name": "force",
            "in": "query",
            "required": false,
            "schema": {
              "type": "boolean",
              "description": "Whether to forcefully cancel the task",
              "default": false,
              "title": "Force"
            },
            "description": "Whether to forcefully cancel the task"
          }
        ],
        "responses": {
          "202": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/agent/tasks/{task_id}/logs": {
      "get": {
        "tags": [
          "agent"
        ],
        "summary": "Get Task Logs",
        "operationId": "get_task_logs_api_v1_agent_tasks__task_id__logs_get",
        "parameters": [
          {
            "name": "task_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Task Id"
            }
          },
          {
            "name": "level",
            "in": "query",
            "required": false,
            "schema": {
              "type": "string",
              "description": "Log level filter (INFO, WARN, ERROR, DEBUG)",
              "default": "INFO",
              "title": "Level"
            },
            "description": "Log level filter (INFO, WARN, ERROR, DEBUG)"
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/agent/tasks/{task_id}/results": {
      "get": {
        "tags": [
          "agent"
        ],
        "summary": "Get Task Results",
        "operationId": "get_task_results_api_v1_agent_tasks__task_id__results_get",
        "parameters": [
          {
            "name": "task_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Task Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "ErrorResponse": {
        "properties": {
          "error_code": {
            "type": "string",
            "title": "Error Code"
          },
          "message": {
            "type": "string",
            "title": "Message"
          },
          "details": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Details"
          }
        },
        "type": "object",
        "required": [
          "error_code",
          "message"
        ],
        "title": "ErrorResponse",
        "example": {
          "details": "Catalog 'my_catalog' was not found in catalog store 'my_store'",
          "error_code": "CATALOG_NOT_FOUND",
          "message": "The specified catalog does not exist"
        }
      },
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            },
            "type": "array",
            "title": "Detail"
          }
        },
        "type": "object",
        "title": "HTTPValidationError"
      },
      "SQLQuery": {
        "properties": {
          "sql": {
            "type": "string",
            "title": "Sql"
          }
        },
        "type": "object",
        "required": [
          "sql"
        ],
        "title": "SQLQuery"
      },
      "ValidationError": {
        "properties": {
          "loc": {
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "type": "array",
            "title": "Location"
          },
          "msg": {
            "type": "string",
            "title": "Message"
          },
          "type": {
            "type": "string",
            "title": "Error Type"
          }
        },
        "type": "object",
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "title": "ValidationError"
      }
    }
  }
}
```
