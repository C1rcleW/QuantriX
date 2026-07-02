/** Drag-and-drop file import zone. */

import { type DragEvent, useCallback, useRef, useState } from "react";

interface Props {
  onImport: (file: File) => void;
}

const ACCEPTED = ".sav,.zsav,.csv,.tsv,.txt";

export function ImportDropzone({ onImport }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) onImport(file);
    },
    [onImport]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onImport(file);
    },
    [onImport]
  );

  return (
    <div
      style={dragging ? styles.dropzoneActive : styles.dropzone}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <div style={styles.icon}>📊</div>
      <p style={styles.text}>
        Drop your data file here, or click to browse
      </p>
      <p style={styles.hint}>
        Supports SPSS (.sav), CSV, TSV, and text files
      </p>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        onChange={handleChange}
        style={{ display: "none" }}
      />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  dropzone: {
    width: 400,
    padding: "48px 24px",
    border: "2px dashed #ccc",
    borderRadius: 12,
    textAlign: "center",
    cursor: "pointer",
    background: "#fafbfc",
    transition: "all 0.2s",
  },
  dropzoneActive: {
    width: 400,
    padding: "48px 24px",
    border: "2px dashed #1a73e8",
    borderRadius: 12,
    textAlign: "center",
    cursor: "pointer",
    background: "#e8f0fe",
    transition: "all 0.2s",
  },
  icon: { fontSize: 40, marginBottom: 12 },
  text: {
    fontSize: 16,
    fontWeight: 600,
    color: "#555",
    margin: "0 0 8px",
  },
  hint: {
    fontSize: 12,
    color: "#999",
    margin: 0,
  },
};
