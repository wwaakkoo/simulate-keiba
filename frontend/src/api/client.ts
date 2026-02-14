import type { PredictionResponse } from "../types/prediction";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

interface ApiResponse<TData> {
    data: TData;
    status: number;
}

interface ApiError {
    error: string;
    detail?: string;
    status: number;
}

type ApiResult<TData> = ApiResponse<TData> | ApiError;

function isApiError<TData>(result: ApiResult<TData>): result is ApiError {
    return 'error' in result;
}

async function fetchApi<TData>(
    endpoint: string,
    options?: RequestInit,
): Promise<TData> {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({
            error: 'Unknown error',
            status: response.status,
        }));
        throw new Error(
            isApiError<TData>(errorBody) ? errorBody.error : `HTTP ${response.status}`,
        );
    }

    return response.json() as Promise<TData>;
}

export const apiClient = {
    get: <TData>(endpoint: string) => fetchApi<TData>(endpoint),

    post: <TData>(endpoint: string, body: unknown) =>
        fetchApi<TData>(endpoint, {
            method: 'POST',
            body: JSON.stringify(body),
        }),

    predictRace: (raceId: string) =>
        fetchApi<PredictionResponse>(`/races/${raceId}/predict`, {
            method: 'POST',
        }),
};
