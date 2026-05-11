import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import VersionSelector from "../components/VersionSelector";
import VersionDiff from "../components/VersionDiff";

export default function SkillVersionsPage() {
  const { skillId } = useParams();
  const [versions, setVersions] = useState([]);
  const [selectedV1, setSelectedV1] = useState(null);
  const [selectedV2, setSelectedV2] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/skills/${skillId}/versions`)
      .then(r => r.json())
      .then(data => {
        setVersions(data.versions || []);
        if (data.versions?.length >= 2) {
          setSelectedV1(data.versions[1].version);
          setSelectedV2(data.versions[0].version);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load versions:', err);
        setLoading(false);
      });
  }, [skillId]);

  const handleRestore = async (version) => {
    if (!confirm(`Restore version ${version}?`)) return;
    setActionLoading(true);
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`/api/v1/skills/${skillId}/versions/${version}/restore`, {
        method: "POST",
        headers: token ? { "Authorization": `Bearer ${token}` } : {},
      });
      if (res.ok) {
        alert("Version restored!");
        window.location.reload();
      } else {
        const err = await res.json().catch(() => ({}));
        alert(`Failed to restore: ${err.detail || res.status}`);
      }
    } catch (err) {
      alert(`Failed to restore: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async (version) => {
    if (!confirm(`Delete version ${version}?`)) return;
    setActionLoading(true);
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`/api/v1/skills/${skillId}/versions/${version}`, {
        method: "DELETE",
        headers: token ? { "Authorization": `Bearer ${token}` } : {},
      });
      if (res.ok) {
        alert("Version deleted!");
        window.location.reload();
      } else {
        const err = await res.json().catch(() => ({}));
        alert(`Failed to delete: ${err.detail || res.status}`);
      }
    } catch (err) {
      alert(`Failed to delete: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">版本历史</h1>

      <div className="mb-6 flex gap-4 items-center">
        <span>对比:</span>
        <VersionSelector skillId={skillId} currentVersion={selectedV1} onSelect={setSelectedV1} />
        <span>→</span>
        <VersionSelector skillId={skillId} currentVersion={selectedV2} onSelect={setSelectedV2} />
      </div>

      {selectedV1 && selectedV2 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">差异</h2>
          <VersionDiff skillId={skillId} v1={selectedV1} v2={selectedV2} />
        </div>
      )}

      <h2 className="text-lg font-semibold mb-4">所有版本</h2>
      <div className="space-y-4">
        {versions.map(v => (
          <div key={v.id} className="border rounded p-4 flex justify-between items-center">
            <div>
              <div className="font-medium">{v.version}</div>
              <div className="text-sm text-gray-500">
                {new Date(v.created_at).toLocaleString()}
              </div>
              {v.description && <div className="text-sm mt-1">{v.description}</div>}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleRestore(v.version)}
                disabled={actionLoading}
                className="px-3 py-1 bg-blue-500 text-white rounded text-sm disabled:opacity-50"
              >
                恢复
              </button>
              <button
                onClick={() => handleDelete(v.version)}
                disabled={actionLoading}
                className="px-3 py-1 bg-red-500 text-white rounded text-sm disabled:opacity-50"
              >
                删除
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}