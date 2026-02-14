export interface OnboardingState {
  step: string | null;
  completed: boolean;
  path: 'guided' | 'demo' | 'skipped' | null;
  data: Record<string, unknown>;
}

export interface OnboardingUpdateData {
  step?: string;
  completed?: boolean;
  path?: 'guided' | 'demo' | 'skipped';
  data?: Record<string, unknown>;
}
