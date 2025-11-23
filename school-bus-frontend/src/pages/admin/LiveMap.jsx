import { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import api from '../../services/api';
import L from 'leaflet';
import { FaSync, FaBus } from 'react-icons/fa';

// Fix icon lỗi của Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let BusIcon = L.icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
    shadowUrl: iconShadow,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -10]
});

const LiveMap = () => {
    const [activeTrips, setActiveTrips] = useState([]);
    const [totalVehicles, setTotalVehicles] = useState(0); // State mới: Tổng số xe
    const [lastUpdate, setLastUpdate] = useState(new Date());
    const mapRef = useRef(null);

    const fetchData = async () => {
        try {
            // 1. Lấy tổng số xe trong hệ thống
            const resVehicles = await api.get('/routes/vehicles/');
            // API trả về danh sách hoặc object phân trang (results)
            const vehicleCount = resVehicles.data.count || resVehicles.data.length || resVehicles.data.results?.length || 0;
            setTotalVehicles(vehicleCount);

            // 2. Lấy danh sách chuyến đang chạy
            const resTrips = await api.get('/tracking/trips/active/');
            const trips = resTrips.data || [];
            
            // 3. Lấy chi tiết vị trí cho từng chuyến
            const tripsWithLoc = await Promise.all(trips.map(async (trip) => {
                try {
                    const detail = await api.get(`/tracking/trips/${trip.id}/tracking/`);
                    // Merge dữ liệu: Ưu tiên dữ liệu từ API tracking chi tiết
                    return { 
                        ...trip, 
                        ...detail.data,
                        // Đảm bảo có object current_location để không lỗi render
                        current_location: detail.data.current_location || { lat: 0, lng: 0 }
                    };
                } catch (e) {
                    console.warn(`Không tải được vị trí chuyến ${trip.id}`);
                    return null;
                }
            }));
            
            // Lọc bỏ các chuyến lỗi hoặc chưa có tọa độ
            const validTrips = tripsWithLoc.filter(t => t && t.current_location && t.current_location.lat !== 0);
            
            setActiveTrips(validTrips);
            setLastUpdate(new Date());
        } catch (error) {
            console.error("Lỗi tải dữ liệu giám sát:", error);
        }
    };

    // Auto refresh mỗi 10 giây
    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] bg-white rounded-lg shadow overflow-hidden relative">
            {/* Header */}
            <div className="p-4 border-b flex justify-between items-center bg-white z-10">
                <div>
                    <h2 className="font-bold text-lg text-gray-800 flex items-center gap-2">
                        <FaBus className="text-blue-600" /> Giám sát Hạm đội
                    </h2>
                    <p className="text-xs text-gray-500">
                        Cập nhật: {lastUpdate.toLocaleTimeString()}
                    </p>
                </div>
                <button 
                    onClick={fetchData}
                    className="p-2 hover:bg-gray-100 rounded-full text-blue-600 transition-colors"
                    title="Làm mới ngay"
                >
                    <FaSync />
                </button>
            </div>

            {/* Map */}
            <div className="flex-1 relative z-0">
                <MapContainer 
                    center={[10.762622, 106.660172]} 
                    zoom={12} 
                    style={{ height: "100%", width: "100%" }}
                    ref={mapRef}
                >
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; OpenStreetMap'
                    />
                    
                    {activeTrips.map(trip => (
                        <Marker 
                            key={trip.trip?.id || trip.id}
                            position={[
                                trip.current_location.lat, 
                                trip.current_location.lng
                            ]}
                            icon={BusIcon}
                        >
                            <Popup>
                                <div className="min-w-[200px]">
                                    <h4 className="font-bold text-blue-700">
                                        {trip.trip?.route?.name || trip.route_name || 'Chuyến đi'}
                                    </h4>
                                    <div className="text-sm space-y-1 mt-2">
                                        <p>🚗 <b>Xe:</b> {trip.trip?.vehicle?.plate || trip.vehicle_plate}</p>
                                        <p>👤 <b>Tài xế:</b> {trip.trip?.driver?.name || trip.driver_name}</p>
                                        <p>💨 <b>Tốc độ:</b> {Math.round(trip.current_location.speed || 0)} km/h</p>
                                        <p>⏱ <b>Tiến độ:</b> {trip.progress_percentage || 0}%</p>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
                
                {/* Bảng thống kê nổi (Overlay Stats) */}
                <div className="absolute top-4 right-4 bg-white/90 backdrop-blur p-4 rounded-xl shadow-lg z-[1000] min-w-[200px] border border-gray-200">
                    <h3 className="font-bold text-gray-700 mb-2 border-b pb-2">Trạng thái hoạt động</h3>
                    <ul className="space-y-2 text-sm">
                        <li className="flex justify-between">
                            <span>Tổng số xe:</span>
                            <span className="font-bold text-gray-800">{totalVehicles}</span>
                        </li>
                        <li className="flex justify-between text-green-600">
                            <span>Đang chạy:</span>
                            <span className="font-bold">{activeTrips.length}</span>
                        </li>
                        <li className="flex justify-between text-gray-400">
                            <span>Đang nghỉ:</span>
                            {/* Tự động tính số xe nghỉ */}
                            <span className="font-bold">{Math.max(0, totalVehicles - activeTrips.length)}</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default LiveMap;