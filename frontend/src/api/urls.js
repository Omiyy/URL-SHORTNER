import { api } from "./client.js";

/**
 * @typedef {Object} UrlItem
 * @property {string} short_code
 * @property {string} short_url
 * @property {string} original_url
 * @property {number} no_of_clicks
 * @property {string} created_at
 */

/**
 * Create a shortened URL
 * @param {{ original_url: string, custom_alias?: string }} payload
 * @returns {Promise<UrlItem>}
 */
export const createShortUrl = async ({ original_url, custom_alias }) => {
  const body = {
    original_url: original_url.trim(),
  };

  if (custom_alias && custom_alias.trim()) {
    body.custom_alias = custom_alias.trim();
  }

  const response = await api.post("/api/urls", body);
  return response.data;
};

/**
 * Fetch all URLs created by the authenticated user
 * @returns {Promise<UrlItem[]>}
 */
export const getUrls = async () => {
  const response = await api.get("/api/urls");
  return response.data;
};

/**
 * Fetch real-time stats for a specific short code
 * @param {string} shortCode
 * @returns {Promise<UrlItem>}
 */
export const getUrlStats = async (shortCode) => {
  const response = await api.get(`/api/urls/${encodeURIComponent(shortCode)}/stats`);
  return response.data;
};

/**
 * Delete (soft-delete) a shortened URL
 * @param {string} shortCode
 * @returns {Promise<void>}
 */
export const deleteUrl = async (shortCode) => {
  await api.delete(`/api/urls/${encodeURIComponent(shortCode)}`);
};
