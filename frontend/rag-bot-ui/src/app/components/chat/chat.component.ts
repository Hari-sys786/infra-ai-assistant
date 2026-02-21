import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { MessageItem, SourceInfo } from '../../models/api.models';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss'],
})
export class ChatComponent implements OnInit {
  @ViewChild('messageContainer') messageContainer!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;

  messages: MessageItem[] = [];
  inputText = '';
  isLoading = false;
  sessionId: string | undefined;
  selectedSources: SourceInfo[] = [];
  showSources = false;
  agentMode: 'query' | 'compare' | 'config' | 'troubleshoot' = 'query';

  // Compare fields
  compareVendors = '';
  compareTopic = '';

  // Config gen fields
  configRequest = '';
  configVendor = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.messages.push({
      role: 'assistant',
      content:
        'Welcome to the IT Infrastructure Assistant! I can help you with:\n\n' +
        '- **Questions** about networking, servers, firewalls, and more\n' +
        '- **Comparing** vendors (e.g., Cisco vs Juniper)\n' +
        '- **Generating** configurations (e.g., VLAN setup for FortiGate)\n' +
        '- **Troubleshooting** issues step by step\n\n' +
        'How can I help you today?',
      timestamp: new Date(),
    });
  }

  sendMessage(): void {
    const text = this.inputText.trim();
    if (!text || this.isLoading) return;

    // Add user message
    this.messages.push({
      role: 'user',
      content: text,
      timestamp: new Date(),
    });
    this.inputText = '';
    this.isLoading = true;
    this.scrollToBottom();

    switch (this.agentMode) {
      case 'compare':
        this.sendCompare(text);
        break;
      case 'config':
        this.sendConfigGen(text);
        break;
      case 'troubleshoot':
        this.sendTroubleshoot(text);
        break;
      default:
        this.sendQuery(text);
    }
  }

  private sendQuery(text: string): void {
    const history = this.messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }));

    this.api
      .query({
        question: text,
        session_id: this.sessionId,
        top_k: 5,
        conversation_history: history,
      })
      .subscribe({
        next: (res) => {
          this.sessionId = res.session_id;
          this.messages.push({
            role: 'assistant',
            content: res.answer,
            sources: res.sources,
            timestamp: new Date(),
          });
          this.isLoading = false;
          this.scrollToBottom();
        },
        error: (err) => {
          this.messages.push({
            role: 'assistant',
            content: '❌ Error: ' + (err.error?.detail || err.message || 'Unknown error'),
            timestamp: new Date(),
          });
          this.isLoading = false;
          this.scrollToBottom();
        },
      });
  }

  private sendCompare(text: string): void {
    // Parse vendors from text or use fields
    const vendors = this.compareVendors
      ? this.compareVendors.split(',').map((v) => v.trim())
      : this.extractVendors(text);
    const topic = this.compareTopic || text;

    this.api.compare({ vendors, topic, top_k: 5 }).subscribe({
      next: (res) => {
        this.messages.push({
          role: 'assistant',
          content: res.comparison,
          sources: res.sources,
          timestamp: new Date(),
        });
        this.isLoading = false;
        this.scrollToBottom();
      },
      error: (err) => {
        this.messages.push({
          role: 'assistant',
          content: '❌ Error: ' + (err.error?.detail || err.message),
          timestamp: new Date(),
        });
        this.isLoading = false;
        this.scrollToBottom();
      },
    });
  }

  private sendConfigGen(text: string): void {
    this.api
      .generateConfig({
        request: text,
        vendor: this.configVendor || undefined,
        top_k: 5,
      })
      .subscribe({
        next: (res) => {
          this.messages.push({
            role: 'assistant',
            content: res.config,
            sources: res.sources,
            timestamp: new Date(),
          });
          this.isLoading = false;
          this.scrollToBottom();
        },
        error: (err) => {
          this.messages.push({
            role: 'assistant',
            content: '❌ Error: ' + (err.error?.detail || err.message),
            timestamp: new Date(),
          });
          this.isLoading = false;
          this.scrollToBottom();
        },
      });
  }

  private sendTroubleshoot(text: string): void {
    const history = this.messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }));

    this.api
      .troubleshoot({
        problem: text,
        session_id: this.sessionId,
        top_k: 5,
        conversation_history: history,
      })
      .subscribe({
        next: (res) => {
          this.sessionId = res.session_id;
          this.messages.push({
            role: 'assistant',
            content: res.diagnosis,
            sources: res.sources,
            timestamp: new Date(),
          });
          this.isLoading = false;
          this.scrollToBottom();
        },
        error: (err) => {
          this.messages.push({
            role: 'assistant',
            content: '❌ Error: ' + (err.error?.detail || err.message),
            timestamp: new Date(),
          });
          this.isLoading = false;
          this.scrollToBottom();
        },
      });
  }

  private extractVendors(text: string): string[] {
    const known = ['Cisco', 'Juniper', 'Fortinet', 'Dell', 'IBM', 'FortiGate', 'FortiWeb'];
    const found = known.filter((v) => text.toLowerCase().includes(v.toLowerCase()));
    return found.length >= 2 ? found : ['Cisco', 'Juniper'];
  }

  showSourcePanel(sources: SourceInfo[]): void {
    this.selectedSources = sources;
    this.showSources = true;
  }

  closeSources(): void {
    this.showSources = false;
  }

  clearChat(): void {
    this.messages = [];
    this.sessionId = undefined;
    this.ngOnInit();
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messageContainer) {
        const el = this.messageContainer.nativeElement;
        el.scrollTop = el.scrollHeight;
      }
    }, 100);
  }
}
