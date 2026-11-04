"""
PDF Metadata & Fingerprint Transplant Engine
Core engine for deep forensic metadata, trailer ID, and XMP transfer.
"""

import os
import re
from typing import Dict, Any, Tuple, Optional, Callable
import pypdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    NameObject,
    DecodedStreamObject,
    ArrayObject,
    ByteStringObject,
    DictionaryObject
)


def _normalize_pdf_id(raw_id) -> Optional[ArrayObject]:
    """Ensures trailer ID is converted into a valid pypdf ArrayObject of ByteStringObjects."""
    if not raw_id:
        return None
    try:
        new_arr = ArrayObject()
        for item in raw_id:
            if isinstance(item, (bytes, bytearray)):
                new_arr.append(ByteStringObject(bytes(item)))
            elif hasattr(item, "original_bytes"):
                new_arr.append(ByteStringObject(item.original_bytes))
            elif isinstance(item, str):
                new_arr.append(ByteStringObject(item.encode("latin1", errors="ignore")))
            else:
                new_arr.append(ByteStringObject(bytes(item)))
        return new_arr
    except Exception:
        return None


def extract_pdf_fingerprint(file_path: str) -> Dict[str, Any]:
    """
    Extracts all metadata, trailer IDs, XMP identifiers, and version info
    for inspection and forensic verification.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    info_summary: Dict[str, Any] = {
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "file_size_kb": round(os.path.getsize(file_path) / 1024, 2),
        "pdf_version": "Unknown",
        "trailer_id_permanent": "None",
        "trailer_id_changing": "None",
        "xmp_doc_id": "None",
        "xmp_instance_id": "None",
        "has_xmp": False,
        "title": "—",
        "author": "—",
        "creator": "—",
        "producer": "—",
        "creation_date": "—",
        "mod_date": "—",
        "page_count": 0,
        "is_encrypted": False,
        "raw_info": {},
    }

    # 1. Read PDF Header version directly from binary prefix
    try:
        with open(file_path, "rb") as f:
            header = f.read(64)
            match = re.search(rb"%PDF-(\d+\.\d+)", header)
            if match:
                info_summary["pdf_version"] = match.group(1).decode("ascii", errors="ignore")
    except Exception:
        pass

    try:
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            info_summary["is_encrypted"] = True
            try:
                reader.decrypt("")
            except Exception:
                pass

        info_summary["page_count"] = len(reader.pages)

        # 2. Extract Trailer /ID
        trailer = reader.trailer
        if trailer and "/ID" in trailer:
            id_array = trailer["/ID"]
            if len(id_array) > 0:
                raw_id0 = id_array[0]
                if isinstance(raw_id0, (bytes, bytearray)):
                    info_summary["trailer_id_permanent"] = raw_id0.hex()
                elif hasattr(raw_id0, "original_bytes"):
                    info_summary["trailer_id_permanent"] = raw_id0.original_bytes.hex()
                else:
                    info_summary["trailer_id_permanent"] = str(raw_id0)
            if len(id_array) > 1:
                raw_id1 = id_array[1]
                if isinstance(raw_id1, (bytes, bytearray)):
                    info_summary["trailer_id_changing"] = raw_id1.hex()
                elif hasattr(raw_id1, "original_bytes"):
                    info_summary["trailer_id_changing"] = raw_id1.original_bytes.hex()
                else:
                    info_summary["trailer_id_changing"] = str(raw_id1)

        # 3. Extract Document Info Dictionary
        meta = reader.metadata
        if meta:
            if meta.get("/Title"):
                info_summary["title"] = str(meta.get("/Title"))
            if meta.get("/Author"):
                info_summary["author"] = str(meta.get("/Author"))
            if meta.get("/Creator"):
                info_summary["creator"] = str(meta.get("/Creator"))
            if meta.get("/Producer"):
                info_summary["producer"] = str(meta.get("/Producer"))
            if meta.get("/CreationDate"):
                info_summary["creation_date"] = str(meta.get("/CreationDate"))
            if meta.get("/ModDate"):
                info_summary["mod_date"] = str(meta.get("/ModDate"))
            for k, v in meta.items():
                info_summary["raw_info"][str(k)] = str(v)

        # 4. Extract Raw XMP Metadata Stream
        try:
            root = reader.trailer.get("/Root")
            if root:
                root_obj = root.get_object()
                metadata_indirect = root_obj.get("/Metadata")
                if metadata_indirect:
                    metadata_obj = metadata_indirect.get_object()
                    raw_xmp = metadata_obj.get_data()
                    info_summary["has_xmp"] = True
                    # Extract DocumentID and InstanceID
                    doc_id_match = re.search(
                        rb"DocumentID=['\"]([^'\"]+)['\"]|<xmpMM:DocumentID>([^<]+)</xmpMM:DocumentID>",
                        raw_xmp
                    )
                    if doc_id_match:
                        val = doc_id_match.group(1) or doc_id_match.group(2)
                        info_summary["xmp_doc_id"] = val.decode("utf-8", errors="ignore")

                    inst_id_match = re.search(
                        rb"InstanceID=['\"]([^'\"]+)['\"]|<xmpMM:InstanceID>([^<]+)</xmpMM:InstanceID>",
                        raw_xmp
                    )
                    if inst_id_match:
                        val = inst_id_match.group(1) or inst_id_match.group(2)
                        info_summary["xmp_instance_id"] = val.decode("utf-8", errors="ignore")
        except Exception:
            pass

    except Exception as e:
        info_summary["error"] = str(e)

    return info_summary


def transplant_fingerprint(
    original_pdf_path: str,
    target_pdf_path: str,
    output_pdf_path: str,
    mode: str = "injection",  # "injection" or "grafting"
    copy_trailer_id: bool = True,
    copy_xmp: bool = True,
    copy_info: bool = True,
    copy_catalog_attrs: bool = True,
    sync_page_boxes: bool = False,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> Tuple[bool, str]:
    """
    Performs full transplant of metadata and fingerprints.

    Mode 'injection': Takes target PDF (new text/pages) and injects all original
                      metadata, trailer ID, XMP XML stream, and catalog attributes.
    Mode 'grafting':  Takes original PDF (container) and swaps each page's /Contents
                      and /Resources with target PDF's pages.
    """
    def log(msg: str, percent: int):
        if progress_callback:
            progress_callback(msg, percent)

    try:
        log("Открытие оригинального и целевого PDF...", 10)
        reader_orig = PdfReader(original_pdf_path)
        if reader_orig.is_encrypted:
            try:
                reader_orig.decrypt("")
            except Exception:
                return False, "Оригинальный PDF защищен паролем. Снимите пароль перед переносом."

        reader_target = PdfReader(target_pdf_path)
        if reader_target.is_encrypted:
            try:
                reader_target.decrypt("")
            except Exception:
                return False, "Целевой PDF защищен паролем. Снимите пароль перед переносом."

        writer = PdfWriter()

        if mode == "injection":
            log("Перенос страниц целевого документа с сохранением текста...", 25)
            # Base is the target PDF (with the user's new text & visual content)
            for page in reader_target.pages:
                writer.add_page(page)

            # Preserve target AcroForm if exists
            try:
                target_root = reader_target.trailer.get("/Root")
                if target_root:
                    target_root_obj = target_root.get_object()
                    if "/AcroForm" in target_root_obj:
                        writer._root_object[NameObject("/AcroForm")] = target_root_obj["/AcroForm"]
            except Exception:
                pass

            # If requested, synchronize page dimensions (MediaBox/CropBox) from original
            if sync_page_boxes:
                log("Синхронизация геометрии страниц (MediaBox / CropBox)...", 40)
                for idx in range(min(len(writer.pages), len(reader_orig.pages))):
                    orig_page = reader_orig.pages[idx]
                    writer.pages[idx].mediabox = orig_page.mediabox
                    if orig_page.cropbox:
                        writer.pages[idx].cropbox = orig_page.cropbox

            # 2. Copy Catalog (/Root) attributes from original
            if copy_catalog_attrs:
                log("Клонирование параметров каталога и настроек просмотра...", 55)
                try:
                    orig_root = reader_orig.trailer.get("/Root")
                    if orig_root:
                        orig_root_obj = orig_root.get_object()
                        keys_to_clone = [
                            "/ViewerPreferences",
                            "/PageLayout",
                            "/PageMode",
                            "/MarkInfo",
                            "/OutputIntents",
                            "/PieceInfo",
                            "/Lang",
                        ]
                        for key in keys_to_clone:
                            if key in orig_root_obj:
                                writer._root_object[NameObject(key)] = orig_root_obj[key]
                except Exception as e:
                    print(f"Warning copying catalog attributes: {e}")

            # 3. Copy Raw XMP Metadata Stream verbatim
            if copy_xmp:
                log("Клонирование сырого XMP-потока (DocumentID, InstanceID)...", 70)
                try:
                    orig_root = reader_orig.trailer.get("/Root")
                    if orig_root:
                        orig_root_obj = orig_root.get_object()
                        metadata_ref = orig_root_obj.get("/Metadata")
                        if metadata_ref:
                            raw_metadata_obj = metadata_ref.get_object()
                            raw_xmp_bytes = raw_metadata_obj.get_data()
                            xmp_stream = DecodedStreamObject()
                            xmp_stream.set_data(raw_xmp_bytes)
                            xmp_stream[NameObject("/Type")] = NameObject("/Metadata")
                            xmp_stream[NameObject("/Subtype")] = NameObject("/XML")
                            indirect_xmp = writer._add_object(xmp_stream)
                            writer._root_object[NameObject("/Metadata")] = indirect_xmp
                except Exception as e:
                    print(f"Warning copying XMP: {e}")

            # 4. Copy Info Dictionary verbatim (Producer, Creator, Dates, and all custom vendor keys)
            if copy_info and "/Info" in reader_orig.trailer:
                log("Копирование словаря Info (Producer, Creator, даты, кастомные теги)...", 80)
                try:
                    orig_info = reader_orig.trailer["/Info"].get_object()
                    new_info = DictionaryObject()
                    for k, v in orig_info.items():
                        new_info[NameObject(k)] = v
                    writer._info = writer._add_object(new_info)
                except Exception:
                    if reader_orig.metadata:
                        writer.add_metadata(reader_orig.metadata)
            elif copy_info and reader_orig.metadata:
                log("Копирование словаря Info (Producer, Creator, даты)...", 80)
                writer.add_metadata(reader_orig.metadata)

            # 5. Copy Trailer /ID
            if copy_trailer_id and "/ID" in reader_orig.trailer:
                log("Копирование Trailer ID (цифрового отпечатка файла)...", 85)
                normalized_id = _normalize_pdf_id(reader_orig.trailer["/ID"])
                if normalized_id:
                    writer._ID = normalized_id

        elif mode == "grafting":
            log("Инициализация оригинального контейнера структуры PDF...", 30)
            writer.clone_reader_document_root(reader_orig)

            log("Вживление потоков контента (/Contents) и шрифтов (/Resources)...", 50)
            num_pages = min(len(writer.pages), len(reader_target.pages))
            for idx in range(num_pages):
                target_page = reader_target.pages[idx]
                if "/Contents" in target_page:
                    writer.pages[idx][NameObject("/Contents")] = target_page["/Contents"]
                if "/Resources" in target_page:
                    writer.pages[idx][NameObject("/Resources")] = target_page["/Resources"]
                if "/Annots" in target_page:
                    writer.pages[idx][NameObject("/Annots")] = target_page["/Annots"]

            if copy_trailer_id and "/ID" in reader_orig.trailer:
                normalized_id = _normalize_pdf_id(reader_orig.trailer["/ID"])
                if normalized_id:
                    writer._ID = normalized_id

            if copy_info and "/Info" in reader_orig.trailer:
                try:
                    orig_info = reader_orig.trailer["/Info"].get_object()
                    new_info = DictionaryObject()
                    for k, v in orig_info.items():
                        new_info[NameObject(k)] = v
                    writer._info = writer._add_object(new_info)
                except Exception:
                    if reader_orig.metadata:
                        writer.add_metadata(reader_orig.metadata)
            elif copy_info and reader_orig.metadata:
                writer.add_metadata(reader_orig.metadata)
        else:
            return False, f"Неизвестный режим: {mode}"

        log("Запись выходного файла на диск...", 90)
        with open(output_pdf_path, "wb") as f_out:
            writer.write(f_out)

        # 6. Post-process PDF Header Version to match original
        log("Синхронизация версии PDF заголовка...", 95)
        try:
            with open(original_pdf_path, "rb") as f_orig:
                orig_head = f_orig.read(64)
                orig_ver_match = re.search(rb"%PDF-(\d+\.\d+)", orig_head)
                if orig_ver_match:
                    orig_ver = orig_ver_match.group(0)
                    with open(output_pdf_path, "r+b") as f_out:
                        out_head = f_out.read(64)
                        out_ver_match = re.search(rb"%PDF-(\d+\.\d+)", out_head)
                        if out_ver_match and out_ver_match.group(0) != orig_ver:
                            f_out.seek(0)
                            content = f_out.read()
                            patched = re.sub(rb"%PDF-\d+\.\d+", orig_ver, content, count=1)
                            f_out.seek(0)
                            f_out.write(patched)
                            f_out.truncate()
        except Exception:
            pass

        log("Готово! Все данные и цифровые отпечатки успешно перенесены.", 100)
        return True, "Файл успешно создан! Все отпечатки, метаданные и структуры перенесены."

    except Exception as e:
        return False, f"Ошибка при обработке PDF: {str(e)}"
