import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const TwoFAVerificationModal = ({ isOpen, onClose }) => {
    const { verify2FA } = useAuth();
    const [code, setCode] = useState('');
    const [method, setMethod] = useState('totp'); // 'totp' or 'backup'
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleVerify = async () => {
        if (!code || (method === 'totp' && code.length !== 6) || (method === 'backup' && code.length < 8)) {
            setError('Please enter a valid code');
            return;
        }

        setLoading(true);
        setError('');

        try {
            await verify2FA(code, method);
            setCode('');
            // Modal will be closed by AuthContext when verification succeeds
        } catch (err) {
            setError(err.message || 'Verification failed. Please try again.');
            console.error('2FA verification error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleMethodChange = (newMethod) => {
        setMethod(newMethod);
        setCode('');
        setError('');
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && code && !loading) {
            handleVerify();
        }
    };

    const formatCode = (value, method) => {
        if (method === 'totp') {
            // Only allow digits for TOTP, max 6 characters
            return value.replace(/\D/g, '').slice(0, 6);
        } else {
            // For backup codes, allow letters and numbers, format as XXXX-XXXX
            let cleaned = value.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
            if (cleaned.length > 4) {
                cleaned = cleaned.slice(0, 4) + '-' + cleaned.slice(4, 8);
            }
            return cleaned;
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                    Two-Factor Authentication Required
                </h2>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                    Please enter your authentication code to continue.
                </p>

                {/* Method Selection */}
                <div className="flex mb-4 border border-gray-300 dark:border-gray-600 rounded overflow-hidden">
                    <button
                        onClick={() => handleMethodChange('totp')}
                        className={`flex-1 py-2 px-4 text-sm transition-colors ${
                            method === 'totp' 
                                ? 'bg-blue-500 text-white' 
                                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                    >
                        Authenticator App
                    </button>
                    <button
                        onClick={() => handleMethodChange('backup')}
                        className={`flex-1 py-2 px-4 text-sm transition-colors ${
                            method === 'backup' 
                                ? 'bg-blue-500 text-white' 
                                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                    >
                        Backup Code
                    </button>
                </div>

                {/* Code Input */}
                <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(formatCode(e.target.value, method))}
                    onKeyPress={handleKeyPress}
                    placeholder={method === 'totp' ? '000000' : 'XXXX-XXXX'}
                    className="w-full text-center text-xl p-3 border border-gray-300 dark:border-gray-600 rounded mb-4 tracking-widest bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    maxLength={method === 'totp' ? 6 : 9}
                    autoFocus
                />

                {/* Method-specific help text */}
                <div className="mb-4 text-sm text-gray-500 dark:text-gray-400">
                    {method === 'totp' ? (
                        <p>Enter the 6-digit code from your authenticator app</p>
                    ) : (
                        <p>Enter one of your saved backup codes (format: XXXX-XXXX)</p>
                    )}
                </div>

                {error && <p className="text-red-600 dark:text-red-400 text-sm mb-4">{error}</p>}

                <div className="flex space-x-3">
                    <button
                        onClick={onClose}
                        className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded transition-colors"
                        disabled={loading}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleVerify}
                        disabled={loading || !code || (method === 'totp' && code.length !== 6) || (method === 'backup' && code.length < 8)}
                        className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-2 px-4 rounded transition-colors"
                    >
                        {loading ? 'Verifying...' : 'Verify'}
                    </button>
                </div>

                {/* Additional help */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                    <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                        {method === 'totp' ? (
                            <>Don't have your phone? <button onClick={() => handleMethodChange('backup')} className="text-blue-500 hover:text-blue-600 underline">Use a backup code</button></>
                        ) : (
                            <>Have your phone? <button onClick={() => handleMethodChange('totp')} className="text-blue-500 hover:text-blue-600 underline">Use authenticator app</button></>
                        )}
                    </p>
                </div>
            </div>
        </div>
    );
};

export default TwoFAVerificationModal;