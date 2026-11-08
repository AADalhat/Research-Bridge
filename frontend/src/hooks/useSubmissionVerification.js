import { useCallback, useEffect, useRef, useState } from 'react';
import { createSubmission, getSubmission } from '../lib/api';

/**
 * Shared helpers for the real upload/verification milestone.
 * "Completed" means basic backend file verification only. It does not mean
 * metadata extraction, academic approval, or a successful DSpace submission.
 */
const TERMINAL_VERIFICATION_STATUSES = ['completed', 'failed'];
const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 120000;
const SINGLE_REQUEST_TIMEOUT_MS = 15000;
const UPLOAD_TIMEOUT_MS = 60000;

export function isTerminal(result) {
  const verificationStatus = String(
    result?.verification_status ?? result?.status ?? '',
  ).toLowerCase();
  return TERMINAL_VERIFICATION_STATUSES.includes(verificationStatus);
}

/**
 * Maps known HTTP/network failures to safe, actionable student messages.
 * Unknown failures get a generic message; technical detail stays in the
 * development console and never includes credentials or document contents.
 */
export function describeError(error) {
  const safeMessages = {
    400: 'The server could not accept this upload. Check the selected PDF and form details, then try again.',
    401: 'Your session is no longer valid. Please sign in again.',
    403: 'You do not have permission to perform this action.',
    404: 'The submission could not be found. It may have been removed or the server may have restarted.',
    422: 'One or more submitted values were not accepted. Check the form details and try again.',
    0: 'Could not reach the server. Check your connection and that the backend is running.',
  };

  const safeMessage = safeMessages[error?.status] ||
    'Something went wrong while contacting the server. Please try again.';

  if (import.meta.env.DEV) {
    // Development-only diagnostics. Do not log tokens, passwords, or file contents.
    console.error('[Research Bridge] Request failed:', {
      status: error?.status,
      name: error?.name,
      message: error?.message,
    });
  }

  return safeMessage;
}

/**
 * Owns the upload request and status-polling lifecycle.
 * - Upload POST is sent once; an uncertain timeout does not automatically retry.
 * - Status GET runs every two seconds and never overlaps a previous request.
 * - Polling stops on completion/failure, error/timeout, logout, or unmount.
 * - AbortController cancels only the browser request; it does not claim to
 *   cancel backend work because no cancellation endpoint was supplied.
 */
export default function useSubmissionVerification() {
  const [result, setResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState('');
  const [retryCycle, setRetryCycle] = useState(0);
  const uploadControllerRef = useRef(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      uploadControllerRef.current?.abort();
      uploadControllerRef.current = null;
    };
  }, []);

  // The callback passed to UploadForm as onSubmit. It builds the FormData and
  // calls the real POST /api/v1/submissions endpoint exactly once.
  const upload = useCallback(async (form, file) => {
    if (uploadControllerRef.current) {
      throw new Error('An upload is already in progress.');
    }

    const controller = new AbortController();
    uploadControllerRef.current = controller;
    setUploading(true);
    setError('');

    const timeout = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT_MS);

    try {
      const response = await createSubmission(
        {
          file,
          author_name: form.author_name,
          faculty: form.faculty,
          department: form.department,
          language: form.language,
        },
        { signal: controller.signal },
      );

      if (!response?.submission_id) {
        throw new Error('The server response did not include a submission ID.');
      }

      if (isMountedRef.current) {
        setResult(response);
      }
    } catch (requestError) {
      if (requestError.name === 'AbortError') {
        if (isMountedRef.current) {
          setError(
            'The upload timed out. The server may still have received it. Do not upload the same document again until you have checked its status.',
          );
        }
      } else if (isMountedRef.current) {
        setError(describeError(requestError));
      }
      throw requestError;
    } finally {
      clearTimeout(timeout);
      uploadControllerRef.current = null;
      if (isMountedRef.current) {
        setUploading(false);
      }
    }
  }, []);

  const submissionId = result?.submission_id;
  const terminal = isTerminal(result);

  useEffect(() => {
    if (!submissionId || terminal) return undefined;

    let stopped = false;
    let nextPollTimer = null;
    let requestTimeout = null;
    let controller = null;
    const deadline = Date.now() + POLL_TIMEOUT_MS;

    setPolling(true);
    setError('');

    async function checkStatus() {
      if (stopped) return;

      if (Date.now() >= deadline) {
        setPolling(false);
        setError(
          'Status checking timed out. Verification may still be running. Use “Check status again” to resume; do not upload the document again.',
        );
        return;
      }

      controller = new AbortController();
      requestTimeout = setTimeout(
        () => controller.abort(),
        Math.min(SINGLE_REQUEST_TIMEOUT_MS, deadline - Date.now()),
      );

      try {
        const response = await getSubmission(submissionId, {
          signal: controller.signal,
        });

        if (stopped) return;

        setResult({ ...response, submission_id: submissionId });

        if (isTerminal(response)) {
          setPolling(false);
        } else {
          nextPollTimer = setTimeout(checkStatus, POLL_INTERVAL_MS);
        }
      } catch (requestError) {
        if (stopped) return;
        setPolling(false);
        setError(
          requestError.name === 'AbortError'
            ? 'The status request timed out. Use “Check status again” to resume.'
            : describeError(requestError),
        );
      } finally {
        clearTimeout(requestTimeout);
      }
    }

    // First check occurs after the agreed two-second interval.
    nextPollTimer = setTimeout(checkStatus, POLL_INTERVAL_MS);

    return () => {
      stopped = true;
      clearTimeout(nextPollTimer);
      clearTimeout(requestTimeout);
      controller?.abort();
    };
  }, [submissionId, terminal, retryCycle]);

  /**
   * Resumes status checking for the already accepted submission.
   * It does not create another submission or upload the file again.
   */
  const retry = useCallback(() => {
    setRetryCycle((cycle) => cycle + 1);
  }, []);

  return {
    result,
    uploading,
    polling,
    error,
    retry,
    upload,
  };
}
