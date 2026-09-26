import axios from "axios";

// Read baseURL from environment; defaults to relative "/" if empty or not defined
const rawBaseURL =
  typeof import.meta !== "undefined" && import.meta.env
    ? import.meta.env.VITE_API_BASE_URL
    : undefined;
const baseURL = rawBaseURL !== undefined && rawBaseURL.trim() !== "" ? rawBaseURL.trim() : "/";

export const api = axios.create({
  baseURL,
  timeout: 10000,
  withCredentials: true, // Send and receive HttpOnly cookies (refresh token)
  headers: {
    "Content-Type": "application/json",
  },
});

// In-memory access token storage
let inMemoryAccessToken = null;
const authFailureListeners = new Set();

export const setAccessToken = (token) => {
  inMemoryAccessToken = token || null;
};

export const getAccessToken = () => {
  return inMemoryAccessToken;
};

export const clearAccessToken = () => {
  inMemoryAccessToken = null;
};

export const onAuthFailure = (callback) => {
  authFailureListeners.add(callback);
  return () => authFailureListeners.delete(callback);
};

const notifyAuthFailure = () => {
  clearAccessToken();
  authFailureListeners.forEach((callback) => {
    try {
      callback();
    } catch (err) {
      console.error("Error in auth failure listener", err);
    }
  });
};

// Request interceptor: attach in-memory Bearer token
api.interceptors.request.use(
  (config) => {
    if (inMemoryAccessToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${inMemoryAccessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 token refresh retry
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    const is401 = error.response?.status === 401;
    const requestUrl = originalRequest.url || "";
    const isAuthEndpoint =
      requestUrl.includes("/api/auth/login") ||
      requestUrl.includes("/api/auth/register") ||
      requestUrl.includes("/api/auth/refresh");

    // If 401 occurred on a normal protected endpoint and haven't retried yet:
    if (is401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        // Queue this request while refresh is in progress
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Attempt to refresh the access token using the HttpOnly cookie
        const refreshResponse = await api.post("/api/auth/refresh");
        const newAccessToken = refreshResponse.data.access_token;

        setAccessToken(newAccessToken);
        processQueue(null, newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        notifyAuthFailure();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Extracts a user-friendly error message from Axios / backend response
 */
export const extractErrorMessage = (error, defaultMessage = "An unexpected error occurred") => {
  if (!error) return defaultMessage;

  const detail = error.response?.data?.detail;

  if (typeof detail === "string" && detail.trim() !== "") {
    return detail;
  }

  // Handle FastAPI / Pydantic validation error lists
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item?.msg) {
          const loc = item.loc ? item.loc[item.loc.length - 1] : "";
          return loc && loc !== "body" ? `${loc}: ${item.msg}` : item.msg;
        }
        return JSON.stringify(item);
      })
      .join(", ");
  }

  if (error.response?.data?.message) {
    return error.response.data.message;
  }

  if (error.message) {
    return error.message;
  }

  return defaultMessage;
};
