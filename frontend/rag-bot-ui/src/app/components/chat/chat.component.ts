import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { MessageItem, SourceInfo } from '../../models/api.models';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss'],
})
export class ChatComponent implements OnInit, AfterViewChecked {
  @ViewChild('messageContainer') messageContainer!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;

  messages: MessageItem[] = [];
  inputText = '';
  isLoading = false;
  sessionId: string | undefined;
  selectedSources: SourceInfo[] = [];
  showSources = false;
  agentMode: 'query' | 'config' = 'query';
  private shouldScroll = false;

  // Config gen fields
  configRequest = '';
  configVendor = '';

  modes = [
    { value: 'query' as const, label: 'Q&A', icon: '💬' },
    { value: 'config' as const, label: 'Config Gen', icon: '⚙️' },
  ];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.messages.push({
      role: 'assistant',
      content:
        'Welcome to the **IT Infrastructure Assistant**! I can help you with:\n\n' +
        '- **Questions** about networking, servers, firewalls, and more\n' +
        '- **Generating** configurations (e.g., VLAN setup for FortiGate)\n\n' +
        'How can I help you today?',
      timestamp: new Date(),
    });
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  setMode(mode: 'query' | 'config'): void {
    this.agentMode = mode;
  }

  sendMessage(): void {
    const text = this.inputText.trim();
    if (!text || this.isLoading) return;

    this.messages.push({
      role: 'user',
      content: text,
      timestamp: new Date(),
    });
    this.inputText = '';
    this.isLoading = true;
    this.shouldScroll = true;

    // Reset textarea height
    if (this.messageInput) {
      this.messageInput.nativeElement.style.height = 'auto';
    }

    switch (this.agentMode) {
      case 'config':
        this.sendConfigGen(text);
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
          this.shouldScroll = true;
        },
        error: (err) => {
          this.messages.push({
            role: 'assistant',
            content: '❌ Error: ' + (err.error?.detail || err.message || 'Unknown error'),
            timestamp: new Date(),
          });
          this.isLoading = false;
          this.shouldScroll = true;
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
          this.shouldScroll = true;
        },
        error: (err) => {
          this.messages.push({
            role: 'assistant',
            content: '❌ Error: ' + (err.error?.detail || err.message),
            timestamp: new Date(),
          });
          this.isLoading = false;
          this.shouldScroll = true;
        },
      });
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

  onTextareaInput(event: Event): void {
    const textarea = event.target as HTMLTextAreaElement;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
  }

  formatContent(content: string): string {
    // Simple markdown-like rendering
    let html = this.escapeHtml(content);

    // Code blocks (```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Unordered lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    // Clean up <br> inside <ul>
    html = html.replace(/<ul><br>/g, '<ul>');
    html = html.replace(/<br><\/ul>/g, '</ul>');
    html = html.replace(/<\/li><br><li>/g, '</li><li>');

    return html;
  }

  private escapeHtml(text: string): string {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }

  private scrollToBottom(): void {
    if (this.messageContainer) {
      const el = this.messageContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }
}
