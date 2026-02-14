'use client';

import React, { useState } from 'react';

interface OAuthButtonsProps {
  disabled?: boolean;
  loading?: boolean;
}

export default function OAuthButtons({ disabled = false, loading = false }: OAuthButtonsProps) {
  const [redirecting, setRedirecting] = useState<'google' | 'github' | null>(null);

  const handleGoogleClick = () => {
    setRedirecting('google');
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    window.location.href = `${apiUrl}/api/v1/auth/google/`;
  };

  const handleGitHubClick = () => {
    setRedirecting('github');
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    window.location.href = `${apiUrl}/api/v1/auth/github/`;
  };

  const isDisabled = disabled || loading || redirecting !== null;

  return (
    <div className="flex flex-col gap-3 w-full">
      {/* Google Button */}
      <button
        type="button"
        onClick={handleGoogleClick}
        disabled={isDisabled}
        className="w-full h-12 bg-white border border-gray-300 rounded-lg flex items-center justify-center gap-3 hover:bg-gray-50 hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {redirecting === 'google' ? (
          <div className="w-5 h-5 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
        ) : (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19.6 10.227c0-.709-.064-1.39-.182-2.045H10v3.868h5.382a4.6 4.6 0 01-1.996 3.018v2.51h3.232c1.891-1.742 2.982-4.305 2.982-7.35z" fill="#4285F4"/>
            <path d="M10 20c2.7 0 4.964-.895 6.618-2.423l-3.232-2.509c-.895.6-2.04.955-3.386.955-2.605 0-4.81-1.76-5.595-4.123H1.064v2.59A9.996 9.996 0 0010 20z" fill="#34A853"/>
            <path d="M4.405 11.9c-.2-.6-.314-1.24-.314-1.9 0-.66.114-1.3.314-1.9V5.51H1.064A9.996 9.996 0 000 10c0 1.614.386 3.14 1.064 4.49l3.34-2.59z" fill="#FBBC05"/>
            <path d="M10 3.977c1.468 0 2.786.505 3.823 1.496l2.868-2.868C14.959.99 12.695 0 10 0 6.09 0 2.71 2.24 1.064 5.51l3.34 2.59C5.191 5.736 7.396 3.977 10 3.977z" fill="#EA4335"/>
          </svg>
        )}
        <span className="text-gray-700 font-medium">
          {redirecting === 'google' ? 'Redirecting...' : 'Continue with Google'}
        </span>
      </button>

      {/* GitHub Button */}
      <button
        type="button"
        onClick={handleGitHubClick}
        disabled={isDisabled}
        className="w-full h-12 bg-[#24292e] border border-[#24292e] rounded-lg flex items-center justify-center gap-3 hover:bg-[#2f363d] hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {redirecting === 'github' ? (
          <div className="w-5 h-5 border-2 border-gray-600 border-t-white rounded-full animate-spin" />
        ) : (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="white" xmlns="http://www.w3.org/2000/svg">
            <path fillRule="evenodd" clipRule="evenodd" d="M10 0C4.477 0 0 4.477 0 10c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0110 4.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C17.137 18.165 20 14.418 20 10c0-5.523-4.477-10-10-10z"/>
          </svg>
        )}
        <span className="text-white font-medium">
          {redirecting === 'github' ? 'Redirecting...' : 'Continue with GitHub'}
        </span>
      </button>
    </div>
  );
}
