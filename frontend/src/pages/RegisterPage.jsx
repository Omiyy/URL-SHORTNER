import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, CheckCircle2 } from "lucide-react";
import toast from "react-hot-toast";

import { useAuth } from "../context/AuthContext";
import { extractErrorMessage } from "../api";
import ErrorAlert from "../components/ErrorAlert";
import Spinner from "../components/Spinner";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [userName, setUserName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Password strength indicators
  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasDigit = /\d/.test(password);
  const hasLength = password.length >= 8;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await register({ user_name: userName.trim(), password });
      toast.success("Account created! Please sign in.");
      navigate("/login", { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "Registration failed"));
    } finally {
      setLoading(false);
    }
  };

  const PasswordCheck = ({ met, label }) => (
    <li className={`flex items-center gap-1.5 text-xs ${met ? "text-green-600" : "text-slate-400"}`}>
      <CheckCircle2 className={`h-3.5 w-3.5 ${met ? "opacity-100" : "opacity-40"}`} />
      {label}
    </li>
  );

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <div className="w-full max-w-sm animate-slide-up">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-900">Create an account</h1>
          <p className="mt-1 text-sm text-slate-500">
            Start shortening URLs with FastURL
          </p>
        </div>

        {/* Card */}
        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <ErrorAlert message={error} />

            <div>
              <label htmlFor="register-username" className="label">
                Username
              </label>
              <input
                id="register-username"
                type="text"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                className="input-field"
                placeholder="choose_a_username"
                autoComplete="username"
                minLength={3}
                maxLength={30}
                required
                disabled={loading}
              />
              <p className="mt-1 text-xs text-slate-400">
                3–30 characters, letters, numbers & underscores only
              </p>
            </div>

            <div>
              <label htmlFor="register-password" className="label">
                Password
              </label>
              <div className="relative">
                <input
                  id="register-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pr-10"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  minLength={8}
                  maxLength={128}
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>

              {/* Password requirements */}
              {password.length > 0 && (
                <ul className="mt-2 space-y-0.5 animate-fade-in">
                  <PasswordCheck met={hasLength} label="At least 8 characters" />
                  <PasswordCheck met={hasLower} label="One lowercase letter" />
                  <PasswordCheck met={hasUpper} label="One uppercase letter" />
                  <PasswordCheck met={hasDigit} label="One number" />
                </ul>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? <Spinner size="sm" className="text-white" /> : null}
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-medium text-brand-600 hover:text-brand-700 transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
