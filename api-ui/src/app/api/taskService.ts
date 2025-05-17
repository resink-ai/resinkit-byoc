import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8602';

export interface TaskFilter {
    task_type?: string;
    status?: string;
    task_name_contains?: string;
    tags_include_any?: string;
    created_after?: string;
    created_before?: string;
    limit?: number;
    page_token?: string;
    sort_by?: string;
    sort_order?: string;
}

export interface Task {
    id: string;
    task_type: string;
    status: string;
    created_at: string;
    updated_at?: string;
    name?: string;
    tags?: string[];
    [key: string]: any; // For any additional properties
}

export interface TaskListResponse {
    tasks: Task[];
    next_page_token?: string;
}

export interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
}

const taskService = {
    // List tasks with optional filtering
    async listTasks(filters: TaskFilter = {}): Promise<TaskListResponse> {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/v1/agent/tasks`, {
                params: filters,
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching tasks:', error);
            throw error;
        }
    },

    // Get task details by ID
    async getTaskDetails(taskId: string): Promise<Task> {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/v1/agent/tasks/${taskId}`);
            return response.data;
        } catch (error) {
            console.error(`Error fetching task ${taskId}:`, error);
            throw error;
        }
    },

    // Submit a new task (JSON)
    async submitTask(payload: any): Promise<any> {
        try {
            const response = await axios.post(`${API_BASE_URL}/api/v1/agent/tasks`, payload);
            return response.data;
        } catch (error) {
            console.error('Error submitting task:', error);
            throw error;
        }
    },

    // Submit a new task (YAML)
    async submitTaskYaml(yamlPayload: string): Promise<any> {
        try {
            const response = await axios.post(
                `${API_BASE_URL}/api/v1/agent/tasks/yaml`,
                yamlPayload,
                {
                    headers: {
                        'Content-Type': 'text/plain',
                    },
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error submitting YAML task:', error);
            throw error;
        }
    },

    // Cancel a task
    async cancelTask(taskId: string, force: boolean = false): Promise<any> {
        try {
            const response = await axios.post(
                `${API_BASE_URL}/api/v1/agent/tasks/${taskId}/cancel`,
                {},
                {
                    params: { force },
                }
            );
            return response.data;
        } catch (error) {
            console.error(`Error canceling task ${taskId}:`, error);
            throw error;
        }
    },

    // Get task logs
    async getTaskLogs(taskId: string, level: string = 'INFO'): Promise<LogEntry[]> {
        try {
            const response = await axios.get(
                `${API_BASE_URL}/api/v1/agent/tasks/${taskId}/logs`,
                {
                    params: { level },
                }
            );
            return response.data;
        } catch (error) {
            console.error(`Error fetching logs for task ${taskId}:`, error);
            throw error;
        }
    },

    // Get task results
    async getTaskResults(taskId: string): Promise<any> {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/v1/agent/tasks/${taskId}/results`);
            return response.data;
        } catch (error) {
            console.error(`Error fetching results for task ${taskId}:`, error);
            throw error;
        }
    },
};

export default taskService; 