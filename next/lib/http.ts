import axios from "axios";

export const djangoApi = axios.create({
  baseURL: process.env.CATALOG_API_BASE_URL ?? "http://djg:8000",
  timeout: 10000,
  validateStatus: () => true,
});

export const browserApi = axios.create({
  baseURL: "/api",
  timeout: 10000,
  validateStatus: () => true,
});
