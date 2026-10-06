#!/usr/bin/env python3
"""Build a Word (.docx) security report from a findings JSON file.

Standard library only (no python-docx, pandoc or pip install), so it runs
anywhere python3 does. Used by the security-scanner agent.

Usage:
    python3 build_report_docx.py <findings.json> <output.docx>

JSON shape (all text fields are plain text; `inline code` in backticks is
rendered in a monospace font, blank lines split paragraphs and lines that
start with "- " become bullets):

{
  "title": "Security Assessment Report",
  "project": "ABC IT PMO Kanban Board",
  "date": "2026-10-06",
  "version": "1.0",
  "assessor": "security-scanner agent (Claude Code)",
  "classification": "Internal - Confidential",
  "scope": ["index.html (v1)", "v2/index.html (v2)", ...],
  "overall_risk": "Medium",
  "executive_summary": "text",
  "methodology": "text",
  "findings": [{
      "id": "SEC-001", "title": "...", "severity": "High",
      "owasp": "A05:2025 Injection", "cwe": "CWE-79", "cvss": "6.1 (AV:N/...)",
      "confidence": "High", "locations": ["index.html:812"],
      "description": "...", "evidence": "code snippet", "impact": "...",
      "recommendation": "...", "fix_example": "code snippet",
      "effort": "Low", "status": "Open"
  }],
  "strengths": ["..."],
  "roadmap": [{"priority": "P1", "action": "...", "findings": ["SEC-001"], "effort": "Low"}],
  "limitations": ["..."]
}
"""
import json
import re
import sys
import zipfile
from datetime import datetime, timezone

SEVERITIES = ["Critical", "High", "Medium", "Low", "Informational"]
SEV_FILL = {
    "Critical": ("7B1E1E", "FFFFFF"),
    "High": ("C0392B", "FFFFFF"),
    "Medium": ("E67E22", "FFFFFF"),
    "Low": ("F4D03F", "1A1A1A"),
    "Informational": ("7F8C8D", "FFFFFF"),
}
BRAND = "0B3D91"
CONTENT_W = 9026  # A4 width minus 1" margins, in twips

_INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")


def esc(text):
    text = _INVALID_XML.sub("", str(text))
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def norm_sev(sev):
    s = str(sev or "").strip().lower()
    for name in SEVERITIES:
        if s == name.lower() or (s == "info" and name == "Informational"):
            return name
    return "Informational"


# ---------- run / paragraph helpers ----------

def run(text, bold=False, italic=False, color=None, size=None, mono=False):
    props = []
    if mono:
        props.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>')
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    if size:
        props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def rich_runs(text, **kw):
    """Split on `backticks` so inline code renders in Consolas."""
    parts = str(text).split("`")
    return "".join(run(p, mono=(i % 2 == 1), **kw) for i, p in enumerate(parts) if p)


def para(inner, style=None, align=None, after=None, before=None, keep_next=False, indent=None):
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if keep_next:
        ppr.append("<w:keepNext/>")
    if after is not None or before is not None:
        attrs = ""
        if before is not None:
            attrs += f' w:before="{before}"'
        if after is not None:
            attrs += f' w:after="{after}"'
        ppr.append(f"<w:spacing{attrs}/>")
    if indent:
        ppr.append(f'<w:ind w:left="{indent}" w:hanging="260"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    p = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    return f"<w:p>{p}{inner}</w:p>"


def heading(text, level):
    return para(run(text), style=f"Heading{level}")


def text_block(text, **kw):
    """Paragraphs split on blank lines; '- ' lines become bullets."""
    out = []
    if not text:
        return ""
    if isinstance(text, list):
        return "".join(bullet(t) for t in text)
    for block in re.split(r"\n\s*\n", str(text).strip()):
        lines = block.split("\n")
        if all(l.strip().startswith(("- ", "* ")) for l in lines if l.strip()):
            out.extend(bullet(l.strip()[2:]) for l in lines if l.strip())
        else:
            out.append(para(rich_runs(" ".join(l.strip() for l in lines), **kw)))
    return "".join(out)


def bullet(text):
    return para(run("•\t") + rich_runs(text), style="ListBullet", indent=360)


def code_block(code):
    if not code:
        return ""
    lines = str(code).rstrip("\n").split("\n")
    runs = []
    for i, line in enumerate(lines):
        if i:
            runs.append("<w:r><w:br/></w:r>")
        runs.append(run(line, mono=True, size=18))
    return para("".join(runs), style="Code")


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


# ---------- tables ----------

def cell(content_xml, width, fill=None, valign="top"):
    shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
    return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shd}'
            f'<w:vAlign w:val="{valign}"/></w:tcPr>{content_xml}</w:tc>')


def text_cell(text, width, fill=None, bold=False, color=None, mono=False, align=None):
    if mono:
        inner = run(text, mono=True, size=18, bold=bold, color=color)
    else:
        inner = rich_runs(text, bold=bold, color=color)
    return cell(para(inner, after=0, align=align), width, fill)


def sev_cell(sev, width):
    fill, fg = SEV_FILL[norm_sev(sev)]
    return text_cell(norm_sev(sev), width, fill=fill, bold=True, color=fg, align="center")


def table(header, rows, widths):
    """header: list of str; rows: list of lists of pre-rendered <w:tc> xml."""
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    border = '<w:{0} w:val="single" w:sz="4" w:space="0" w:color="BFC5CE"/>'
    borders = "".join(border.format(b) for b in
                      ("top", "left", "bottom", "right", "insideH", "insideV"))
    xml = [f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/>'
           f'<w:tblBorders>{borders}</w:tblBorders>'
           '<w:tblLayout w:type="fixed"/>'
           '<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
           '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar>'
           f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>']
    if header:
        cells = "".join(text_cell(h, w, fill=BRAND, bold=True, color="FFFFFF")
                        for h, w in zip(header, widths))
        xml.append(f'<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>{cells}</w:tr>')
    for r in rows:
        xml.append(f'<w:tr><w:trPr><w:cantSplit/></w:trPr>{"".join(r)}</w:tr>')
    xml.append("</w:tbl>")
    return "".join(xml) + para("", after=120)


def kv_table(pairs):
    widths = [2300, CONTENT_W - 2300]
    rows = []
    for k, v, kind in pairs:
        key = text_cell(k, widths[0], fill="EEF2F8", bold=True)
        if kind == "sev":
            val = sev_cell(v, widths[1])
        elif kind == "mono":
            val = cell("".join(para(run(x, mono=True, size=18), after=0)
                               for x in (v if isinstance(v, list) else [v])), widths[1])
        else:
            val = text_cell(v, widths[1])
        rows.append([key, val])
    return table(None, rows, widths)


# ---------- document sections ----------

def build_body(d):
    findings = sorted(d.get("findings", []),
                      key=lambda f: (SEVERITIES.index(norm_sev(f.get("severity"))), f.get("id", "")))
    counts = {s: 0 for s in SEVERITIES}
    for f in findings:
        counts[norm_sev(f.get("severity"))] += 1

    b = []
    # Cover
    b.append(para("", before=2400))
    b.append(para(run(d.get("title", "Security Assessment Report")), style="Title"))
    b.append(para(run(d.get("project", ""), size=32, color="44546A"), after=480))
    meta = [
        ("Report date", d.get("date", ""), "text"),
        ("Version", d.get("version", "1.0"), "text"),
        ("Assessor", d.get("assessor", "security-scanner agent"), "text"),
        ("Classification", d.get("classification", "Internal - Confidential"), "text"),
        ("Overall risk", d.get("overall_risk", "") or "-", "sev" if d.get("overall_risk") else "text"),
        ("Total findings", str(len(findings)), "text"),
    ]
    b.append(kv_table(meta))
    b.append(page_break())

    # 1. Executive summary
    b.append(heading("1. Executive Summary", 1))
    b.append(text_block(d.get("executive_summary", "")))
    b.append(heading("Findings by severity", 2))
    w = [CONTENT_W // 5] * 5
    b.append(table(None,
                   [[sev_cell(s, w[i]) for i, s in enumerate(SEVERITIES)],
                    [text_cell(str(counts[s]), w[i], bold=True, align="center")
                     for i, s in enumerate(SEVERITIES)]], w))

    # 2. Scope & methodology
    b.append(heading("2. Scope and Methodology", 1))
    b.append(heading("Scope", 2))
    b.append(text_block(d.get("scope", [])))
    b.append(heading("Methodology", 2))
    b.append(text_block(d.get("methodology", "")))
    b.append(heading("Severity rating", 2))
    sw = [1600, CONTENT_W - 1600]
    defs = {
        "Critical": "Exploitable remotely with little effort; leads to data exposure, account or system compromise. Fix immediately.",
        "High": "Likely exploitable with meaningful impact on confidentiality, integrity or availability. Fix before next release.",
        "Medium": "Exploitable under specific conditions, or a missing defence-in-depth control with real impact. Plan a fix.",
        "Low": "Limited impact or hard to exploit; hardening improvement.",
        "Informational": "Best-practice observation with no direct exploit path.",
    }
    b.append(table(["Severity", "Meaning"],
                   [[sev_cell(s, sw[0]), text_cell(defs[s], sw[1])] for s in SEVERITIES], sw))

    # 3. Findings summary
    b.append(page_break())
    b.append(heading("3. Findings Summary", 1))
    fw = [1050, 3176, 1200, 2000, 1600]
    rows = [[text_cell(f.get("id", ""), fw[0], bold=True),
             text_cell(f.get("title", ""), fw[1]),
             sev_cell(f.get("severity"), fw[2]),
             text_cell(f.get("owasp", ""), fw[3]),
             text_cell(f.get("cwe", ""), fw[4])] for f in findings]
    if rows:
        b.append(table(["ID", "Title", "Severity", "OWASP Top 10", "CWE"], rows, fw))
    else:
        b.append(para(rich_runs("No vulnerabilities were identified in scope.")))

    # 4. Detailed findings
    b.append(heading("4. Detailed Findings and Recommended Fixes", 1))
    for f in findings:
        b.append(heading(f"{f.get('id', '')}: {f.get('title', '')}", 2))
        b.append(kv_table([
            ("Severity", f.get("severity"), "sev"),
            ("OWASP category", f.get("owasp", "-"), "text"),
            ("CWE", f.get("cwe", "-"), "text"),
            ("CVSS v3.1", f.get("cvss", "-"), "text"),
            ("Confidence", f.get("confidence", "-"), "text"),
            ("Location(s)", f.get("locations") or ["-"], "mono"),
            ("Fix effort", f.get("effort", "-"), "text"),
            ("Status", f.get("status", "Open"), "text"),
        ]))
        for label, key in (("Description", "description"), ("Impact", "impact")):
            if f.get(key):
                b.append(heading(label, 3))
                b.append(text_block(f[key]))
        if f.get("evidence"):
            b.append(heading("Evidence", 3))
            b.append(code_block(f["evidence"]))
        if f.get("recommendation"):
            b.append(heading("Recommended fix", 3))
            b.append(text_block(f["recommendation"]))
        if f.get("fix_example"):
            b.append(heading("Example fix", 3))
            b.append(code_block(f["fix_example"]))

    # 5. Roadmap
    if d.get("roadmap"):
        b.append(page_break())
        b.append(heading("5. Remediation Roadmap", 1))
        rw = [900, 5126, 1700, 1300]
        b.append(table(["Priority", "Action", "Findings", "Effort"],
                       [[text_cell(r.get("priority", ""), rw[0], bold=True),
                         text_cell(r.get("action", ""), rw[1]),
                         text_cell(", ".join(r.get("findings", [])), rw[2]),
                         text_cell(r.get("effort", ""), rw[3])] for r in d["roadmap"]], rw))

    if d.get("strengths"):
        b.append(heading("6. Existing Security Strengths", 1))
        b.append(text_block(d["strengths"]))
    if d.get("limitations"):
        b.append(heading("7. Limitations", 1))
        b.append(text_block(d["limitations"]))
    return "".join(b)


NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')


def document_xml(d):
    sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rId2"/>'
            '<w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
            'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document {NS}><w:body>{build_body(d)}{sect}</w:body></w:document>')


def footer_xml(d):
    label = f"{d.get('project', '')} | Security Assessment | {d.get('classification', 'Internal - Confidential')}"
    fld = lambda instr: (f'<w:fldSimple w:instr=" {instr} "><w:r><w:rPr><w:sz w:val="16"/></w:rPr>'
                         f'<w:t>1</w:t></w:r></w:fldSimple>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}>'
            f'<w:p><w:pPr><w:tabs><w:tab w:val="right" w:pos="{CONTENT_W}"/></w:tabs></w:pPr>'
            f'{run(label, size=16, color="6B7280")}<w:r><w:tab/></w:r>'
            f'{run("Page ", size=16, color="6B7280")}{fld("PAGE")}'
            f'{run(" of ", size=16, color="6B7280")}{fld("NUMPAGES")}</w:p></w:ftr>')


STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>
<w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="en-GB"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:after="200"/></w:pPr><w:rPr><w:b/><w:color w:val="{BRAND}"/><w:sz w:val="56"/><w:szCs w:val="56"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="360" w:after="160"/><w:pBdr><w:bottom w:val="single" w:sz="8" w:space="4" w:color="{BRAND}"/></w:pBdr><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:color w:val="{BRAND}"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="280" w:after="120"/><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr><w:b/><w:color w:val="1F2937"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="160" w:after="60"/><w:outlineLvl w:val="2"/></w:pPr>
<w:rPr><w:b/><w:color w:val="{BRAND}"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:after="60"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/>
<w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F3F4F6"/><w:pBdr><w:left w:val="single" w:sz="18" w:space="6" w:color="{BRAND}"/></w:pBdr>
<w:spacing w:after="160" w:line="240" w:lineRule="auto"/><w:ind w:left="160"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="18"/></w:rPr></w:style>
</w:styles>"""

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>"""

APP = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>security-scanner</Application></Properties>"""


def core_xml(d):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{esc(d.get("title", "Security Assessment Report"))}</dc:title>'
            f'<dc:subject>{esc(d.get("project", ""))}</dc:subject>'
            f'<dc:creator>{esc(d.get("assessor", "security-scanner agent"))}</dc:creator>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
            '</cp:coreProperties>')


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: build_report_docx.py <findings.json> <output.docx>")
    with open(sys.argv[1], encoding="utf-8") as fh:
        data = json.load(fh)
    with zipfile.ZipFile(sys.argv[2], "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/document.xml", document_xml(data))
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/footer1.xml", footer_xml(data))
        z.writestr("docProps/core.xml", core_xml(data))
        z.writestr("docProps/app.xml", APP)
    n = len(data.get("findings", []))
    print(f"Wrote {sys.argv[2]} ({n} finding{'s' if n != 1 else ''})")


if __name__ == "__main__":
    main()
