import { Outlet } from 'react-router-dom';
import { ThemeProvider } from './ThemeProvider';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { MeshBackground } from './MeshBackground';
import { AmaniChatBubble } from '../ai/AmaniChatBubble';

export function AppLayout() {
    return (
        <ThemeProvider>
            <MeshBackground />
            <div className="flex h-screen overflow-hidden p-4 gap-4">
                {/* Floating Sidebar */}
                <aside className="hidden md:flex flex-col w-64 rounded-2xl glass border-white/10 shadow-2xl overflow-hidden transition-all duration-300">
                    <Sidebar />
                </aside>

                {/* Main Content Area */}
                <main id="main-content" className="flex-1 flex flex-col rounded-2xl glass border-white/10 shadow-2xl overflow-hidden relative" role="main">
                    <Topbar />
                    <div className="flex-1 overflow-y-auto p-6 scrollbar-hide">
                        <Outlet />
                    </div>
                </main>
            </div>

            {/* Global AI Assistant - Available on every page */}
            <AmaniChatBubble />
        </ThemeProvider>
    );
}
