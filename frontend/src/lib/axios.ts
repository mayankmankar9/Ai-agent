// ✅ src/lib/axios.ts
import axios from 'axios';
import { auth } from './firebase';

const instance = axios.create({
  baseURL: 'http://localhost:8000',
});

instance.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default instance;
