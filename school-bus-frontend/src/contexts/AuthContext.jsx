import { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkLogin = async () => {
            const token = localStorage.getItem('access_token');
            if (token) {
                try {
                    const res = await api.get('/auth/profile/');
                    // Kiểm tra cấu trúc trả về từ API profile
                    const data = res.data;
                    // Nếu data có field 'user' bên trong thì lấy, không thì lấy chính nó
                    const userData = data.user || data;
                    setUser(userData);
                } catch (e) {
                    console.error("Check login failed:", e);
                    localStorage.clear();
                    setUser(null);
                }
            }
            setLoading(false);
        };
        checkLogin();
    }, []);

    const login = async (username, password) => {
        try {
            const res = await api.post('/auth/login/', { username, password });
            
            // Debug: Xem dữ liệu thực tế trả về là gì
            console.log("Login Response:", res.data);

            const { user: profileData, tokens } = res.data;
            
            // --- SỬA LỖI ---
            // Logic an toàn: Thử lấy profileData.user, nếu không có thì dùng chính profileData
            const userData = profileData?.user || profileData;
            
            if (!userData || !userData.role) {
                console.error("Invalid user data structure:", userData);
                return { success: false, message: "Lỗi dữ liệu người dùng từ server" };
            }
            
            localStorage.setItem('access_token', tokens.access);
            localStorage.setItem('refresh_token', tokens.refresh);
            
            setUser(userData);
            
            console.log("Login success. Role:", userData.role);
            return { success: true, role: userData.role };
            
        } catch (error) {
            console.error("Login error:", error);
            return { 
                success: false, 
                message: error.response?.data?.detail || error.response?.data?.error || 'Đăng nhập thất bại' 
            };
        }
    };

    const logout = () => {
        localStorage.clear();
        setUser(null);
        window.location.href = '/login';
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);