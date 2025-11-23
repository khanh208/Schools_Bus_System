import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaUserGraduate, FaBus, FaUserTie, FaExclamationTriangle } from 'react-icons/fa';

const Dashboard = () => {
    const [stats, setStats] = useState({
        total_students: 0,
        active_trips: 0,
        total_drivers: 0,
        alerts: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                // Gọi API thống kê thật (Backend cần có endpoint này)
                // Nếu chưa có, bạn có thể dùng tạm các API list để đếm
                const [resStudents, resTrips, resDrivers] = await Promise.all([
                    api.get('/students/students/statistics/'),
                    api.get('/tracking/trips/active/'),
                    api.get('/auth/drivers/')
                ]);

                setStats({
                    total_students: resStudents.data.total_students || 0,
                    active_trips: resTrips.data.length || 0,
                    total_drivers: resDrivers.data.count || 0,
                    alerts: 0 // Tạm thời chưa có logic cảnh báo
                });
            } catch (error) {
                console.error("Lỗi tải thống kê:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
        // Auto refresh mỗi 30s
        const interval = setInterval(fetchStats, 30000);
        return () => clearInterval(interval);
    }, []);

    const cards = [
        { title: 'Tổng số Học sinh', value: stats.total_students, icon: <FaUserGraduate />, color: 'border-l-blue-500 text-blue-600' },
        { title: 'Xe đang chạy', value: stats.active_trips, icon: <FaBus />, color: 'border-l-green-500 text-green-600' },
        { title: 'Tài xế', value: stats.total_drivers, icon: <FaUserTie />, color: 'border-l-yellow-500 text-yellow-600' },
        { title: 'Cảnh báo', value: stats.alerts, icon: <FaExclamationTriangle />, color: 'border-l-red-500 text-red-600' },
    ];

    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Tổng quan hệ thống</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {cards.map((card, index) => (
                    <div key={index} className={`bg-white rounded-xl shadow-sm p-6 border-l-4 ${card.color} flex items-center justify-between`}>
                        <div>
                            <p className="text-sm text-gray-500 font-medium uppercase mb-1">{card.title}</p>
                            <p className="text-3xl font-bold text-gray-800">
                                {loading ? '...' : card.value}
                            </p>
                        </div>
                        <div className={`text-3xl opacity-20`}>{card.icon}</div>
                    </div>
                ))}
            </div>

            {/* Placeholder cho biểu đồ hoặc bản đồ nhỏ */}
            <div className="bg-white rounded-xl shadow-sm p-6 min-h-[400px] flex items-center justify-center text-gray-400 border-2 border-dashed border-gray-100">
                Khu vực hiển thị Biểu đồ thống kê (Đang phát triển)
            </div>
        </div>
    );
};

export default Dashboard;