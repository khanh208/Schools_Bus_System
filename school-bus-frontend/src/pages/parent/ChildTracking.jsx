import { useEffect, useState, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import api from '../../services/api';
import L from 'leaflet';
import { FaArrowLeft, FaClock, FaRoad, FaUserTie, FaPhone } from 'react-icons/fa';

// Icon Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const busIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -20]
});

const getSocketUrl = (tripId) => {
    // Prefer explicit env; fallback to current location origin
    let apiUrlRaw = import.meta.env.VITE_API_URL || window.location.origin;
    apiUrlRaw = apiUrlRaw.replace(/\/+$/, ''); // remove trailing slash(es)
    if (!apiUrlRaw) return null;

    // Convert http/https => ws/wss
    let baseUrl;
    if (apiUrlRaw.startsWith('https://')) {
        baseUrl = apiUrlRaw.replace(/^https:\/\//, 'wss://');
    } else if (apiUrlRaw.startsWith('http://')) {
        baseUrl = apiUrlRaw.replace(/^http:\/\//, 'ws://');
    } else if (apiUrlRaw.startsWith('ws://') || apiUrlRaw.startsWith('wss://')) {
        baseUrl = apiUrlRaw;
    } else {
        // fallback: use window.location.protocol
        baseUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + apiUrlRaw;
    }

    // Remove possible trailing /api segment
    baseUrl = baseUrl.replace(/\/api\/?$/, '');

    const token = localStorage.getItem('access_token');
    const qs = token ? `?token=${encodeURIComponent(token)}` : '';
    return `${baseUrl}/ws/trips/${tripId}/${qs}`;
};

const ChildTracking = () => {
    const { tripId } = useParams();
    const navigate = useNavigate();

    // State
    const [tripInfo, setTripInfo] = useState(null);
    const [busLocation, setBusLocation] = useState(null);
    const [speed, setSpeed] = useState(0);
    const [eta, setEta] = useState(null);
    const [isConnected, setIsConnected] = useState(false);

    // WS refs
    const ws = useRef(null);
    const unmountedRef = useRef(false);
    const retryRef = useRef(0);
    const reconnectTimerRef = useRef(null);
    const connectTimeoutRef = useRef(null);

    const socketUrl = useMemo(() => getSocketUrl(tripId), [tripId]);

    useEffect(() => {
        if (!socketUrl) {
            console.warn('WebSocket URL not available, skipping WS connect');
            return;
        }

        unmountedRef.current = false;

        const connect = () => {
            if (unmountedRef.current) return;

            if (reconnectTimerRef.current) {
                clearTimeout(reconnectTimerRef.current);
                reconnectTimerRef.current = null;
            }

            try {
                if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
                    ws.current.close();
                }
            } catch (e) { /* ignore */ }

            console.log('Trying WS connect to', socketUrl);
            try {
                ws.current = new WebSocket(socketUrl);
            } catch (err) {
                console.error('WebSocket construction failed:', err);
                scheduleReconnect();
                return;
            }

            // If CONNECTING takes too long, force close and retry
            if (connectTimeoutRef.current) clearTimeout(connectTimeoutRef.current);
            connectTimeoutRef.current = setTimeout(() => {
                try {
                    if (ws.current && ws.current.readyState === WebSocket.CONNECTING) {
                        console.warn('WebSocket stuck CONNECTING, force close to retry');
                        ws.current.close();
                    }
                } catch (e) { /* ignore */ }
            }, 10000);

            ws.current.onopen = () => {
                if (connectTimeoutRef.current) { clearTimeout(connectTimeoutRef.current); connectTimeoutRef.current = null; }
                console.log('✅ Parent Tracking: WebSocket Connected');
                setIsConnected(true);
                retryRef.current = 0;
            };

            ws.current.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'location_update') {
                        const { lat, lng, speed: s } = msg.data;
                        if (typeof lat === 'number' && typeof lng === 'number') {
                            setBusLocation([lat, lng]);
                        }
                        setSpeed(s ? Math.round(s) : 0);
                    } else if (msg.type === 'eta_update') {
                        setEta(msg.data?.minutes_remaining ?? null);
                    } else if (msg.type === 'initial_data') {
                        const data = msg.data || {};
                        if (data.driver_info && !data.driver) data.driver = data.driver_info;
                        if (data.vehicle_info && !data.vehicle) data.vehicle = data.vehicle_info;
                        setTripInfo(data);
                        if (data.current_location) {
                            setBusLocation([data.current_location.lat, data.current_location.lng]);
                            setSpeed(data.current_location.speed || 0);
                        }
                    } else {
                        // handle other message types if any
                    }
                } catch (e) {
                    console.error('WS Message Error:', e);
                }
            };

            ws.current.onclose = (ev) => {
                if (connectTimeoutRef.current) { clearTimeout(connectTimeoutRef.current); connectTimeoutRef.current = null; }
                console.log('⚠️ WS Closed', ev.code, ev.reason);
                setIsConnected(false);
                if (unmountedRef.current) return;
                scheduleReconnect();
            };

            ws.current.onerror = (err) => {
                console.error('WS Error Event', err);
                // Let onclose handle retry/backoff
            };
        };

        const scheduleReconnect = () => {
            retryRef.current = Math.min(retryRef.current + 1, 8);
            const delay = Math.min(3000 * (2 ** (retryRef.current - 1)), 30000);
            console.log(`Reconnecting in ${delay}ms (attempt ${retryRef.current})`);
            if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = setTimeout(() => {
                connect();
            }, delay);
        };

        connect();

        return () => {
            unmountedRef.current = true;
            if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
            if (connectTimeoutRef.current) clearTimeout(connectTimeoutRef.current);
            try { if (ws.current) ws.current.close(); } catch (e) {}
        };
    }, [socketUrl]);

    // API fallback to load initial trip data
    useEffect(() => {
        let cancelled = false;
        const fetchTrip = async () => {
            try {
                const res = await api.get(`/tracking/trips/${tripId}/tracking/`);
                if (cancelled) return;
                const dataTrip = res.data.trip || {};
                if (dataTrip.driver_info && !dataTrip.driver) dataTrip.driver = dataTrip.driver_info;
                if (dataTrip.vehicle_info && !dataTrip.vehicle) dataTrip.vehicle = dataTrip.vehicle_info;
                // Update only if ws hasn't provided data yet
                setTripInfo(prev => prev ? prev : dataTrip);
                if (res.data.current_location) {
                    setBusLocation([res.data.current_location.lat, res.data.current_location.lng]);
                }
                setEta(res.data.eta_minutes ?? null);
            } catch (error) {
                console.error('API Load Error:', error);
            }
        };
        fetchTrip();
        return () => { cancelled = true; };
    }, [tripId]);

    const driverName = tripInfo?.driver?.name || tripInfo?.driver_info?.name || 'Đang cập nhật';
    const driverPhone = tripInfo?.driver?.phone || tripInfo?.driver_info?.phone || '';
    const plateNumber = tripInfo?.vehicle?.plate || tripInfo?.vehicle?.plate_number || '';

    return (
        <div className="flex flex-col h-full relative bg-gray-100">
            <div className="absolute top-4 left-4 z-[1000]">
                <button 
                    onClick={() => navigate(-1)}
                    className="bg-white p-3 rounded-full shadow-lg text-gray-600 hover:text-blue-600 transition-colors"
                >
                    <FaArrowLeft />
                </button>
            </div>

            <div className="flex-1 z-0">
                <MapContainer 
                    center={busLocation || [10.762, 106.660]} 
                    zoom={15} 
                    style={{ height: "100%", width: "100%" }}
                >
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; OpenStreetMap contributors'
                    />
                    {busLocation && (
                        <Marker position={busLocation} icon={busIcon}>
                            <Popup>
                                <div className="text-center">
                                    <b className="block text-blue-600">Xe đang ở đây</b>
                                    <span className="text-xs text-gray-500">{speed} km/h</span>
                                </div>
                            </Popup>
                        </Marker>
                    )}
                </MapContainer>
            </div>

            <div className="bg-white p-5 rounded-t-3xl shadow-[0_-4px_20px_rgba(0,0,0,0.1)] z-10 -mt-6 relative">
                <div className="flex justify-center mb-2">
                    <span className={`w-10 h-1 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                </div>

                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="font-bold text-xl text-gray-800">
                            {tripInfo?.route?.name || 'Đang tải...'}
                        </h2>
                        <p className="text-sm text-gray-500 font-medium">
                            {plateNumber}
                        </p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                        tripInfo?.status === 'in_progress' ? 'bg-green-100 text-green-700' : 
                        tripInfo?.status === 'completed' ? 'bg-gray-100 text-gray-600' : 'bg-blue-100 text-blue-700'
                    }`}>
                        {tripInfo?.status === 'in_progress' ? 'ĐANG CHẠY' : tripInfo?.status || '...'}
                    </div>
                </div>

                <div className="flex gap-4 mb-6">
                    <div className="flex-1 bg-orange-50 p-3 rounded-xl flex items-center gap-3 border border-orange-100">
                        <div className="bg-white p-2 rounded-full text-orange-500 shadow-sm">
                            <FaClock />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 font-medium">Dự kiến đến</p>
                            <p className="font-bold text-gray-800 text-lg">
                                {eta ? `${Math.round(eta)}'` : '--'}
                            </p>
                        </div>
                    </div>
                    
                    <div className="flex-1 bg-blue-50 p-3 rounded-xl flex items-center gap-3 border border-blue-100">
                        <div className="bg-white p-2 rounded-full text-blue-500 shadow-sm">
                            <FaRoad />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 font-medium">Tốc độ</p>
                            <p className="font-bold text-gray-800 text-lg">{speed} km/h</p>
                        </div>
                    </div>
                </div>
                
                <div className="pt-4 border-t border-gray-100">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 border border-gray-200">
                            <FaUserTie size={20} />
                        </div>
                        <div>
                            <p className="font-bold text-gray-800 text-sm">Tài xế: {driverName}</p>
                            <p className="text-xs text-gray-500">{driverPhone}</p>
                        </div>
                        {driverPhone && (
                            <a 
                                href={`tel:${driverPhone}`}
                                className="ml-auto bg-green-500 text-white p-3 rounded-full shadow-lg hover:bg-green-600 active:scale-95 transition-transform"
                            >
                                <FaPhone />
                            </a>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChildTracking;