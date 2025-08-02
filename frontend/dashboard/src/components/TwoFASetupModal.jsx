import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

const TwoFASetupModal = ({ isOpen, onClose }) => {
    const { start2FASetup, verify2FASetup, twoFASetupData } = useAuth();
    const [step, setStep] = useState(1); // 1: intro, 2: QR code, 3: verify, 4: backup codes
    const [code, setCode] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [backupCodes, setBackupCodes] = useState([]);
    const [setupData, setSetupData] = useState(null);

    useEffect(() => {
        if (isOpen && step === 2 && !setupData) {
            initiate2FASetup();
        }
    }, [isOpen, step]);

    const initiate2FASetup = async () => {
        setLoading(true);
        setError('');
        
        try {
            const data = await start2FASetup();
            setSetupData(data);
        } catch (err) {
            setError('Failed to start 2FA setup. Please try again.');
            console.error('2FA setup initiation error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleVerifySetup = async () => {
        if (!code || code.length !== 6) {
            setError('Please enter a valid 6-digit code');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const result = await verify2FASetup(code);
            setBackupCodes(result.backup_codes);
            setStep(4);
        } catch (err) {
            setError(err.message || 'Invalid code. Please try again.');
            console.error('2FA setup verification error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleComplete = () => {
        setStep(1);
        setCode('');
        setError('');
        setSetupData(null);
        setBackupCodes([]);
        onClose();
    };

    const downloadBackupCodes = () => {
        const content = `NetPilot 2FA Backup Codes
Generated: ${new Date().toLocaleDateString()}

These codes can be used if you lose access to your authenticator app.
Each code can only be used once.

${backupCodes.join('\n')}

Important: Store these codes in a safe place!`;
        
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'netpilot-backup-codes.txt';
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && step === 3 && code.length === 6 && !loading) {
            handleVerifySetup();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
                {/* Step 1: Introduction */}
                {step === 1 && (
                    <div>
                        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                            Set Up Two-Factor Authentication
                        </h2>
                        <p className="text-gray-600 dark:text-gray-300 mb-6">
                            Add an extra layer of security to your account by enabling two-factor authentication.
                            You'll need an authenticator app like Google Authenticator, Authy, or Microsoft Authenticator.
                        </p>
                        <div className="flex space-x-3">
                            <button
                                onClick={() => setStep(2)}
                                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded transition-colors"
                            >
                                Get Started
                            </button>
                            <button
                                onClick={onClose}
                                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded transition-colors"
                            >
                                Skip for Now
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 2: QR Code */}
                {step === 2 && (
                    <div>
                        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                            Scan QR Code
                        </h2>
                        {loading ? (
                            <div className="text-center py-8">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                                <p className="mt-2 text-gray-600 dark:text-gray-300">Generating QR code...</p>
                            </div>
                        ) : setupData ? (
                            <div>
                                <p className="text-gray-600 dark:text-gray-300 mb-4">
                                    Scan this QR code with your authenticator app:
                                </p>
                                <div className="text-center mb-4">
                                    <div className="bg-white p-4 rounded-lg inline-block">
                                        <img 
                                            src={setupData.qr_code} 
                                            alt="2FA QR Code" 
                                            className="mx-auto border rounded"
                                        />
                                    </div>
                                </div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                                    Or enter this code manually: 
                                    <code className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded block mt-1 font-mono text-xs break-all">
                                        {setupData.secret}
                                    </code>
                                </p>
                                <button
                                    onClick={() => setStep(3)}
                                    className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded transition-colors"
                                >
                                    Continue
                                </button>
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
                                <button
                                    onClick={initiate2FASetup}
                                    className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded transition-colors"
                                >
                                    Try Again
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* Step 3: Verify Code */}
                {step === 3 && (
                    <div>
                        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                            Verify Setup
                        </h2>
                        <p className="text-gray-600 dark:text-gray-300 mb-4">
                            Enter the 6-digit code from your authenticator app:
                        </p>
                        <input
                            type="text"
                            value={code}
                            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                            onKeyPress={handleKeyPress}
                            placeholder="000000"
                            className="w-full text-center text-xl p-3 border border-gray-300 dark:border-gray-600 rounded mb-4 tracking-widest bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            maxLength={6}
                            autoFocus
                        />
                        {error && <p className="text-red-600 dark:text-red-400 text-sm mb-4">{error}</p>}
                        <div className="flex space-x-3">
                            <button
                                onClick={() => setStep(2)}
                                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded transition-colors"
                            >
                                Back
                            </button>
                            <button
                                onClick={handleVerifySetup}
                                disabled={loading || code.length !== 6}
                                className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-2 px-4 rounded transition-colors"
                            >
                                {loading ? 'Verifying...' : 'Verify'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 4: Backup Codes */}
                {step === 4 && (
                    <div>
                        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                            Save Backup Codes
                        </h2>
                        <p className="text-gray-600 dark:text-gray-300 mb-4">
                            Save these backup codes in a safe place. You can use them to access your account 
                            if you lose your authenticator device. Each code can only be used once.
                        </p>
                        <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded mb-4 max-h-32 overflow-y-auto">
                            {backupCodes.map((code, index) => (
                                <div key={index} className="font-mono text-sm mb-1 text-gray-900 dark:text-gray-100">
                                    {code}
                                </div>
                            ))}
                        </div>
                        <div className="flex space-x-3">
                            <button
                                onClick={downloadBackupCodes}
                                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white py-2 px-4 rounded transition-colors"
                            >
                                Download
                            </button>
                            <button
                                onClick={handleComplete}
                                className="flex-1 bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded transition-colors"
                            >
                                Complete Setup
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TwoFASetupModal;