import assert from "node:assert";
import {
  api,
  setAccessToken,
  getAccessToken,
  clearAccessToken,
  extractErrorMessage,
} from "./client.js";
import { registerUser, loginUser, refreshToken, logoutUser, getCurrentUser } from "./auth.js";
import { createShortUrl, getUrls, getUrlStats, deleteUrl } from "./urls.js";

console.log("Running Step 1 Foundation Verifications...\n");

// 1. Verify withCredentials
assert.strictEqual(api.defaults.withCredentials, true, "api.defaults.withCredentials must be true for HttpOnly cookies");
console.log("✓ withCredentials is true");

// 2. Verify token storage
clearAccessToken();
assert.strictEqual(getAccessToken(), null, "Initial token must be null");
setAccessToken("test-token-123");
assert.strictEqual(getAccessToken(), "test-token-123", "Token should match set value");
clearAccessToken();
assert.strictEqual(getAccessToken(), null, "Token should be cleared");
console.log("✓ In-memory access token storage works as expected");

// 3. Verify request interceptor adds Authorization header
setAccessToken("sample-bearer-token");
const mockConfig = { headers: {} };
const interceptor = api.interceptors.request.handlers[0].fulfilled;
const modifiedConfig = interceptor(mockConfig);
assert.strictEqual(
  modifiedConfig.headers.Authorization,
  "Bearer sample-bearer-token",
  "Bearer header must be attached by request interceptor"
);
clearAccessToken();
console.log("✓ Request interceptor successfully injects Bearer header");

// 4. Verify extractErrorMessage
assert.strictEqual(
  extractErrorMessage({ response: { data: { detail: "User already exists" } } }),
  "User already exists"
);
assert.strictEqual(
  extractErrorMessage({
    response: {
      data: {
        detail: [
          { loc: ["body", "password"], msg: "String should have at least 8 characters" },
        ],
      },
    },
  }),
  "password: String should have at least 8 characters"
);
assert.strictEqual(
  extractErrorMessage(null, "Fallback message"),
  "Fallback message"
);
console.log("✓ extractErrorMessage parses FastAPI string and validation error lists correctly");

// 5. Verify function definitions exist
assert.strictEqual(typeof registerUser, "function");
assert.strictEqual(typeof loginUser, "function");
assert.strictEqual(typeof refreshToken, "function");
assert.strictEqual(typeof logoutUser, "function");
assert.strictEqual(typeof getCurrentUser, "function");
assert.strictEqual(typeof createShortUrl, "function");
assert.strictEqual(typeof getUrls, "function");
assert.strictEqual(typeof getUrlStats, "function");
assert.strictEqual(typeof deleteUrl, "function");
console.log("✓ All auth and url endpoint service functions are exported and callable");

console.log("\nAll Step 1 foundation checks PASSED successfully!");
