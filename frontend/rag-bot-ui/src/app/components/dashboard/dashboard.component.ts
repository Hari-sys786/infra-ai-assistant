import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AnalyticsResponse, HealthResponse } from '../../models/api.models';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit {
  analytics: AnalyticsResponse | null = null;
  health: HealthResponse | null = null;
  isLoading = true;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.isLoading = true;
    this.error = '';

    this.api.health().subscribe({
      next: (res) => {
        this.health = res;
      },
      error: (err) => {
        this.error = 'Backend not reachable. Is the server running on port 8000?';
        this.isLoading = false;
      },
    });

    this.api.getAnalytics().subscribe({
      next: (res) => {
        this.analytics = res;
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
      },
    });
  }

  formatTime(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleString();
  }
}
