import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8001",
});

export const predictPrice = async (payload) => {
  const response = await api.post(
    "/api/v1/predict",
    payload,
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  return response.data;
};

export const analyzeImage = async (file) => {
  const formData = new FormData();

  formData.append("image", file);

  const response = await api.post(
    "/api/v1/analyze-image",
    formData
  );

  return response.data;
};