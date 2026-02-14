'use client';

import React from 'react';

interface PasswordStrengthProps {
  password: string;
}

type StrengthLevel = 'weak' | 'medium' | 'strong';

interface StrengthInfo {
  level: StrengthLevel;
  color: string;
  text: string;
  width: string;
}

/**
 * Calculate password strength based on various criteria
 */
const calculateStrength = (password: string): StrengthInfo => {
  if (!password) {
    return {
      level: 'weak',
      color: 'bg-red-500',
      text: '',
      width: 'w-0',
    };
  }

  let score = 0;

  // Length check
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;

  // Character variety checks
  if (/[a-z]/.test(password)) score++; // lowercase
  if (/[A-Z]/.test(password)) score++; // uppercase
  if (/[0-9]/.test(password)) score++; // numbers
  if (/[^a-zA-Z0-9]/.test(password)) score++; // special chars

  // Determine strength level
  if (score <= 2) {
    return {
      level: 'weak',
      color: 'bg-red-500',
      text: 'Weak',
      width: 'w-1/3',
    };
  } else if (score <= 4) {
    return {
      level: 'medium',
      color: 'bg-yellow-500',
      text: 'Medium',
      width: 'w-2/3',
    };
  } else {
    return {
      level: 'strong',
      color: 'bg-green-500',
      text: 'Strong',
      width: 'w-full',
    };
  }
};

export const PasswordStrength: React.FC<PasswordStrengthProps> = ({ password }) => {
  const strength = calculateStrength(password);

  if (!password) {
    return null;
  }

  return (
    <div className="mt-2">
      {/* Progress bar */}
      <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full ${strength.color} transition-all duration-300 ${strength.width}`}
        />
      </div>

      {/* Strength label */}
      <p className={`text-xs mt-1 font-medium ${
        strength.level === 'weak' ? 'text-red-400' :
        strength.level === 'medium' ? 'text-yellow-400' :
        'text-green-400'
      }`}>
        Password strength: {strength.text}
      </p>
    </div>
  );
};
