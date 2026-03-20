import axios from "axios";

export const browserApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_CATALOG_API_BASE_URL ?? "http://localhost:8000/api",
  timeout: 10000,
  validateStatus: () => true,
});
