'use client';

import { useState, useEffect } from 'react';
import { TaskFilter } from '@/app/api/taskService';

interface FilterPanelProps {
    currentFilters: TaskFilter;
    onApplyFilters: (filters: TaskFilter) => void;
    onClearFilters: () => void;
}

export default function FilterPanel({
    currentFilters,
    onApplyFilters,
    onClearFilters,
}: FilterPanelProps) {
    const [localFilters, setLocalFilters] = useState<TaskFilter>({
        task_type: '',
        status: '',
        task_name_contains: '',
        tags_include_any: '',
        created_after: '',
        created_before: '',
    });

    useEffect(() => {
        // Update local filters when current filters change
        setLocalFilters({
            task_type: currentFilters.task_type || '',
            status: currentFilters.status || '',
            task_name_contains: currentFilters.task_name_contains || '',
            tags_include_any: currentFilters.tags_include_any || '',
            created_after: currentFilters.created_after || '',
            created_before: currentFilters.created_before || '',
        });
    }, [currentFilters]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setLocalFilters((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Filter out empty values
        const filtersToApply: TaskFilter = {};
        Object.entries(localFilters).forEach(([key, value]) => {
            if (value) {
                filtersToApply[key as keyof TaskFilter] = value;
            }
        });

        onApplyFilters(filtersToApply);
    };

    return (
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg mb-6">
            <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">
                Filter Tasks
            </h3>
            <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                        <label
                            htmlFor="task_type"
                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                        >
                            Task Type
                        </label>
                        <input
                            type="text"
                            id="task_type"
                            name="task_type"
                            value={localFilters.task_type}
                            onChange={handleInputChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                            placeholder="Filter by task type"
                        />
                    </div>
                    <div>
                        <label
                            htmlFor="status"
                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                        >
                            Status
                        </label>
                        <select
                            id="status"
                            name="status"
                            value={localFilters.status}
                            onChange={handleInputChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                        >
                            <option value="">All Statuses</option>
                            <option value="pending">Pending</option>
                            <option value="running">Running</option>
                            <option value="success">Success</option>
                            <option value="failed">Failed</option>
                            <option value="canceled">Canceled</option>
                        </select>
                    </div>
                    <div>
                        <label
                            htmlFor="task_name_contains"
                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                        >
                            Task Name Contains
                        </label>
                        <input
                            type="text"
                            id="task_name_contains"
                            name="task_name_contains"
                            value={localFilters.task_name_contains}
                            onChange={handleInputChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                            placeholder="Search in task names"
                        />
                    </div>
                    <div>
                        <label
                            htmlFor="tags_include_any"
                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                        >
                            Tags Include Any
                        </label>
                        <input
                            type="text"
                            id="tags_include_any"
                            name="tags_include_any"
                            value={localFilters.tags_include_any}
                            onChange={handleInputChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                            placeholder="Comma-separated tags"
                        />
                    </div>
                    <div>
                        <label
                            htmlFor="created_after"
                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                        >
                            Created After
                        </label>
                        <input
                            type="datetime-local"
                            id="created_after"
                            name="created_after"
                            value={localFilters.created_after}
                            onChange={handleInputChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                        />
                    </div>
                    <div>
                        <label
                            htmlFor="created_before"
                            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                        >
                            Created Before
                        </label>
                        <input
                            type="datetime-local"
                            id="created_before"
                            name="created_before"
                            value={localFilters.created_before}
                            onChange={handleInputChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                        />
                    </div>
                </div>
                <div className="mt-6 flex justify-end space-x-3">
                    <button
                        type="button"
                        onClick={onClearFilters}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-700 dark:text-white dark:border-gray-600 dark:hover:bg-gray-600"
                    >
                        Clear Filters
                    </button>
                    <button
                        type="submit"
                        className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-dark"
                    >
                        Apply Filters
                    </button>
                </div>
            </form>
        </div>
    );
} 