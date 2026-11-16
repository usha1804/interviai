// Runtime validation coverage for persisted resume retrieval and ATS requests.
import { beforeEach, describe, expect, it, vi } from 'vitest';

const client = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  delete: vi.fn(),
}));

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      ...client,
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
    post: vi.fn(),
  },
}));

import { atsService, resumeService } from './api';

describe('resume and ATS API services', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('retrieves the latest persisted resume for the authenticated user', async () => {
    const savedResume = {
      id: 12,
      file_name: 'resume.pdf',
      resume_text: 'Python developer',
      extraction_status: 'completed',
    };
    client.get.mockResolvedValue({ data: savedResume });

    await expect(resumeService.getLatest()).resolves.toEqual({ data: savedResume });
    expect(client.get).toHaveBeenCalledWith('/resume/latest');
  });

  it('uploads resume files as multipart data with time for extraction', async () => {
    const formData = new FormData();
    formData.append('file', new Blob(['resume']), 'resume.pdf');
    client.post.mockResolvedValue({ data: { id: 12, extraction_status: 'completed' } });

    await resumeService.upload(formData);

    expect(client.post).toHaveBeenCalledWith(
      '/resume/upload',
      formData,
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 75000,
      }),
    );
  });

  it('submits the persisted resume ID rather than relying on component-only text', async () => {
    const request = { resume_id: 12, jd_text: 'Python developer role' };
    client.post.mockResolvedValue({ data: { ats_score: 72, report_id: 4 } });

    await atsService.analyze(request);

    expect(client.post).toHaveBeenCalledWith(
      '/ats/analyze',
      request,
      { timeout: 75000 },
    );
  });
});
