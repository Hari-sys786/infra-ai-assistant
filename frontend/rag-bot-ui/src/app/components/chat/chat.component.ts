import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { MessageItem, SourceInfo, HealthResponse, DocumentInfo } from '../../models/api.models';

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

  // Dashboard stats
  health: HealthResponse | null = null;
  totalDocs = 0;
  totalChunks = 0;
  totalQueries = 0;
  documents: DocumentInfo[] = [];

  // Upload
  showUpload = false;
  uploadVendor = '';
  isUploading = false;
  uploadMsg = '';
  uploadOk = false;
  isDragging = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadStats();
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  loadStats(): void {
    this.api.health().subscribe({
      next: (h) => this.health = h,
      error: () => {},
    });
    this.api.getAnalytics().subscribe({
      next: (a) => this.totalQueries = a.total_queries,
      error: () => {},
    });
    this.api.getDocuments().subscribe({
      next: (d) => {
        this.documents = d.documents;
        this.totalDocs = d.documents.length;
        this.totalChunks = d.total_chunks;
      },
      error: () => {},
    });
  }

  // ── Chat ──

  sendMessage(): void {
    const text = this.inputText.trim();
    if (!text || this.isLoading) return;

    this.messages.push({ role: 'user', content: text, timestamp: new Date() });
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

    this.api.query({ question: text, session_id: this.sessionId, top_k: 5, conversation_history: history })
      .subscribe({
        next: (res) => {
          this.sessionId = res.session_id;
          this.messages.push({ role: 'assistant', content: res.answer, sources: res.sources, timestamp: new Date() });
          this.isLoading = false;
          this.shouldScroll = true;
          this.totalQueries++;
        },
        error: (err) => {
          this.messages.push({ role: 'assistant', content: '❌ ' + (err.error?.detail || err.message || 'Something went wrong.'), timestamp: new Date() });
          this.isLoading = false;
          this.shouldScroll = true;
        },
      });
  }

  clearChat(): void {
    this.messages = [];
    this.sessionId = undefined;
  }

  // ── Upload ──

  toggleUpload(): void {
    this.showUpload = !this.showUpload;
    this.uploadMsg = '';
  }

  onDragOver(e: DragEvent): void {
    e.preventDefault();
    e.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(e: DragEvent): void {
    e.preventDefault();
    this.isDragging = false;
  }

  onDrop(e: DragEvent): void {
    e.preventDefault();
    this.isDragging = false;
    const file = e.dataTransfer?.files[0];
    if (file) this.uploadFile(file);
  }

  onFileSelected(e: Event): void {
    const input = e.target as HTMLInputElement;
    if (input.files?.[0]) {
      this.uploadFile(input.files[0]);
      input.value = '';
    }
  }

  uploadFile(file: File): void {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'html', 'htm'].includes(ext || '')) {
      this.uploadMsg = '❌ Only PDF and HTML files are supported.';
      this.uploadOk = false;
      return;
    }

    this.isUploading = true;
    this.uploadMsg = '';
    const vendor = this.uploadVendor.trim() || 'Uploaded';

    this.api.uploadDocument(file, vendor).subscribe({
      next: (res) => {
        this.uploadMsg = `✅ ${res.filename} — ${res.chunks_added} chunks indexed`;
        this.uploadOk = true;
        this.isUploading = false;
        this.loadStats();
      },
      error: (err) => {
        this.uploadMsg = '❌ ' + (err.error?.detail || 'Upload failed');
        this.uploadOk = false;
        this.isUploading = false;
      },
    });
  }

  deleteDocument(doc: DocumentInfo): void {
    this.api.deleteDocument(doc.vendor, doc.document).subscribe({
      next: () => this.loadStats(),
      error: () => {},
    });
  }

  // ── Sources ──

  showSourcePanel(sources: SourceInfo[]): void {
    this.selectedSources = sources;
    this.showSources = true;
  }

  closeSources(): void {
    this.showSources = false;
  }

  // ── Helpers ──

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  onTextareaInput(event: Event): void {
    const el = event.target as HTMLTextAreaElement;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }

  formatContent(content: string): string {
    let h = this.esc(content);
    h = h.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
    h = h.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>');
    h = h.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code class="lang-$1">$2</code></pre>');
    h = h.replace(/`([^`]+)`/g, '<code class="ic">$1</code>');
    h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');
    h = h.replace(/^(\d+)\. (.+)$/gm, '<li class="ol-item" value="$1">$2</li>');
    h = h.replace(/^- (.+)$/gm, '<li>$1</li>');
    h = h.replace(/(<li[^>]*>.*<\/li>\n?)+/g, '<ul class="md-list">$&</ul>');
    h = h.replace(/\n/g, '<br>');
    h = h.replace(/<ul class="md-list"><br>/g, '<ul class="md-list">');
    h = h.replace(/<br><\/ul>/g, '</ul>');
    h = h.replace(/<\/li><br><li/g, '</li><li');
    h = h.replace(/<\/h[34]><br>/g, (m) => m.replace('<br>', ''));
    return h;
  }

  private esc(t: string): string {
    return t.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[c] || c));
  }

  private scrollToBottom(): void {
    if (this.messageContainer) {
      this.messageContainer.nativeElement.scrollTop = this.messageContainer.nativeElement.scrollHeight;
    }
  }
}
