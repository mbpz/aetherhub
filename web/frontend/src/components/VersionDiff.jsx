import { useState, useEffect } from "react";

export default function VersionDiff({ skillId, v1, v2 }) {
  const [diff, setDiff] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/skills/${skillId}/versions/diff?v1=${v1}&v2=${v2}`)
      .then(r => r.json())
      .then(data => {
        setDiff(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load diff:', err);
        setLoading(false);
      });
  }, [skillId, v1, v2]);

  if (loading) return <div>Loading diff...</div>;
  if (!diff) return <div>Failed to load diff</div>;

  return (
    <div className="font-mono text-sm">
      <div className="mb-2 text-gray-600">
        {diff.v1} → {diff.v2}: +{diff.stats.additions} -{diff.stats.deletions}
      </div>
      <pre className="bg-gray-50 p-4 rounded overflow-x-auto">
        {diff.diff || "(no changes)"}
      </pre>
    </div>
  );
}