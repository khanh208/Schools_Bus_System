import { useEffect, useState, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import api from '../../services/api';
import { FaPlay, FaStop, FaCheckCircle, FaUserCheck } from 'react-icons/fa';
import L from 'leaflet';
import AttendanceModal from '../../components/driver/AttendanceModal'; // Import Modal Điểm Danh

// Cấu hình Icon Leaflet
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
    const [showAttendance, setShowAttendance] = useState(false); // State cho Modal Điểm danh
    
    const watchIdRef = useRef(null);
    const ws = useRef(null);
    const socketUrl = useMemo(() => getSocketUrl(tripId), [tripId]);

    // 1. Kết nối WebSocket
    useEffect(() => {
        if (!socketUrl) return;
        let timeoutId = null;

        const connect = () => {
            if (ws.current) ws.current.close();

            ws.current = new WebSocket(socketUrl);

            ws.current.onopen = () => {
                console.log('✅ Driver: WS Connected');
                setIsConnected(true);
            };

            ws.current.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'initial_data') {
                        setTrip(prev => ({...prev, ...msg.data}));
                        if (msg.data.status === 'in_progress') setIsTracking(true);
                    }
                } catch (e) { console.error(e); }
            };

            ws.current.onclose = () => {
                console.log('🔌 Driver: WS Closed');
                setIsConnected(false);
                timeoutId = setTimeout(connect, 3000);
            };
            
            ws.current.onerror = (err) => {
                console.error("WS Error", err);
                ws.current.close();
            };
        };

        connect();

        return () => {
            if (timeoutId) clearTimeout(timeoutId);
            if (ws.current) ws.current.close();
        };
    }, [socketUrl]);

    // Hàm gửi dữ liệu
    const sendLocationUpdate = (payload) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(payload));
        } else {
            // console.warn("⚠️ WebSocket not ready, cannot send location");
        }
    };

    // 2. Lấy thông tin chuyến đi (API)
    useEffect(() => {
        const fetchTrip = async () => {
            try {
                const res = await api.get(`/tracking/trips/${tripId}/`);
                setTrip(res.data);
                if (res.data.status === 'in_progress') setIsTracking(true);
            } catch (error) {
                console.error("Lỗi tải chuyến đi:", error);
                navigate('/driver/home');
            }
        };
        fetchTrip();
    }, [tripId, navigate]);

    // 3. GPS Tracking
    useEffect(() => {
        if (isTracking) {
            if ('geolocation' in navigator) {
                console.log("🛰️ Bắt đầu theo dõi GPS...");
                watchIdRef.current = navigator.geolocation.watchPosition(
                    (position) => {
                        const { latitude, longitude, speed, heading, accuracy } = position.coords;
                        setCurrentLocation([latitude, longitude]);

                        const payload = {
                            type: 'location_update',
                            lat: latitude,
                            lng: longitude,
                            speed: speed,
                            heading: heading,
                            accuracy: accuracy,
                            battery_level: 100 
                        };
                        sendLocationUpdate(payload);
                    },
                    (error) => console.error("Lỗi GPS:", error),
                    { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
                );
            } else {
                alert("Trình duyệt không hỗ trợ GPS!");
            }
        } else {
            if (watchIdRef.current !== null) {
                navigator.geolocation.clearWatch(watchIdRef.current);
                watchIdRef.current = null;
            }
        }

        return () => {
            if (watchIdRef.current !== null) navigator.geolocation.clearWatch(watchIdRef.current);
        };
    }, [isTracking]);

    // Xử lý nút bấm
    const handleStartTrip = async () => {
        if (window.confirm('Bắt đầu chuyến đi?')) {
            try {
                await api.post(`/tracking/trips/${tripId}/start/`);
                setTrip(prev => ({ ...prev, status: 'in_progress' }));
                setIsTracking(true);
            } catch (e) { alert("Lỗi bắt đầu chuyến"); }
        }
    };

    const handleCompleteTrip = async () => {
        if (window.confirm('Kết thúc chuyến đi?')) {
            try {
                await api.post(`/tracking/trips/${tripId}/complete/`);
                setTrip(prev => ({ ...prev, status: 'completed' }));
                setIsTracking(false);
                navigate('/driver/home');
            } catch (e) { alert("Lỗi kết thúc chuyến"); }
        }
    };

    if (!trip) return <div className="p-6 text-center">Đang tải dữ liệu...</div>;

    return (
        <div className="flex flex-col h-full relative bg-gray-100">
            {/* Map */}
            <div className="flex-1 z-0 relative">
                <MapContainer 
                    center={currentLocation || [10.762, 106.660]} 
                    zoom={15} 
                    style={{ height: "100%" }}
                >
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    {currentLocation && <Marker position={currentLocation}><Popup>Vị trí hiện tại</Popup></Marker>}
                </MapContainer>
            </div>

            {/* Control Panel */}
            <div className="bg-white rounded-t-3xl shadow-[0_-4px_20px_rgba(0,0,0,0.1)] p-5 z-10 absolute bottom-0 left-0 right-0">
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h2 className="font-bold text-lg text-gray-800">{trip.route_name}</h2>
                        <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
                            <p className="text-sm text-gray-500">
                                {trip.checked_in_students}/{trip.total_students} HS
                            </p>
                        </div>
                    </div>
                    
                    {/* --- NÚT ĐIỂM DANH (MỚI) --- */}
                    <div className="flex gap-2">
                        <button 
                            onClick={() => setShowAttendance(true)}
                            className="p-3 bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 shadow-sm active:scale-95 transition-all"
                            title="Điểm danh học sinh"
                        >
                            <FaUserCheck size={24} />
                        </button>
                    </div>
                </div>

                {/* Main Button */}
                {trip.status === 'scheduled' && (
                    <button onClick={handleStartTrip} className="w-full py-3.5 bg-green-600 text-white rounded-xl font-bold shadow-lg hover:bg-green-700 active:scale-95 transition-all flex items-center justify-center gap-2">
                        <FaPlay /> BẮT ĐẦU CHUYẾN ĐI
                    </button>
                )}
                
                {trip.status === 'in_progress' && (
                    <button onClick={handleCompleteTrip} className="w-full py-3.5 bg-red-600 text-white rounded-xl font-bold shadow-lg hover:bg-red-700 active:scale-95 transition-all flex items-center justify-center gap-2">
                        <FaStop /> KẾT THÚC CHUYẾN ĐI
                    </button>
                )}

                {trip.status === 'completed' && (
                    <div className="w-full py-3 bg-gray-500 text-white rounded-xl font-bold text-center flex items-center justify-center gap-2">
                        <FaCheckCircle /> ĐÃ HOÀN THÀNH
                    </div>
                )}
            </div>

            {/* --- MODAL ĐIỂM DANH --- */}
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