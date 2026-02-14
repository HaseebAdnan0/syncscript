# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

### Zustand State Management with Persistence
- Use `create` from `zustand` and `persist` middleware for localStorage persistence
- `partialize` option controls which state fields are persisted (persist only refreshToken and user, not accessToken for security)
- Access state outside React components with `useAuthStore.getState()`
- TypeScript interface defines state shape and actions
- Persist name: `'auth-storage'` creates key in localStorage

### Axios Interceptor Pattern for JWT Auto-Refresh
- Create axios instance with `baseURL` from environment variable
- Request interceptor: attach `Authorization: Bearer {token}` header from auth store
- Response interceptor: catch 401 errors and attempt token refresh
- Use flag (`isRefreshing`) to prevent multiple simultaneous refresh requests
- Queue failed requests during refresh and replay with new token
- On refresh failure: clear auth state and redirect to `/login`
- Mark original request with `_retry` flag to prevent infinite loops
- Use `axios.post` directly for refresh call (not the intercepted instance) to avoid recursion

### API Error Handling Pattern
- Create custom `ApiError` class extending Error with `statusCode` and `errors` fields
- `handleApiError` helper transforms axios errors into structured ApiError
- Extract field-specific errors from DRF response format
- Check `error.response` (server responded with error), `error.request` (no response), or fallback to message

---

## 2026-02-14 - US-009: API Client with JWT Auto-Refresh

### What was implemented
- Created Zustand auth store with localStorage persistence for tokens and user data
- Implemented Axios API client with automatic JWT token refresh on 401 errors
- Request interceptor attaches Bearer token to all API requests
- Response interceptor handles token refresh flow with request queuing
- Custom ApiError class for structured error handling
- Environment variable configuration with .env.local.example

### Files changed/created
**New files:**
- `frontend/src/stores/auth.ts` - Zustand auth store with persist middleware
- `frontend/src/lib/api.ts` - Axios client with JWT auto-refresh interceptors
- `frontend/.env.local.example` - Environment variables template

**Modified files:**
- `frontend/package.json` - Added axios and zustand dependencies

### Learnings

**Zustand Persist Middleware Security:**
- Only persist `refreshToken` and `user`, NOT `accessToken` for security
- Access tokens should be short-lived (15min) and stored only in memory
- Refresh tokens are longer-lived (7 days) and can be persisted to localStorage
- Use `partialize` option to selectively persist state fields
- `getState()` method allows accessing store outside React components (needed for interceptors)

**Axios Interceptor Request Queuing:**
- When refresh is in progress, queue all failed 401 requests
- Store promises in array with `resolve`/`reject` callbacks
- After successful refresh, process queue with new token and retry all requests
- After failed refresh, reject all queued requests and clear auth
- This prevents race conditions when multiple API calls fail simultaneously

**Preventing Infinite Refresh Loops:**
- Mark original request with `_retry` flag before attempting refresh
- Check `!originalRequest._retry` before triggering refresh
- Use separate axios instance (not the intercepted one) for refresh call
- This prevents the refresh call itself from triggering another refresh

**Server-Side Rendering Considerations:**
- Check `typeof window !== 'undefined'` before redirecting to login
- Next.js runs code on both server and client, window is only available client-side
- Environment variables prefixed with `NEXT_PUBLIC_` are available in browser

**Token Refresh Flow Best Practices:**
- Only one refresh attempt at a time using `isRefreshing` flag
- Queue concurrent requests during refresh to avoid multiple refresh calls
- Clear auth and redirect to login only after refresh fails (not on first 401)
- Update both the store and the original request's Authorization header
- Process queued requests before returning the retried original request

---

