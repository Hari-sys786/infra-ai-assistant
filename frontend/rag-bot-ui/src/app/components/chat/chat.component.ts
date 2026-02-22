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
  private shouldScroll = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.messages.push({
      role: 'assistant',
      content:
        'Hello! I\'m your **IT Infrastructure Assistant**. I can help you with questions about networking, servers, firewalls, storage, and more — all powered by your indexed documentation.\n\n' +
        'Try asking something like:\n' +
        '- *What is FortiGate?*\n' +
        '- *How do I configure VLANs?*\n' +
        '- *Dell PowerEdge specifications*',
      timestamp: new Date(),
    });
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
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

    if (this.messageInput) {
      this.messageInput.nativeElement.style.height = 'auto';
    }

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
            content: '❌ ' + (err.error?.detail || err.message || 'Something went wrong. Please try again.'),
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
    let html = this.escapeHtml(content);

    // Headers (### → h3, ## → h2)
    html = html.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>');

    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code class="lang-$1">$2</code></pre>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Ordered lists
    html = html.replace(/^(\d+)\. (.+)$/gm, '<li class="ol-item" value="$1">$2</li>');

    // Unordered lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul class="md-list">$&</ul>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    // Clean up
    html = html.replace(/<ul class="md-list"><br>/g, '<ul class="md-list">');
    html = html.replace(/<br><\/ul>/g, '</ul>');
    html = html.replace(/<\/li><br><li>/g, '</li><li>');
    html = html.replace(/<\/h[34]><br>/g, (m) => m.replace('<br>', ''));

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
