'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { notification, Tabs, Input, Button, Form, Space, Typography } from 'antd';
import { useForm as useReactHookForm } from 'react-hook-form';
import taskService from '../app/api/taskService';

const { TextArea } = Input;
const { Title } = Typography;

export default function TaskSubmissionForm() {
    const router = useRouter();
    const [submitting, setSubmitting] = useState(false);
    const [inputMethod, setInputMethod] = useState('json');
    const { handleSubmit } = useReactHookForm();
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
                    notification.error({
                        message: 'Error',
                        description: 'Please add at least one key-value pair',
                    });
                    setSubmitting(false);
                    return;
                }

                // Submit JSON
                await taskService.submitTask(payload);
            } else {
                // Submit YAML
                if (!yamlInput.trim()) {
                    notification.error({
                        message: 'Error',
                        description: 'Please enter YAML content',
                    });
                    setSubmitting(false);
                    return;
                }
                await taskService.submitTaskYaml(yamlInput);
            }

            notification.success({
                message: 'Success',
                description: 'Task submitted successfully',
            });
            router.push('/tasks');
        } catch (err: any) {
            notification.error({
                message: 'Error',
                description: `Failed to submit task: ${err.message || 'Unknown error'}`,
            });
            console.error('Error submitting task:', err);
        } finally {
            setSubmitting(false);
        }
    };

    // Tab items configuration
    const tabItems = [
        {
            key: 'json',
            label: 'JSON',
            children: (
                <Form onFinish={handleSubmit(onSubmit)} layout="vertical" className="space-y-4">
                    <div className="space-y-4">
                        {jsonFields.map((field, index) => (
                            <Space key={index} className="flex w-full">
                                <div style={{ width: '33%' }}>
                                    <Input
                                        placeholder="Key"
                                        value={field.key}
                                        onChange={(e) => updateJsonField(index, 'key', e.target.value)}
                                    />
                                </div>
                                <div style={{ width: '67%' }} className="flex space-x-2">
                                    <Input
                                        placeholder="Value"
                                        value={field.value}
                                        onChange={(e) => updateJsonField(index, 'value', e.target.value)}
                                    />
                                    <Button
                                        type="primary"
                                        danger
                                        onClick={() => removeJsonField(index)}
                                        disabled={jsonFields.length <= 1}
                                    >
                                        &times;
                                    </Button>
                                </div>
                            </Space>
                        ))}
                    </div>

                    <div>
                        <Button
                            type="dashed"
                            onClick={addJsonField}
                        >
                            Add Field
                        </Button>
                    </div>

                    <div className="pt-4 flex justify-end space-x-3">
                        <Button
                            onClick={() => router.push('/tasks')}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="primary"
                            htmlType="submit"
                            loading={submitting}
                        >
                            {submitting ? 'Submitting...' : 'Submit Task'}
                        </Button>
                    </div>
                </Form>
            )
        },
        {
            key: 'yaml',
            label: 'YAML',
            children: (
                <Form onFinish={handleSubmit(onSubmit)} layout="vertical" className="space-y-4">
                    <div>
                        <TextArea
                            value={yamlInput}
                            onChange={(e) => setYamlInput(e.target.value)}
                            placeholder="Enter YAML here..."
                            rows={10}
                            className="font-mono text-sm"
                        />
                    </div>

                    <div className="pt-4 flex justify-end space-x-3">
                        <Button
                            onClick={() => router.push('/tasks')}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="primary"
                            htmlType="submit"
                            loading={submitting}
                        >
                            {submitting ? 'Submitting...' : 'Submit Task'}
                        </Button>
                    </div>
                </Form>
            )
        }
    ];

    return (
        <div className="bg-white shadow-md rounded-lg p-6">
            <Title level={4} className="mb-6">
                Submit New Task
            </Title>

            <Tabs
                defaultActiveKey="json"
                onChange={(key) => setInputMethod(key)}
                className="mb-6"
                type="card"
                items={tabItems}
            />
        </div>
    );
} 