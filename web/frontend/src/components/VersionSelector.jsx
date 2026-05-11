import { useState, useEffect } from "react";

export default function VersionSelector({ skillId, currentVersion, onSelect }) {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/skills/${skillId}/versions`)
      .then(r => r.json())
      .then(data => {
        setVersions(data.versions || []);
        setLoading(false);
      });
  }, [skillId]);

  if (loading) return <span>Loading versions...</span>;

  return (
    <select
      value={currentVersion}
      onChange={e => onSelect(e.target.value)}
      className="border rounded px-2 py-1"
    >
      {versions.map(v => (
        <option key={v.version} value={v.version}>
          {v.version} - {new Date(v.created_at).toLocaleDateString()}
        </option>
      ))}
    </select>
  );
}