import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  refreshToken,
  getCurrentUser,
  logoutUser,
  loginUser as apiLogin,
  registerUser as apiRegister,
  onAuthFailure,
  clearAccessToken,
} from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true while restoring session
  const navigate = useNavigate();

  // Clear auth state and redirect to login
  const clearAuth = useCallback(() => {
    clearAccessToken();
    setUser(null);
  }, []);

  // On mount, attempt to restore session via refresh cookie
  useEffect(() => {
    let cancelled = false;

    const restore = async () => {
      try {
        const data = await refreshToken(); // sets in-memory access token
        if (!cancelled && data.user) setUser(data.user);
      } catch {
        // No valid refresh cookie; user is not signed in
        if (!cancelled) clearAuth();
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    restore();
    return () => { cancelled = true; };
  }, [clearAuth]);

  // Listen for auth failures from the interceptor (e.g. refresh failed)
  useEffect(() => {
    const unsubscribe = onAuthFailure(() => {
      clearAuth();
      navigate("/login", { replace: true });
    });
    return unsubscribe;
  }, [clearAuth, navigate]);

  const login = useCallback(async (credentials) => {
    const data = await apiLogin(credentials);
    if (data.user) setUser(data.user);
    return data;
  }, []);

  const register = useCallback(async (credentials) => {
    return await apiRegister(credentials);
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } finally {
      clearAuth();
      navigate("/login", { replace: true });
    }
  }, [clearAuth, navigate]);

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
