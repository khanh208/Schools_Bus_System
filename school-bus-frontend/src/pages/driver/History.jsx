import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
// THÊM FaUsers VÀO ĐÂY
import { FaHistory, FaRoute, FaCalendarCheck, FaCheckCircle, FaUsers } from 'react-icons/fa';

const History = () => {
    const [trips, setTrips] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                // Gọi API lấy các chuyến đã hoàn thành
                const res = await api.get('/tracking/trips/?status=completed');
                setTrips(res.data.results || res.data);
            } catch (error) {
                console.error("Lỗi tải lịch sử:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('vi-VN', {
            weekday: 'long', year: 'numeric', month: 'numeric', day: 'numeric'
        });
    };

    const formatTime = (timeString) => {
        if (!timeString) return '--:--';
        return new Date(timeString).toLocaleTimeString('vi-VN', {
            hour: '2-digit', minute: '2-digit'
        });
    };

    return (
        <div className="flex flex-col h-full bg-gray-50">
            {/* Header */}
            <div className="bg-white p-4 shadow-sm sticky top-0 z-10 border-b border-gray-200">
                <div className="flex items-center gap-2">
                    <FaHistory className="text-blue-600 text-xl" />
                    <h2 className="text-lg font-bold text-gray-800">Lịch sử hoạt động</h2>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 pb-24 space-y-4">
                {loading ? (
                    <div className="text-center py-10 text-gray-400">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                        Đang tải dữ liệu...
                    </div>
                ) : trips.length === 0 ? (
                    <div className="text-center py-20 text-gray-400 flex flex-col items-center">
                        <FaCalendarCheck size={48} className="mb-4 opacity-20" />
                        <p>Bạn chưa có chuyến đi nào hoàn thành.</p>
                    </div>
                ) : (
                    trips.map(trip => (
                        <div 
                            key={trip.id} 
                            onClick={() => navigate(`/driver/trip/${trip.id}`)}
                            className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 active:scale-[0.98] transition-transform cursor-pointer"
                        >
                            {/* Date & Status */}
                            <div className="flex justify-between items-center mb-3 pb-2 border-b border-gray-50">
                                <span className="text-sm font-bold text-gray-600">
                                    {formatDate(trip.trip_date)}
                                </span>
                                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full flex items-center gap-1">
                                    <FaCheckCircle size={10} /> Hoàn thành
                                </span>
                            </div>

                            {/* Route Info */}
                            <div className="mb-3">
                                <h3 className="font-bold text-gray-800 text-lg flex items-center gap-2">
                                    <FaRoute className="text-blue-500" size={16} />
                                    {trip.route_name}
                                </h3>
                                <p className="text-xs text-gray-500 ml-6 font-mono">{trip.route_code}</p>
                            </div>

                            {/* Details Grid */}
                            <div className="grid grid-cols-2 gap-3 bg-gray-50 p-3 rounded-lg">
                                <div>
                                    <p className="text-xs text-gray-400 mb-1">Giờ chạy thực tế</p>
                                    <p className="text-sm font-bold text-gray-700">
                                        {formatTime(trip.actual_start_time)}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-gray-400 mb-1">Sĩ số</p>
                                    <p className="text-sm font-bold text-gray-700 flex items-center justify-end gap-1">
                                        <FaUsers className="text-gray-400" />
                                        {trip.checked_in_students}/{trip.total_students}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default History;