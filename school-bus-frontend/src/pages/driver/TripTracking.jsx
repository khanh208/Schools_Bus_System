// school-bus-frontend/src/pages/driver/TripTracking.jsx

import { useEffect, useState, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import api from '../../services/api';
import { FaPlay, FaStop, FaCheckCircle, FaUserCheck } from 'react-icons/fa';
import L from 'leaflet';
import AttendanceModal from '../../components/driver/AttendanceModal';

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
    
    if (!apiUrl) {
        console.error("❌ VITE_API_URL not defined");
        return null;
    }
    
    // Chuyển đổi http/https -> ws/wss
    let baseUrl;
    if (apiUrl.startsWith('https://')) {
        baseUrl = apiUrl.replace('https://', 'wss://');
    } else if (apiUrl.startsWith('http://')) {
        baseUrl = apiUrl.replace('http://', 'ws://');
    } else {
        baseUrl = 'ws://localhost:8000';
    }
    
    // Loại bỏ /api nếu có
    baseUrl = baseUrl.replace(/\/api\/?$/, '');
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error("❌ No access token found");
        return null;
    }
    
    return `${baseUrl}/ws/trips/${tripId}/?token=${encodeURIComponent(token)}`;
};

const TripTracking = () => {
    const { tripId } = useParams();
    const navigate = useNavigate();
    const [trip, setTrip] = useState(null);
    const [currentLocation, setCurrentLocation] = useState(null);
    const [isTracking, setIsTracking] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [showAttendance, setShowAttendance] = useState(false);
    
    const watchIdRef = useRef(null);
    const ws = useRef(null);
    const socketUrl = useMemo(() => getSocketUrl(tripId), [tripId]);

    // 1. WebSocket Connection
    // school-bus-frontend/src/pages/driver/TripTracking.jsx

useEffect(() => {
    if (!socketUrl) {
        console.error("❌ Cannot create WebSocket: URL is null");
        return;
    }

    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;
    let reconnectTimer = null;
    let isComponentMounted = true; // ✅ THÊM FLAG

    const connect = () => {
        if (!isComponentMounted) return; // ✅ Dừng nếu component unmounted
        
        if (ws.current) {
            ws.current.close();
            ws.current = null;
        }

        console.log(`🔌 Connecting to: ${socketUrl.split('?')[0]}...`);
        
        try {
            ws.current = new WebSocket(socketUrl);
        } catch (error) {
            console.error("❌ WebSocket creation failed:", error);
            scheduleReconnect();
            return;
        }

        ws.current.onopen = () => {
            if (!isComponentMounted) { // ✅ Kiểm tra trước khi update state
                ws.current.close();
                return;
            }
            console.log('✅ WebSocket Connected');
            setIsConnected(true);
            reconnectAttempts = 0;
        };

        ws.current.onmessage = (event) => {
            if (!isComponentMounted) return; // ✅ Bỏ qua nếu unmounted
            
            try {
                const msg = JSON.parse(event.data);
                console.log("📩 WS Message:", msg.type);
                
                if (msg.type === 'initial_data') {
                    setTrip(prev => ({...prev, ...msg.data}));
                    if (msg.data.status === 'in_progress') setIsTracking(true);
                }
            } catch (e) {
                console.error("Parse error:", e);
            }
        };

        ws.current.onerror = (error) => {
            // Chỉ log nếu không phải do unmount
            if (isComponentMounted) {
                console.error("❌ WebSocket Error:", error);
            }
        };

        ws.current.onclose = (event) => {
            console.log(`🔌 WebSocket Closed (Code: ${event.code})`);
            setIsConnected(false);
            
            // Chỉ reconnect nếu component vẫn còn mount và không phải close bình thường
            if (isComponentMounted && event.code !== 1000) {
                scheduleReconnect();
            }
        };
    };

    const scheduleReconnect = () => {
        if (!isComponentMounted || reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                console.error("❌ Max reconnect attempts reached");
            }
            return;
        }
        
        reconnectAttempts++;
        const delay = Math.min(1000 * (2 ** reconnectAttempts), 10000);
        console.log(`🔄 Reconnecting in ${delay}ms (Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
        
        reconnectTimer = setTimeout(connect, delay);
    };

    connect();

    return () => {
        isComponentMounted = false; // ✅ Đánh dấu unmounted
        if (reconnectTimer) clearTimeout(reconnectTimer);
        if (ws.current) {
            ws.current.close(1000, "Component unmounted");
            ws.current = null;
        }
    };
}, [socketUrl]);

    const sendLocationUpdate = (payload) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(payload));
        }
    };

    // 2. Lấy thông tin chuyến (API)
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
                            speed: speed || 0,
                            heading: heading || 0,
                            accuracy: accuracy || 0
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
            if (watchIdRef.current !== null) {
                navigator.geolocation.clearWatch(watchIdRef.current);
            }
        };
    }, [isTracking]);

    const handleStartTrip = async () => {
        if (window.confirm('Bắt đầu chuyến đi?')) {
            try {
                await api.post(`/tracking/trips/${tripId}/start/`);
                setTrip(prev => ({ ...prev, status: 'in_progress' }));
                setIsTracking(true);
            } catch (e) {
                alert("Lỗi bắt đầu chuyến");
            }
        }
    };

    const handleCompleteTrip = async () => {
        if (window.confirm('Kết thúc chuyến đi?')) {
            try {
                await api.post(`/tracking/trips/${tripId}/complete/`);
                setTrip(prev => ({ ...prev, status: 'completed' }));
                setIsTracking(false);
                navigate('/driver/home');
            } catch (e) {
                alert("Lỗi kết thúc chuyến");
            }
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
                    {currentLocation && (
                        <Marker position={currentLocation}>
                            <Popup>Vị trí hiện tại</Popup>
                        </Marker>
                    )}
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

                {trip.status === 'scheduled' && (
                    <button 
                        onClick={handleStartTrip} 
                        className="w-full py-3.5 bg-green-600 text-white rounded-xl font-bold shadow-lg hover:bg-green-700 active:scale-95 transition-all flex items-center justify-center gap-2"
                    >
                        <FaPlay /> BẮT ĐẦU CHUYẾN ĐI
                    </button>
                )}
                
                {trip.status === 'in_progress' && (
                    <button 
                        onClick={handleCompleteTrip} 
                        className="w-full py-3.5 bg-red-600 text-white rounded-xl font-bold shadow-lg hover:bg-red-700 active:scale-95 transition-all flex items-center justify-center gap-2"
                    >
                        <FaStop /> KẾT THÚC CHUYẾN ĐI
                    </button>
                )}

                {trip.status === 'completed' && (
                    <div className="w-full py-3 bg-gray-500 text-white rounded-xl font-bold text-center flex items-center justify-center gap-2">
                        <FaCheckCircle /> ĐÃ HOÀN THÀNH
                    </div>
                )}
            </div>

            {/* Modal Điểm danh */}
            {showAttendance && (
                <AttendanceModal 
                    trip={trip} 
                    onClose={() => setShowAttendance(false)} 
                />
            )}
        </div>
    );
};

// ✅ QUAN TRỌNG: Phải có dòng này
export default TripTracking;