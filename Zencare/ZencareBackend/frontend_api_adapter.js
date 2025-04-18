/**
 * Zencare API Adapter for Frontend
 * 
 * This file contains helper functions for the frontend to interact with the backend API.
 * Copy this file to your frontend project.
 */

import axios from 'axios';

// Set your API base URL here
const API_BASE_URL = 'https://zencare-backend-2.onrender.com';
// const API_BASE_URL = 'http://localhost:8000'; // For local development

// Axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Set auth token for all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token'); // Using the same key as in your api.js
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Login function
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise} - Promise with the login response
 */
export const login = async (email, password) => {
  try {
    const response = await api.post('/auth/login/', { email, password });
    if (response.data.access) {
      localStorage.setItem('access_token', response.data.access); // Store with the same key
    }
    return response;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

/**
 * Register function for patients
 * @param {Object} userData - User registration data
 * @returns {Promise} - Promise with the registration response
 */
export const register = async (userData) => {
  try {
    const response = await api.post('/auth/register/', userData);
    return response;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

/**
 * Book an appointment
 * @param {Object} appointmentData - Must include doctorId, date, time, and optional description
 * @returns {Promise} - Promise with the appointment creation response
 */
export const book = async (appointmentData) => {
  const token = localStorage.getItem("access_token");
  try {
    // Transform the data to match the expected field names in the backend
    const formattedData = {
      doctor: parseInt(appointmentData.doctorId), // Ensure doctor ID is an integer
      appointment_date: appointmentData.date,     // Should be in YYYY-MM-DD format
      appointment_time: appointmentData.time,     // Should add :00 seconds if needed
      symptoms: appointmentData.description || "" // Map description to symptoms
    };
    
    console.log("Sending to API:", formattedData);
    
    // Make POST request to backend with appointment data
    const response = await axios.post(`${API_BASE_URL}/appointment/create/`, formattedData, {
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
    });
    return response;
  } catch (error) {
    console.error("Error booking appointment:", error.response ? error.response.data : error.message);
    throw error;
  }
};

/**
 * Get list of doctors
 * @param {string} specialization - Optional specialization filter
 * @returns {Promise} - Promise with the doctors list
 */
export const getDoctors = async (specialization = '') => {
  try {
    const params = specialization ? { profession: specialization } : {};
    const response = await api.get('/doctors/', { params });
    return response;
  } catch (error) {
    console.error('Get doctors error:', error);
    throw error;
  }
};

/**
 * Get user profile
 * @returns {Promise} - Promise with the user profile
 */
export const getProfile = async () => {
  try {
    const response = await api.get('/profile/');
    return response;
  } catch (error) {
    console.error('Get profile error:', error);
    throw error;
  }
};

/**
 * Get appointments
 * @returns {Promise} - Promise with the appointments list
 */
export const getAppointments = async () => {
  try {
    const response = await api.get('/appointment/');
    return response;
  } catch (error) {
    console.error('Get appointments error:', error);
    throw error;
  }
};

export default {
  login,
  register,
  book,
  getDoctors,
  getProfile,
  getAppointments,
}; 