import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { FaCalendarAlt, FaRoute, FaClock, FaUsers } from 'react-icons/fa';

const DriverHome = () => {
    const [trips, setTrips] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchTrips = async () => {
            try {
                // Gọi API lấy chuyến đi hôm nay của tài xế
                const res = await api.get('/tracking/trips/today/');
                setTrips(res.data);
            } catch (error) {
                console.error("Lỗi tải chuyến đi:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchTrips();
    }, []);

    const getStatusBadge = (status) => {
        const styles = {
            scheduled: 'bg-blue-100 text-blue-800',
            in_progress: 'bg-green-100 text-green-800 border border-green-200 animate-pulse',
            completed: 'bg-gray-100 text-gray-800',
            cancelled: 'bg-red-100 text-red-800'
        };
        const labels = {
            scheduled: 'Sắp chạy',
            in_progress: 'Đang chạy',
            completed: 'Hoàn thành',
            cancelled: 'Đã hủy'
        };
        return (
            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${styles[status] || styles.completed}`}>
                {labels[status] || status}
            </span>
        );
    };

    return (
        <div className="space-y-4">
            <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                <FaCalendarAlt className="text-blue-600" /> Lịch trình hôm nay
            </h2>

            {loading ? (
                <div className="text-center py-10 text-gray-500">Đang tải lịch trình...</div>
            ) : trips.length === 0 ? (
                <div className="bg-white p-6 rounded-xl shadow text-center">
                    <p className="text-gray-500">Hôm nay bạn không có chuyến nào.</p>
                </div>
            ) : trips.map(trip => (
                <div 
                    key={trip.id} 
                    onClick={() => navigate(`/driver/trip/${trip.id}`)}
                    className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 active:bg-blue-50 transition-colors cursor-pointer relative overflow-hidden"
                >
                    {trip.status === 'in_progress' && (
                        <div className="absolute top-0 left-0 w-1 h-full bg-green-500"></div>
                    )}
                    
                    <div className="flex justify-between items-start mb-3">
                        <div>
                            <h3 className="font-bold text-gray-800 text-lg">{trip.route_name}</h3>
                            <p className="text-sm text-gray-500 font-mono">{trip.route_code}</p>
                        </div>
                        {getStatusBadge(trip.status)}
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                            <FaClock className="text-gray-400" />
                            <span>{new Date(trip.scheduled_start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <FaUsers className="text-gray-400" />
                            <span>{trip.checked_in_students}/{trip.total_students} HS</span>
                        </div>
                        <div className="col-span-2 flex items-center gap-2">
                            <FaRoute className="text-gray-400" />
                            <span className="truncate">{trip.vehicle_plate}</span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default DriverHome;