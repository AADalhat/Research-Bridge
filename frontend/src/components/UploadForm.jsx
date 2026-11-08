import React, { useEffect, useState } from 'react';
import { ACADEMIC } from '../lib/workflow.mjs';
import { Card, ErrorBox, Field, Notice } from './UI';

/**
 * Student upload form.
 *
 * The form collects the student-facing details, including publication year and
 * project type. Only the fields accepted by POST /api/v1/submissions are sent:
 * file, author_name, faculty, department and language.
 *
 * Contract:
 * - `onSubmit` is required and must be a function.
 * - It receives `(form, file)`.
 * - The parent owns the API request; this component does not call fetch.
 */
export default function UploadForm({
  onSubmit,
  busy = false,
  locked = false,
}) {
  const [form, setForm] = useState({
    author_name: '',
    year: '',
    faculty: '',
    department: '',
    language: 'English',
    projectType: 'Thesis',
  });
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');

  // Create a local object URL for preview and revoke it when the selection
  // changes or this component unmounts.
  useEffect(() => {
    if (!file) {
      setPreviewUrl('');
      return undefined;
    }

    const isPdf =
      file.type === 'application/pdf' ||
      file.name.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      setPreviewUrl('');
      return undefined;
    }

    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  function chooseFile(selectedFile) {
    setError('');

    if (!selectedFile) return;

    const isPdf =
      selectedFile.type === 'application/pdf' ||
      selectedFile.name.toLowerCase().endsWith('.pdf');

    if (!isPdf) {
      setError('Choose a PDF document.');
      return;
    }

    if (selectedFile.size === 0) {
      setError('The selected document is empty. Choose a valid PDF.');
      return;
    }

    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('Choose a PDF smaller than 50 MB.');
      return;
    }

    setFile(selectedFile);
  }

  function updateField(fieldName, value) {
    setForm((currentForm) => ({
      ...currentForm,
      [fieldName]: value,
      // Changing faculty resets department so the pair remains consistent.
      ...(fieldName === 'faculty' ? { department: '' } : {}),
    }));
  }

  async function handleSubmit(formEvent) {
    formEvent.preventDefault();
    setError('');

    // Validate the callback contract before attempting the network request.
    if (typeof onSubmit !== 'function') {
      if (import.meta.env.DEV) {
        console.error(
          '[Research Bridge] UploadForm requires an onSubmit function prop.',
        );
      }
      setError(
        'The upload action is unavailable. Please refresh the page and try again.',
      );
      return;
    }

    if (!file) {
      setError('Select a PDF document to upload.');
      return;
    }

    if (!form.author_name.trim()) {
      setError('Enter the author name.');
      return;
    }
    if (!/^\d{4}$/.test(form.year.trim())) {
      setError('Enter a four-digit publication year.');
      return;
    }
    if (!form.faculty || !form.department || !form.language) {
      setError('Complete all fields before uploading.');
      return;
    }

    try {
      // Pass the function reference supplied by the parent; do not invoke it here.
      await onSubmit(form, file);
    } catch (submitError) {
      // The parent hook supplies the safe user-facing message through its own
      // error state. Avoid exposing raw JavaScript exception text to students.
      if (import.meta.env.DEV) {
        console.error(
          '[Research Bridge] Upload submission failed:',
          {
            name: submitError?.name,
            status: submitError?.status,
          },
        );
      }
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <fieldset
        disabled={busy || locked}
        style={{
          border: 0,
          padding: 0,
          margin: 0,
          minWidth: 0,
        }}
      >
        <Card title="Author Information">
          <div className="grid two">
            <Field
              label="Author’s name"
              hint="Enter your surname first, then your first name and other names."
            >
              <input
                required
                value={form.author_name}
                onChange={(event) => updateField('author_name', event.target.value)}
              />
            </Field>

            <Field label="Publication year">
              <input
                required
                inputMode="numeric"
                placeholder="For example: 2026"
                value={form.year}
                onChange={(event) => updateField('year', event.target.value)}
              />
            </Field>

            <Field label="Faculty">
              <select
                required
                value={form.faculty}
                onChange={(event) => updateField('faculty', event.target.value)}
              >
                <option value="">Select faculty</option>
                {Object.keys(ACADEMIC).map((facultyName) => (
                  <option key={facultyName}>{facultyName}</option>
                ))}
              </select>
            </Field>

            <Field label="Department">
              <select
                required
                value={form.department}
                onChange={(event) => updateField('department', event.target.value)}
              >
                <option value="">Select department</option>
                {(ACADEMIC[form.faculty] || []).map((departmentName) => (
                  <option key={departmentName}>{departmentName}</option>
                ))}
              </select>
            </Field>

            <Field label="Language">
              <select
                required
                value={form.language}
                onChange={(event) => updateField('language', event.target.value)}
              >
                {['English', 'Hausa', 'Arabic', 'French', 'Other'].map(
                  (language) => (
                    <option key={language}>{language}</option>
                  ),
                )}
              </select>
            </Field>

            <Field label="Project type">
              <select
                required
                value={form.projectType}
                onChange={(event) => updateField('projectType', event.target.value)}
              >
                {['Thesis', 'Dissertation', 'Other'].map((projectType) => (
                  <option key={projectType}>{projectType}</option>
                ))}
              </select>
            </Field>
          </div>

          <small>
            Faculty and department options are demonstration fixtures, not an
            official university directory.
          </small>
        </Card>

        <Card title="Research Document">
          <div
            className="upload"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              chooseFile(event.dataTransfer.files[0]);
            }}
          >
            <h2>
              {file ? file.name : 'Upload your research PDF'}
            </h2>
            <p>Drag a PDF here or choose a document below.</p>

            <label className="fileinput">
              Select PDF · Maximum 50 MB
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={(event) => chooseFile(event.target.files[0])}
              />
            </label>

            {file && (
              <small>
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </small>
            )}
          </div>

          {previewUrl && (
            <div style={{ marginTop: 20 }}>
              <label>Local PDF preview</label>
              <iframe
                className="preview"
                title="Selected PDF preview"
                src={previewUrl}
              />
            </div>
          )}

          <ErrorBox>{error}</ErrorBox>

          <div className="actions">
            <span className="muted">
              PDF only · Client-side checks are preliminary
            </span>
            <button className="primary" disabled={busy || locked}>
              {busy ? 'Uploading…' : locked ? 'Upload received' : 'Upload document'}
            </button>
          </div>
        </Card>
      </fieldset>
    </form>
  );
}
