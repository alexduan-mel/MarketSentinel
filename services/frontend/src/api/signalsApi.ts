import { apiRequest } from "./apiClient";
import type { Signal } from "../types";

const shouldMock = import.meta.env.VITE_API_MOCK === "true";

const mockSignals: Signal[] = [
  {
    id: "sig-001",
    ticker: "NVDA",
    sentiment: "Bullish",
    title: "Strong institutional buying detected with positive earnings revision",
    description: "Strong institutional buying detected with positive earnings revision",
    confidence: 0.87,
    timestamp: "09:23 PM",
    tags: ["Equity", "Watchlist"],
    highConfidence: true
  },
  {
    id: "sig-002",
    ticker: "TSLA",
    sentiment: "Bearish",
    title: "Delivery miss signals demand weakness, margin pressure expected",
    description: "Delivery miss signals demand weakness, margin pressure expected",
    confidence: 0.79,
    timestamp: "08:47 PM",
    tags: ["Equity", "Watchlist"],
    highConfidence: false
  },
  {
    id: "sig-003",
    ticker: "AAPL",
    sentiment: "Bullish",
    title: "Product launch momentum building, supply chain indicators positive",
    description: "Product launch momentum building, supply chain indicators positive",
    confidence: 0.81,
    timestamp: "07:12 PM",
    tags: ["Equity", "Watchlist"],
    highConfidence: true
  }
];

export async function listSignals(): Promise<Signal[]> {
  if (shouldMock) {
    return mockSignals;
  }
  return apiRequest<Signal[]>("/api/signals");
}

export async function getSignal(id: string): Promise<Signal> {
  if (shouldMock) {
    const signal = mockSignals.find((item) => item.id === id);
    if (!signal) {
      throw new Error("Signal not found");
    }
    return signal;
  }
  return apiRequest<Signal>(`/api/signals/${id}`);
}
