import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  QueryRequest,
  QueryResponse,
  DocumentListResponse,
  AnalyticsResponse,
  HealthResponse,
  ConfigResponse,
} from '../models/api.models';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }

  // Health check
  health(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/health`);
  }

  // Query
  query(request: QueryRequest): Observable<QueryResponse> {
    return this.http.post<QueryResponse>(`${this.baseUrl}/query`, request);
  }

  // Upload document
  uploadDocument(file: File, vendor: string): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('vendor', vendor);
    return this.http.post(`${this.baseUrl}/upload`, formData);
  }

  // Documents
  getDocuments(): Observable<DocumentListResponse> {
    return this.http.get<DocumentListResponse>(`${this.baseUrl}/documents`);
  }

  deleteDocument(vendor: string, documentName: string): Observable<any> {
    return this.http.delete(
      `${this.baseUrl}/documents/${encodeURIComponent(vendor)}/${encodeURIComponent(documentName)}`
    );
  }

  // Analytics
  getAnalytics(): Observable<AnalyticsResponse> {
    return this.http.get<AnalyticsResponse>(`${this.baseUrl}/analytics`);
  }

  // Config
  getConfig(): Observable<ConfigResponse> {
    return this.http.get<ConfigResponse>(`${this.baseUrl}/config`);
  }

  updateConfig(config: { anthropic_model?: string }): Observable<any> {
    return this.http.post(`${this.baseUrl}/config`, config);
  }
}
