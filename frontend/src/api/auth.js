import { api, clearAccessToken, setAccessToken } from "./client.js";

/**
 * Register a new user account
 * @param {{ user_name: string, password: string }} data
 * @returns {Promise<{ user_id: string, user_name: string, created_at: string }>}
 */
export const registerUser = async ({ user_name, password }) => {
  const response = await api.post("/api/auth/register", {
    user_name,
    password,
  });
  return response.data;
};

/**
 * Login user with credentials; sets HttpOnly refresh cookie in browser and in-memory access token
 * @param {{ user_name: string, password: string }} data
 * @returns {Promise<{ access_token: string, token_type: string }>}
 */
export const loginUser = async ({ user_name, password }) => {
  const response = await api.post("/api/auth/login", {
    user_name,
    password,
  });
  const { access_token } = response.data;
  if (access_token) {
    setAccessToken(access_token);
  }
  return response.data;
};

let refreshPromise = null;

/**
 * Refresh access token using HttpOnly cookie
 * @returns {Promise<{ access_token: string, token_type: string, user?: any }>}
 */
export const refreshToken = async () => {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const response = await api.post("/api/auth/refresh");
      const { access_token } = response.data;
      if (access_token) {
        setAccessToken(access_token);
      }
      return response.data;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

/**
 * Log out user; revokes refresh session and clears cookie
 * @returns {Promise<void>}
 */
export const logoutUser = async () => {
  try {
    await api.post("/api/auth/logout");
  } finally {
    clearAccessToken();
  }
};

/**
 * Get current authenticated user profile
 * @returns {Promise<{ user_id: string, user_name: string, created_at: string }>}
 */
export const getCurrentUser = async () => {
  const response = await api.get("/api/auth/me");
  return response.data;
};
