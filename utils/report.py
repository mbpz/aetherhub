"""报告生成器"""
from typing import Dict, Any
import json
import os


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, artifact: Dict[str, Any],
                 verification_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成验证报告

        Args:
            artifact: 技能产物
            verification_result: 验证结果

        Returns:
            报告信息
        """
        report_id = f"report_{int(__import__('time').time())}"
        report_path = os.path.join(self.output_dir, f"{report_id}.json")

        report = {
            "report_id": report_id,
            "artifact_id": artifact["artifact_id"],
            "intent": artifact["intent"],
            "verification": verification_result,
            "artifact": {
                "atomic_skills": artifact["atomic_skills"],
                "constraints": artifact["constraints"]
            },
            "metadata": {
                "generated_at": __import__('datetime').datetime.now().isoformat()
            }
        }

        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return {
            "report_id": report_id,
            "report_path": report_path,
            "report_url": f"file://{os.path.abspath(report_path)}"
        }
