import { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
    FaHome, FaUsers, FaUserTie, FaUserFriends, FaBus, 
    FaRoute, FaMapMarkedAlt, FaSignOutAlt, FaBars, FaChartBar, FaDatabase 
} from 'react-icons/fa';

const AdminLayout = () => {
    const { user, logout } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    const menuItems = [
        { path: '/admin/dashboard', name: 'Dashboard', icon: <FaHome /> },
        { path: '/admin/users', name: 'Người dùng', icon: <FaUsers /> },
        { path: '/admin/drivers', name: 'Tài xế', icon: <FaUserTie /> },
        { path: '/admin/parents', name: 'Phụ huynh', icon: <FaUserFriends /> },
        { path: '/admin/students', name: 'Học sinh', icon: <FaUsers /> },
        { path: '/admin/vehicles', name: 'Xe Bus', icon: <FaBus /> },
        { path: '/admin/routes', name: 'Tuyến đường', icon: <FaRoute /> },
        { path: '/admin/tracking', name: 'Giám sát', icon: <FaMapMarkedAlt /> },
        { path: '/admin/reports', name: 'Báo cáo', icon: <FaChartBar /> },
        { path: '/admin/backup', name: 'Sao lưu', icon: <FaDatabase /> },   
        { path: '/admin/trips', name: 'Chuyến đi', icon: <FaCalendarCheck /> },
    ];

    return (
        <div className="flex h-screen bg-gray-100">
            {/* Sidebar */}
            <div className={`${isSidebarOpen ? 'w-64' : 'w-20'} bg-slate-800 text-white transition-all duration-300 flex flex-col`}>
                <div className="p-4 flex items-center justify-between border-b border-slate-700">
                    <h1 className={`font-bold text-xl ${!isSidebarOpen && 'hidden'}`}>School Bus</h1>
                    <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 hover:bg-slate-700 rounded">
                        <FaBars />
                    </button>
                </div>
                
                <nav className="flex-1 overflow-y-auto py-4">
                    <ul className="space-y-1">
                        {menuItems.map((item) => (
                            <li key={item.path}>
                                <Link 
                                    to={item.path}
                                    className={`flex items-center px-4 py-3 hover:bg-slate-700 transition-colors ${
                                        location.pathname === item.path ? 'bg-slate-700 border-l-4 border-blue-500' : ''
                                    }`}
                                >
                                    <span className="text-xl">{item.icon}</span>
                                    <span className={`ml-3 ${!isSidebarOpen && 'hidden'}`}>{item.name}</span>
                                </Link>
                            </li>
                        ))}
                    </ul>
                </nav>

                <div className="p-4 border-t border-slate-700">
                    <button 
                        onClick={logout}
                        className="flex items-center w-full px-4 py-2 text-red-400 hover:bg-slate-700 rounded transition-colors"
                    >
                        <FaSignOutAlt />
                        <span className={`ml-3 ${!isSidebarOpen && 'hidden'}`}>Đăng xuất</span>
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <header className="bg-white shadow-sm h-16 flex items-center justify-between px-6">
                    <h2 className="text-xl font-semibold text-gray-800">
                        {menuItems.find(i => i.path === location.pathname)?.name || 'Admin Portal'}
                    </h2>
                    <div className="flex items-center gap-3">
                        <span className="text-gray-600">Xin chào, <b>{user?.full_name || user?.username}</b></span>
                        <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                            {user?.full_name?.charAt(0) || 'A'}
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default AdminLayout;