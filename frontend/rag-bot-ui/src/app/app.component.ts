import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {
  sidebarOpen = true;

  navItems = [
    { label: 'Chat', icon: 'chat', route: '/chat' },
    { label: 'Upload', icon: 'upload', route: '/upload' },
    { label: 'Dashboard', icon: 'dashboard', route: '/dashboard' },
  ];

  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen;
  }
}
