import hashlib
import re
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import fitz
import numpy as np
from rapidocr_onnxruntime import RapidOCR

from src.database import Database

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_PAGES = 200
POD_STORAGE_DIR = Path("data/pod_documents")

POD_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ocr_engine = RapidOCR()


# ============================================================
# BASIC HELPERS
# ============================================================


def _calculate_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def _find_existing_pod(file_hash: str) -> dict | None:
    """Find an already processed POD using its SHA-256 hash."""
    db = Database()

    try:
        row = db.execute_one(
            """
            SELECT
                id,
                original_filename,
                file_hash,
                file_path,
                page_count,
                text_length,
                receiver_name,
                delivery_date,
                signature_detected,
                awb_matched,
                verification_status
            FROM pod_documents
            WHERE file_hash = %s
            LIMIT 1
            """,
            (file_hash,),
        )

        if row is None:
            return None

        return {
            "pod_document_id": row[0],
            "original_filename": row[1],
            "file_hash": row[2],
            "file_path": row[3],
            "page_count": row[4],
            "text_length": row[5],
            "receiver_name": row[6],
            "delivery_date": row[7],
            "signature_detected": (None if row[8] is None else bool(row[8])),
            "awb_matched": bool(row[9]),
            "verification_status": row[10],
        }

    finally:
        db.close()


# ============================================================
# AWB EXTRACTION
# ============================================================


def _extract_awb_candidates(text: str) -> list[str]:
    """
    Extract likely AWB values.

    Priority 1:
        Explicit AWB / Waybill labels.

    Priority 2:
        Standalone 12-15 digit numeric values.
    """
    candidates = set()

    explicit_patterns = [
        r"\bAWB[\s:#-]*([A-Za-z0-9]{8,20})\b",
        r"\bWaybill[\s:#-]*([A-Za-z0-9]{8,20})\b",
    ]

    for pattern in explicit_patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for value in matches:
            candidates.add(value.strip())

    standalone_numbers = re.findall(
        r"\b\d{12,15}\b",
        text,
    )

    for value in standalone_numbers:
        candidates.add(value)

    return sorted(candidates)


# ============================================================
# POD METADATA EXTRACTION
# ============================================================


def _extract_receiver_name(text: str) -> str | None:
    """
    Try to extract receiver/consignee name from POD text.

    This is intentionally conservative.
    """
    patterns = [
        r"(?:receiver|received\s*by|consignee|customer\s*name)"
        r"\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{2,100})",
        r"(?:receiver|received\s*by|consignee|customer)"
        r"\s+([A-Za-z][A-Za-z .'-]{2,100})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip()
            value = re.sub(r"\s+", " ", value)

            if len(value) >= 3:
                return value[:255]

    return None


def _extract_delivery_date(text: str):
    """
    Extract a likely delivery date.

    Supported formats:
        DD-MM-YYYY
        DD/MM/YYYY
        DD.MM.YYYY
        YYYY-MM-DD
        YYYY/MM/DD
        YYYY.MM.DD
    """
    date_patterns = [
        r"(?:delivery\s*date|delivered\s*date|delivery|delivered|date)"
        r"\s*[:\-]?\s*"
        r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
        r"(?:delivery\s*date|delivered\s*date|delivery|delivered|date)"
        r"\s*[:\-]?\s*"
        r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})",
    ]

    formats = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
    ]

    for pattern in date_patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        raw_date = match.group(1).strip()

        for fmt in formats:
            try:
                return datetime.strptime(
                    raw_date,
                    fmt,
                ).date()
            except ValueError:
                continue

    return None


def _detect_signature(text: str) -> bool | None:
    """
    Detect explicit signature-related text.

    Returns:
        True  -> signature language detected
        False -> explicit no-signature language
        None  -> insufficient evidence
    """
    lower_text = text.lower()

    positive_patterns = [
        r"\bsignature\b",
        r"\bsigned\b",
        r"\bsign\s*by\b",
        r"\breceived\s*signature\b",
        r"\bauthorized\s*signature\b",
        r"\bsignature\s*obtained\b",
    ]

    negative_patterns = [
        r"\bno\s+signature\b",
        r"\bsignature\s+not\s+available\b",
        r"\bsignature\s+missing\b",
        r"\bunsigned\b",
    ]

    for pattern in negative_patterns:
        if re.search(pattern, lower_text):
            return False

    for pattern in positive_patterns:
        if re.search(pattern, lower_text):
            return True

    return None


def _extract_pod_metadata(text: str) -> dict:
    """Extract receiver, delivery date and signature information."""
    return {
        "receiver_name": _extract_receiver_name(text),
        "delivery_date": _extract_delivery_date(text),
        "signature_detected": _detect_signature(text),
    }


# ============================================================
# PDF + OCR
# ============================================================


def _pixmap_to_bgr(page) -> np.ndarray:
    """Convert a PDF page to an OpenCV BGR image."""
    pixmap = page.get_pixmap(
        matrix=fitz.Matrix(2, 2),
        alpha=False,
    )

    image_bytes = pixmap.tobytes("png")

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8,
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR,
    )

    if image is None:
        raise ValueError("Unable to decode PDF page image.")

    return image


def _has_colored_ink(image: np.ndarray) -> bool:
    """
    Detect significant colored ink such as purple/blue/red stamps.
    """
    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV,
    )

    saturation = hsv[:, :, 1]

    colored_pixels = np.sum(saturation > 70)
    total_pixels = saturation.size

    if total_pixels == 0:
        return False

    colored_ratio = colored_pixels / total_pixels

    return colored_ratio > 0.01


def _remove_colored_ink(
    image: np.ndarray,
) -> np.ndarray:
    """
    Suppress colored stamp/ink while preserving
    dark printed text as much as possible.
    """
    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV,
    )

    saturation = hsv[:, :, 1]

    colored_mask = (saturation > 70).astype(np.uint8) * 255

    kernel = np.ones(
        (3, 3),
        np.uint8,
    )

    colored_mask = cv2.dilate(
        colored_mask,
        kernel,
        iterations=1,
    )

    result = image.copy()

    result[colored_mask > 0] = (
        255,
        255,
        255,
    )

    return result


def _enhance_for_ocr(
    image: np.ndarray,
) -> np.ndarray:
    """Improve contrast and create a clean grayscale image."""
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    return clahe.apply(gray)


def _run_ocr(image) -> list:
    """
    Run RapidOCR.

    Each item:
        [bounding_box, text, confidence]
    """
    result, _ = ocr_engine(image)

    if not result:
        return []

    return [
        item for item in result if (item and len(item) >= 3 and str(item[1]).strip())
    ]


def _ocr_item_to_dict(item) -> dict | None:
    """Convert one RapidOCR result into a normalized dictionary."""
    if not item or len(item) < 3:
        return None

    box = item[0]
    text = str(item[1]).strip()

    try:
        confidence = float(item[2])
    except (TypeError, ValueError):
        confidence = None

    if not text or not box:
        return None

    try:
        points = [
            (
                float(point[0]),
                float(point[1]),
            )
            for point in box
        ]

        x_values = [point[0] for point in points]

        y_values = [point[1] for point in points]

        return {
            "text": text,
            "confidence": confidence,
            "bbox": {
                "x1": int(min(x_values)),
                "y1": int(min(y_values)),
                "x2": int(max(x_values)),
                "y2": int(max(y_values)),
            },
        }

    except (
        TypeError,
        ValueError,
        IndexError,
    ):
        return None


def _group_ocr_items_into_rows(
    ocr_items: list[dict],
    y_tolerance: int = 18,
) -> list[list[dict]]:
    """Group OCR items belonging to the same visual row."""
    rows = []

    sorted_items = sorted(
        ocr_items,
        key=lambda item: (
            item["bbox"]["y1"],
            item["bbox"]["x1"],
        ),
    )

    for item in sorted_items:
        center_y = (item["bbox"]["y1"] + item["bbox"]["y2"]) / 2

        target_row = None

        for row in rows:
            row_center_y = sum(
                (x["bbox"]["y1"] + x["bbox"]["y2"]) / 2 for x in row
            ) / len(row)

            if abs(center_y - row_center_y) <= y_tolerance:
                target_row = row
                break

        if target_row is None:
            rows.append([item])
        else:
            target_row.append(item)

    for row in rows:
        row.sort(key=lambda item: item["bbox"]["x1"])

    return rows


def _native_text_to_items(page) -> list[dict]:
    """
    Convert native PDF words into the same positional structure used by OCR.

    Native PDF text is preferred because many POD pages contain real text
    objects. Keeping word coordinates lets the same row/serial logic work
    without requiring RapidOCR on every page.
    """
    items = []

    try:
        words = page.get_text("words") or []
    except Exception:
        return items

    for word in words:
        if len(word) < 5:
            continue

        x1, y1, x2, y2, raw_text = word[:5]
        text = str(raw_text or "").strip()

        if not text:
            continue

        items.append(
            {
                "text": text,
                "confidence": None,
                "bbox": {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2),
                },
            }
        )

    return items


def _clean_section_text(text: str) -> str:
    """Normalize OCR/native section text for remark matching."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _extract_rto_sections_from_items(
    ocr_items: list[dict],
) -> list[dict]:
    """
    Detect all positive RTO sections on a page.

    Examples:
        RTO:20DTO:0  -> RTO group, expected_count=20
        RTO:1DT0:0   -> RTO group, expected_count=1
        RTO:0DTO:3   -> DTO-only, ignored

    OCR may produce small variations such as:
        RTO
        RO
        R7O
        DT0
        DTO
        D70

    Only the RTO count is used to start an RTO remark group.
    """
    if not ocr_items:
        return []

    rows = _group_ocr_items_into_rows(ocr_items)
    sections = []

    # OCR normalization:
    # R7O / RO -> RTO
    # DT0 / D70 / DTC -> DTO
    def normalize_marker(text: str) -> str:
        value = _clean_section_text(text).upper()

        value = re.sub(r"\bR7O\b", "RTO", value)
        value = re.sub(r"\bRO\b", "RTO", value)

        value = re.sub(r"DT0", "DTO", value)
        value = re.sub(r"D70", "DTO", value)
        value = re.sub(r"DTC", "DTO", value)

        return value

    # Match RTO count from a row.
    # We intentionally only capture the number immediately after RTO.
    rto_pattern = re.compile(
        r"\bRTO\s*[:\-]?\s*(\d+)",
        re.IGNORECASE,
    )

    for row_index, row in enumerate(rows):
        normalized_values = [normalize_marker(item.get("text", "")) for item in row]

        row_text = " ".join(value for value in normalized_values if value).strip()

        if not row_text:
            continue

        match = rto_pattern.search(row_text)

        if not match:
            continue

        count = int(match.group(1))

        # RTO:0DTO:N is DTO-only.
        if count <= 0:
            continue

        y_values = [(item.get("bbox") or {}).get("y1", 0) for item in row]

        section_y = min(y_values) if y_values else None

        # Try to capture text immediately before RTO as detail.
        detail_parts = []

        for value in normalized_values:
            if not value:
                continue

            if "RTO" in value:
                break

            detail_parts.append(value)

        # If nothing is on the same row, inspect the previous row.
        if not detail_parts and row_index > 0:
            previous_row = rows[row_index - 1]

            previous_text = " ".join(
                _clean_section_text(item.get("text", "")) for item in previous_row
            ).strip()

            if previous_text and len(previous_text) <= 120:
                detail_parts.append(previous_text)

        detail = " | ".join(detail_parts)[:500] or "RTO"

        sections.append(
            {
                "remark": "RTO",
                "remark_confidence": None,
                "condition_category": None,
                "condition_detail": detail,
                "expected_count": count,
                "remarks_header_y": section_y,
                "count_y": section_y,
                "section_y": section_y,
                "section_type": "RTO",
            }
        )

    return sections


def _extract_rto_section_from_items(
    ocr_items: list[dict],
) -> dict | None:
    """
    Backward-compatible wrapper.

    Returns the first positive RTO section, if one exists.
    """
    sections = _extract_rto_sections_from_items(ocr_items)

    return sections[0] if sections else None


# ============================================================
# CONDITION / PAGE HELPERS
# ============================================================


def _normalize_condition(
    text: str,
) -> tuple[str | None, str | None]:
    text = re.sub(
        r"\s+",
        " ",
        str(text or ""),
    ).strip()

    if not text:
        return None, None

    lower = text.lower()

    if "good condition" in lower:
        return "GOOD", text

    if "damage" in lower or "damaged" in lower:
        return "DAMAGE", text

    if "missing" in lower:
        return "MISSING", text

    if "short" in lower:
        return "SHORT", text

    if "refused" in lower:
        return "REFUSED", text

    if "rejected" in lower:
        return "REJECTED", text

    return None, text


def _extract_page_date(text: str):
    return _extract_delivery_date(text)


def _extract_warehouse(text: str) -> str | None:
    patterns = [
        r"warehouse\s*[:\-]\s*(.+)",
        r"warehouse\s+(.+)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        value = re.sub(
            r"\s+",
            " ",
            match.group(1),
        ).strip()

        value = re.split(
            r"\b(?:date|remark|remarks|condition)\b\s*[:\-]?",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        if len(value) >= 3:
            return value[:255]

    return None


# ============================================================
# PAGE REMARK EXTRACTION
# ============================================================


def _extract_page_remarks(
    ocr_items: list[dict],
) -> dict:
    """
    Extract page-level remark/condition information.

    RTO groups are detected from the actual document text, for example:
        RTO:20DTO:0
        RTO:1DTO:0
        RTO:0DTO:3

    The RTO count is always read from the document. Nothing is hardcoded.
    """
    rto_section = _extract_rto_section_from_items(ocr_items)

    if rto_section is not None:
        return rto_section

    # Preserve the original Remarks/Count behavior for documents that
    # genuinely contain a separate Remarks + Count layout.
    remarks = []
    remarks_header_y = None
    count_y = None
    expected_count = None

    for item in ocr_items:
        value = _clean_section_text(item.get("text", ""))
        if value.lower().rstrip(":") != "remarks":
            continue

        remarks_header_y = (item.get("bbox") or {}).get("y1")
        break

    if remarks_header_y is None:
        return {
            "remark": None,
            "remark_confidence": None,
            "condition_category": None,
            "condition_detail": None,
            "expected_count": None,
            "remarks_header_y": None,
            "count_y": None,
        }

    for item in ocr_items:
        value = _clean_section_text(item.get("text", ""))
        if value.lower().rstrip(":") != "count":
            continue

        count_y = (item.get("bbox") or {}).get("y1")
        break

    if count_y is not None:
        candidates = []

        for item in ocr_items:
            value = _clean_section_text(item.get("text", ""))

            if not value.isdigit():
                continue

            y1 = (item.get("bbox") or {}).get("y1", 0)

            if count_y < y1 <= count_y + 50:
                candidates.append(
                    {
                        "value": int(value),
                        "distance": y1 - count_y,
                    }
                )

        if candidates:
            candidates.sort(key=lambda item: item["distance"])
            expected_count = candidates[0]["value"]

    for item in ocr_items:
        value = _clean_section_text(item.get("text", ""))

        if not value:
            continue

        y1 = (item.get("bbox") or {}).get("y1", 0)

        if y1 <= remarks_header_y or y1 > remarks_header_y + 100:
            continue

        lower = value.lower()

        if lower.rstrip(":") in {"count", "remarks"}:
            continue

        if expected_count is not None and lower == str(expected_count):
            continue

        if any(
            keyword in lower
            for keyword in (
                "rto",
                "damage",
                "damaged",
                "short",
                "missing",
                "good condition",
                "rejected",
                "refused",
            )
        ):
            remarks.append(
                {
                    "text": value,
                    "confidence": item.get("confidence"),
                    "bbox": item.get("bbox"),
                }
            )

    if not remarks:
        return {
            "remark": None,
            "remark_confidence": None,
            "condition_category": None,
            "condition_detail": None,
            "expected_count": expected_count,
            "remarks_header_y": remarks_header_y,
            "count_y": count_y,
        }

    remark_text = " | ".join(item["text"] for item in remarks)
    confidences = [
        item["confidence"] for item in remarks if item.get("confidence") is not None
    ]
    confidence = sum(confidences) / len(confidences) if confidences else None
    condition_category, _ = _normalize_condition(remark_text)

    return {
        "remark": remark_text,
        "remark_confidence": confidence,
        "condition_category": condition_category,
        "condition_detail": remark_text,
        "expected_count": expected_count,
        "remarks_header_y": remarks_header_y,
        "count_y": count_y,
    }


# ============================================================
# AWB ROW EXTRACTION
# ============================================================


def _extract_awb_rows(
    ocr_items: list[dict],
    page_remarks: dict | None = None,
) -> list[dict]:
    """
    Extract individual AWB records from positional OCR/native words.

    Supports both:
        1. 29848122504984
        2. 1.29848122504984

    The second form is common in the native PDF text of this POD.
    """
    rows = _group_ocr_items_into_rows(ocr_items)
    results = []

    awb_pattern = re.compile(r"(?<!\d)(\d{12,15})(?!\d)")
    serial_awb_pattern = re.compile(r"^\s*(\d{1,4})\s*[\.\):\-]\s*(\d{12,15})\s*$")
    serial_pattern = re.compile(r"^\d{1,4}$")

    for row in rows:
        row = sorted(row, key=lambda item: item["bbox"]["x1"])
        awb_items = []

        for index, item in enumerate(row):
            value = _clean_section_text(item.get("text", ""))

            combined = serial_awb_pattern.search(value)
            if combined:
                awb_items.append(
                    {
                        "index": index,
                        "awb": combined.group(2),
                        "serial": int(combined.group(1)),
                        "item": item,
                    }
                )
                continue

            match = awb_pattern.search(value)
            if match:
                awb_items.append(
                    {
                        "index": index,
                        "awb": match.group(1),
                        "serial": None,
                        "item": item,
                    }
                )

        if not awb_items:
            continue

        detected_serials = {}

        for awb_position, awb_entry in enumerate(awb_items):
            if awb_entry.get("serial") is not None:
                detected_serials[awb_position] = awb_entry["serial"]
                continue

            index = awb_entry["index"]
            bbox = awb_entry["item"]["bbox"]

            for previous in reversed(row[:index]):
                previous_text = _clean_section_text(previous.get("text", ""))
                previous_bbox = previous["bbox"]

                if previous_bbox["x2"] > bbox["x1"]:
                    continue

                gap = bbox["x1"] - previous_bbox["x2"]

                if gap > 100:
                    break

                if serial_pattern.fullmatch(previous_text):
                    detected_serials[awb_position] = int(previous_text)
                    break

        serial_numbers = {}

        for position in range(len(awb_items)):
            if position in detected_serials:
                serial_numbers[position] = detected_serials[position]
                continue

            previous_positions = [p for p in detected_serials if p < position]
            next_positions = [p for p in detected_serials if p > position]

            inferred = None

            if previous_positions:
                previous_position = max(previous_positions)
                candidate = detected_serials[previous_position] + (
                    position - previous_position
                )
                if candidate > 0:
                    inferred = candidate

            if next_positions:
                next_position = min(next_positions)
                candidate = detected_serials[next_position] - (next_position - position)
                if candidate > 0:
                    if inferred is None or candidate == inferred:
                        inferred = candidate

            serial_numbers[position] = inferred

        for awb_position, awb_entry in enumerate(awb_items):
            item = awb_entry["item"]

            results.append(
                {
                    "awb": awb_entry["awb"],
                    "serial_number": serial_numbers.get(awb_position),
                    "condition_category": None,
                    "condition_detail": None,
                    "confidence": item.get("confidence"),
                    "remark": None,
                    "remark_confidence": None,
                    "bbox": item.get("bbox"),
                }
            )

    return results


# ============================================================
# DOCUMENT-LEVEL AWB EXTRACTION
# ============================================================


def _extract_document_awb_rows(
    pages: list[dict],
) -> list[dict]:
    """
    Extract every AWB from the complete document.

    RTO handling:
      - RTO:N is read dynamically from the document
      - RTO:0 sections are ignored
      - multiple RTO groups are supported
      - groups may continue across pages
      - each group receives exactly N AWBs
      - RTO processing never removes AWB rows
    """

    all_rows = []
    rto_sections = []

    # ---------------------------------------------------------
    # PASS 1: Collect ALL AWBs.
    # ---------------------------------------------------------
    for page_data in pages:
        page_number = page_data["page"]
        ocr_items = page_data.get("ocr_items", [])

        if not ocr_items:
            page_text = page_data.get("text", "")
            page_awbs = _extract_awb_candidates(page_text)

            for awb in page_awbs:
                all_rows.append(
                    {
                        "awb": awb,
                        "source_page": page_number,
                        "confidence": None,
                        "remark": None,
                        "remark_confidence": None,
                        "bbox": None,
                        "serial_number": None,
                        "condition_category": None,
                        "condition_detail": None,
                        "extraction_method": "NATIVE_TEXT",
                    }
                )

            continue

        rows = _extract_awb_rows(
            ocr_items,
            None,
        )

        for row in rows:
            row["source_page"] = page_number
            row["extraction_method"] = (
                "OCR" if page_data.get("ocr_used") else "NATIVE_TEXT"
            )
            all_rows.append(row)

        for section in _extract_rto_sections_from_items(ocr_items):
            section = dict(section)
            section["page"] = page_number
            rto_sections.append(section)

    if not all_rows or not rto_sections:
        return all_rows

    # ---------------------------------------------------------
    # Document order.
    # ---------------------------------------------------------
    all_rows.sort(
        key=lambda row: (
            row.get("source_page", 0),
            (row.get("bbox") or {}).get("y1", 0),
            (row.get("bbox") or {}).get("x1", 0),
        )
    )

    rto_sections.sort(
        key=lambda section: (
            section["page"],
            (
                section.get("section_y")
                if section.get("section_y") is not None
                else float("inf")
            ),
        )
    )

    # ---------------------------------------------------------
    # Find the first AWB after every RTO marker.
    # ---------------------------------------------------------
    anchors = []

    for section in rto_sections:
        page = section["page"]
        marker_y = section.get("section_y")

        anchor = None

        for index, row in enumerate(all_rows):
            if row.get("source_page") != page:
                continue

            row_y = (row.get("bbox") or {}).get("y1")

            if marker_y is None:
                anchor = index
                break

            if row_y is not None and row_y > marker_y:
                anchor = index
                break

        if anchor is None:
            # No AWB below marker on this page.
            # Continue from the first AWB on a later page.
            for index, row in enumerate(all_rows):
                if row.get("source_page", 0) > page:
                    anchor = index
                    break

        if anchor is not None:
            anchors.append(
                {
                    "section": section,
                    "anchor": anchor,
                }
            )

    # ---------------------------------------------------------
    # Assignment map.
    #
    # Processing backwards is important:
    #
    # Later RTO groups reserve their own AWBs first.
    # Earlier groups can then continue past those reserved
    # rows until their own expected count is reached.
    # ---------------------------------------------------------
    assigned = set()

    for item in reversed(anchors):
        section = item["section"]
        anchor = item["anchor"]

        expected_count = int(section.get("expected_count") or 0)

        if expected_count <= 0:
            continue

        collected = 0

        for index in range(anchor, len(all_rows)):

            if collected >= expected_count:
                break

            if index in assigned:
                continue

            row = all_rows[index]

            row["remark"] = section["remark"]
            row["remark_confidence"] = section.get("remark_confidence")
            row["condition_category"] = section.get("condition_category")
            row["condition_detail"] = section.get("condition_detail")

            assigned.add(index)
            collected += 1

    return all_rows


# ============================================================
# PAGE TEXT + OCR EXTRACTION
# ============================================================


def _extract_page_text(
    document: fitz.Document,
) -> tuple[str, list[dict]]:
    """
    Extract native PDF text with positional words first.

    Native words are converted into the same structure used by RapidOCR,
    so RTO sections and serial/AWB rows can be parsed from real PDF text.

    RapidOCR remains the fallback for pages where native text is absent.
    """
    all_text = []
    page_results = []

    for page_number, page in enumerate(document, start=1):
        native_text = page.get_text("text").strip()
        native_items = _native_text_to_items(page)

        page_text = native_text
        ocr_used = False
        ocr_items = native_items

        # Use OCR only when native extraction is insufficient.
        if len(native_text) < 20 or len(native_items) < 3:
            image = _pixmap_to_bgr(page)

            if _has_colored_ink(image):
                image = _remove_colored_ink(image)

            enhanced = _enhance_for_ocr(image)
            result = _run_ocr(enhanced)

            ocr_items = []

            for item in result:
                normalized = _ocr_item_to_dict(item)
                if normalized:
                    ocr_items.append(normalized)

            if ocr_items:
                page_text = "\n".join(item["text"] for item in ocr_items).strip()
                ocr_used = True

        all_text.append(page_text)

        page_results.append(
            {
                "page": page_number,
                "text": page_text,
                "ocr_used": ocr_used,
                "ocr_items": ocr_items,
            }
        )

    return (
        "\n".join(all_text).strip(),
        page_results,
    )


# ============================================================
# AWB DATABASE VERIFICATION
# ============================================================


def _verify_awb_candidates(
    awb_candidates: list[dict],
) -> list[dict]:
    if not awb_candidates:
        return []

    db = Database()

    try:
        unique_awbs = sorted({item["awb"] for item in awb_candidates})

        matched_awbs = set()

        batch_size = 500

        for start in range(
            0,
            len(unique_awbs),
            batch_size,
        ):
            batch = unique_awbs[start : start + batch_size]

            placeholders = ",".join(["%s"] * len(batch))

            query = f"""
                SELECT AWB
                FROM shipments
                WHERE AWB IN ({placeholders})
            """

            rows = db.execute(
                query,
                tuple(batch),
            )

            for row in rows:
                matched_awbs.add(str(row[0]))

        verification = []
        seen = set()

        for item in awb_candidates:
            awb = item["awb"]
            source_page = item["source_page"]

            key = (
                awb,
                source_page,
            )

            if key in seen:
                continue

            seen.add(key)

            verification.append(
                {
                    "awb": awb,
                    "source_page": source_page,
                    "matched": (awb in matched_awbs),
                    "source": "shipments",
                    "confidence": item.get("confidence"),
                    "remark": item.get("remark"),
                    "remark_confidence": item.get("remark_confidence"),
                    "bbox": item.get("bbox"),
                    "serial_number": item.get("serial_number"),
                    "condition_category": item.get("condition_category"),
                    "condition_detail": item.get("condition_detail"),
                    "extraction_method": item.get("extraction_method"),
                }
            )

        return verification

    finally:
        db.close()


# ============================================================
# SAVE POD DOCUMENT
# ============================================================


def _save_pod_document(
    original_filename: str,
    file_hash: str,
    file_path: str,
    page_count: int,
    text_length: int,
    awb_verification: list[dict],
    metadata: dict,
) -> dict:
    matched_awbs = [item["awb"] for item in awb_verification if item["matched"]]

    primary_awb = matched_awbs[0] if matched_awbs else None

    if matched_awbs:
        verification_status = "AWB_MATCHED"
    elif awb_verification:
        verification_status = "AWB_NOT_MATCHED"
    else:
        verification_status = "AWB_NOT_FOUND"

    db = Database()

    try:
        db.execute(
            """
            INSERT INTO pod_documents (
                awb,
                original_filename,
                file_hash,
                file_path,
                page_count,
                text_length,
                receiver_name,
                delivery_date,
                signature_detected,
                awb_matched,
                verification_status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            """,
            (
                primary_awb,
                original_filename,
                file_hash,
                file_path,
                page_count,
                text_length,
                metadata.get("receiver_name"),
                metadata.get("delivery_date"),
                metadata.get("signature_detected"),
                bool(matched_awbs),
                verification_status,
            ),
        )

        db.connection.commit()

        row = db.execute_one(
            """
            SELECT id
            FROM pod_documents
            WHERE file_hash = %s
            LIMIT 1
            """,
            (file_hash,),
        )

        if row is None:
            raise RuntimeError(
                "POD document was inserted but " "its ID could not be retrieved."
            )

        pod_document_id = row[0]

        for item in awb_verification:
            bbox = item.get("bbox") or {}

            db.execute(
                """
                INSERT IGNORE INTO pod_document_awbs (
                    pod_document_id,
                    awb,
                    source_page,
                    matched,
                    confidence,
                    remark,
                    remark_confidence,
                    bbox_x1,
                    bbox_y1,
                    bbox_x2,
                    bbox_y2,
                    serial_number,
                    condition_category,
                    condition_detail,
                    extraction_method
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    pod_document_id,
                    item["awb"],
                    item["source_page"],
                    item["matched"],
                    item.get("confidence"),
                    item.get("remark"),
                    item.get("remark_confidence"),
                    bbox.get("x1"),
                    bbox.get("y1"),
                    bbox.get("x2"),
                    bbox.get("y2"),
                    item.get("serial_number"),
                    item.get("condition_category"),
                    item.get("condition_detail"),
                    item.get("extraction_method"),
                ),
            )

        db.connection.commit()

        return {
            "pod_document_id": pod_document_id,
            "primary_awb": primary_awb,
            "total_awbs": len(awb_verification),
            "matched_awbs": len(matched_awbs),
            "receiver_name": metadata.get("receiver_name"),
            "delivery_date": metadata.get("delivery_date"),
            "signature_detected": metadata.get("signature_detected"),
            "verification_status": (verification_status),
        }

    except Exception:
        db.connection.rollback()
        raise

    finally:
        db.close()


# ============================================================
# PROCESS POD PDF
# ============================================================


def process_pod_pdf(
    file_bytes: bytes,
    original_filename: str,
) -> dict:
    if not original_filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are allowed for POD upload.")

    if not file_bytes:
        raise ValueError("Uploaded POD PDF is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("POD PDF exceeds the 10 MB size limit.")

    file_hash = _calculate_sha256(file_bytes)

    # --------------------------------------------------------
    # Check whether already processed.
    # --------------------------------------------------------

    existing_pod = _find_existing_pod(file_hash)

    if existing_pod is not None:
        return {
            "status": "already_processed",
            "message": ("This POD has already been processed."),
            "pod_document_id": (existing_pod["pod_document_id"]),
            "original_filename": (existing_pod["original_filename"]),
            "file_hash": existing_pod["file_hash"],
            "page_count": existing_pod["page_count"],
            "text_length": existing_pod["text_length"],
            "receiver_name": existing_pod["receiver_name"],
            "delivery_date": existing_pod["delivery_date"],
            "signature_detected": existing_pod["signature_detected"],
            "awb_matched": existing_pod["awb_matched"],
            "verification_status": existing_pod["verification_status"],
            "storage_path": existing_pod["file_path"],
        }

    safe_filename = f"{uuid.uuid4().hex}.pdf"

    pdf_path = POD_STORAGE_DIR / safe_filename

    try:
        pdf_path.write_bytes(file_bytes)

        with fitz.open(pdf_path) as document:
            if document.page_count > MAX_PAGES:
                raise ValueError(
                    "POD PDF exceeds maximum " f"allowed pages ({MAX_PAGES})."
                )

            page_count = document.page_count

            full_text, page_results = _extract_page_text(document)

        # --------------------------------------------------------
        # Metadata.
        # --------------------------------------------------------

        metadata = _extract_pod_metadata(full_text)

        # --------------------------------------------------------
        # IMPORTANT:
        #
        # Use DOCUMENT-level AWB extraction.
        #
        # This is where dynamic Remarks + Count and
        # continuation-page propagation happen.
        # --------------------------------------------------------

        document_rows = _extract_document_awb_rows(page_results)

        # --------------------------------------------------------
        # Add source-page information to all candidates.
        # --------------------------------------------------------

        awb_candidates = []

        for item in document_rows:
            awb_candidates.append(
                {
                    "awb": item["awb"],
                    "source_page": item["source_page"],
                    "confidence": item.get("confidence"),
                    "remark": item.get("remark"),
                    "remark_confidence": item.get("remark_confidence"),
                    "bbox": item.get("bbox"),
                    "serial_number": item.get("serial_number"),
                    "condition_category": item.get("condition_category"),
                    "condition_detail": item.get("condition_detail"),
                    "extraction_method": item.get("extraction_method"),
                }
            )

        # --------------------------------------------------------
        # Remove duplicate AWB/page combinations.
        # --------------------------------------------------------

        unique_candidates = []
        seen = set()

        for item in awb_candidates:
            key = (
                item["awb"],
                item["source_page"],
            )

            if key in seen:
                continue

            seen.add(key)
            unique_candidates.append(item)

        # --------------------------------------------------------
        # Verify against shipments table.
        # --------------------------------------------------------

        awb_verification = _verify_awb_candidates(unique_candidates)

        # --------------------------------------------------------
        # Save document + AWB records.
        # --------------------------------------------------------

        db_result = _save_pod_document(
            original_filename=original_filename,
            file_hash=file_hash,
            file_path=pdf_path.as_posix(),
            page_count=page_count,
            text_length=len(full_text),
            awb_verification=awb_verification,
            metadata=metadata,
        )

        ocr_pages = [
            {
                "page": page["page"],
                "method": "OCR",
            }
            for page in page_results
            if page["ocr_used"]
        ]

        return {
            "status": "success",
            "original_filename": original_filename,
            "stored_filename": safe_filename,
            "file_hash": file_hash,
            "page_count": page_count,
            "text_length": len(full_text),
            "ocr_pages": ocr_pages,
            "receiver_name": metadata.get("receiver_name"),
            "delivery_date": metadata.get("delivery_date"),
            "signature_detected": metadata.get("signature_detected"),
            "awb_candidates": unique_candidates,
            "awb_verification": awb_verification,
            "database": db_result,
            "storage_path": str(pdf_path),
        }

    except Exception:
        if pdf_path.exists():
            pdf_path.unlink()

        raise


# ============================================================
# BACKFILL POD METADATA
# ============================================================


def backfill_pod_metadata(
    pod_document_id: int,
):
    """
    Extract and update receiver/date/signature metadata
    for an existing POD document.
    """
    db = Database()
    cursor = None

    try:
        cursor = db.connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, file_path
            FROM pod_documents
            WHERE id = %s
            """,
            (pod_document_id,),
        )

        pod = cursor.fetchone()

        if not pod:
            return {
                "success": False,
                "error": (f"POD document " f"{pod_document_id} not found"),
            }

        pdf_path = Path(pod["file_path"])

        if not pdf_path.exists():
            return {
                "success": False,
                "error": (f"POD file not found: " f"{pdf_path}"),
            }

        with fitz.open(pdf_path) as pdf:
            native_text = "\n".join(page.get_text("text") or "" for page in pdf)

            ocr_text, _ = _extract_page_text(pdf)

        combined_text = native_text + "\n" + ocr_text

        metadata = _extract_pod_metadata(combined_text)

        cursor.execute(
            """
            UPDATE pod_documents
            SET
                receiver_name = %s,
                delivery_date = %s,
                signature_detected = %s
            WHERE id = %s
            """,
            (
                metadata.get("receiver_name"),
                metadata.get("delivery_date"),
                metadata.get("signature_detected"),
                pod_document_id,
            ),
        )

        db.connection.commit()

        return {
            "success": True,
            "pod_document_id": pod_document_id,
            "receiver_name": metadata.get("receiver_name"),
            "delivery_date": metadata.get("delivery_date"),
            "signature_detected": metadata.get("signature_detected"),
        }

    finally:
        if cursor is not None:
            cursor.close()

        db.close()


# ============================================================
# BACKFILL AWBS
# ============================================================


def backfill_pod_awbs(
    pod_document_id: int,
    file_path: str,
) -> dict:
    """
    Backfill AWB records using the same document-level
    extraction logic as the normal POD processing flow.

    This means dynamic Remarks + Count and continuation
    pages behave consistently.
    """
    pdf_path = Path(file_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"POD PDF not found: {pdf_path}")

    db = Database()

    try:
        with fitz.open(pdf_path) as document:
            _, pages = _extract_page_text(document)

        document_rows = _extract_document_awb_rows(pages)

        inserted = 0
        skipped = 0
        total_candidates = len(document_rows)

        for item in document_rows:
            awb = item["awb"]
            page_number = item["source_page"]

            existing = db.execute_one(
                """
                SELECT id
                FROM pod_document_awbs
                WHERE pod_document_id = %s
                  AND awb = %s
                  AND source_page = %s
                LIMIT 1
                """,
                (
                    pod_document_id,
                    awb,
                    page_number,
                ),
            )

            if existing:
                skipped += 1
                continue

            shipment = db.execute_one(
                """
                SELECT AWB
                FROM shipments
                WHERE AWB = %s
                LIMIT 1
                """,
                (awb,),
            )

            matched = bool(shipment)

            db.execute(
                """
                INSERT INTO pod_document_awbs
                (
                    pod_document_id,
                    awb,
                    source_page,
                    matched,
                    confidence,
                    remark,
                    remark_confidence,
                    bbox_x1,
                    bbox_y1,
                    bbox_x2,
                    bbox_y2,
                    serial_number,
                    condition_category,
                    condition_detail,
                    extraction_method
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    pod_document_id,
                    awb,
                    page_number,
                    matched,
                    item.get("confidence"),
                    item.get("remark"),
                    item.get("remark_confidence"),
                    (item.get("bbox") or {}).get("x1"),
                    (item.get("bbox") or {}).get("y1"),
                    (item.get("bbox") or {}).get("x2"),
                    (item.get("bbox") or {}).get("y2"),
                    item.get("serial_number"),
                    item.get("condition_category"),
                    item.get("condition_detail"),
                    item.get("extraction_method"),
                ),
            )

            inserted += 1

        db.connection.commit()

        return {
            "pod_document_id": pod_document_id,
            "pages_processed": len(pages),
            "total_candidates": total_candidates,
            "inserted": inserted,
            "skipped_existing": skipped,
        }

    except Exception:
        db.connection.rollback()
        raise

    finally:
        db.close()


# ============================================================
# BACKFILL AWB VISUAL METADATA
# ============================================================


def backfill_pod_awb_visual_metadata(
    pod_document_id: int,
) -> dict:
    """
    Backfill visual OCR metadata for existing POD AWB records.

    Updates:
        - OCR confidence
        - remark
        - remark confidence
        - bounding box
        - serial number
        - condition
        - extraction method

    Important:
        - Does NOT change the original AWB.
        - Does NOT change matched/shipment fields.
        - Does NOT insert new AWB records.
        - Uses the same document-level remark propagation
          logic as normal processing.
    """
    db = Database()

    try:
        document = db.execute_one(
            """
            SELECT file_path
            FROM pod_documents
            WHERE id = %s
            LIMIT 1
            """,
            (pod_document_id,),
        )

        if document is None:
            raise ValueError(f"POD document " f"{pod_document_id} was not found.")

        file_path = document[0]

        if not file_path:
            raise ValueError(f"POD document " f"{pod_document_id} has no file path.")

        file_path = str(file_path).replace(
            "\\",
            "/",
        )

        pdf_path = Path(file_path)

        if not pdf_path.is_absolute():
            project_root = Path(__file__).resolve().parents[2]

            pdf_path = project_root / pdf_path

        if not pdf_path.exists():
            raise ValueError(f"POD PDF file was not found: " f"{pdf_path}")

        # -----------------------------------------------------
        # Re-run complete extraction.
        # -----------------------------------------------------

        with fitz.open(str(pdf_path)) as document_pdf:
            _, pages = _extract_page_text(document_pdf)

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # Use document-level extraction so remark propagation
        # is identical to the normal processing path.
        # -----------------------------------------------------

        document_rows = _extract_document_awb_rows(pages)

        updated = 0
        missing = 0

        ocr_pages = sum(1 for page in pages if page.get("ocr_used"))

        ocr_awbs = sum(
            1 for item in document_rows if item.get("extraction_method") == "OCR"
        )

        # -----------------------------------------------------
        # Update existing DB records only.
        # -----------------------------------------------------

        for item in document_rows:
            if item.get("extraction_method") != "OCR":
                continue

            awb = item["awb"]
            page_number = item["source_page"]

            existing = db.execute_one(
                """
                SELECT id
                FROM pod_document_awbs
                WHERE pod_document_id = %s
                  AND awb = %s
                  AND source_page = %s
                LIMIT 1
                """,
                (
                    pod_document_id,
                    awb,
                    page_number,
                ),
            )

            if existing is None:
                missing += 1
                continue

            bbox = item.get("bbox") or {}

            db.execute(
                """
                UPDATE pod_document_awbs
                SET
                    confidence = %s,
                    remark = %s,
                    remark_confidence = %s,
                    bbox_x1 = %s,
                    bbox_y1 = %s,
                    bbox_x2 = %s,
                    bbox_y2 = %s,
                    serial_number = %s,
                    condition_category = %s,
                    condition_detail = %s,
                    extraction_method = %s
                WHERE id = %s
                """,
                (
                    item.get("confidence"),
                    item.get("remark"),
                    item.get("remark_confidence"),
                    bbox.get("x1"),
                    bbox.get("y1"),
                    bbox.get("x2"),
                    bbox.get("y2"),
                    item.get("serial_number"),
                    item.get("condition_category"),
                    item.get("condition_detail"),
                    "OCR",
                    existing[0],
                ),
            )

            updated += 1

        db.connection.commit()

        return {
            "pod_document_id": pod_document_id,
            "pages_processed": len(pages),
            "ocr_pages": ocr_pages,
            "ocr_awbs_found": ocr_awbs,
            "records_updated": updated,
            "records_missing": missing,
        }

    except Exception:
        db.connection.rollback()
        raise

    finally:
        db.close()


# ============================================================
# FIND POD BY AWB
# ============================================================


def find_pods_by_awb(
    awb: str,
) -> list[dict]:
    awb = str(awb).strip()

    if not awb:
        return []

    db = Database()

    try:
        rows = db.execute(
            """
            SELECT
                p.id AS pod_document_id,
                p.original_filename,
                p.file_hash,
                p.page_count,
                p.created_at,
                p.receiver_name,
                p.delivery_date,
                p.signature_detected,
                a.awb,
                a.source_page,
                a.extraction_method,
                a.matched
            FROM pod_document_awbs a
            INNER JOIN pod_documents p
                ON p.id = a.pod_document_id
            WHERE a.awb = %s
            ORDER BY
                p.created_at DESC,
                a.source_page
            """,
            (awb,),
        )

        return [
            {
                "pod_document_id": row[0],
                "original_filename": row[1],
                "file_hash": row[2],
                "page_count": row[3],
                "created_at": row[4],
                "receiver_name": row[5],
                "delivery_date": row[6],
                "signature_detected": (None if row[7] is None else bool(row[7])),
                "awb": row[8],
                "source_page": row[9],
                "extraction_method": row[10],
                "shipment_matched": bool(row[11]),
            }
            for row in rows
        ]

    finally:
        db.close()


# ============================================================
# LIST AWBS
# ============================================================


def list_pod_awbs(
    pod_document_id: int,
) -> list[dict]:
    db = Database()

    try:
        rows = db.execute(
            """
            SELECT
                awb,
                source_page,
                extraction_method,
                matched,
                confidence,
                remark,
                remark_confidence,
                bbox_x1,
                bbox_y1,
                bbox_x2,
                bbox_y2
            FROM pod_document_awbs
            WHERE pod_document_id = %s
            ORDER BY source_page, id
            """,
            (pod_document_id,),
        )

        return [
            {
                "awb": row[0],
                "source_page": row[1],
                "extraction_method": row[2],
                "shipment_matched": bool(row[3]),
                "confidence": row[4],
                "remark": row[5],
                "remark_confidence": row[6],
                "bbox": {
                    "x1": row[7],
                    "y1": row[8],
                    "x2": row[9],
                    "y2": row[10],
                },
            }
            for row in rows
        ]

    finally:
        db.close()
