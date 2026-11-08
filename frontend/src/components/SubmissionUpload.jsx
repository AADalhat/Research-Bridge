import React from 'react';
import { Card, ErrorBox, Notice } from './UI';
import UploadForm from './UploadForm';
import useSubmissionVerification from '../hooks/useSubmissionVerification';

/**
 * Student upload workspace.
 *
 * This component owns the real upload and verification lifecycle:
 * - UploadForm receives the hook's `upload` function through `onSubmit`.
 * - The hook owns the POST request and status polling.
 * - Unmounting or logout aborts browser requests and polling, but does not
 *   claim to cancel work already accepted by the backend.
 *
 * The backend's technical verification details are not shown to the student.
 * Only the backend-provided message is displayed.
 */
export default function SubmissionUpload() {
  const {
    result,
    uploading,
    polling,
    error,
    retry,
    upload,
  } = useSubmissionVerification();

  const hasResult = Boolean(result);
  const verificationStatus = String(
    result?.verification_status ?? '',
  ).toLowerCase();

  return (
    <>
      <h1>Project Submission</h1>
      <p>Upload your research document to begin processing.</p>

      <ErrorBox>{error}</ErrorBox>

      {hasResult && (
        <Card title="Submission Received">
          <Notice>
            {result.message || 'Your document has been received.'}
          </Notice>

          {polling && (
            <p role="status">Checking submission status…</p>
          )}

          {!polling &&
            verificationStatus !== 'completed' &&
            verificationStatus !== 'failed' && (
              <button onClick={retry}>Check status again</button>
            )}

          <p className="help">
            Your submission is being checked. You will be able to continue when
            the check is complete.
          </p>
        </Card>
      )}

      {/*
        The exact prop name is `onSubmit`.
        The value is the hook's `upload` function reference, not `upload()`.
      */}
      <UploadForm
        onSubmit={upload}
        busy={uploading}
        locked={hasResult}
      />
    </>
  );
}
