import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';

// Layouts
import AdminLayout from './layouts/AdminLayout';
import DriverLayout from './layouts/DriverLayout';
import ParentLayout from './layouts/ParentLayout'; // Sẽ tạo layout này ngay sau đây
import Drivers from './pages/admin/Drivers';
import Parents from './pages/admin/Parents';
import LiveMap from './pages/admin/LiveMap';
import Trips from './pages/admin/Trips';


// Pages (Admin)
import Dashboard from './pages/admin/Dashboard';
import Users from './pages/admin/Users';
import Students from './pages/admin/Students';
import RoutesPage from './pages/admin/Routes';
import Vehicles from './pages/admin/Vehicles';
import RouteDetail from './pages/admin/RouteDetail';
// Pages (Driver)
import DriverHome from './pages/driver/Home';
import TripTracking from './pages/driver/TripTracking';
import Reports from './pages/admin/Reports';
import Backup from './pages/admin/Backup';

// Pages (Parent)
import ParentHome from './pages/parent/Home';
import ChildTracking from './pages/parent/ChildTracking';
import FindRoute from './pages/parent/FindRoute';

// Component bảo vệ Route
const ProtectedRoute = ({ allowedRoles }) => {
    const { user } = useAuth();
    
    if (!user) return <Navigate to="/login" replace />;
    if (allowedRoles && !allowedRoles.includes(user.role)) {
        return <div className="p-10 text-red-500 text-center font-bold">Bạn không có quyền truy cập trang này.</div>;
    }
    return <Outlet />;
};

function App() {
    return (
        <AuthProvider>
            <Router>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    
                    {/* --- ADMIN ROUTES --- */}
                    <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
                        <Route path="/admin" element={<AdminLayout />}>
                            <Route index element={<Navigate to="dashboard" replace />} />
                            <Route path="trips" element={<Trips />} />
                            <Route path="dashboard" element={<Dashboard />} />
                            <Route path="users" element={<Users />} />
                            <Route path="students" element={<Students />} />
                            <Route path="routes" element={<RoutesPage />} />
                            <Route path="vehicles" element={<Vehicles />} />
                            
                            <Route path="drivers" element={<Drivers />} />
                            <Route path="parents" element={<Parents />} />
                            <Route path="tracking" element={<LiveMap />} />
                            <Route path="reports" element={<Reports />} />
                            <Route path="backup" element={<Backup />} />    
                            <Route path="routes" element={<RoutesPage />} />
                            <Route path="routes/:id" element={<RouteDetail />} />
                        </Route>
                    </Route>

                    {/* --- DRIVER ROUTES --- */}
                    <Route element={<ProtectedRoute allowedRoles={['driver']} />}>
                        <Route path="/driver" element={<DriverLayout />}>
                            <Route index element={<Navigate to="home" replace />} />
                            <Route path="home" element={<DriverHome />} />
                            <Route path="trip/:tripId" element={<TripTracking />} />
                            <Route path="history" element={<h1 className="p-4">Lịch sử (Coming soon)</h1>} />
                        </Route>
                    </Route>

                    {/* --- PARENT ROUTES --- */}
                    <Route element={<ProtectedRoute allowedRoles={['parent']} />}>
                         {/* Bạn cần tạo file ParentLayout.jsx ở bước tiếp theo nếu chưa có, 
                             hoặc tạm thời dùng Outlet nếu muốn test nhanh */}
                        <Route path="/parent" element={<ParentLayout />}>
                            <Route index element={<Navigate to="home" replace />} />
                            <Route path="home" element={<ParentHome />} />
                            <Route path="tracking/:tripId" element={<ChildTracking />} />
                            <Route path="find-route" element={<FindRoute />} />
                            <Route path="notifications" element={<h1 className="p-4">Thông báo (Coming soon)</h1>} />
                        </Route>
                    </Route>

                    <Route path="/" element={<Navigate to="/login" />} />
                </Routes>
            </Router>
        </AuthProvider>
    );
}

export default App;