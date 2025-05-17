'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { notification, Table, Button, Space, Tag, Badge } from 'antd';
import { format } from 'date-fns';
import {
    PlusIcon,
    ArrowUpIcon,
    ArrowDownIcon,
    XCircleIcon,
    EyeIcon,
} from '@heroicons/react/24/outline';
import taskService, { Task, TaskFilter, TaskListResponse } from '../app/api/taskService';
import FilterPanel from '../components/FilterPanel';

export default function TaskList() {
    const router = useRouter();
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [nextPageToken, setNextPageToken] = useState<string | undefined>();
    const [filters, setFilters] = useState<TaskFilter>({
        limit: 20,
        sort_by: 'created_at',
        sort_order: 'desc',
    });
    const [showFilterPanel, setShowFilterPanel] = useState(false);

    const fetchTasks = async () => {
        setLoading(true);
        try {
            const response: TaskListResponse = await taskService.listTasks(filters);
            setTasks(response.tasks || []);
            setNextPageToken(response.next_page_token);
            setError(null);
        } catch (err) {
            setError('Failed to fetch tasks. Please try again.');
            console.error('Error fetching tasks:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
    }, [filters]);

    const handleSort = (column: string) => {
        setFilters(prev => ({
            ...prev,
            sort_by: column,
            sort_order: prev.sort_by === column && prev.sort_order === 'asc' ? 'desc' : 'asc',
        }));
    };

    const handleNextPage = () => {
        if (nextPageToken) {
            setFilters(prev => ({
                ...prev,
                page_token: nextPageToken,
            }));
        }
    };

    const handlePrevPage = () => {
        // This is simplified; in a real app, you'd need to manage previous page tokens
        setFilters(prev => ({
            ...prev,
            page_token: undefined, // Go back to first page
        }));
    };

    const applyFilters = (newFilters: TaskFilter) => {
        setFilters(prev => ({
            ...prev,
            ...newFilters,
            page_token: undefined, // Reset pagination when applying new filters
        }));
        setShowFilterPanel(false);
    };

    const clearFilters = () => {
        setFilters({
            limit: 20,
            sort_by: 'created_at',
            sort_order: 'desc',
        });
        setShowFilterPanel(false);
    };

    const handleCancelTask = async (taskId: string) => {
        if (window.confirm(`Are you sure you want to cancel task ${taskId}?`)) {
            try {
                await taskService.cancelTask(taskId);
                notification.success({
                    message: 'Success',
                    description: 'Task cancellation initiated',
                });
                fetchTasks(); // Refresh the list
            } catch (err) {
                notification.error({
                    message: 'Error',
                    description: 'Failed to cancel task',
                });
                console.error('Error canceling task:', err);
            }
        }
    };

    const handleViewTask = (taskId: string) => {
        router.push(`/tasks/${taskId}`);
    };

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

    const renderSortIcon = (column: string) => {
        if (filters.sort_by !== column) return null;

        return filters.sort_order === 'asc'
            ? <ArrowUpIcon className="w-4 h-4 inline ml-1" />
            : <ArrowDownIcon className="w-4 h-4 inline ml-1" />;
    };

    return (
        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-4">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                    Task Dashboard
                </h2>
                <div className="flex space-x-2">
                    <button
                        onClick={() => setShowFilterPanel(!showFilterPanel)}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                        {showFilterPanel ? 'Hide Filters' : 'Show Filters'}
                    </button>
                    <button
                        onClick={() => router.push('/tasks/new')}
                        className="flex items-center px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-dark"
                    >
                        <PlusIcon className="w-5 h-5 mr-2" />
                        Submit New Task
                    </button>
                </div>
            </div>

            {/* Filter Panel */}
            {showFilterPanel && (
                <FilterPanel
                    currentFilters={filters}
                    onApplyFilters={applyFilters}
                    onClearFilters={clearFilters}
                />
            )}

            {/* Error Message */}
            {error && (
                <div className="mb-4 p-4 text-sm text-red-700 bg-red-100 rounded-lg">
                    {error}
                </div>
            )}

            {/* Task Table */}
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left text-gray-500 dark:text-gray-400">
                    <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                        <tr>
                            <th
                                scope="col"
                                className="px-6 py-3 cursor-pointer"
                                onClick={() => handleSort('id')}
                            >
                                Task ID {renderSortIcon('id')}
                            </th>
                            <th
                                scope="col"
                                className="px-6 py-3 cursor-pointer"
                                onClick={() => handleSort('task_type')}
                            >
                                Task Type {renderSortIcon('task_type')}
                            </th>
                            <th
                                scope="col"
                                className="px-6 py-3 cursor-pointer"
                                onClick={() => handleSort('status')}
                            >
                                Status {renderSortIcon('status')}
                            </th>
                            <th
                                scope="col"
                                className="px-6 py-3 cursor-pointer"
                                onClick={() => handleSort('created_at')}
                            >
                                Created At {renderSortIcon('created_at')}
                            </th>
                            <th scope="col" className="px-6 py-3">
                                Tags
                            </th>
                            <th scope="col" className="px-6 py-3">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan={6} className="px-6 py-4 text-center">
                                    Loading tasks...
                                </td>
                            </tr>
                        ) : tasks.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="px-6 py-4 text-center">
                                    No tasks found. Try adjusting your filters.
                                </td>
                            </tr>
                        ) : (
                            tasks.map((task) => (
                                <tr
                                    key={task.id}
                                    className="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                                >
                                    <td
                                        className="px-6 py-4 font-medium text-primary cursor-pointer"
                                        onClick={() => handleViewTask(task.id)}
                                    >
                                        {task.id}
                                    </td>
                                    <td className="px-6 py-4">{task.task_type}</td>
                                    <td className="px-6 py-4">
                                        <span
                                            className={`${getStatusColor(
                                                task.status
                                            )} px-2 py-1 rounded-full text-xs font-medium`}
                                        >
                                            {task.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        {format(new Date(task.created_at), 'MMM d, yyyy HH:mm:ss')}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-wrap gap-1">
                                            {task.tags?.map((tag) => (
                                                <span
                                                    key={`${task.id}-${tag}`}
                                                    className="bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 text-xs font-medium px-2 py-0.5 rounded"
                                                >
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex space-x-2">
                                            <button
                                                onClick={() => handleViewTask(task.id)}
                                                title="View Details"
                                                className="text-blue-600 hover:text-blue-900"
                                            >
                                                <EyeIcon className="w-5 h-5" />
                                            </button>
                                            {['pending', 'running'].includes(task.status.toLowerCase()) && (
                                                <button
                                                    onClick={() => handleCancelTask(task.id)}
                                                    title="Cancel Task"
                                                    className="text-red-600 hover:text-red-900"
                                                >
                                                    <XCircleIcon className="w-5 h-5" />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex justify-between items-center mt-4">
                <div>
                    <button
                        onClick={handlePrevPage}
                        disabled={!filters.page_token}
                        className={`px-3 py-1 rounded ${!filters.page_token
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                            }`}
                    >
                        Previous
                    </button>
                    <button
                        onClick={handleNextPage}
                        disabled={!nextPageToken}
                        className={`ml-2 px-3 py-1 rounded ${!nextPageToken
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                            }`}
                    >
                        Next
                    </button>
                </div>
                <div className="text-sm text-gray-500">
                    Items per page:
                    <select
                        value={filters.limit || 20}
                        onChange={(e) =>
                            setFilters((prev) => ({
                                ...prev,
                                limit: Number(e.target.value),
                                page_token: undefined,
                            }))
                        }
                        className="ml-2 p-1 border rounded"
                    >
                        <option value={10}>10</option>
                        <option value={20}>20</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                    </select>
                </div>
            </div>
        </div>
    );
} 