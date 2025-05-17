'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-toastify';
import { useForm } from 'react-hook-form';
import { Tab } from '@headlessui/react';
import taskService from '../app/api/taskService';

export default function TaskSubmissionForm() {
    const router = useRouter();
    const [submitting, setSubmitting] = useState(false);
    const [inputMethod, setInputMethod] = useState('json');
    const { register, handleSubmit, formState: { errors } } = useForm();
    const [yamlInput, setYamlInput] = useState('');
    const [jsonFields, setJsonFields] = useState<{ key: string; value: string }[]>([
        { key: '', value: '' },
    ]);

    // Add another key-value field to the JSON form
    const addJsonField = () => {
        setJsonFields([...jsonFields, { key: '', value: '' }]);
    };

    // Remove a field from the JSON form
    const removeJsonField = (index: number) => {
        const newFields = [...jsonFields];
        newFields.splice(index, 1);
        setJsonFields(newFields);
    };

    // Update a field in the JSON form
    const updateJsonField = (index: number, field: 'key' | 'value', value: string) => {
        const newFields = [...jsonFields];
        newFields[index][field] = value;
        setJsonFields(newFields);
    };

    // Handle form submission
    const onSubmit = async (data: any) => {
        setSubmitting(true);

        try {
            if (inputMethod === 'json') {
                // Build JSON payload from fields
                const payload: Record<string, any> = {};
                jsonFields.forEach(field => {
                    if (field.key.trim()) {
                        try {
                            // Try to parse as JSON if applicable
                            payload[field.key] = JSON.parse(field.value);
                        } catch {
                            // If not valid JSON, use as string
                            payload[field.key] = field.value;
                        }
                    }
                });

                if (Object.keys(payload).length === 0) {
                    toast.error('Please add at least one key-value pair');
                    setSubmitting(false);
                    return;
                }

                // Submit JSON
                await taskService.submitTask(payload);
            } else {
                // Submit YAML
                if (!yamlInput.trim()) {
                    toast.error('Please enter YAML content');
                    setSubmitting(false);
                    return;
                }
                await taskService.submitTaskYaml(yamlInput);
            }

            toast.success('Task submitted successfully');
            router.push('/tasks');
        } catch (err: any) {
            toast.error(`Failed to submit task: ${err.message || 'Unknown error'}`);
            console.error('Error submitting task:', err);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6">
                Submit New Task
            </h2>

            <Tab.Group defaultIndex={0} onChange={(index) => setInputMethod(index === 0 ? 'json' : 'yaml')}>
                <Tab.List className="flex space-x-1 rounded-xl bg-gray-100 dark:bg-gray-700 p-1 mb-6">
                    <Tab
                        className={({ selected }) =>
                            selected
                                ? 'w-full rounded-lg py-2.5 text-sm font-medium leading-5 bg-white dark:bg-gray-800 shadow text-primary'
                                : 'w-full rounded-lg py-2.5 text-sm font-medium leading-5 text-gray-700 dark:text-gray-400 hover:bg-white/[0.12] hover:text-gray-900 dark:hover:text-white'
                        }
                    >
                        JSON
                    </Tab>
                    <Tab
                        className={({ selected }) =>
                            selected
                                ? 'w-full rounded-lg py-2.5 text-sm font-medium leading-5 bg-white dark:bg-gray-800 shadow text-primary'
                                : 'w-full rounded-lg py-2.5 text-sm font-medium leading-5 text-gray-700 dark:text-gray-400 hover:bg-white/[0.12] hover:text-gray-900 dark:hover:text-white'
                        }
                    >
                        YAML
                    </Tab>
                </Tab.List>
                <Tab.Panels>
                    <Tab.Panel>
                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                            <div className="space-y-4">
                                {jsonFields.map((field, index) => (
                                    <div key={index} className="flex space-x-2">
                                        <div className="w-1/3">
                                            <input
                                                type="text"
                                                placeholder="Key"
                                                value={field.key}
                                                onChange={(e) => updateJsonField(index, 'key', e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                                            />
                                        </div>
                                        <div className="w-2/3 flex space-x-2">
                                            <input
                                                type="text"
                                                placeholder="Value"
                                                value={field.value}
                                                onChange={(e) => updateJsonField(index, 'value', e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => removeJsonField(index)}
                                                className="px-3 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
                                                disabled={jsonFields.length <= 1}
                                            >
                                                &times;
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div>
                                <button
                                    type="button"
                                    onClick={addJsonField}
                                    className="px-4 py-2 text-sm font-medium text-primary bg-white border border-primary rounded-md hover:bg-gray-50"
                                >
                                    Add Field
                                </button>
                            </div>

                            <div className="pt-4 flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => router.push('/tasks')}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {submitting ? 'Submitting...' : 'Submit Task'}
                                </button>
                            </div>
                        </form>
                    </Tab.Panel>
                    <Tab.Panel>
                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                            <div>
                                <textarea
                                    value={yamlInput}
                                    onChange={(e) => setYamlInput(e.target.value)}
                                    placeholder="Enter YAML here..."
                                    rows={10}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary font-mono text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                                />
                            </div>

                            <div className="pt-4 flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => router.push('/tasks')}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {submitting ? 'Submitting...' : 'Submit Task'}
                                </button>
                            </div>
                        </form>
                    </Tab.Panel>
                </Tab.Panels>
            </Tab.Group>
        </div>
    );
} 