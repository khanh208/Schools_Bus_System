import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { FaBus, FaHistory, FaSignOutAlt, FaUser } from 'react-icons/fa';

const DriverLayout = () => {
    const { logout, user } = useAuth();
    const location = useLocation();

    const navItems = [
        { path: '/driver/home', icon: <FaBus />, label: 'Chuyến đi' },
        { path: '/driver/history', icon: <FaHistory />, label: 'Lịch sử' },
    ];

    return (
        <div className="flex flex-col h-screen bg-gray-100">
            {/* Header Mobile */}
            <header className="bg-blue-600 text-white p-4 shadow-md flex justify-between items-center z-10">
                <div>
                    <h1 className="font-bold text-lg">SchoolBus Driver</h1>
                    <p className="text-xs opacity-90">Xin chào, {user?.full_name}</p>
                </div>
                <button onClick={logout} className="p-2 bg-blue-700 rounded-full hover:bg-blue-800">
                    <FaSignOutAlt />
                </button>
            </header>

            {/* Content Area (Scrollable) */}
            <main className="flex-1 overflow-y-auto p-4 pb-20">
                <Outlet />
            </main>

            {/* Bottom Navigation Bar */}
            <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around items-center h-16 z-10">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                        <Link 
                            key={item.path} 
                            to={item.path}
                            className={`flex flex-col items-center justify-center w-full h-full ${
                                isActive ? 'text-blue-600' : 'text-gray-400 hover:text-gray-600'
                            }`}
                        >
                            <span className="text-xl mb-1">{item.icon}</span>
                            <span className="text-xs font-medium">{item.label}</span>
                        </Link>
                    );
                })}
                <div className="flex flex-col items-center justify-center w-full h-full text-gray-400">
                    <FaUser className="text-xl mb-1" />
                    <span className="text-xs font-medium">Cá nhân</span>
                </div>
            </nav>
        </div>
    );
};

export default DriverLayout;