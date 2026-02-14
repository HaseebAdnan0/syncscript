export interface User {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  email_verified: boolean;
  created_at: string;
}
