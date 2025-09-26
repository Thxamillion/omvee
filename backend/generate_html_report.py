#!/usr/bin/env python3
"""
HTML Report Generator for Model Comparison Results

Generates a comprehensive visual HTML report from model comparison test results.
Includes charts, metrics tables, and detailed analysis.

Usage: python generate_html_report.py [results_file.json]
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

def load_comparison_results(results_file: Optional[str] = None) -> Dict[str, Any]:
    """Load the most recent comparison results file"""
    results_dir = Path("model_comparison_results")

    if results_file:
        file_path = Path(results_file)
        if not file_path.exists():
            file_path = results_dir / results_file
    else:
        # Find the most recent comparison results file
        comparison_files = list(results_dir.glob("comparison_results_*.json"))
        if not comparison_files:
            raise FileNotFoundError("No comparison results files found")
        file_path = max(comparison_files, key=lambda f: f.stat().st_mtime)

    print(f"📊 Loading results from: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_html_report(results: Dict[str, Any]) -> str:
    """Generate comprehensive HTML report"""

    models_tested = results.get("models_tested", [])
    test_data_info = results.get("test_data_info", {})
    model_results = results.get("results", {})

    # Calculate summary statistics
    summary_stats = []
    for model in models_tested:
        model_data = model_results.get(model, [])
        successful_runs = [r for r in model_data if r.get("success", False)]

        if successful_runs:
            # Average metrics across successful runs
            avg_coverage = sum(r["metrics"]["coverage_percentage"] for r in successful_runs) / len(successful_runs)
            avg_scenes = sum(r["metrics"]["scene_count"] for r in successful_runs) / len(successful_runs)
            avg_speed = sum(r["processing_time"] for r in successful_runs) / len(successful_runs)
            avg_cost = sum(r["metrics"]["estimated_cost"]["total_cost"] for r in successful_runs) / len(successful_runs)

            # Calculate consistency (variance across runs)
            if len(successful_runs) > 1:
                coverages = [r["metrics"]["coverage_percentage"] for r in successful_runs]
                consistency = abs(coverages[0] - coverages[1])
                consistency_rating = "High" if consistency < 2 else "Medium" if consistency < 5 else "Low"
            else:
                consistency = 0
                consistency_rating = "Single Run"

            summary_stats.append({
                "model": model,
                "success_rate": len(successful_runs) / len(model_data) * 100,
                "avg_coverage": avg_coverage,
                "avg_scenes": avg_scenes,
                "avg_speed": avg_speed,
                "avg_cost": avg_cost,
                "consistency": consistency,
                "consistency_rating": consistency_rating,
                "runs": len(model_data),
                "successful_runs": len(successful_runs)
            })
        else:
            summary_stats.append({
                "model": model,
                "success_rate": 0,
                "avg_coverage": 0,
                "avg_scenes": 0,
                "avg_speed": 0,
                "avg_cost": 0,
                "consistency": 0,
                "consistency_rating": "Failed",
                "runs": len(model_data),
                "successful_runs": 0
            })

    # Sort by coverage percentage
    summary_stats.sort(key=lambda x: x["avg_coverage"], reverse=True)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OMVEE Model Comparison Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
        }}
        .header-info {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header-info h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h4 {{
            margin: 0 0 10px 0;
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .stat-card .value {{
            font-size: 1.8em;
            font-weight: bold;
            margin: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #e8f4f8;
        }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 8px;
        }}
        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }}
        .model-details {{
            margin-top: 40px;
        }}
        .model-card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .model-card-header {{
            background: #34495e;
            color: white;
            padding: 15px 20px;
            font-weight: bold;
            font-size: 1.1em;
        }}
        .model-card-body {{
            padding: 20px;
        }}
        .success {{
            color: #27ae60;
            font-weight: bold;
        }}
        .failure {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .consistency-high {{ color: #27ae60; }}
        .consistency-medium {{ color: #f39c12; }}
        .consistency-low {{ color: #e74c3c; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 OMVEE Model Comparison Report</h1>

        <div class="header-info">
            <h3>Test Configuration</h3>
            <p><strong>Song:</strong> "{test_data_info.get('title', 'Unknown')}" by {test_data_info.get('artist', 'Unknown')}</p>
            <p><strong>Duration:</strong> {test_data_info.get('duration', 0):.1f} seconds ({test_data_info.get('segment_count', 0)} segments)</p>
            <p><strong>Generated:</strong> {datetime.fromisoformat(results.get('timestamp', '')).strftime('%Y-%m-%d %H:%M:%S') if results.get('timestamp') else 'Unknown'}</p>
            <p><strong>Models Tested:</strong> {len(models_tested)}</p>
        </div>

        <div class="stat-grid">
            <div class="stat-card">
                <h4>Total Models Tested</h4>
                <p class="value">{len(models_tested)}</p>
            </div>
            <div class="stat-card">
                <h4>Test Song Duration</h4>
                <p class="value">{test_data_info.get('duration', 0):.1f}s</p>
            </div>
            <div class="stat-card">
                <h4>Total Segments</h4>
                <p class="value">{test_data_info.get('segment_count', 0)}</p>
            </div>
            <div class="stat-card">
                <h4>Best Coverage</h4>
                <p class="value">{max([s['avg_coverage'] for s in summary_stats if s['avg_coverage'] > 0], default=0):.1f}%</p>
            </div>
        </div>

        <h2>📊 Model Performance Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Success Rate</th>
                    <th>Coverage %</th>
                    <th>Scenes</th>
                    <th>Speed (s)</th>
                    <th>Cost ($)</th>
                    <th>Consistency</th>
                </tr>
            </thead>
            <tbody>
                {"".join(f'''
                <tr>
                    <td><strong>{stat['model']}</strong></td>
                    <td class="{'success' if stat['success_rate'] > 0 else 'failure'}">{stat['success_rate']:.0f}%</td>
                    <td>{stat['avg_coverage']:.1f}%</td>
                    <td>{stat['avg_scenes']:.0f}</td>
                    <td>{stat['avg_speed']:.1f}</td>
                    <td>${stat['avg_cost']:.4f}</td>
                    <td class="consistency-{stat['consistency_rating'].lower()}">{stat['consistency_rating']}</td>
                </tr>
                ''' for stat in summary_stats)}
            </tbody>
        </table>

        <div class="chart-container">
            <h3>📈 Coverage Comparison</h3>
            <div class="chart-wrapper">
                <canvas id="coverageChart"></canvas>
            </div>
        </div>

        <div class="chart-container">
            <h3>⚡ Speed vs Cost Analysis</h3>
            <div class="chart-wrapper">
                <canvas id="speedCostChart"></canvas>
            </div>
        </div>

        <div class="model-details">
            <h2>🔍 Detailed Model Results</h2>
            {"".join(generate_model_detail_card(model, model_results.get(model, []), summary_stats) for model in models_tested)}
        </div>

        <div class="footer">
            <p>Generated by OMVEE Model Comparison Tool • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <script>
        // Coverage Chart
        const coverageCtx = document.getElementById('coverageChart').getContext('2d');
        new Chart(coverageCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([stat['model'] for stat in summary_stats])},
                datasets: [{{
                    label: 'Coverage Percentage',
                    data: {json.dumps([stat['avg_coverage'] for stat in summary_stats])},
                    backgroundColor: [
                        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'
                    ],
                    borderColor: [
                        '#2980b9', '#c0392b', '#27ae60', '#e67e22', '#8e44ad'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Coverage Percentage (%)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.parsed.y.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Speed vs Cost Chart
        const speedCostCtx = document.getElementById('speedCostChart').getContext('2d');
        new Chart(speedCostCtx, {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Models',
                    data: {json.dumps([{"x": stat['avg_speed'], "y": stat['avg_cost'], "model": stat['model']} for stat in summary_stats if stat['avg_speed'] > 0])},
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    pointRadius: 8,
                    pointHoverRadius: 10
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: 'Processing Time (seconds)'
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: 'Estimated Cost ($)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const point = context.raw;
                                return point.model + ': ' + context.parsed.x.toFixed(1) + 's, $' + context.parsed.y.toFixed(4);
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    return html

def generate_model_detail_card(model: str, runs: List[Dict], summary_stats: List[Dict]) -> str:
    """Generate detailed card for a specific model"""
    model_stat = next((s for s in summary_stats if s['model'] == model), None)
    if not model_stat:
        return ""

    successful_runs = [r for r in runs if r.get("success", False)]
    failed_runs = [r for r in runs if not r.get("success", False)]

    status_class = "success" if successful_runs else "failure"
    status_text = f"{len(successful_runs)}/{len(runs)} successful" if runs else "No runs"

    details_html = ""
    if successful_runs:
        # Show metrics from first successful run
        first_run = successful_runs[0]
        metrics = first_run.get("metrics", {})

        details_html = f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 15px 0;">
            <div><strong>Coverage:</strong> {metrics.get('coverage_percentage', 0):.1f}%</div>
            <div><strong>Scenes:</strong> {metrics.get('scene_count', 0)}</div>
            <div><strong>Avg Scene Length:</strong> {metrics.get('avg_scene_length', 0):.1f}s</div>
            <div><strong>Processing Time:</strong> {first_run.get('processing_time', 0):.1f}s</div>
            <div><strong>Estimated Cost:</strong> ${metrics.get('estimated_cost', {}).get('total_cost', 0):.4f}</div>
            <div><strong>Gaps:</strong> {metrics.get('gaps', {}).get('count', 0)} ({metrics.get('gaps', {}).get('percentage', 0):.1f}%)</div>
        </div>

        <h4>Gap Analysis:</h4>
        <p>{metrics.get('gaps', {}).get('count', 0)} gaps totaling {metrics.get('gaps', {}).get('total_duration', 0):.1f}s ({metrics.get('gaps', {}).get('percentage', 0):.1f}% of song)</p>

        <h4>Lyric Coverage:</h4>
        <p>{metrics.get('lyric_coverage', {}).get('covered_word_count', 0)}/{metrics.get('lyric_coverage', {}).get('original_word_count', 0)} words covered ({metrics.get('lyric_coverage', {}).get('coverage_percentage', 0):.1f}%)</p>
        """

    if failed_runs:
        error_details = []
        for run in failed_runs:
            error_details.append(f"Run {run.get('run', '?')}: {run.get('error', 'Unknown error')}")

        details_html += f"""
        <h4>Failures:</h4>
        <ul>
            {"".join(f"<li>{error}</li>" for error in error_details)}
        </ul>
        """

    return f"""
    <div class="model-card">
        <div class="model-card-header">
            {model} <span class="{status_class}" style="float: right;">({status_text})</span>
        </div>
        <div class="model-card-body">
            {details_html}
        </div>
    </div>
    """

def main():
    """Main function"""
    results_file = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        results = load_comparison_results(results_file)
        html_content = generate_html_report(results)

        # Save HTML report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"model_comparison_report_{timestamp}.html"

        with open(output_file, 'w') as f:
            f.write(html_content)

        print(f"✅ HTML report generated: {output_file}")
        print(f"📊 Open in browser: file://{os.path.abspath(output_file)}")

        return output_file

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return None

if __name__ == "__main__":
    main()