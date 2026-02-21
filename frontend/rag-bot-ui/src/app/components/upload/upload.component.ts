import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { DocumentInfo } from '../../models/api.models';

@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.scss'],
})
export class UploadComponent implements OnInit {
  documents: DocumentInfo[] = [];
  totalChunks = 0;
  isUploading = false;
  uploadProgress = '';
  uploadSuccess = false;
  vendor = 'Uploaded';
  isDragging = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadDocuments();
  }

  loadDocuments(): void {
    this.api.getDocuments().subscribe({
      next: (res) => {
        this.documents = res.documents;
        this.totalChunks = res.total_chunks;
      },
      error: (err) => {
        console.error('Error loading documents:', err);
      },
    });
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.uploadFile(files[0]);
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.uploadFile(input.files[0]);
    }
  }

  uploadFile(file: File): void {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'html' && ext !== 'htm') {
      this.uploadProgress = '❌ Only PDF and HTML files are supported.';
      this.uploadSuccess = false;
      return;
    }

    this.isUploading = true;
    this.uploadProgress = `Uploading ${file.name}...`;
    this.uploadSuccess = false;

    this.api.uploadDocument(file, this.vendor).subscribe({
      next: (res) => {
        this.uploadProgress = `✅ ${res.filename} uploaded — ${res.chunks_added} chunks indexed.`;
        this.uploadSuccess = true;
        this.isUploading = false;
        this.loadDocuments();
      },
      error: (err) => {
        this.uploadProgress = '❌ Upload failed: ' + (err.error?.detail || err.message);
        this.uploadSuccess = false;
        this.isUploading = false;
      },
    });
  }

  deleteDocument(doc: DocumentInfo): void {
    if (!confirm(`Delete ${doc.document} from ${doc.vendor}?`)) return;

    this.api.deleteDocument(doc.vendor, doc.document).subscribe({
      next: () => {
        this.loadDocuments();
      },
      error: (err) => {
        console.error('Error deleting document:', err);
      },
    });
  }
}
