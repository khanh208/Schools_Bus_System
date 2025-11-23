import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { FaHome, FaBell, FaSignOutAlt, FaSearchLocation } from 'react-icons/fa';

const ParentLayout = () => {
    const { logout, user } = useAuth();
    const location = useLocation();

    const navItems = [
        { path: '/parent/home', icon: <FaHome />, label: 'Trang chủ' },
        { path: '/parent/find-route', icon: <FaSearchLocation />, label: 'Tìm tuyến' },
        { path: '/parent/notifications', icon: <FaBell />, label: 'Thông báo' },
    ];

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white px-4 py-3 shadow-sm flex justify-between items-center sticky top-0 z-20">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
                        {user?.full_name?.charAt(0)}
                    </div>
                    <div>
                        <h1 className="font-bold text-gray-800 text-sm leading-tight">School Bus</h1>
                        <p className="text-xs text-gray-500">Phụ huynh</p>
                    </div>
                </div>
                <button onClick={logout} className="text-gray-400 hover:text-red-500">
                    <FaSignOutAlt />
                </button>
            </header>

            {/* Content */}
            <main className="flex-1 overflow-y-auto p-4 pb-24">
                <Outlet />
            </main>

            {/* Bottom Nav */}
            <nav className="fixed bottom-4 left-4 right-4 bg-white rounded-2xl shadow-lg border border-gray-100 p-2 flex justify-around items-center z-20">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                        <Link 
                            key={item.path} 
                            to={item.path}
                            className={`p-3 rounded-xl transition-all duration-300 flex gap-2 items-center ${
                                isActive ? 'bg-blue-600 text-white shadow-md px-4' : 'text-gray-400 hover:bg-gray-50'
                            }`}
                        >
                            <span className="text-xl">{item.icon}</span>
                            {isActive && <span className="text-xs font-bold whitespace-nowrap">{item.label}</span>}
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
};

export default ParentLayout;