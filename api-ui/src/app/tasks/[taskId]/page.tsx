'use client';

import { useParams } from 'next/navigation';
import MainLayout from '../../../components/MainLayout';
import TaskDetails from '../../../components/TaskDetails';

export default function TaskDetailPage() {
    const params = useParams();
    const taskId = params.taskId as string;

    return (
        <MainLayout>
            <TaskDetails taskId={taskId} />
        </MainLayout>
    );
} 