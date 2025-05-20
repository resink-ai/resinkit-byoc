'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { notification, Input, Button, Form, Typography } from 'antd';
import { useForm as useReactHookForm } from 'react-hook-form';
import taskService from '../app/api/taskService';

const { TextArea } = Input;
const { Title } = Typography;

export default function TaskSubmissionForm() {
    const router = useRouter();
    const [submitting, setSubmitting] = useState(false);
    const { handleSubmit } = useReactHookForm();
    const [yamlInput, setYamlInput] = useState('');

    // Handle form submission
    const onSubmit = async (data: any) => {
        setSubmitting(true);

        try {
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

    return (
        <div className="bg-white shadow-md rounded-lg p-6">
            <Title level={4} className="mb-6">
                Submit New Task
            </Title>

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
        </div>
    );
} 