"""
Comprehensive test script for PDF Metadata & Fingerprint Transplant Engine
"""

import os
from engine import extract_pdf_fingerprint, transplant_fingerprint
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject, ArrayObject, ByteStringObject

def create_sample_files():
    # 1. Create a rich Original PDF (simulating an official bank statement, certificate, or invoice)
    orig_writer = PdfWriter()
    page = orig_writer.add_blank_page(width=595, height=842)
    
    # Add metadata
    orig_writer.add_metadata({
        "/Title": "Official Original Document 2023",
        "/Author": "Corporate Issuer Bank LLC",
        "/Subject": "Financial Statement & Verification",
        "/Creator": "Adobe InDesign 18.2 (Windows)",
        "/Producer": "Adobe PDF Library 16.0.3",
        "/CreationDate": "D:20220815143022+03'00'",
        "/ModDate": "D:20220815143022+03'00'",
    })
    
    # Add Trailer ID
    orig_writer._ID = ArrayObject([
        ByteStringObject(b"\xaa\xbb\xcc\xdd\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c"),
        ByteStringObject(b"\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff\x00")
    ])
    
    # Add XMP Stream
    xmp_raw = b"""<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"
    xmlns:pdf="http://ns.adobe.com/pdf/1.3/"
    xmpMM:DocumentID="uuid:4a5b6c7d-8e9f-0123-4567-89abcdef0123"
    xmpMM:InstanceID="uuid:9f8e7d6c-5b4a-3210-fedc-ba9876543210"
    pdf:Producer="Adobe PDF Library 16.0.3"/>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""
    
    xmp_stream = DecodedStreamObject()
    xmp_stream.set_data(xmp_raw)
    xmp_stream[NameObject("/Type")] = NameObject("/Metadata")
    xmp_stream[NameObject("/Subtype")] = NameObject("/XML")
    indirect_xmp = orig_writer._add_object(xmp_stream)
    orig_writer._root_object[NameObject("/Metadata")] = indirect_xmp
    
    with open("sample_original.pdf", "wb") as f:
        orig_writer.write(f)
        
    # 2. Create Target PDF (the user's modified file, created e.g. from Chrome or LibreOffice with new text)
    target_writer = PdfWriter()
    p2 = target_writer.add_blank_page(width=595, height=842)
    target_writer.add_metadata({
        "/Title": "My Edited Document",
        "/Creator": "Google Chrome Headless",
        "/Producer": "Skia/PDF m120",
    })
    target_writer._ID = ArrayObject([ByteStringObject(b"target_id_111111"), ByteStringObject(b"target_id_222222")])
    with open("sample_target.pdf", "wb") as f:
        target_writer.write(f)
        
    print("Sample PDFs created successfully.")

def run_tests():
    create_sample_files()
    
    print("\n--- TEST: Extract Fingerprints ---")
    orig_fp = extract_pdf_fingerprint("sample_original.pdf")
    print("Original FP:", {k: v for k, v in orig_fp.items() if k in ("producer", "creator", "trailer_id_permanent", "xmp_doc_id")})
    
    target_fp = extract_pdf_fingerprint("sample_target.pdf")
    print("Target FP Before:", {k: v for k, v in target_fp.items() if k in ("producer", "creator", "trailer_id_permanent", "xmp_doc_id")})
    
    print("\n--- TEST: Mode 'injection' ---")
    ok, msg = transplant_fingerprint("sample_original.pdf", "sample_target.pdf", "output_injected.pdf", mode="injection")
    print("Injection Result:", ok, msg)
    assert ok, msg
    
    out_fp = extract_pdf_fingerprint("output_injected.pdf")
    print("Injected Output FP:", {k: v for k, v in out_fp.items() if k in ("producer", "creator", "trailer_id_permanent", "xmp_doc_id")})
    
    assert out_fp["producer"] == orig_fp["producer"], "Producer mismatch!"
    assert out_fp["creator"] == orig_fp["creator"], "Creator mismatch!"
    assert out_fp["trailer_id_permanent"] == orig_fp["trailer_id_permanent"], "Permanent ID mismatch!"
    assert out_fp["trailer_id_changing"] == orig_fp["trailer_id_changing"], "Changing ID mismatch!"
    assert out_fp["xmp_doc_id"] == orig_fp["xmp_doc_id"], "XMP DocumentID mismatch!"
    print(">> Mode 'injection' PASSED 100%!")
    
    print("\n--- TEST: Mode 'grafting' ---")
    ok2, msg2 = transplant_fingerprint("sample_original.pdf", "sample_target.pdf", "output_grafted.pdf", mode="grafting")
    print("Grafting Result:", ok2, msg2)
    assert ok2, msg2
    
    out_fp2 = extract_pdf_fingerprint("output_grafted.pdf")
    print("Grafted Output FP:", {k: v for k, v in out_fp2.items() if k in ("producer", "creator", "trailer_id_permanent", "xmp_doc_id")})
    assert out_fp2["producer"] == orig_fp["producer"], "Producer mismatch!"
    assert out_fp2["creator"] == orig_fp["creator"], "Creator mismatch!"
    assert out_fp2["trailer_id_permanent"] == orig_fp["trailer_id_permanent"], "Permanent ID mismatch!"
    print(">> Mode 'grafting' PASSED 100%!")

if __name__ == "__main__":
    run_tests()
