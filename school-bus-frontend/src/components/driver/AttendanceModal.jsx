import { useEffect, useState, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import api from '../../services/api';
import { FaPlay, FaStop, FaCheckCircle, FaUserCheck } from 'react-icons/fa';
import L from 'leaflet';
import AttendanceModal from '../../components/driver/AttendanceModal'; // <--- IMPORT MỚI

// --- CẤU HÌNH ICON LEAFLET (Giữ nguyên) ---
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const getSocketUrl = (tripId) => {
    const apiUrl = import.meta.env.VITE_API_URL;
    const baseUrl = apiUrl.replace('http', 'ws').replace('/api', '');
    const token = localStorage.getItem('access_token');
    return token ? `${baseUrl}/ws/trips/${tripId}/?token=${token}` : null;
};

const TripTracking = () => {
    const { tripId } = useParams();
    const navigate = useNavigate();
    const [trip, setTrip] = useState(null);
    const [currentLocation, setCurrentLocation] = useState(null);
    const [isTracking, setIsTracking] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [showAttendance, setShowAttendance] = useState(false); // <--- STATE MỚI
    
    const watchIdRef = useRef(null);
    const ws = useRef(null);
    const socketUrl = useMemo(() => getSocketUrl(tripId), [tripId]);

    // 1. WebSocket (Giữ nguyên logic cũ)
    useEffect(() => {
        if (!socketUrl) return;
        let timeoutId = null;
        const connect = () => {
            if (ws.current) ws.current.close();
            ws.current = new WebSocket(socketUrl);
            ws.current.onopen = () => { setIsConnected(true); };
            ws.current.onclose = () => { 
                setIsConnected(false); 
                timeoutId = setTimeout(connect, 3000); 
            };
            ws.current.onerror = () => ws.current.close();
        };
        connect();
        return () => {
            if (timeoutId) clearTimeout(timeoutId);
            if (ws.current) ws.current.close();
        };
    }, [socketUrl]);

    const sendLocationUpdate = (payload) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(payload));
        }
    };

    // 2. Lấy thông tin chuyến (Giữ nguyên)
    useEffect(() => {
        const fetchTrip = async () => {
            try {
                const res = await api.get(`/tracking/trips/${tripId}/`);
                setTrip(res.data);
                if (res.data.status === 'in_progress') setIsTracking(true);
            } catch (error) { navigate('/driver/home'); }
        };
        fetchTrip();
    }, [tripId, navigate]);

    // 3. GPS (Giữ nguyên)
    useEffect(() => {
        if (isTracking) {
            if ('geolocation' in navigator) {
                watchIdRef.current = navigator.geolocation.watchPosition(
                    (position) => {
                        const { latitude, longitude, speed, heading, accuracy } = position.coords;
                        setCurrentLocation([latitude, longitude]);
                        const payload = { type: 'location_update', lat: latitude, lng: longitude, speed, heading, accuracy };
                        sendLocationUpdate(payload);
                    },
                    (error) => console.error("GPS Error"),
                    { enableHighAccuracy: true, timeout: 5000 }
                );
            }
        } else {
            if (watchIdRef.current !== null) navigator.geolocation.clearWatch(watchIdRef.current);
        }
        return () => { if (watchIdRef.current !== null) navigator.geolocation.clearWatch(watchIdRef.current); };
    }, [isTracking]);

    const handleStartTrip = async () => {
        if (window.confirm('Bắt đầu chuyến đi?')) {
            await api.post(`/tracking/trips/${tripId}/start/`);
            setTrip(prev => ({ ...prev, status: 'in_progress' }));
            setIsTracking(true);
        }
    };

    const handleCompleteTrip = async () => {
        if (window.confirm('Xác nhận hoàn thành?')) {
            await api.post(`/tracking/trips/${tripId}/complete/`);
            setTrip(prev => ({ ...prev, status: 'completed' }));
            setIsTracking(false);
            navigate('/driver/home');
        }
    };

    if (!trip) return <div className="p-5 text-center">Đang tải...</div>;

    return (
        <div className="flex flex-col h-full relative">
            <div className="flex-1 relative z-0">
                <MapContainer center={currentLocation || [10.762, 106.660]} zoom={15} style={{ height: "100%" }}>
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    {currentLocation && <Marker position={currentLocation}><Popup>Bạn ở đây</Popup></Marker>}
                </MapContainer>
            </div>

            <div className="bg-white rounded-t-2xl shadow p-5 z-10 absolute bottom-0 left-0 right-0 pb-20 sm:pb-5">
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h2 className="font-bold text-lg text-gray-800">{trip.route_name}</h2>
                        <div className="flex items-center gap-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                {isConnected ? 'Online' : 'Offline'}
                            </span>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        {/* NÚT ĐIỂM DANH ĐÃ ĐƯỢC KÍCH HOẠT */}
                        <button 
                            onClick={() => setShowAttendance(true)} // <--- SỰ KIỆN MỞ MODAL
                            className="p-3 bg-blue-100 text-blue-600 rounded-full hover:bg-blue-200 shadow-sm transition-colors"
                        >
                            <FaUserCheck size={20} />
                        </button>
                    </div>
                </div>

                {trip.status === 'scheduled' && (
                    <button onClick={handleStartTrip} className="w-full py-3 bg-green-600 text-white rounded-xl font-bold shadow-lg">
                        BẮT ĐẦU CHUYẾN ĐI
                    </button>
                )}
                
                {trip.status === 'in_progress' && (
                    <button onClick={handleCompleteTrip} className="w-full py-3 bg-red-600 text-white rounded-xl font-bold shadow-lg">
                        KẾT THÚC CHUYẾN ĐI
                    </button>
                )}

                {trip.status === 'completed' && (
                    <div className="w-full py-3 bg-gray-500 text-white rounded-xl font-bold text-center">
                        ĐÃ HOÀN THÀNH
                    </div>
                )}
            </div>

            {/* HIỂN THỊ MODAL ĐIỂM DANH */}
            {showAttendance && (
                <AttendanceModal 
                    trip={trip} 
                    onClose={() => setShowAttendance(false)} 
                />
            )}
        </div>
    );
};

export default TripTracking;