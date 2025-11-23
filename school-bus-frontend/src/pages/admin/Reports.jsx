import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import api from '../../services/api';

const Reports = () => {
    const [stats, setStats] = useState(null);

    // Dữ liệu mẫu cho biểu đồ
    const dataTrip = [
        { name: 'T2', trips: 40 }, { name: 'T3', trips: 30 },
        { name: 'T4', trips: 45 }, { name: 'T5', trips: 50 }, { name: 'T6', trips: 35 }
    ];
    const dataStatus = [
        { name: 'Đúng giờ', value: 80, color: '#22c55e' },
        { name: 'Trễ', value: 10, color: '#f59e0b' },
        { name: 'Hủy', value: 5, color: '#ef4444' },
    ];

    useEffect(() => {
        // Gọi API thật để lấy số liệu tổng
        api.get('/reports/daily/dashboard_stats/').then(res => setStats(res.data)).catch(console.error);
    }, []);

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-800">Báo cáo hoạt động</h2>
            
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-6 rounded-xl shadow border-l-4 border-blue-500">
                    <h3 className="text-gray-500 text-sm">Tổng chuyến hôm nay</h3>
                    <p className="text-3xl font-bold">{stats?.total_trips_today || 0}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow border-l-4 border-green-500">
                    <h3 className="text-gray-500 text-sm">Đang hoạt động</h3>
                    <p className="text-3xl font-bold text-green-600">{stats?.trips_active || 0}</p>
                </div>
                 <div className="bg-white p-6 rounded-xl shadow border-l-4 border-purple-500">
                    <h3 className="text-gray-500 text-sm">Tổng người dùng</h3>
                    <p className="text-3xl font-bold">{stats?.total_users || 0}</p>
                </div>
                 <div className="bg-white p-6 rounded-xl shadow border-l-4 border-red-500">
                    <h3 className="text-gray-500 text-sm">Đã hủy</h3>
                    <p className="text-3xl font-bold text-red-600">{stats?.trips_cancelled || 0}</p>
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-xl shadow h-80">
                    <h3 className="font-bold mb-4">Lượng chuyến đi trong tuần</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={dataTrip}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="trips" fill="#3b82f6" radius={[4,4,0,0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
                 <div className="bg-white p-6 rounded-xl shadow h-80 flex flex-col items-center">
                    <h3 className="font-bold mb-4 w-full text-left">Tỷ lệ hoàn thành</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie data={dataStatus} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                                {dataStatus.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default Reports;