#!/usr/bin/env python3
"""
Here are the steps, with progress bar percentages for each step:

document_to_pixels
- 0%-3%: Convert document into a PDF (skipped if the input file is a PDF)
- 3%-5%: Split PDF into individual pages, and count those pages
- 5%-50%: Convert each page into pixels (each page takes 45/n%, where n is the number of pages)

pixels_to_pdf:
- 50%-95%: Convert each page of pixels into a PDF (each page takes 45/n%, where n is the number of pages)
- 95%-100%: Compress the final PDF
"""

import sys
import subprocess
import glob
import os
import json
import shutil

import magic
from PIL import Image


class DangerzoneConverter:
    def __init__(self):
        pass

    def document_to_pixels(self):
        percentage = 0.0

        conversions = {
            # .pdf
            "application/pdf": {"type": None},
            # .docx
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
                "type": "libreoffice",
                "libreoffice_output_filter": "writer_pdf_Export",
            },
            # .doc
            "application/msword": {
                "type": "libreoffice",
                "libreoffice_output_filter": "writer_pdf_Export",
            },
            # .docm
            "application/vnd.ms-word.document.macroEnabled.12": {
                "type": "libreoffice",
                "libreoffice_output_filter": "writer_pdf_Export",
            },
            # .xlsx
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                "type": "libreoffice",
                "libreoffice_output_filter": "calc_pdf_Export",
            },
            # .xls
            "application/vnd.ms-excel": {
                "type": "libreoffice",
                "libreoffice_output_filter": "calc_pdf_Export",
            },
            # .pptx
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": {
                "type": "libreoffice",
                "libreoffice_output_filter": "impress_pdf_Export",
            },
            # .ppt
            "application/vnd.ms-powerpoint": {
                "type": "libreoffice",
                "libreoffice_output_filter": "impress_pdf_Export",
            },
            # .odt
            "application/vnd.oasis.opendocument.text": {
                "type": "libreoffice",
                "libreoffice_output_filter": "writer_pdf_Export",
            },
            # .odg
            "application/vnd.oasis.opendocument.graphics": {
                "type": "libreoffice",
                "libreoffice_output_filter": "impress_pdf_Export",
            },
            # .odp
            "application/vnd.oasis.opendocument.presentation": {
                "type": "libreoffice",
                "libreoffice_output_filter": "impress_pdf_Export",
            },
            # .ops
            "application/vnd.oasis.opendocument.spreadsheet": {
                "type": "libreoffice",
                "libreoffice_output_filter": "calc_pdf_Export",
            },
            # .jpg
            "image/jpeg": {"type": "convert"},
            # .gif
            "image/gif": {"type": "convert"},
            # .png
            "image/png": {"type": "convert"},
            # .tif
            "image/tiff": {"type": "convert"},
            "image/x-tiff": {"type": "convert"},
        }

        # Detect MIME type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file("/tmp/input_file")

        # Validate MIME type
        if mime_type not in conversions:
            self.output(True, "The document format is not supported", percentage)
            return 1

        # Convert input document to PDF
        conversion = conversions[mime_type]
        if conversion["type"] is None:
            pdf_filename = "/tmp/input_file"
        elif conversion["type"] == "libreoffice":
            self.output(False, "Converting to PDF using LibreOffice", percentage)
            args = [
                "libreoffice",
                "--headless",
                "--convert-to",
                f"pdf:{conversion['libreoffice_output_filter']}",
                "--outdir",
                "/tmp",
                "/tmp/input_file",
            ]
            try:
                p = subprocess.run(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                self.output(
                    True,
                    "Error converting document to PDF, LibreOffice timed out after 60 seconds",
                    percentage,
                )
                return 1

            if p.returncode != 0:
                self.output(
                    True,
                    f"Conversion to PDF with LibreOffice failed",
                    percentage,
                )
                return 1
            pdf_filename = "/tmp/input_file.pdf"
        elif conversion["type"] == "convert":
            self.output(False, "Converting to PDF using GraphicsMagick", percentage)
            args = [
                "gm",
                "convert",
                "/tmp/input_file",
                "/tmp/input_file.pdf",
            ]
            try:
                p = subprocess.run(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                self.output(
                    True,
                    "Error converting document to PDF, GraphicsMagick timed out after 60 seconds",
                    percentage,
                )
                return 1
            if p.returncode != 0:
                self.output(
                    True,
                    "Conversion to PDF with GraphicsMagick failed",
                    percentage,
                )
                return 1
            pdf_filename = "/tmp/input_file.pdf"
        else:
            self.output(
                True,
                "Invalid conversion type",
                percentage,
            )
            return 1

        percentage += 3

        # Separate PDF into pages
        self.output(
            False,
            "Separating document into pages",
            percentage,
        )
        args = ["pdftk", pdf_filename, "burst", "output", "/tmp/page-%d.pdf"]
        try:
            p = subprocess.run(
                args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60
            )
        except subprocess.TimeoutExpired:
            self.output(
                True,
                "Error separating document into pages, pdfseparate timed out after 60 seconds",
                percentage,
            )
            return 1
        if p.returncode != 0:
            self.output(
                True,
                "Separating document into pages failed",
                percentage,
            )
            return 1

        page_filenames = glob.glob("/tmp/page-*.pdf")

        percentage += 2

        # Convert to RGB pixel data
        percentage_per_page = 45.0 / len(page_filenames)
        for page in range(1, len(page_filenames) + 1):
            pdf_filename = f"/tmp/page-{page}.pdf"
            png_filename = f"/tmp/page-{page}.png"
            rgb_filename = f"/tmp/page-{page}.rgb"
            width_filename = f"/tmp/page-{page}.width"
            height_filename = f"/tmp/page-{page}.height"
            filename_base = f"/tmp/page-{page}"

            self.output(
                False,
                f"Converting page {page}/{len(page_filenames)} to pixels",
                percentage,
            )

            # Convert to png
            try:
                p = subprocess.run(
                    ["pdftocairo", pdf_filename, "-png", "-singlefile", filename_base],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                self.output(
                    True,
                    "Error converting from PDF to PNG, pdftocairo timed out after 60 seconds",
                    percentage,
                )
                return 1
            if p.returncode != 0:
                self.output(
                    True,
                    "Conversion from PDF to PNG failed",
                    percentage,
                )
                return 1

            # Save the width and height
            im = Image.open(png_filename)
            width, height = im.size
            with open(width_filename, "w") as f:
                f.write(str(width))
            with open(height_filename, "w") as f:
                f.write(str(height))

            # Convert to RGB pixels
            try:
                p = subprocess.run(
                    [
                        "gm",
                        "convert",
                        png_filename,
                        "-depth",
                        "8",
                        f"rgb:{rgb_filename}",
                    ],
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                self.output(
                    True,
                    "Error converting from PNG to pixels, convert timed out after 60 seconds",
                    percentage,
                )
                return 1
            if p.returncode != 0:
                self.output(
                    True,
                    "Conversion from PNG to RGB failed",
                    percentage,
                )
                return 1

            # Delete the png
            os.remove(png_filename)

            percentage += percentage_per_page

        self.output(
            False,
            "Converted document to pixels",
            percentage,
        )

        # Move converted files into /dangerzone
        for filename in (
            glob.glob("/tmp/page-*.rgb")
            + glob.glob("/tmp/page-*.width")
            + glob.glob("/tmp/page-*.height")
        ):
            shutil.move(filename, "/dangerzone")

        return 0

    def pixels_to_pdf(self):
        percentage = 50.0

        num_pages = len(glob.glob("/dangerzone/page-*.rgb"))

        # Convert RGB files to PDF files
        percentage_per_page = 45.0 / num_pages
        for page in range(1, num_pages + 1):
            filename_base = f"/dangerzone/page-{page}"
            rgb_filename = f"{filename_base}.rgb"
            width_filename = f"{filename_base}.width"
            height_filename = f"{filename_base}.height"
            png_filename = f"/tmp/page-{page}.png"
            ocr_filename = f"/tmp/page-{page}"
            pdf_filename = f"/tmp/page-{page}.pdf"

            with open(width_filename) as f:
                width = f.read().strip()
            with open(height_filename) as f:
                height = f.read().strip()

            if os.environ.get("OCR") == "1":
                # OCR the document
                self.output(
                    False,
                    f"Converting page {page}/{num_pages} from pixels to searchable PDF",
                    percentage,
                )

                args = [
                    "gm",
                    "convert",
                    "-size",
                    f"{width}x{height}",
                    "-depth",
                    "8",
                    f"rgb:{rgb_filename}",
                    f"png:{png_filename}",
                ]
                try:
                    p = subprocess.run(
                        args,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=120,
                    )
                except subprocess.TimeoutExpired:
                    self.output(
                        True,
                        "Error converting pixels to PNG, convert timed out after 120 seconds",
                        percentage,
                    )
                    return 1
                if p.returncode != 0:
                    self.output(
                        True,
                        f"Page {page}/{num_pages} conversion to PNG failed",
                        percentage,
                    )
                    return 1

                args = [
                    "tesseract",
                    png_filename,
                    ocr_filename,
                    "-l",
                    os.environ.get("OCR_LANGUAGE"),
                    "--dpi",
                    "70",
                    "pdf",
                ]
                try:
                    p = subprocess.run(
                        args,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=120,
                    )
                except subprocess.TimeoutExpired:
                    self.output(
                        True,
                        "Error converting PNG to searchable PDF, tesseract timed out after 120 seconds",
                        percentage,
                    )
                    return 1
                if p.returncode != 0:
                    self.output(
                        True,
                        f"Page {page}/{num_pages} OCR failed",
                        percentage,
                    )
                    return 1

            else:
                # Don't OCR
                self.output(
                    False,
                    f"Converting page {page}/{num_pages} from pixels to PDF",
                    percentage,
                )

                args = [
                    "gm",
                    "convert",
                    "-size",
                    f"{width}x{height}",
                    "-depth",
                    "8",
                    f"rgb:{rgb_filename}",
                    f"pdf:{pdf_filename}",
                ]
                try:
                    p = subprocess.run(
                        args,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=120,
                    )
                except subprocess.TimeoutExpired:
                    self.output(
                        True,
                        "Error converting RGB to PDF, convert timed out after 120 seconds",
                        percentage,
                    )
                    return 1
                if p.returncode != 0:
                    self.output(
                        True,
                        f"Page {page}/{num_pages} conversion to PDF failed",
                        percentage,
                    )
                    return 1

            percentage += percentage_per_page

        # Merge pages into a single PDF
        self.output(
            False,
            f"Merging {num_pages} pages into a single PDF",
            percentage,
        )
        args = ["pdfunite"]
        for page in range(1, num_pages + 1):
            args.append(f"/tmp/page-{page}.pdf")
        args.append(f"/tmp/safe-output.pdf")
        try:
            p = subprocess.run(
                args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120
            )
        except subprocess.TimeoutExpired:
            self.output(
                True,
                "Error merging pages into a single PDF, pdfunite timed out after 120 seconds",
                percentage,
            )
            return 1
        if p.returncode != 0:
            self.output(
                True,
                "Merging pages into a single PDF failed",
                percentage,
            )
            return 1

        percentage += 2

        # Compress
        self.output(
            False,
            f"Compressing PDF",
            percentage,
        )
        compress_timeout = num_pages * 3
        try:
            p = subprocess.run(
                ["ps2pdf", "/tmp/safe-output.pdf", "/tmp/safe-output-compressed.pdf"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=compress_timeout,
            )
        except subprocess.TimeoutExpired:
            self.output(
                True,
                f"Error compressing PDF, ps2pdf timed out after {compress_timeout} seconds",
                percentage,
            )
            return 1
        if p.returncode != 0:
            self.output(
                True,
                f"Compressing PDF failed",
                percentage,
            )
            return 1

        percentage = 100.0
        self.output(False, "Safe PDF created", percentage)

        # Move converted files into /safezone
        shutil.move("/tmp/safe-output.pdf", "/safezone")
        shutil.move("/tmp/safe-output-compressed.pdf", "/safezone")

        return 0

    def output(self, error, text, percentage):
        print(json.dumps({"error": error, "text": text, "percentage": int(percentage)}))
        sys.stdout.flush()


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} [document-to-pixels]|[pixels-to-pdf]")
        return -1

    converter = DangerzoneConverter()

    if sys.argv[1] == "document-to-pixels":
        return converter.document_to_pixels()

    if sys.argv[1] == "pixels-to-pdf":
        return converter.pixels_to_pdf()

    return -1


if __name__ == "__main__":
    sys.exit(main())
