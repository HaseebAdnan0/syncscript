export type CitationFormat = 'apa7' | 'mla9' | 'chicago17' | 'bibtex' | 'ieee' | 'harvard';

export interface User {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  email_verified: boolean;
  created_at: string;
  default_citation_format?: CitationFormat | null;
}
