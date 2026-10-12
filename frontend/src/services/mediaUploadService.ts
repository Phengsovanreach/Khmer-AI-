/**
 * Dynamic Internet-Based Media Upload Service
 * 
 * Provides production-ready, chunked, resumable, and single-part media uploads
 * with real-time byte measurement, rolling-window transfer speed calculation,
 * accurate ETA estimation, pause, resume, cancel, and exponential backoff retry.
 * 
 * © 2026 Phengsovanreach. All rights reserved.
 */

import { AuthService } from './authService';

export type UploadPhase =
  | 'idle'
  | 'preparing'
  | 'uploading'
  | 'processing'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface UploadProgressInfo {
  phase: UploadPhase;
  statusKhmer: string;
  statusEnglish: string;
  progressPercent: number; // 0 - 100
  uploadedBytes: number;
  totalBytes: number;
  formattedUploaded: string;
  formattedTotal: string;
  speedBytesPerSec: number;
  formattedSpeed: string;
  etaSeconds: number | null;
  formattedEta: string;
  currentChunk: number;
  totalChunks: number;
  uploadId: string | null;
  error: string | null;
  isSlow: boolean;
}

export interface UploadOptions {
  apiBase: string;
  sourceLang?: string;
  targetLang?: string;
  name?: string;
  chunkSize?: number; // default 5MB
  maxRetries?: number;
  onProgress?: (info: UploadProgressInfo) => void;
}

export function formatBytes(bytes: number, decimals = 1): string {
  if (bytes <= 0 || isNaN(bytes)) return '0 MB';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  if (i === 0) return `${bytes} Bytes`;
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export function formatSpeed(bytesPerSec: number): string {
  if (!bytesPerSec || bytesPerSec <= 0 || isNaN(bytesPerSec)) {
    return '0 KB/s';
  }
  if (bytesPerSec >= 1024 * 1024) {
    return `${(bytesPerSec / (1024 * 1024)).toFixed(1)} MB/s`;
  }
  return `${(bytesPerSec / 1024).toFixed(0)} KB/s`;
}

export function formatEta(seconds: number | null): string {
  if (seconds === null || seconds < 0 || !isFinite(seconds)) {
    return 'Calculating... (កំពុងគណនា)';
  }
  const s = Math.round(seconds);
  if (s <= 1) return 'A few seconds (ប្រហែលពីរបីវិនាទី)';
  if (s < 60) return `Approximately ${s} seconds (ប្រហែល ${s} វិនាទី)`;
  const mins = Math.floor(s / 60);
  const remSecs = s % 60;
  if (mins === 1 && remSecs === 0) return 'Approximately 1 minute (ប្រហែល ១ នាទី)';
  if (remSecs === 0) return `Approximately ${mins} minutes (ប្រហែល ${mins} នាទី)`;
  return `Approximately ${mins}m ${remSecs}s (ប្រហែល ${mins} នាទី ${remSecs} វិនាទី)`;
}

interface SpeedSample {
  time: number;
  bytes: number;
}

export class MediaUploadController {
  private file: File;
  private options: UploadOptions;
  private uploadId: string | null = null;
  private chunkSize: number;
  private totalChunks: number;
  private uploadedChunks: Set<number> = new Set();
  private isPaused = false;
  private isCancelled = false;
  private activeXhr: XMLHttpRequest | null = null;
  private speedSamples: SpeedSample[] = [];
  private smoothedSpeed = 0;
  private lastProgressDispatch = 0;
  private slowCounter = 0;
  private currentProgress: UploadProgressInfo;

  constructor(file: File, options: UploadOptions) {
    this.file = file;
    this.options = {
      chunkSize: 5 * 1024 * 1024, // 5MB chunks
      maxRetries: 3,
      sourceLang: 'auto',
      targetLang: 'km',
      ...options,
    };
    this.chunkSize = this.options.chunkSize || 5 * 1024 * 1024;
    this.totalChunks = Math.max(1, Math.ceil(file.size / this.chunkSize));

    this.currentProgress = {
      phase: 'preparing',
      statusKhmer: 'កំពុង Upload ឯកសារមេឌៀទៅកាន់ម៉ាស៊ីនបម្រើ...',
      statusEnglish: 'Preparing media upload...',
      progressPercent: 0,
      uploadedBytes: 0,
      totalBytes: file.size,
      formattedUploaded: '0 MB',
      formattedTotal: formatBytes(file.size),
      speedBytesPerSec: 0,
      formattedSpeed: '0 KB/s',
      etaSeconds: null,
      formattedEta: 'Calculating... (កំពុងគណនា)',
      currentChunk: 0,
      totalChunks: this.totalChunks,
      uploadId: null,
      error: null,
      isSlow: false,
    };
  }

  public getProgress(): UploadProgressInfo {
    return { ...this.currentProgress };
  }

  private updateProgress(patch: Partial<UploadProgressInfo>) {
    this.currentProgress = { ...this.currentProgress, ...patch };
    if (this.options.onProgress) {
      this.options.onProgress(this.currentProgress);
    }
  }

  private recordSpeedSample(totalTransferred: number) {
    const now = performance.now();
    this.speedSamples.push({ time: now, bytes: totalTransferred });

    // Keep samples within a 1500ms sliding window
    const windowStart = now - 1500;
    while (this.speedSamples.length > 2 && this.speedSamples[0].time < windowStart) {
      this.speedSamples.shift();
    }

    if (this.speedSamples.length >= 2) {
      const oldest = this.speedSamples[0];
      const newest = this.speedSamples[this.speedSamples.length - 1];
      const deltaMs = newest.time - oldest.time;
      const deltaBytes = newest.bytes - oldest.bytes;

      if (deltaMs > 200 && deltaBytes >= 0) {
        const rawSpeed = (deltaBytes / deltaMs) * 1000;
        // Exponential Moving Average smoothing (alpha = 0.35)
        if (this.smoothedSpeed === 0) {
          this.smoothedSpeed = rawSpeed;
        } else {
          this.smoothedSpeed = 0.35 * rawSpeed + 0.65 * this.smoothedSpeed;
        }
      }
    }

    // Detect persistent slow connection (< 40 KB/s)
    if (this.smoothedSpeed > 0 && this.smoothedSpeed < 40 * 1024) {
      this.slowCounter++;
    } else {
      this.slowCounter = 0;
    }

    const remainingBytes = Math.max(0, this.file.size - totalTransferred);
    let eta: number | null = null;
    if (this.smoothedSpeed > 1024) {
      eta = remainingBytes / this.smoothedSpeed;
    }

    const percent = Math.min(
      99.9,
      Math.round((totalTransferred / Math.max(1, this.file.size)) * 1000) / 10
    );

    this.updateProgress({
      uploadedBytes: totalTransferred,
      progressPercent: percent,
      formattedUploaded: formatBytes(totalTransferred),
      speedBytesPerSec: this.smoothedSpeed,
      formattedSpeed: formatSpeed(this.smoothedSpeed),
      etaSeconds: eta,
      formattedEta: formatEta(eta),
      isSlow: this.slowCounter > 8,
    });
  }

  public async start(): Promise<any> {
    this.isPaused = false;
    this.isCancelled = false;
    this.updateProgress({
      phase: 'preparing',
      statusKhmer: 'កំពុង Upload ឯកសារមេឌៀទៅកាន់ម៉ាស៊ីនបម្រើ...',
      statusEnglish: 'Initializing dynamic upload session...',
      error: null,
    });

    try {
      // 1. Initialize Chunked Upload on Server
      const initUrl = `${this.options.apiBase}/api/upload/init`;
      const authHeaders = AuthService.getAuthHeaders();
      const initRes = await fetch(initUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        credentials: 'include',
        body: JSON.stringify({
          filename: this.file.name,
          file_size: this.file.size,
          chunk_size: this.chunkSize,
          total_chunks: this.totalChunks,
          source_language: this.options.sourceLang || 'auto',
          target_language: this.options.targetLang || 'km',
          name: this.options.name,
        }),
      });

      if (!initRes.ok) {
        const errJson = await initRes.json().catch(() => ({}));
        throw new Error(errJson.detail || 'បរាជ័យក្នុងការចាប់ផ្តើម Upload Session');
      }

      const initData = await initRes.json();
      this.uploadId = initData.upload_id;
      this.uploadedChunks = new Set(initData.uploaded_chunks || []);

      this.updateProgress({
        uploadId: this.uploadId,
        phase: 'uploading',
        statusKhmer: 'កំពុង Upload ឯកសារមេឌៀទៅកាន់ម៉ាស៊ីនបម្រើ...',
        statusEnglish: 'Uploading media chunks...',
        totalChunks: this.totalChunks,
      });

      // 2. Upload chunks in sequential or pipeline mode
      await this.uploadRemainingChunks();

      if (this.isCancelled) {
        throw new Error('ការ Upload ត្រូវបានបោះបង់ (Upload cancelled)');
      }
      if (this.isPaused) {
        return null;
      }

      // 3. Finalize and complete upload
      this.updateProgress({
        phase: 'processing',
        progressPercent: 100,
        formattedUploaded: formatBytes(this.file.size),
        statusKhmer: 'កំពុងផ្ទៀងផ្ទាត់ និងផ្គុំឯកសារមេឌៀ (Verifying & Assembling)...',
        statusEnglish: 'Validating and assembling media with server...',
        formattedSpeed: formatSpeed(this.smoothedSpeed),
        formattedEta: 'Finishing... (ជិតរួចរាល់)',
      });

      const completeUrl = `${this.options.apiBase}/api/upload/complete`;
      const compRes = await fetch(completeUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        credentials: 'include',
        body: JSON.stringify({
          upload_id: this.uploadId,
          source_language: this.options.sourceLang || 'auto',
          target_language: this.options.targetLang || 'km',
          name: this.options.name,
        }),
      });

      if (!compRes.ok) {
        const errJson = await compRes.json().catch(() => ({}));
        throw new Error(errJson.detail || 'បរាជ័យក្នុងការផ្គុំឯកសារមេឌៀ');
      }

      const jobData = await compRes.json();
      this.updateProgress({
        phase: 'completed',
        progressPercent: 100,
        statusKhmer: 'បាន Upload និងផ្ទៀងផ្ទាត់ជោគជ័យ ១០០%!',
        statusEnglish: 'Upload completed and validated successfully!',
        formattedEta: 'Done (រួចរាល់)',
      });

      return jobData;
    } catch (err: any) {
      if (this.isCancelled) {
        this.updateProgress({
          phase: 'cancelled',
          statusKhmer: 'ការ Upload ត្រូវបានបោះបង់',
          statusEnglish: 'Upload cancelled',
        });
        throw err;
      }
      if (this.isPaused) {
        this.updateProgress({
          phase: 'paused',
          statusKhmer: 'ការ Upload ត្រូវបានផ្អាកបណ្តោះអាសន្ន',
          statusEnglish: 'Upload paused',
        });
        return null;
      }

      this.updateProgress({
        phase: 'failed',
        error: err.message || 'ការ Upload បរាជ័យ',
        statusKhmer: 'ការ Upload បានបរាជ័យ',
        statusEnglish: 'Upload failed',
      });
      throw err;
    }
  }

  private async uploadRemainingChunks(): Promise<void> {
    const total = this.totalChunks;

    for (let idx = 0; idx < total; idx++) {
      if (this.isCancelled || this.isPaused) break;

      // Skip already uploaded chunks (resumption support)
      if (this.uploadedChunks.has(idx)) {
        continue;
      }

      this.updateProgress({ currentChunk: idx + 1 });

      const start = idx * this.chunkSize;
      const end = Math.min(this.file.size, start + this.chunkSize);
      const chunkBlob = this.file.slice(start, end);

      let retriesLeft = this.options.maxRetries || 3;
      let success = false;
      let lastErr: any = null;

      while (retriesLeft >= 0 && !success && !this.isPaused && !this.isCancelled) {
        try {
          await this.uploadSingleChunk(idx, chunkBlob);
          this.uploadedChunks.add(idx);
          success = true;
        } catch (err: any) {
          lastErr = err;
          retriesLeft--;
          if (retriesLeft >= 0 && !this.isPaused && !this.isCancelled) {
            // Exponential backoff: 1000ms, 2000ms, 4000ms
            const delay = Math.pow(2, 3 - retriesLeft) * 500;
            await new Promise((res) => setTimeout(res, delay));
          }
        }
      }

      if (!success && !this.isPaused && !this.isCancelled) {
        throw new Error(
          `បរាជ័យក្នុងការ Upload Chunk ${idx + 1}/${total} ក្រោយការព្យាយាម ៣ ដង: ${lastErr?.message || 'Network error'}`
        );
      }
    }
  }

  private uploadSingleChunk(index: number, blob: Blob): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isCancelled) return reject(new Error('Cancelled'));
      if (this.isPaused) return reject(new Error('Paused'));

      const xhr = new XMLHttpRequest();
      this.activeXhr = xhr;

      const fd = new FormData();
      fd.append('upload_id', this.uploadId!);
      fd.append('chunk_index', String(index));
      fd.append('chunk', blob, `chunk_${index}.part`);

      const baseTransferred = this.calculateBaseTransferred();

      xhr.upload.onprogress = (evt) => {
        if (evt.lengthComputable) {
          const currentTotal = baseTransferred + evt.loaded;
          const now = performance.now();
          if (now - this.lastProgressDispatch > 250 || currentTotal >= this.file.size) {
            this.lastProgressDispatch = now;
            this.recordSpeedSample(currentTotal);
          }
        }
      };

      xhr.onload = () => {
        this.activeXhr = null;
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            if (data.uploaded_chunks) {
              data.uploaded_chunks.forEach((c: number) => this.uploadedChunks.add(c));
            }
            this.recordSpeedSample(this.calculateBaseTransferred());
            resolve();
          } catch (e) {
            resolve();
          }
        } else {
          try {
            const errJson = JSON.parse(xhr.responseText);
            reject(new Error(errJson.detail || `Chunk ${index} failed with HTTP ${xhr.status}`));
          } catch {
            reject(new Error(`Chunk ${index} failed with HTTP ${xhr.status}`));
          }
        }
      };

      xhr.onerror = () => {
        this.activeXhr = null;
        reject(new Error('ការតភ្ជាប់អ៊ីនធឺណិតដាច់ ឬមានបញ្ហាបណ្តាញ (Network connection lost)'));
      };

      xhr.ontimeout = () => {
        this.activeXhr = null;
        reject(new Error('Upload chunk timed out.'));
      };

      xhr.onabort = () => {
        this.activeXhr = null;
        reject(new Error(this.isPaused ? 'Paused' : 'Cancelled'));
      };

      xhr.open('POST', `${this.options.apiBase}/api/upload/chunk`);
      xhr.withCredentials = true;
      const token = AuthService.getToken();
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.timeout = 45000; // 45 seconds per chunk
      xhr.send(fd);
    });
  }

  private calculateBaseTransferred(): number {
    let bytes = 0;
    for (const idx of this.uploadedChunks) {
      const start = idx * this.chunkSize;
      const end = Math.min(this.file.size, start + this.chunkSize);
      bytes += end - start;
    }
    return bytes;
  }

  public pause() {
    if (this.currentProgress.phase !== 'uploading') return;
    this.isPaused = true;
    if (this.activeXhr) {
      this.activeXhr.abort();
      this.activeXhr = null;
    }
    this.speedSamples = [];
    this.smoothedSpeed = 0;
    this.updateProgress({
      phase: 'paused',
      speedBytesPerSec: 0,
      formattedSpeed: '0 KB/s',
      formattedEta: 'Paused (បានផ្អាក)',
      statusKhmer: 'ការ Upload ត្រូវបានផ្អាកបណ្តោះអាសន្ន',
      statusEnglish: 'Upload paused. Ready to resume.',
    });
  }

  public async resume(): Promise<any> {
    if (this.currentProgress.phase !== 'paused' && this.currentProgress.phase !== 'failed') return null;
    this.isPaused = false;
    this.isCancelled = false;

    this.updateProgress({
      phase: 'uploading',
      statusKhmer: 'កំពុងបន្ត Upload ឯកសារមេឌៀ (Resuming)...',
      statusEnglish: 'Resuming media upload...',
      formattedEta: 'Recalculating... (កំពុងគណនាឡើងវិញ)',
    });

    try {
      // Refresh status from server to sync uploaded chunk indices
      const authHeaders = AuthService.getAuthHeaders();
      if (this.uploadId) {
        const statusRes = await fetch(`${this.options.apiBase}/api/upload/status/${this.uploadId}`, {
          headers: { ...authHeaders },
          credentials: 'include',
        });
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          this.uploadedChunks = new Set(statusData.uploaded_chunks || []);
        }
      }

      await this.uploadRemainingChunks();

      if (this.isCancelled || this.isPaused) return null;

      // Finalize
      this.updateProgress({
        phase: 'processing',
        progressPercent: 100,
        formattedUploaded: formatBytes(this.file.size),
        statusKhmer: 'កំពុងផ្ទៀងផ្ទាត់ និងផ្គុំឯកសារមេឌៀ (Verifying & Assembling)...',
        statusEnglish: 'Validating assembled media with server...',
      });

      const completeUrl = `${this.options.apiBase}/api/upload/complete`;
      const compRes = await fetch(completeUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        credentials: 'include',
        body: JSON.stringify({
          upload_id: this.uploadId,
          source_language: this.options.sourceLang || 'auto',
          target_language: this.options.targetLang || 'km',
          name: this.options.name,
        }),
      });

      if (!compRes.ok) {
        const errJson = await compRes.json().catch(() => ({}));
        throw new Error(errJson.detail || 'បរាជ័យក្នុងការផ្គុំឯកសារមេឌៀ');
      }

      const jobData = await compRes.json();
      this.updateProgress({
        phase: 'completed',
        progressPercent: 100,
        statusKhmer: 'បាន Upload និងផ្ទៀងផ្ទាត់ជោគជ័យ ១០០%!',
        statusEnglish: 'Upload completed and validated successfully!',
      });
      return jobData;
    } catch (err: any) {
      if (this.isPaused || this.isCancelled) return null;
      this.updateProgress({
        phase: 'failed',
        error: err.message || 'ការបន្ត Upload បរាជ័យ',
        statusKhmer: 'ការបន្ត Upload បរាជ័យ',
        statusEnglish: 'Resume failed',
      });
      throw err;
    }
  }

  public async cancel(): Promise<void> {
    this.isCancelled = true;
    this.isPaused = false;
    if (this.activeXhr) {
      this.activeXhr.abort();
      this.activeXhr = null;
    }

    if (this.uploadId) {
      try {
        const authHeaders = AuthService.getAuthHeaders();
        await fetch(`${this.options.apiBase}/api/upload/${this.uploadId}`, {
          method: 'DELETE',
          headers: { ...authHeaders },
          credentials: 'include',
        });
      } catch {
        // ignore server delete errors on cancellation
      }
    }

    this.updateProgress({
      phase: 'cancelled',
      speedBytesPerSec: 0,
      formattedSpeed: '0 KB/s',
      formattedEta: 'Cancelled',
      statusKhmer: 'ការ Upload ត្រូវបានបោះបង់ និងសម្អាតរួចរាល់',
      statusEnglish: 'Upload cancelled and cleaned up.',
    });
  }
}
