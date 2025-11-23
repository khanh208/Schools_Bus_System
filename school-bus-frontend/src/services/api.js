// src/services/api.js
import axios from 'axios';
import { jwtDecode } from "jwt-decode";

const API_URL = import.meta.env.VITE_API_URL;

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor: Tự động gắn Access Token vào mỗi request
api.interceptors.request.use(
    async (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            const decoded = jwtDecode(token);
            const currentTime = Date.now() / 1000;

            // Nếu token sắp hết hạn (còn dưới 10s), thử refresh
            if (decoded.exp < currentTime + 10) {
                try {
                    const refreshToken = localStorage.getItem('refresh_token');
                    const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
                        refresh: refreshToken
                    });
                    
                    const newAccess = response.data.access;
                    localStorage.setItem('access_token', newAccess);
                    config.headers['Authorization'] = `Bearer ${newAccess}`;
                } catch (error) {
                    // Refresh lỗi -> Logout
                    localStorage.clear();
                    window.location.href = '/login';
                }
            } else {
                config.headers['Authorization'] = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => Promise.reject(error)
);

export default api;