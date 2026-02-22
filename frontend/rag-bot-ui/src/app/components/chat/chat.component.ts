import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { MessageItem, SourceInfo, HealthResponse, DocumentInfo } from '../../models/api.models';

interface UploadItem {
  file: File;
  name: string;
  size: string;
  status: 'pending' | 'uploading' | 'done' | 'error';
  msg: string;
  chunks: number;
}

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

  // Dashboard
  health: HealthResponse | null = null;
  totalDocs = 0;
  totalChunks = 0;
  totalQueries = 0;
  documents: DocumentInfo[] = [];

  // Upload
  showUpload = false;
  uploads: UploadItem[] = [];
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
    this.api.health().subscribe({ next: (h) => this.health = h, error: () => {} });
    this.api.getAnalytics().subscribe({ next: (a) => this.totalQueries = a.total_queries, error: () => {} });
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

    if (this.messageInput) this.messageInput.nativeElement.style.height = 'auto';

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
  }

  onDragOver(e: DragEvent): void { e.preventDefault(); e.stopPropagation(); this.isDragging = true; }
  onDragLeave(e: DragEvent): void { e.preventDefault(); this.isDragging = false; }

  onDrop(e: DragEvent): void {
    e.preventDefault();
    this.isDragging = false;
    const files = e.dataTransfer?.files;
    if (files) this.addFiles(files);
  }

  onFileSelected(e: Event): void {
    const input = e.target as HTMLInputElement;
    if (input.files) {
      this.addFiles(input.files);
      input.value = '';
    }
  }

  addFiles(files: FileList): void {
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (!['pdf', 'html', 'htm'].includes(ext || '')) {
        this.uploads.unshift({
          file, name: file.name, size: this.fmtSize(file.size),
          status: 'error', msg: 'Unsupported format', chunks: 0,
        });
        continue;
      }
      const item: UploadItem = {
        file, name: file.name, size: this.fmtSize(file.size),
        status: 'uploading', msg: 'Indexing…', chunks: 0,
      };
      this.uploads.unshift(item);
      this.uploadOne(item);
    }
  }

  uploadOne(item: UploadItem): void {
    this.api.uploadDocument(item.file, '').subscribe({
      next: (res) => {
        item.status = 'done';
        item.chunks = res.chunks_added;
        item.msg = `${res.chunks_added} chunks indexed`;
        this.loadStats();
      },
      error: (err) => {
        item.status = 'error';
        item.msg = err.error?.detail || 'Upload failed';
      },
    });
  }

  removeUploadItem(i: number): void {
    this.uploads.splice(i, 1);
  }

  deleteDocument(doc: DocumentInfo): void {
    this.api.deleteDocument(doc.vendor, doc.document).subscribe({
      next: () => this.loadStats(),
      error: () => {},
    });
  }

  fmtSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  }

  // ── Sources ──

  showSourcePanel(sources: SourceInfo[]): void { this.selectedSources = sources; this.showSources = true; }
  closeSources(): void { this.showSources = false; }

  // ── Helpers ──

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); this.sendMessage(); }
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
