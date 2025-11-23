import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { FaArrowLeft, FaMapMarkerAlt, FaUserGraduate, FaPlus, FaTrash } from 'react-icons/fa';

const RouteDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [route, setRoute] = useState(null);
    const [stops, setStops] = useState([]);
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);

    // Form thêm điểm dừng
    const [newStop, setNewStop] = useState({ 
        stop_name: '', 
        stop_order: 1, 
        lat: 10.762622, 
        lng: 106.660172,
        estimated_arrival: '07:00' 
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [resRoute, resStops, resStudents] = await Promise.all([
                    api.get(`/routes/routes/${id}/`),
                    api.get(`/routes/routes/${id}/stops/`),
                    api.get(`/routes/routes/${id}/students/`)
                ]);
                setRoute(resRoute.data);
                setStops(resStops.data);
                setStudents(resStudents.data);
                // Tự động tăng thứ tự điểm dừng tiếp theo
                setNewStop(prev => ({...prev, stop_order: resStops.data.length + 1}));
            } catch (error) {
                alert("Lỗi tải dữ liệu");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    const handleAddStop = async (e) => {
        e.preventDefault();
        try {
            await api.post('/routes/stops/', { ...newStop, route: id });
            alert("Thêm điểm dừng thành công!");
            // Reload stops
            const res = await api.get(`/routes/routes/${id}/stops/`);
            setStops(res.data);
            setNewStop(prev => ({...prev, stop_name: '', stop_order: res.data.length + 1}));
        } catch (error) {
            alert("Lỗi thêm điểm dừng: " + JSON.stringify(error.response?.data));
        }
    };

    const handleDeleteStop = async (stopId) => {
        if (window.confirm("Xóa điểm dừng này?")) {
            await api.delete(`/routes/stops/${stopId}/`);
            setStops(stops.filter(s => s.id !== stopId));
        }
    };

    if (loading) return <div className="p-6">Đang tải...</div>;
    if (!route) return <div className="p-6">Không tìm thấy tuyến.</div>;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <button onClick={() => navigate('/admin/routes')} className="p-2 bg-white rounded shadow hover:bg-gray-50">
                    <FaArrowLeft />
                </button>
                <div>
                    <h2 className="text-2xl font-bold text-gray-800">{route.route_name}</h2>
                    <p className="text-gray-500">{route.route_code} • {route.route_type}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Cột trái: Danh sách Điểm dừng */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white rounded-xl shadow p-6">
                        <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                            <FaMapMarkerAlt className="text-red-500"/> Lộ trình & Điểm dừng
                        </h3>
                        
                        <div className="space-y-3">
                            {stops.map((stop) => (
                                <div key={stop.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-red-100 text-red-600 flex items-center justify-center font-bold text-sm">
                                            {stop.stop_order}
                                        </div>
                                        <div>
                                            <p className="font-medium">{stop.stop_name}</p>
                                            <p className="text-xs text-gray-500">Đến: {stop.estimated_arrival}</p>
                                        </div>
                                    </div>
                                    <button onClick={() => handleDeleteStop(stop.id)} className="text-gray-400 hover:text-red-500">
                                        <FaTrash />
                                    </button>
                                </div>
                            ))}
                        </div>

                        {/* Form thêm nhanh */}
                        <form onSubmit={handleAddStop} className="mt-6 pt-4 border-t grid grid-cols-12 gap-2">
                            <input 
                                type="number" placeholder="STT" className="col-span-2 border p-2 rounded" required
                                value={newStop.stop_order} onChange={e => setNewStop({...newStop, stop_order: e.target.value})}
                            />
                            <input 
                                placeholder="Tên điểm dừng" className="col-span-5 border p-2 rounded" required
                                value={newStop.stop_name} onChange={e => setNewStop({...newStop, stop_name: e.target.value})}
                            />
                            <input 
                                type="time" className="col-span-3 border p-2 rounded" required
                                value={newStop.estimated_arrival} onChange={e => setNewStop({...newStop, estimated_arrival: e.target.value})}
                            />
                            <button className="col-span-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-bold">
                                <FaPlus />
                            </button>
                        </form>
                        <p className="text-xs text-gray-400 mt-2">* Nhập tọa độ Lat/Lng chi tiết trong chỉnh sửa</p>
                    </div>
                </div>

                {/* Cột phải: Danh sách Học sinh */}
                <div className="space-y-6">
                    <div className="bg-white rounded-xl shadow p-6">
                        <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                            <FaUserGraduate className="text-blue-600"/> Học sinh ({students.length})
                        </h3>
                        <div className="max-h-[500px] overflow-y-auto space-y-3">
                            {students.length === 0 ? (
                                <p className="text-gray-500 text-sm text-center py-4">Chưa có học sinh đăng ký</p>
                            ) : students.map((assignment) => (
                                <div key={assignment.id} className="flex items-center gap-3 p-2 border-b last:border-0">
                                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                                        <FaUserGraduate size={14} className="text-gray-500"/>
                                    </div>
                                    <div className="overflow-hidden">
                                        <p className="font-medium text-sm truncate">{assignment.student_name}</p>
                                        <p className="text-xs text-gray-500">Đón tại: {assignment.stop_name}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RouteDetail;