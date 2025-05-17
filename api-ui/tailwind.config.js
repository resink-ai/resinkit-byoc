/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#0070f3',
                    dark: '#0060df',
                    light: '#339af0',
                },
                secondary: {
                    DEFAULT: '#718096',
                    dark: '#4a5568',
                    light: '#a0aec0',
                },
                success: '#10b981',
                error: '#ef4444',
                warning: '#f59e0b',
                info: '#3b82f6',
            },
        },
    },
    plugins: [],
}; 