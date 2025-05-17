'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-toastify';
import { Tab } from '@headlessui/react';
import { format } from 'date-fns';
import { ArrowLeftIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { JsonView } from 'react-json-view-lite';
import 'react-json-view-lite/dist/index.css';
import taskService, { Task, LogEntry } from '../app/api/taskService';

interface TaskDetailsProps {
    taskId: string;
}

export default function TaskDetails({ taskId }: TaskDetailsProps) {
    const router = useRouter();
    const [task, setTask] = useState<Task | null>(null);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [results, setResults] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [logsLoading, setLogsLoading] = useState(false);
    const [resultsLoading, setResultsLoading] = useState(false);
    const [logLevel, setLogLevel] = useState('INFO');
    const [error, setError] = useState<string | null>(null);
    const [selectedTab, setSelectedTab] = useState(0);

    // Function to fetch task details
    const fetchTaskDetails = useCallback(async () => {
        setLoading(true);
        try {
            const taskData = await taskService.getTaskDetails(taskId);
            setTask(taskData);
            setError(null);
        } catch (err) {
            setError('Failed to fetch task details. Please try again.');
            console.error('Error fetching task details:', err);
        } finally {
            setLoading(false);
        }
    }, [taskId]);

    // Function to fetch task logs
    const fetchTaskLogs = useCallback(async () => {
        if (!taskId) return;

        setLogsLoading(true);
        try {
            const logsData = await taskService.getTaskLogs(taskId, logLevel);
            setLogs(logsData || []);
        } catch (err) {
            toast.error('Failed to fetch logs');
            console.error('Error fetching logs:', err);
        } finally {
            setLogsLoading(false);
        }
    }, [taskId, logLevel]);

    // Function to fetch task results
    const fetchTaskResults = useCallback(async () => {
        if (!taskId) return;

        setResultsLoading(true);
        try {
            const resultsData = await taskService.getTaskResults(taskId);
            setResults(resultsData);
        } catch (err) {
            toast.error('Failed to fetch results');
            console.error('Error fetching results:', err);
        } finally {
            setResultsLoading(false);
        }
    }, [taskId]);

    // Initial data fetch
    useEffect(() => {
        fetchTaskDetails();
    }, [fetchTaskDetails]);

    // Fetch logs when tab changes to logs or log level changes
    useEffect(() => {
        if (selectedTab === 1) {
            fetchTaskLogs();
        }
    }, [selectedTab, fetchTaskLogs]);

    // Fetch results when tab changes to results
    useEffect(() => {
        if (selectedTab === 2) {
            fetchTaskResults();
        }
    }, [selectedTab, fetchTaskResults]);

    // Handle task cancellation
    const handleCancelTask = async (force: boolean = false) => {
        if (window.confirm(`Are you sure you want to cancel this task${force ? ' forcefully' : ''}?`)) {
            try {
                await taskService.cancelTask(taskId, force);
                toast.success('Task cancellation initiated');
                fetchTaskDetails(); // Refresh task details
            } catch (err) {
                toast.error('Failed to cancel task');
                console.error('Error canceling task:', err);
            }
        }
    };

    // Get status color for display
    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'running':
                return 'bg-blue-100 text-blue-800';
            case 'success':
                return 'bg-green-100 text-green-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            case 'canceled':
                return 'bg-yellow-100 text-yellow-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    // Get log level color for display
    const getLogLevelColor = (level: string) => {
        switch (level.toUpperCase()) {
            case 'ERROR':
                return 'text-red-600';
            case 'WARN':
                return 'text-yellow-600';
            case 'INFO':
                return 'text-blue-600';
            case 'DEBUG':
                return 'text-gray-600';
            default:
                return 'text-gray-600';
        }
    };

    if (loading) {
        return (
            <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6 flex justify-center items-center h-64">
                <p className="text-gray-600 dark:text-gray-300">Loading task details...</p>
            </div>
        );
    }

    if (error || !task) {
        return (
            <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
                <div className="mb-4 p-4 text-sm text-red-700 bg-red-100 rounded-lg">
                    {error || 'Failed to load task details'}
                </div>
                <button
                    onClick={() => router.push('/tasks')}
                    className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                    <ArrowLeftIcon className="w-5 h-5 mr-2" />
                    Back to Tasks
                </button>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
            {/* Header section */}
            <div className="mb-6">
                <div className="flex justify-between items-start">
                    <div>
                        <button
                            onClick={() => router.push('/tasks')}
                            className="inline-flex items-center mb-4 text-sm font-medium text-primary hover:underline"
                        >
                            <ArrowLeftIcon className="w-4 h-4 mr-1" />
                            Back to Tasks
                        </button>
                        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                            {task.name ? `${task.name} (${task.id})` : `Task ${task.id}`}
                        </h2>
                        <div className="flex items-center mt-2">
                            <span
                                className={`${getStatusColor(
                                    task.status
                                )} px-2 py-1 rounded-full text-xs font-medium mr-2`}
                            >
                                {task.status}
                            </span>
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                                {format(new Date(task.created_at), 'MMM d, yyyy HH:mm:ss')}
                            </span>
                        </div>
                    </div>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => fetchTaskDetails()}
                            className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                            title="Refresh details"
                        >
                            <ArrowPathIcon className="w-5 h-5" />
                        </button>
                        {['pending', 'running'].includes(task.status.toLowerCase()) && (
                            <>
                                <button
                                    onClick={() => handleCancelTask(false)}
                                    className="px-3 py-2 text-sm font-medium text-white bg-yellow-500 rounded-md hover:bg-yellow-600"
                                >
                                    Cancel Task
                                </button>
                                <button
                                    onClick={() => handleCancelTask(true)}
                                    className="px-3 py-2 text-sm font-medium text-white bg-red-500 rounded-md hover:bg-red-600"
                                >
                                    Force Cancel
                                </button>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Tabs section */}
            <Tab.Group onChange={setSelectedTab}>
                <Tab.List className="flex border-b border-gray-200 dark:border-gray-700">
                    <Tab
                        className={({ selected }) =>
                            `py-2 px-4 text-sm font-medium border-b-2 ${selected
                                ? 'border-primary text-primary'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`
                        }
                    >
                        Overview
                    </Tab>
                    <Tab
                        className={({ selected }) =>
                            `py-2 px-4 text-sm font-medium border-b-2 ${selected
                                ? 'border-primary text-primary'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`
                        }
                    >
                        Logs
                    </Tab>
                    <Tab
                        className={({ selected }) =>
                            `py-2 px-4 text-sm font-medium border-b-2 ${selected
                                ? 'border-primary text-primary'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`
                        }
                    >
                        Results
                    </Tab>
                </Tab.List>
                <Tab.Panels className="mt-6">
                    {/* Overview Tab */}
                    <Tab.Panel>
                        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                            <h3 className="text-md font-medium text-gray-800 dark:text-gray-200 mb-4">
                                Task Properties
                            </h3>
                            <div className="space-y-2">
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="col-span-1 text-sm font-medium text-gray-600 dark:text-gray-400">
                                        Task ID
                                    </div>
                                    <div className="col-span-2 text-sm text-gray-800 dark:text-gray-200">
                                        {task.id}
                                    </div>
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="col-span-1 text-sm font-medium text-gray-600 dark:text-gray-400">
                                        Task Type
                                    </div>
                                    <div className="col-span-2 text-sm text-gray-800 dark:text-gray-200">
                                        {task.task_type}
                                    </div>
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="col-span-1 text-sm font-medium text-gray-600 dark:text-gray-400">
                                        Status
                                    </div>
                                    <div className="col-span-2 text-sm text-gray-800 dark:text-gray-200">
                                        <span
                                            className={`${getStatusColor(
                                                task.status
                                            )} px-2 py-1 rounded-full text-xs font-medium`}
                                        >
                                            {task.status}
                                        </span>
                                    </div>
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="col-span-1 text-sm font-medium text-gray-600 dark:text-gray-400">
                                        Created At
                                    </div>
                                    <div className="col-span-2 text-sm text-gray-800 dark:text-gray-200">
                                        {format(new Date(task.created_at), 'MMM d, yyyy HH:mm:ss')}
                                    </div>
                                </div>
                                {task.updated_at && (
                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="col-span-1 text-sm font-medium text-gray-600 dark:text-gray-400">
                                            Updated At
                                        </div>
                                        <div className="col-span-2 text-sm text-gray-800 dark:text-gray-200">
                                            {format(new Date(task.updated_at), 'MMM d, yyyy HH:mm:ss')}
                                        </div>
                                    </div>
                                )}
                                {task.tags && task.tags.length > 0 && (
                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="col-span-1 text-sm font-medium text-gray-600 dark:text-gray-400">
                                            Tags
                                        </div>
                                        <div className="col-span-2 text-sm text-gray-800 dark:text-gray-200">
                                            <div className="flex flex-wrap gap-1">
                                                {task.tags.map((tag, index) => (
                                                    <span
                                                        key={index}
                                                        className="bg-gray-100 dark:bg-gray-600 text-gray-800 dark:text-gray-300 text-xs font-medium px-2 py-0.5 rounded"
                                                    >
                                                        {tag}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Additional task properties (dynamic) */}
                            <h3 className="text-md font-medium text-gray-800 dark:text-gray-200 mt-6 mb-4">
                                Additional Properties
                            </h3>
                            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                                <JsonView data={task} />
                            </div>
                        </div>
                    </Tab.Panel>

                    {/* Logs Tab */}
                    <Tab.Panel>
                        <div className="mb-4 flex justify-between items-center">
                            <div className="flex items-center">
                                <label htmlFor="logLevel" className="text-sm font-medium text-gray-700 dark:text-gray-300 mr-2">
                                    Log Level:
                                </label>
                                <select
                                    id="logLevel"
                                    value={logLevel}
                                    onChange={(e) => setLogLevel(e.target.value)}
                                    className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                                >
                                    <option value="INFO">INFO</option>
                                    <option value="WARN">WARN</option>
                                    <option value="ERROR">ERROR</option>
                                    <option value="DEBUG">DEBUG</option>
                                </select>
                            </div>
                            <button
                                onClick={fetchTaskLogs}
                                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                            >
                                <ArrowPathIcon className="w-4 h-4 mr-2" />
                                Refresh Logs
                            </button>
                        </div>

                        <div className="bg-gray-800 text-gray-100 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
                            {logsLoading ? (
                                <div className="flex justify-center items-center h-full">
                                    <p>Loading logs...</p>
                                </div>
                            ) : logs.length === 0 ? (
                                <div className="flex justify-center items-center h-full">
                                    <p>No logs available</p>
                                </div>
                            ) : (
                                logs.map((log, index) => (
                                    <div key={index} className="mb-1">
                                        <span className="text-gray-400">{log.timestamp}</span>{' '}
                                        <span className={getLogLevelColor(log.level)}>
                                            [{log.level}]
                                        </span>{' '}
                                        {log.message}
                                    </div>
                                ))
                            )}
                        </div>
                    </Tab.Panel>

                    {/* Results Tab */}
                    <Tab.Panel>
                        <div className="mb-4 flex justify-end">
                            <button
                                onClick={fetchTaskResults}
                                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                            >
                                <ArrowPathIcon className="w-4 h-4 mr-2" />
                                Refresh Results
                            </button>
                        </div>

                        <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 min-h-52">
                            {resultsLoading ? (
                                <div className="flex justify-center items-center h-32">
                                    <p className="text-gray-600 dark:text-gray-300">Loading results...</p>
                                </div>
                            ) : results ? (
                                <JsonView data={results} />
                            ) : (
                                <div className="flex justify-center items-center h-32">
                                    <p className="text-gray-600 dark:text-gray-300">No results available</p>
                                </div>
                            )}
                        </div>
                    </Tab.Panel>
                </Tab.Panels>
            </Tab.Group>
        </div>
    );
} 