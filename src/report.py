"""
report.py - הרכבת דו"ח HTML סופי
צוות 3, זוג B

מקבל את כל החלקים ומחזיר HTML string מלא ומעוצב.

ראו docs/api_contract.md לפורמט הקלט.
"""

from datetime import datetime


def _build_images_table(images_data):
    """בונה טבלת תמונות מפורטת."""
    if not images_data:
        return '<p class="empty-state">אין נתונים להצגה.</p>'

    rows = ""
    for img in images_data:
        if img.get("has_gps") and img.get("latitude") is not None and img.get("longitude") is not None:
            gps_cell = f'<span class="badge badge-gps">✓ {img["latitude"]:.4f}, {img["longitude"]:.4f}</span>'
        else:
            gps_cell = '<span class="badge badge-no">✗ אין</span>'

        camera = img.get("camera_model") or img.get("camera_make") or "—"
        dt = img.get("datetime") or "—"

        rows += f"""
        <tr>
            <td class="td-filename">{img.get("filename", "—")}</td>
            <td>{dt}</td>
            <td>{camera}</td>
            <td>{gps_cell}</td>
        </tr>
        """

    return f"""
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>שם קובץ</th>
                    <th>תאריך ושעה</th>
                    <th>מכשיר</th>
                    <th>GPS</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """


def _build_cameras_section(analysis):
    """בונה סקשן מכשירים."""
    cameras = analysis.get("unique_cameras", [])
    if not cameras:
        return '<p class="empty-state">לא זוהו מכשירים.</p>'

    items = "".join(f'<div class="camera-chip">📷 {cam}</div>' for cam in cameras)
    return f'<div class="camera-grid">{items}</div>'


def _build_insights_section(analysis):
    """בונה סקשן תובנות עם 2 פריטים גלויים וכפתור View more."""
    insights = analysis.get("insights", [])
    if not insights:
        return '<p class="empty-state">אין תובנות זמינות.</p>'

    items = ""
    for i, insight in enumerate(insights):
        hidden_class = " hidden-insight" if i >= 2 else ""
        items += f'<li class="insight-item{hidden_class}">{insight}</li>'

    button_html = ""
    if len(insights) > 2:
        button_html = """
        <button type="button" class="insights-toggle-btn" onclick="toggleInsights(this)">
            View more
        </button>
        """

    return f"""
    <div class="insights-wrapper">
        <ul class="insights-list">
            {items}
        </ul>
        {button_html}
    </div>
    """


def _build_timeline_section(timeline_html):
    """בונה את סקשן ציר הזמן עם fallback אם אין תוכן."""
    if not timeline_html or not str(timeline_html).strip():
        return '<p class="empty-state">ציר הזמן אינו זמין כרגע.</p>'
    return timeline_html


def create_report(images_data, map_html, timeline_html, analysis):
    """
    מרכיב את כל חלקי הדו"ח ל-HTML מלא.

    Args:
        images_data: רשימת מילונים מ-extract_all
        map_html: HTML string מ-create_map
        timeline_html: HTML string מ-create_timeline
        analysis: מילון מ-analyze

    Returns:
        HTML string מלא
    """
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    total = analysis.get("total_images", 0)
    gps_count = analysis.get("images_with_gps", 0)
    dt_count = analysis.get("images_with_datetime", 0)
    cameras = analysis.get("unique_cameras", [])
    date_range = analysis.get("date_range", {})

    date_range_str = ""
    if date_range.get("start") and date_range.get("end"):
        date_range_str = f"""
        <div class="date-range">
            <span class="date-pill">📅 {date_range["start"]}</span>
            <span class="date-separator">—</span>
            <span class="date-pill">{date_range["end"]}</span>
        </div>
        """

    images_table = _build_images_table(images_data)
    cameras_section = _build_cameras_section(analysis)
    insights_section = _build_insights_section(analysis)
    timeline_section = _build_timeline_section(timeline_html)

    safe_map_html = (
        (map_html or "")
        .replace("&", "&amp;")
        .replace("'", "&apos;")
    )

    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Intel — דו"ח מודיעין</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        .coord-link {{
            color: var(--accent);
            font-weight: 800;
            text-decoration: none;
            border-bottom: 1px dashed var(--accent);
        }}

        .coord-link:hover {{
            color: var(--blue);
            border-bottom-color: var(--blue);
        }}
        :root {{
            --navy: #0d1b2a;
            --blue: #1b4f72;
            --accent: #2e86ab;
            --accent-soft: #64b5d6;
            --light: #e8f4fd;
            --bg: #f4f7fb;
            --white: #ffffff;
            --text: #1a1a2e;
            --muted: #6b7a8d;
            --border: #d8e1eb;
            --ok-bg: #dff5e8;
            --ok-text: #17653b;
            --no-bg: #fde8e8;
            --no-text: #a12b2b;
            --radius: 16px;
            --shadow: 0 8px 24px rgba(13, 27, 42, 0.08);
        }}


        body {{
            font-family: 'Heebo', sans-serif;
            background: linear-gradient(180deg, #eef3f8 0%, var(--bg) 100%);
            color: var(--text);
            line-height: 1.6;
        }}

        .report-header {{
            background: linear-gradient(135deg, var(--navy) 0%, var(--blue) 60%, var(--accent) 100%);
            color: white;
            padding: 56px 32px 40px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 10px 26px rgba(13, 27, 42, 0.18);
        }}

        .report-header::before {{
            content: "";
            position: absolute;
            top: -80px;
            right: -80px;
            width: 280px;
            height: 280px;
            background: rgba(255,255,255,0.08);
            border-radius: 50%;
        }}

        .report-header::after {{
            content: "";
            position: absolute;
            bottom: -60px;
            left: -60px;
            width: 220px;
            height: 220px;
            background: rgba(100, 210, 255, 0.10);
            border-radius: 50%;
        }}

        .header-inner {{
            max-width: 1100px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}

        .report-header h1 {{
            font-size: 2.7rem;
            font-weight: 900;
            letter-spacing: -0.04em;
        }}

        .report-header h1 span {{
            color: #8ddcff;
        }}

        .report-header .subtitle {{
            margin-top: 10px;
            font-size: 1.05rem;
            opacity: 0.9;
            font-weight: 300;
        }}

        .report-header .generated {{
            margin-top: 14px;
            font-size: 0.9rem;
            opacity: 0.8;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 28px 18px 42px;
        }}

        .section {{
            background: var(--white);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 24px;
            margin-bottom: 24px;
            border: 1px solid rgba(216, 225, 235, 0.65);
        }}

        .section-title {{
            font-size: 1.08rem;
            font-weight: 800;
            color: var(--blue);
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--light);
            letter-spacing: 0.01em;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
        }}

        .stat-card {{
            background: linear-gradient(180deg, #f4faff 0%, var(--light) 100%);
            border-radius: 14px;
            padding: 22px 16px;
            text-align: center;
            border-top: 4px solid var(--accent);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
        }}

        .stat-number {{
            font-size: 2.5rem;
            font-weight: 900;
            color: var(--blue);
            line-height: 1;
        }}

        .stat-label {{
            margin-top: 8px;
            font-size: 0.9rem;
            color: var(--muted);
            font-weight: 700;
        }}

        .date-range {{
            margin-top: 18px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .date-pill {{
            background: #f1f8ff;
            border: 1px solid var(--border);
            color: var(--blue);
            padding: 7px 12px;
            border-radius: 999px;
            font-size: 0.9rem;
            font-weight: 600;
        }}

        .date-separator {{
            color: var(--muted);
            font-weight: 700;
        }}

        .insights-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .insight-item {{
            background: linear-gradient(180deg, #f6fbff 0%, var(--light) 100%);
            border-right: 5px solid var(--accent);
            padding: 14px 16px;
            border-radius: 10px 0 0 10px;
            font-size: 0.96rem;
        }}

        .camera-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .camera-chip {{
            background: linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%);
            color: white;
            padding: 9px 16px;
            border-radius: 999px;
            font-size: 0.9rem;
            font-weight: 700;
            box-shadow: 0 4px 12px rgba(27, 79, 114, 0.18);
        }}

        .map-wrapper {{
            border-radius: 14px;
            overflow: hidden;
            background: #f8fbff;
            border: 1px solid var(--border);
            padding: 12px;
        }}

        .map-frame {{
            width: 100%;
            height: 560px;
            border: none;
            border-radius: 12px;
            display: block;
            background: white;
        }}

        .timeline-wrapper {{
            background: #fbfdff;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px;
        }}

        .table-wrapper {{
            overflow-x: auto;
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            background: white;
        }}

        th {{
            background: linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%);
            color: white;
            padding: 13px 14px;
            text-align: right;
            font-weight: 700;
            letter-spacing: 0.02em;
            white-space: nowrap;
        }}
        td {{
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:nth-child(even) td {{
            background: #fafcff;
        }}

        .td-filename {{
            font-family: monospace;
            color: var(--blue);
            font-size: 0.84rem;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 800;
            white-space: nowrap;
        }}

        .badge-gps {{
            background: var(--ok-bg);
            color: var(--ok-text);
        }}

        .badge-no {{
            background: var(--no-bg);
            color: var(--no-text);
        }}

        .empty-state {{
            color: var(--muted);
            background: #f8fbfe;
            border: 1px dashed var(--border);
            border-radius: 12px;
            padding: 18px;
            text-align: center;
        }}

        .report-footer {{
            text-align: center;
            color: var(--muted);
            font-size: 0.82rem;
            padding: 10px 20px 30px;
        }}

        @media (max-width: 768px) {{
            .report-header {{
                padding: 42px 22px 30px;
            }}

            .report-header h1 {{
                font-size: 2.1rem;
            }}

            .container {{
                padding: 20px 12px 32px;
            }}

            .section {{
                padding: 18px;
            }}

            .map-frame {{
                height: 420px;
            }}

            .stats-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}

        @media (max-width: 520px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}

            .map-frame {{
                height: 340px;
            }}
        }}
        .insights-wrapper {{
    display: flex;
    flex-direction: column;
    gap: 14px;
}}

        .hidden-insight {{
            display: none;
        }}

        .insights-toggle-btn {{
            align-self: flex-start;
            background: linear-gradient(135deg, var(--accent) 0%, var(--blue) 100%);
            color: white;
            border: none;
            border-radius: 999px;
            padding: 9px 16px;
            font-size: 0.88rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(27, 79, 114, 0.18);
        }}

        .insights-toggle-btn:hover {{
            opacity: 0.92;
        }}
        .tab-nav {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 22px;
    justify-content: center;
}}

.tab-btn {{
    border: 1px solid var(--border);
    background: white;
    color: var(--blue);
    border-radius: 999px;
    padding: 10px 16px;
    font-size: 0.92rem;
    font-weight: 800;
    cursor: pointer;
    transition: 0.22s ease;
    box-shadow: 0 2px 8px rgba(13, 27, 42, 0.06);
}}

.tab-btn:hover {{
    background: var(--light);
    border-color: var(--accent);
}}

.tab-btn.active {{
    background: linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%);
    color: white;
    border-color: transparent;
    box-shadow: 0 6px 16px rgba(27, 79, 114, 0.18);
}}

.report-tab-section {{
    display: none;
}}

.report-tab-section.active {{
    display: block;
}}
</style>
</head>
<body>

<div class="report-header">
    <div class="header-inner">
        <h1>Image <span>Intel</span></h1>
        <p class="subtitle">דו"ח מודיעין חזותי — ניתוח נתוני EXIF מתמונות</p>
        <div class="generated">נוצר ב־{now}</div>
    </div>
</div>

<div class="container">
    <div class="tab-nav">
        <button type="button" class="tab-btn active" data-tab="overview-section" onclick="showTab('overview-section', this)">סיכום</button>
        <button type="button" class="tab-btn" data-tab="insights-section" onclick="showTab('insights-section', this)">תובנות</button>
        <button type="button" class="tab-btn" data-tab="map-section" onclick="showTab('map-section', this)">מפה</button>
        <button type="button" class="tab-btn" data-tab="timeline-section" onclick="showTab('timeline-section', this)">ציר זמן</button>
        <button type="button" class="tab-btn" data-tab="cameras-section" onclick="showTab('cameras-section', this)">מכשירים</button>
        <button type="button" class="tab-btn" data-tab="images-section" onclick="showTab('images-section', this)">תמונות</button>
    </div>

    <div class="section report-tab-section active" id="overview-section">
    <div class="section-title">סיכום</div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total}</div>
                <div class="stat-label">תמונות</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{gps_count}</div>
                <div class="stat-label">עם GPS</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{dt_count}</div>
                <div class="stat-label">עם תאריך</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(cameras)}</div>
                <div class="stat-label">מכשירים</div>
            </div>
        </div>
        {date_range_str}
    </div>

    <div class="section report-tab-section" id="insights-section">
        <div class="section-title">תובנות מרכזיות</div>
        {insights_section}
    </div>

    <div class="section report-tab-section" id="map-section">
    <div class="section-title">מפה אינטראקטיבית</div>
        <div class="map-wrapper">
            <iframe class="map-frame" srcdoc='{safe_map_html}'></iframe>
        </div>
    </div>

    <div class="section report-tab-section" id="timeline-section">
    <div class="section-title">ציר זמן</div>
        <div class="timeline-wrapper">
            {timeline_section}
        </div>
    </div>

    <div class="section report-tab-section" id="cameras-section">
    <div class="section-title">מכשירים שזוהו</div>
        {cameras_section}
    </div>

    <div class="section report-tab-section" id="images-section">
    <div class="section-title">כל התמונות — פירוט מלא</div>
        {images_table}
    </div>

</div>

<div class="report-footer">Image Intel &nbsp;|&nbsp; האקתון 2025</div>
<script>
document.addEventListener("click", function (event) {{
    const link = event.target.closest(".coord-link");
    if (!link) return;

    event.preventDefault();

    const lat = parseFloat(link.dataset.lat);
    const lon = parseFloat(link.dataset.lon);

   showTab("map-section");

    const mapSection = document.getElementById("map-section");
    if (mapSection) {{
        mapSection.scrollIntoView({{ behavior: "smooth", block: "start" }});
    }}

    const iframe = document.querySelector(".map-frame");
    if (!iframe || !iframe.contentWindow) return;

    setTimeout(() => {{
        iframe.contentWindow.postMessage({{
            type: "focusMap",
            lat: lat,
            lon: lon
        }}, "*");
    }}, 500);
}});
</script>
<script>
function toggleInsights(button) {{
    const wrapper = button.closest(".insights-wrapper");
    if (!wrapper) return;

    const hiddenItems = wrapper.querySelectorAll(".hidden-insight");
    const isHidden = hiddenItems.length > 0 && hiddenItems[0].style.display !== "list-item";

    hiddenItems.forEach(item => {{
        item.style.display = isHidden ? "list-item" : "none";
    }});

    button.textContent = isHidden ? "View less" : "View more";
}}
</script>
<script>
function showTab(sectionId, buttonEl = null) {{
    const sections = document.querySelectorAll(".report-tab-section");
    const buttons = document.querySelectorAll(".tab-btn");

    sections.forEach(section => section.classList.remove("active"));
    buttons.forEach(btn => btn.classList.remove("active"));

    const target = document.getElementById(sectionId);
    if (target) {{
        target.classList.add("active");
    }}

    if (buttonEl) {{
        buttonEl.classList.add("active");
    }} else {{
        const matchingBtn = document.querySelector(`.tab-btn[data-tab="${{sectionId}}"]`);
        if (matchingBtn) {{
            matchingBtn.classList.add("active");
        }}
    }}
}}
</script>
</body>
</html>"""