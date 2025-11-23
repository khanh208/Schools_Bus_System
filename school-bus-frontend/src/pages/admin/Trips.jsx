import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaCalendarAlt, FaSearch, FaBan, FaCheckCircle, FaClock, FaSpinner } from 'react-icons/fa';

const Trips = () => {
    const [trips, setTrips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterDate, setFilterDate] = useState(new Date().toISOString().split('T')[0]); // Mặc định hôm nay

    const fetchTrips = async () => {
        setLoading(true);
        try {
            // Gọi API filter theo ngày
            const res = await api.get(`/tracking/trips/?date=${filterDate}`);
            setTrips(res.data.results || res.data);
        } catch (error) {
            console.error("Lỗi tải danh sách chuyến đi:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTrips();
    }, [filterDate]);

    const handleCancelTrip = async (id) => {
        const reason = window.prompt("Nhập lý do hủy chuyến:");
        if (reason) {
            try {
                await api.post(`/tracking/trips/${id}/cancel/`, { reason });
                alert("Đã hủy chuyến thành công!");
                fetchTrips(); // Reload
            } catch (error) {
                alert("Lỗi hủy chuyến: " + JSON.stringify(error.response?.data || error.message));
            }
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'scheduled': return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-bold">Sắp chạy</span>;
            case 'in_progress': return <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-bold flex items-center gap-1"><FaSpinner className="animate-spin"/> Đang chạy</span>;
            case 'completed': return <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-bold">Hoàn thành</span>;
            case 'cancelled': return <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-bold">Đã hủy</span>;
            default: return status;
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-md min-h-[500px]">
            {/* Header & Filter */}
            <div className="p-6 border-b border-gray-200 flex flex-col sm:flex-row justify-between items-center gap-4">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                    <FaClock className="text-blue-600" /> Quản lý Chuyến đi
                </h2>
                
                <div className="flex items-center gap-2">
                    <span className="text-gray-500 text-sm">Xem ngày:</span>
                    <input 
                        type="date" 
                        className="border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                        value={filterDate}
                        onChange={(e) => setFilterDate(e.target.value)}
                    />
                    <button onClick={fetchTrips} className="bg-gray-100 p-2 rounded-lg hover:bg-gray-200 text-gray-600">
                        <FaSearch />
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
                        <tr>
                            <th className="px-6 py-3 font-bold">ID</th>
                            <th className="px-6 py-3 font-bold">Tuyến đường</th>
                            <th className="px-6 py-3 font-bold">Tài xế & Xe</th>
                            <th className="px-6 py-3 font-bold">Thời gian (Dự kiến)</th>
                            <th className="px-6 py-3 font-bold">Sĩ số</th>
                            <th className="px-6 py-3 font-bold text-center">Trạng thái</th>
                            <th className="px-6 py-3 font-bold text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody className="text-sm divide-y divide-gray-100">
                        {loading ? (
                            <tr><td colSpan="7" className="text-center py-8 text-gray-500">Đang tải dữ liệu...</td></tr>
                        ) : trips.length === 0 ? (
                            <tr><td colSpan="7" className="text-center py-8 text-gray-500">Không có chuyến đi nào trong ngày này.</td></tr>
                        ) : trips.map((trip) => (
                            <tr key={trip.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4 font-mono text-gray-500">#{trip.id}</td>
                                <td className="px-6 py-4">
                                    <div className="font-bold text-gray-800">{trip.route_name}</div>
                                    <div className="text-xs text-gray-500">{trip.route_code}</div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="font-medium text-blue-600">{trip.driver_name}</div>
                                    <div className="text-xs text-gray-500 bg-gray-100 inline-block px-1 rounded mt-1">{trip.vehicle_plate}</div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <FaClock className="text-gray-400"/>
                                        {new Date(trip.scheduled_start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="font-bold">{trip.checked_in_students}</span> / {trip.total_students}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    {getStatusBadge(trip.status)}
                                </td>
                                <td className="px-6 py-4 text-right">
                                    {['scheduled', 'in_progress'].includes(trip.status) && (
                                        <button 
                                            onClick={() => handleCancelTrip(trip.id)}
                                            className="text-red-500 hover:bg-red-50 px-3 py-1 rounded border border-red-200 text-xs font-bold flex items-center gap-1 ml-auto"
                                            title="Hủy chuyến này"
                                        >
                                            <FaBan /> Hủy
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Trips;