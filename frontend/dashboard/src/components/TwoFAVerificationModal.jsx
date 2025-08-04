import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const TwoFAVerificationModal = ({ isOpen, onClose }) => {
    const { verify2FA, logout, reset2FA } = useAuth();
    const [code, setCode] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleVerify = async () => {
        if (!code || code.length !== 6) {
            setError('Please enter the complete 6-digit PIN from your authenticator app');
            return;
        }

        setLoading(true);
        setError('');

        try {
            await verify2FA(code);
            setCode('');
            setError(''); // Clear any previous errors
            // Modal will be closed by AuthContext when verification succeeds
        } catch (err) {
            // Extract user-friendly error message
            let errorMessage = 'Please try again.';
            
            if (err.response && err.response.data && err.response.data.message) {
                errorMessage = err.response.data.message;
            } else if (err.message) {
                errorMessage = err.message;
            }
            
            setError(errorMessage);
            console.error('2FA verification error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = async () => {
        try {
            await logout();
        } catch (err) {
            console.error('Logout error:', err);
        }
    };

    const handleReset2FA = async () => {
        try {
            setLoading(true);
            await reset2FA();
            // Modal will be closed and setup modal will open automatically
        } catch (err) {
            // Extract user-friendly error message
            let errorMessage = 'Failed to reset 2FA. Please try again.';
            
            if (err.response && err.response.data && err.response.data.message) {
                errorMessage = err.response.data.message;
            } else if (err.message) {
                errorMessage = err.message;
            }
            
            setError(errorMessage);
            console.error('Reset 2FA error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && code && !loading) {
            handleVerify();
        }
    };

    const formatCode = (value) => {
        // Only allow digits for TOTP, max 6 characters
        return value.replace(/\D/g, '').slice(0, 6);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                    Two-Factor Authentication Required
                </h2>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                    Please enter the 6-digit code from your authenticator app to continue.
                </p>

                {/* Code Input */}
                <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(formatCode(e.target.value))}
                    onKeyPress={handleKeyPress}
                    placeholder="000000"
                    className="w-full text-center text-xl p-3 border border-gray-300 dark:border-gray-600 rounded mb-4 tracking-widest bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    maxLength={6}
                    autoFocus
                />

                {error && <p className="text-red-600 dark:text-red-400 text-sm mb-4">{error}</p>}

                <div className="flex space-x-3">
                    <button
                        onClick={handleLogout}
                        className="flex-1 bg-red-500 hover:bg-red-600 text-white py-2 px-4 rounded transition-colors"
                        disabled={loading}
                    >
                        Log Out
                    </button>
                    <button
                        onClick={handleVerify}
                        disabled={loading || !code || code.length !== 6}
                        className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-2 px-4 rounded transition-colors"
                    >
                        {loading ? 'Verifying...' : 'Verify'}
                    </button>
                </div>

                {/* Reset 2FA Option */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                    <p className="text-xs text-gray-500 dark:text-gray-400 text-center mb-3">
                        Having trouble? You can reset your 2FA setup and scan a new QR code.
                    </p>
                    <button
                        onClick={handleReset2FA}
                        disabled={loading}
                        className="w-full bg-gray-500 hover:bg-gray-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-2 px-4 rounded transition-colors text-sm"
                    >
                        {loading ? 'Resetting...' : 'Reset 2FA & Scan New QR Code'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default TwoFAVerificationModal;