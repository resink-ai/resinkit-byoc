import Link from 'next/link';
import { ReactNode } from 'react';
import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';
import { Layout, Menu, Typography, notification } from 'antd';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

interface MainLayoutProps {
    children: ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
    // Configure notification globally
    notification.config({
        placement: 'topRight',
        duration: 5,
    });

    return (
        <Layout className="h-screen">
            {/* Sidebar */}
            <Sider
                width={256}
                className="hidden md:block"
                theme="light"
                breakpoint="lg"
                collapsedWidth="0"
            >
                <div className="py-4">
                    <div className="px-6 py-2">
                        <Title level={4} className="m-0">Resinkit</Title>
                    </div>
                    <Menu
                        mode="inline"
                        defaultSelectedKeys={['tasks']}
                        className="mt-6"
                        items={[
                            {
                                key: 'tasks',
                                icon: <ClipboardDocumentListIcon className="w-5 h-5" />,
                                label: <Link href="/tasks">Tasks</Link>,
                            }
                        ]}
                    />
                </div>
            </Sider>

            {/* Main content */}
            <Layout>
                {/* Header */}
                <Header className="bg-white shadow-md px-6 flex items-center">
                    <Title level={4} className="m-0 md:hidden">Resinkit</Title>
                </Header>

                {/* Main content container */}
                <Content className="overflow-y-auto p-6">
                    <div className="container mx-auto">
                        {children}
                    </div>
                </Content>
            </Layout>
        </Layout>
    );
} 