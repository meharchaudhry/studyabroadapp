import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AuthGuard from './components/AuthGuard';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import OTPVerify from './pages/OTPVerify';
import VisaChat from './pages/VisaChat';
import Dashboard from './pages/Dashboard';
import Universities from './pages/Universities';
import UniversityDetail from './pages/UniversityDetail';
import Jobs from './pages/Jobs';
import Finance from './pages/Finance';
import Housing from './pages/Housing';
import BookingAppointments from './pages/BookingAppointments';
import Decision from './pages/Decision';
import AIAgent from './pages/AIAgent';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/verify-otp" element={<OTPVerify />} />

        <Route element={<AuthGuard />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/universities" element={<Universities />} />
            <Route path="/universities/:id" element={<UniversityDetail />} />
            <Route path="/housing" element={<Housing />} />
            <Route path="/appointments" element={<BookingAppointments />} />
            <Route path="/visa-chat" element={<VisaChat />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/finance" element={<Finance />} />
            <Route path="/decision" element={<Decision />} />
            <Route path="/ai-coach" element={<AIAgent />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
