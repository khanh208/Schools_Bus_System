import { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import api from '../../services/api';
import L from 'leaflet';
import { FaSync, FaBus } from 'react-icons/fa';

// Icon Xe Bus
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let BusIcon = L.icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png', // Icon xe bus
    shadowUrl: iconShadow,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -10]
});

const LiveMap = () => {
    const [activeTrips, setActiveTrips] = useState([]);
    const [lastUpdate, setLastUpdate] = useState(new Date());
    const mapRef = useRef(null);

    const fetchActiveTrips = async () => {
        try {
            // Gọi API lấy danh sách chuyến đang chạy
            const res = await api.get('/tracking/trips/active/');
            const trips = res.data || [];
            
            // Lấy vị trí mới nhất cho từng trip (API này cần trả về current_location)
            // Nếu API list chưa có location, ta cần gọi chi tiết hoặc backend hỗ trợ.
            // Ở đây giả sử ta gọi detail cho từng chuyến để lấy location chính xác nhất
            const tripsWithLoc = await Promise.all(trips.map(async (trip) => {
                try {
                    const detail = await api.get(`/tracking/trips/${trip.id}/tracking/`);
                    return { ...trip, ...detail.data };
                } catch (e) {
                    return trip;
                }
            }));
            
            setActiveTrips(tripsWithLoc.filter(t => t.current_location));
            setLastUpdate(new Date());
        } catch (error) {
            console.error("Lỗi tải dữ liệu tracking:", error);
        }
    };

    // Auto refresh mỗi 10 giây
    useEffect(() => {
        fetchActiveTrips();
        const interval = setInterval(fetchActiveTrips, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b flex justify-between items-center bg-white z-10">
                <div>
                    <h2 className="font-bold text-lg text-gray-800 flex items-center gap-2">
                        <FaBus className="text-blue-600" /> Giám sát Hạm đội
                    </h2>
                    <p className="text-xs text-gray-500">
                        Cập nhật lúc: {lastUpdate.toLocaleTimeString()} • {activeTrips.length} xe đang chạy
                    </p>
                </div>
                <button 
                    onClick={fetchActiveTrips}
                    className="p-2 hover:bg-gray-100 rounded-full text-blue-600 transition-colors"
                    title="Làm mới"
                >
                    <FaSync />
                </button>
            </div>

            <div className="flex-1 relative">
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
                                    <h4 className="font-bold text-blue-700">{trip.trip?.route_info?.name}</h4>
                                    <div className="text-sm space-y-1 mt-2">
                                        <p>🚗 <b>Xe:</b> {trip.trip?.vehicle_info?.plate}</p>
                                        <p>👤 <b>Tài xế:</b> {trip.trip?.driver_info?.name}</p>
                                        <p>💨 <b>Tốc độ:</b> {Math.round(trip.current_location.speed || 0)} km/h</p>
                                        <p>⏱ <b>Tiến độ:</b> {trip.progress_percentage}%</p>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
                
                {/* Overlay Stats */}
                <div className="absolute top-4 right-4 bg-white/90 backdrop-blur p-4 rounded-xl shadow-lg z-[1000] max-w-xs">
                    <h3 className="font-bold text-gray-700 mb-2">Trạng thái hoạt động</h3>
                    <ul className="space-y-2 text-sm">
                        <li className="flex justify-between">
                            <span>Tổng số xe:</span>
                            <span className="font-bold">10</span>
                        </li>
                        <li className="flex justify-between text-green-600">
                            <span>Đang chạy:</span>
                            <span className="font-bold">{activeTrips.length}</span>
                        </li>
                        <li className="flex justify-between text-gray-400">
                            <span>Đang nghỉ:</span>
                            <span className="font-bold">{10 - activeTrips.length}</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default LiveMap;