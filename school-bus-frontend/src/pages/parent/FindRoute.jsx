import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import api from '../../services/api';
import { FaSearch, FaBus } from 'react-icons/fa';
import L from 'leaflet';
import { useNavigate } from 'react-router-dom';

// Icon
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

const FindRoute = () => {
    const [position, setPosition] = useState(null);
    const [results, setResults] = useState([]); 
    const [children, setChildren] = useState([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    // 1. Lấy danh sách con
    useEffect(() => {
        const fetchChildren = async () => {
            try {
                const res = await api.get('/auth/parents/children/');
                setChildren(res.data);
            } catch (error) {
                console.error("Lỗi tải danh sách con:", error);
            }
        };
        fetchChildren();
    }, []);

    // Component xử lý click trên bản đồ
    const LocationMarker = () => {
        useMapEvents({
            click(e) {
                setPosition(e.latlng);
            },
        });
        return position === null ? null : (
            <Marker position={position} icon={DefaultIcon}></Marker>
        );
    };

    // 2. Tìm kiếm tuyến
    const handleSearch = async () => {
        if (!position) {
            alert("Vui lòng chọn vị trí nhà của bạn trên bản đồ");
            return;
        }
        
        setLoading(true);
        try {
            const res = await api.post('/routes/routes/find_suitable/', {
                lat: position.lat,
                lng: position.lng,
                max_distance: 5 // km
            });
            setResults(res.data.nearby_stops || []);
            
            if (!res.data.nearby_stops || res.data.nearby_stops.length === 0) {
                alert("Không tìm thấy tuyến xe nào gần vị trí này.");
            }
        } catch (error) {
            console.error(error);
            alert("Lỗi tìm kiếm");
        } finally {
            setLoading(false);
        }
    };

    // 3. Xử lý Đăng ký
    const handleRegister = async (stop) => {
        if (children.length === 0) {
            alert("Bạn chưa có thông tin học sinh nào để đăng ký.");
            return;
        }

        let studentId = children[0].id;

        // Nếu có nhiều con, cho chọn
        if (children.length > 1) {
            const choice = window.prompt(
                `Nhập ID học sinh muốn đăng ký:\n` + 
                children.map(c => `${c.id}: ${c.full_name}`).join('\n'),
                children[0].id
            );
            if (!choice) return;
            studentId = parseInt(choice);
        }

        if (!window.confirm(`Đăng ký đón/trả tại điểm "${stop.stop_name}"?`)) return;

        try {
            await api.post('/routes/assignments/', {
                student: studentId,
                route: stop.route_id,
                stop: stop.stop_id,
                assignment_type: 'both',
                start_date: new Date().toISOString().split('T')[0]
            });
            
            alert("Đăng ký thành công!");
            navigate('/parent/home');
        } catch (error) {
            console.error(error);
            alert(error.response?.data?.message || "Đăng ký thất bại. Có thể học sinh đã có tuyến.");
        }
    };

    return (
        // Thêm 'relative' để làm khung mốc tọa độ
        <div className="flex flex-col h-full relative">
            
            {/* Thanh tìm kiếm: Tăng z-index lên 1000 để nằm trên bản đồ */}
            <div className="p-4 bg-white shadow-sm z-[1000] relative">
                <h2 className="text-lg font-bold text-gray-800 mb-2">Tìm tuyến xe phù hợp</h2>
                <p className="text-sm text-gray-500 mb-4">Chạm vào bản đồ để chọn vị trí đón</p>
                <button 
                    onClick={handleSearch}
                    disabled={loading || !position}
                    className="w-full bg-blue-600 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 disabled:opacity-50 hover:bg-blue-700 transition-colors"
                >
                    {loading ? 'Đang tìm...' : <><FaSearch /> Tìm tuyến xe gần đây</>}
                </button>
            </div>

            {/* Bản đồ: z-index mặc định (0) */}
            <div className="flex-1 relative z-0">
                <MapContainer 
                    center={[10.762622, 106.660172]} 
                    zoom={13} 
                    style={{ height: "100%", width: "100%" }}
                >
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    <LocationMarker />
                </MapContainer>
            </div>

            {/* Bảng kết quả: Tăng z-index lên 1000 để nổi lên trên bản đồ */}
            {results.length > 0 && (
                <div className="bg-white p-4 shadow-[0_-4px_20px_rgba(0,0,0,0.15)] z-[1000] h-1/2 overflow-y-auto absolute bottom-0 left-0 right-0 rounded-t-3xl border-t border-gray-100">
                    <h3 className="font-bold text-gray-800 mb-3 sticky top-0 bg-white pb-2 border-b z-10">
                        Kết quả ({results.length} điểm dừng gần nhất)
                    </h3>
                    {/* Thêm padding bottom để không bị che bởi thanh điều hướng */}
                    <div className="space-y-3 pb-10">
                        {results.map((stop, index) => (
                            <div key={index} className="border border-gray-200 rounded-xl p-4 flex items-start gap-3 hover:bg-blue-50 transition-colors shadow-sm">
                                <div className="bg-blue-100 p-3 rounded-full text-blue-600 mt-1">
                                    <FaBus />
                                </div>
                                <div className="flex-1">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h4 className="font-bold text-gray-800 text-lg">{stop.route_code}</h4>
                                            <p className="text-sm text-gray-600 font-medium">{stop.stop_name}</p>
                                        </div>
                                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-bold whitespace-nowrap">
                                            {stop.distance_km} km
                                        </span>
                                    </div>
                                    
                                    <div className="mt-3 flex gap-2">
                                        <button 
                                            onClick={() => handleRegister(stop)}
                                            className="flex-1 bg-blue-600 text-white text-sm py-2 rounded-lg font-bold hover:bg-blue-700 transition-colors shadow"
                                        >
                                            Đăng ký ngay
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default FindRoute;