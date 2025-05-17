import Link from 'next/link';
import { ReactNode } from 'react';
import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

interface MainLayoutProps {
    children: ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
            {/* Sidebar */}
            <aside className="z-20 flex-shrink-0 hidden w-64 overflow-y-auto bg-white dark:bg-gray-800 md:block">
                <div className="py-4">
                    <div className="px-6 py-2">
                        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                            Resinkit
                        </h2>
                    </div>
                    <ul className="mt-6">
                        <li className="relative px-6 py-3">
                            <span className="absolute inset-y-0 left-0 w-1 bg-primary rounded-tr-lg rounded-br-lg" />
                            <Link
                                href="/tasks"
                                className="inline-flex items-center w-full text-sm font-semibold transition-colors duration-150 hover:text-primary dark:hover:text-primary"
                            >
                                <ClipboardDocumentListIcon className="w-5 h-5 mr-3" />
                                <span>Tasks</span>
                            </Link>
                        </li>
                    </ul>
                </div>
            </aside>

            {/* Main content */}
            <div className="flex flex-col flex-1 w-full overflow-y-auto">
                {/* Header */}
                <header className="z-10 py-4 bg-white shadow-md dark:bg-gray-800">
                    <div className="container flex items-center justify-between h-full px-6 mx-auto">
                        <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 md:hidden">
                            Resinkit
                        </h2>
                    </div>
                </header>

                {/* Main content container */}
                <main className="h-full overflow-y-auto">
                    <div className="container px-6 mx-auto py-4">
                        {children}
                    </div>
                </main>
            </div>

            {/* Toast container for notifications */}
            <ToastContainer
                position="top-right"
                autoClose={5000}
                hideProgressBar={false}
                newestOnTop
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
                theme="light"
            />
        </div>
    );
} 