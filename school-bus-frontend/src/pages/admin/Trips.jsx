import { useEffect, useState } from 'react';
import api from '../../services/api';
import { FaCalendarAlt, FaSearch, FaBan, FaCheckCircle, FaClock, FaSpinner, FaPlus, FaTimes } from 'react-icons/fa';

const Trips = () => {
    const [trips, setTrips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterDate, setFilterDate] = useState(new Date().toISOString().split('T')[0]);
    
    // State cho Modal & Form
    const [showModal, setShowModal] = useState(false);
    const [routes, setRoutes] = useState([]);
    const [drivers, setDrivers] = useState([]);
    const [vehicles, setVehicles] = useState([]);
    
    const initialForm = {
        route: '',
        driver: '',
        vehicle: '',
        trip_date: filterDate,
        trip_type: 'morning_pickup',
        start_time: '07:00', // Giờ bắt đầu (để ghép vào ngày)
        end_time: '08:00',   // Giờ kết thúc
        notes: ''
    };
    const [formData, setFormData] = useState(initialForm);

    // 1. Tải danh sách chuyến đi
    const fetchTrips = async () => {
        setLoading(true);
        try {
            const res = await api.get(`/tracking/trips/?date=${filterDate}`);
            setTrips(res.data.results || res.data);
        } catch (error) {
            console.error("Lỗi tải chuyến đi:", error);
        } finally {
            setLoading(false);
        }
    };

    // 2. Tải dữ liệu cho Dropdown (Tuyến, Tài xế, Xe)
    const fetchOptions = async () => {
        try {
            const [resRoutes, resDrivers, resVehicles] = await Promise.all([
                api.get('/routes/routes/'),
                api.get('/auth/drivers/?available=true'), // Lấy tài xế đang rảnh
                api.get('/routes/vehicles/?status=active') // Lấy xe đang hoạt động
            ]);
            setRoutes(resRoutes.data.results || resRoutes.data);
            setDrivers(resDrivers.data.results || resDrivers.data);
            setVehicles(resVehicles.data.results || resVehicles.data);
        } catch (e) { console.error(e); }
    };

    useEffect(() => {
        fetchTrips();
    }, [filterDate]);

    // Mở modal tạo mới
    const handleCreate = () => {
        fetchOptions(); // Tải options mới nhất
        setFormData({ ...initialForm, trip_date: filterDate });
        setShowModal(true);
    };

    // Xử lý Lưu chuyến đi mới
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Ghép Ngày + Giờ để tạo DateTime chuẩn ISO
            const startDateTime = `${formData.trip_date}T${formData.start_time}:00`;
            const endDateTime = `${formData.trip_date}T${formData.end_time}:00`;

            await api.post('/tracking/trips/', {
                route: formData.route,
                driver: formData.driver,
                vehicle: formData.vehicle,
                trip_date: formData.trip_date,
                trip_type: formData.trip_type,
                scheduled_start_time: startDateTime,
                scheduled_end_time: endDateTime,
                notes: formData.notes
            });

            alert("Lên lịch chuyến đi thành công!");
            setShowModal(false);
            fetchTrips();
        } catch (error) {
            alert("Lỗi: " + JSON.stringify(error.response?.data || error.message));
        }
    };

    // Hủy chuyến
    const handleCancelTrip = async (id) => {
        const reason = window.prompt("Nhập lý do hủy chuyến:");
        if (reason) {
            try {
                await api.post(`/tracking/trips/${id}/cancel/`, { reason });
                fetchTrips();
            } catch (error) { alert("Lỗi hủy chuyến"); }
        }
    };
    
    // Tự động chọn Xe và Tài xế khi chọn Tuyến (nếu tuyến đã gán sẵn)
    const handleRouteChange = (routeId) => {
        const selectedRoute = routes.find(r => r.id == routeId);
        setFormData(prev => ({
            ...prev,
            route: routeId,
            // Nếu tuyến có gán sẵn thì chọn luôn, không thì giữ nguyên
            driver: selectedRoute?.driver || prev.driver,
            vehicle: selectedRoute?.vehicle || prev.vehicle
        }));
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
                    <div className="flex items-center gap-2 bg-gray-50 p-1 rounded-lg border">
                        <span className="text-gray-500 text-sm pl-2">Ngày:</span>
                        <input 
                            type="date" 
                            className="bg-transparent px-2 py-1 text-sm outline-none"
                            value={filterDate}
                            onChange={(e) => setFilterDate(e.target.value)}
                        />
                    </div>
                    <button onClick={handleCreate} className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 shadow">
                        <FaPlus /> Lên lịch
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
                            <th className="px-6 py-3 font-bold">Loại / Thời gian</th>
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
                                    <div className="text-xs font-bold mb-1 text-gray-500">
                                        {trip.trip_type === 'morning_pickup' ? '☀️ Sáng (Đón)' : '🌙 Chiều (Trả)'}
                                    </div>
                                    <div className="flex items-center gap-2 text-gray-700">
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
                                    {['scheduled'].includes(trip.status) && (
                                        <button 
                                            onClick={() => handleCancelTrip(trip.id)}
                                            className="text-red-500 hover:bg-red-50 px-3 py-1 rounded border border-red-200 text-xs font-bold flex items-center gap-1 ml-auto"
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

            {/* MODAL TẠO CHUYẾN */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1100] p-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-[fadeIn_0.2s]">
                        <div className="p-4 border-b flex justify-between items-center bg-gray-50 rounded-t-2xl">
                            <h3 className="font-bold text-lg text-gray-800">Lên lịch Chuyến đi Mới</h3>
                            <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600"><FaTimes size={20}/></button>
                        </div>
                        
                        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
                            
                            {/* Chọn Tuyến */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Tuyến đường (*)</label>
                                <select required className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={formData.route} onChange={e => handleRouteChange(e.target.value)}>
                                    <option value="">-- Chọn tuyến --</option>
                                    {routes.map(r => (
                                        <option key={r.id} value={r.id}>{r.route_name} ({r.route_code})</option>
                                    ))}
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                {/* Chọn Tài xế */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Tài xế (*)</label>
                                    <select required className="w-full border p-2 rounded outline-none"
                                        value={formData.driver} onChange={e => setFormData({...formData, driver: e.target.value})}>
                                        <option value="">-- Chọn tài xế --</option>
                                        {drivers.map(d => (
                                            <option key={d.id} value={d.id}>{d.user.full_name}</option>
                                        ))}
                                    </select>
                                </div>
                                {/* Chọn Xe */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Xe (*)</label>
                                    <select required className="w-full border p-2 rounded outline-none"
                                        value={formData.vehicle} onChange={e => setFormData({...formData, vehicle: e.target.value})}>
                                        <option value="">-- Chọn xe --</option>
                                        {vehicles.map(v => (
                                            <option key={v.id} value={v.id}>{v.plate_number}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Ngày chạy</label>
                                    <input type="date" required className="w-full border p-2 rounded outline-none"
                                        value={formData.trip_date} onChange={e => setFormData({...formData, trip_date: e.target.value})} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Loại chuyến</label>
                                    <select className="w-full border p-2 rounded outline-none"
                                        value={formData.trip_type} onChange={e => setFormData({...formData, trip_type: e.target.value})}>
                                        <option value="morning_pickup">☀️ Sáng (Đón)</option>
                                        <option value="afternoon_dropoff">🌙 Chiều (Trả)</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Giờ khởi hành</label>
                                    <input type="time" required className="w-full border p-2 rounded outline-none"
                                        value={formData.start_time} onChange={e => setFormData({...formData, start_time: e.target.value})} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Giờ kết thúc (Dự kiến)</label>
                                    <input type="time" required className="w-full border p-2 rounded outline-none"
                                        value={formData.end_time} onChange={e => setFormData({...formData, end_time: e.target.value})} />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú</label>
                                <textarea className="w-full border p-2 rounded outline-none" rows="2"
                                    value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} 
                                    placeholder="Ví dụ: Xe chạy tăng cường..."
                                />
                            </div>

                            <button type="submit" className="w-full bg-green-600 text-white py-3 rounded-xl font-bold hover:bg-green-700 shadow-lg mt-2">
                                Xác nhận Lên lịch
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Trips;