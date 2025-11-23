import { useEffect, useState, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { FaUserGraduate, FaBus, FaMapMarkerAlt, FaExclamationCircle } from 'react-icons/fa';

const getSocketUrl = () => {
    const apiUrl = import.meta.env.VITE_API_URL;
    const baseUrl = apiUrl.replace('http', 'ws').replace('/api', '');
    const token = localStorage.getItem('access_token');
    return token ? `${baseUrl}/ws/notifications/?token=${token}` : null;
};

const ParentHome = () => {
    const [childrenData, setChildrenData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isConnected, setIsConnected] = useState(false);
    const navigate = useNavigate();
    
    const socketUrl = useMemo(() => getSocketUrl(), []);
    const ws = useRef(null);

    // 1. Kết nối WebSocket
    useEffect(() => {
        if (!socketUrl) return;

        const connect = () => {
            // Đóng cũ nếu có
            if (ws.current) ws.current.close();

            ws.current = new WebSocket(socketUrl);

            ws.current.onopen = () => {
                console.log('✅ WS Connected');
                setIsConnected(true);
                // Gửi request lấy dữ liệu
                ws.current.send(JSON.stringify({ type: 'get_children_status' }));
            };

            ws.current.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    if (message.type !== 'pong') console.log("📩 WS:", message.type);
                    
                    if (message.type === 'children_status') {
                        setChildrenData(message.data);
                        setLoading(false);
                    } else if (['attendance', 'trip_update', 'notification'].includes(message.type)) {
                         ws.current.send(JSON.stringify({ type: 'get_children_status' }));
                    }
                } catch (e) {
                    console.error(e);
                }
            };

            ws.current.onclose = () => {
                console.log('🔌 WS Disconnected');
                setIsConnected(false);
                // Tự động kết nối lại sau 3s
                setTimeout(() => {
                    if (ws.current?.readyState === WebSocket.CLOSED) connect();
                }, 3000);
            };
            
            ws.current.onerror = (err) => console.error("WS Error", err);
        };

        connect();

        return () => {
            if (ws.current) ws.current.close();
        };
    }, [socketUrl]);

    // 2. Fallback API (Chạy song song để đảm bảo có dữ liệu)
    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                const res = await api.get('/auth/parents/children/');
                setChildrenData(prev => prev.length === 0 ? res.data : prev);
                setLoading(false);
            } catch (error) {
                console.warn("API error:", error);
                setLoading(false);
            }
        };
        fetchInitialData();
    }, []);

    const getStatusInfo = (status) => {
        switch (status) {
            case 'Present': return { text: 'Đã đến lớp', color: 'text-green-600', bg: 'bg-green-50' };
            case 'Absent': return { text: 'Vắng mặt', color: 'text-red-600', bg: 'bg-red-50' };
            case 'Late': return { text: 'Đi muộn', color: 'text-orange-600', bg: 'bg-orange-50' };
            default: return { text: 'Chưa điểm danh', color: 'text-gray-500', bg: 'bg-gray-50' };
        }
    };

    return (
        <div className="space-y-6 pb-24">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-xl font-bold text-gray-800">Con của bạn</h2>
                    <p className={`text-xs flex items-center gap-1 ${isConnected ? 'text-green-600' : 'text-orange-500'}`}>
                        <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-600' : 'bg-orange-500'}`}></span>
                        {isConnected ? 'Trực tuyến' : 'Đang kết nối...'}
                    </p>
                </div>
                <button onClick={() => navigate('/parent/find-route')} className="text-sm bg-blue-100 text-blue-600 px-3 py-2 rounded-lg font-medium">
                    + Tìm tuyến
                </button>
            </div>

            {loading && childrenData.length === 0 && <div className="text-center py-10 text-gray-400">Đang tải dữ liệu...</div>}

            {!loading && childrenData.length === 0 && (
                <div className="bg-white p-6 rounded-2xl shadow-sm text-center border border-gray-100">
                    <FaExclamationCircle className="mx-auto text-gray-300 text-4xl mb-2" />
                    <p className="text-gray-500">Bạn chưa đăng ký thông tin học sinh nào.</p>
                </div>
            )}

            {childrenData.map((child, index) => {
                // SỬA LỖI KEY: Dùng index làm fallback nếu thiếu id
                const key = child.student_id || child.id || index;
                const status = getStatusInfo(child.attendance_today?.status);
                
                return (
                    <div key={key} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-4">
                        <div className="p-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white flex items-center gap-4">
                            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
                                <FaUserGraduate size={24} />
                            </div>
                            <div>
                                <h3 className="font-bold text-lg">{child.name || child.full_name}</h3>
                                <p className="text-blue-100 text-sm">{child.class || child.class_name || 'Chưa xếp lớp'}</p>
                            </div>
                        </div>

                        <div className="p-4 space-y-4">
                            <div className={`flex items-center justify-between p-3 rounded-xl ${status.bg}`}>
                                <span className="text-gray-600 text-sm font-medium">Hôm nay:</span>
                                <span className={`font-bold ${status.color}`}>{status.text}</span>
                            </div>

                            {child.current_trip ? (
                                <div className="border border-blue-200 rounded-xl p-4 bg-blue-50/50">
                                    <div className="flex items-center gap-2 mb-2 text-blue-700 font-bold">
                                        <FaBus /><span>Đang di chuyển</span>
                                    </div>
                                    <p className="text-sm text-gray-600 mb-3">Tuyến: {child.route?.code}</p>
                                    <button 
                                        onClick={() => navigate(`/parent/tracking/${child.current_trip.id}`)}
                                        className="w-full py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 flex items-center justify-center gap-2"
                                    >
                                        <FaMapMarkerAlt /> Xem vị trí
                                    </button>
                                </div>
                            ) : (
                                <div className="text-center py-3 text-gray-400 text-xs border-t border-dashed">
                                    Không có chuyến đi nào đang hoạt động.
                                </div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default ParentHome;