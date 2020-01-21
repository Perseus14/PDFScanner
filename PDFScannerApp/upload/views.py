from django.shortcuts import render, reverse
from django.views import View
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils.encoding import smart_str

import magic
import os
import ocrmypdf as ocr
from datetime import datetime

# Create your views here.

MEDIA_DIR = settings.MEDIA_ROOT
PDF_DIR = os.path.join(MEDIA_DIR, "pdfs")

if not os.path.isdir(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

if not os.path.isdir(PDF_DIR):
    os.makedirs(PDF_DIR)


class Download(View):
    def get(self, request):
        pdf_name = request.GET["pdf_name"]
        file_path = os.path.join(PDF_DIR, pdf_name)
        if os.path.exists(file_path):
            with open(file_path, "rb") as fh:
                response = HttpResponse(fh.read(), content_type="application/download")
                response[
                    "Content-Disposition"
                ] = "inline; filename=" + os.path.basename(file_path)
                return response
        return Http404


class Success(View):
    template_name = "success.html"

    def convert(self, pdf_filename):
        pdf_filepath = os.path.join(PDF_DIR, pdf_filename)
        error_msg = ""
        if not os.path.isfile(pdf_filepath):
            error_msg = "File not found"
            return False, "", error_msg

        now = datetime.now().strftime("%d%m%Y-%H%M%S")

        new_pdf_filename = pdf_filename[:-4] + now + "_searchable.pdf"
        new_pdf_filepath = os.path.join(PDF_DIR, new_pdf_filename)

        try:
            ocr.ocr(
                input_file=pdf_filepath, output_file=new_pdf_filepath, skip_text=True
            )
        except Exception as e:
            error_msg = "OCR exception occured"
            return False, "", error_msg

        if os.path.isfile(new_pdf_filepath):
            return True, new_pdf_filename, error_msg

        error_msg = "File not found"
        return False, "", error_msg

    def get(self, request):
        pdf_filename = request.GET["pdf_name"]
        print(pdf_filename)
        pdf_filepath = os.path.join(PDF_DIR, pdf_filename)
        if not os.path.isfile(pdf_filepath):
            messages.add_message(
                request, messages.ERROR, "PDF document not found!"
            )
            return HttpResponseRedirect(reverse("upload:home"))

        flag, new_pdf_filename, status_msg = self.convert(pdf_filename)

        # Remove uploaded pdf file
        os.remove(pdf_filepath)

        if not flag:
            messages.add_message(request, messages.ERROR, status_msg)
            return HttpResponseRedirect(reverse("upload:home"))

        json_response = {"pdf_name":new_pdf_filename}

        return JsonResponse(json_response)
  

    def post(self, request):
        pdf_file = request.FILES["pdf_file"]
        mime_type = magic.from_buffer(pdf_file.open().read(1024)).lower()
        if "pdf" not in mime_type:
            messages.add_message(
                request, messages.ERROR, "Please upload a PDF document!"
            )
            return HttpResponseRedirect(reverse("upload:home"))

        fs = FileSystemStorage(PDF_DIR)

        pdf_filename = fs.save(pdf_file.name, pdf_file)
        pdf_filepath = os.path.join(PDF_DIR, pdf_filename)

        #flag, new_pdf_filename, status_msg = self.convert(pdf_filename)

        # Remove uploaded pdf file
        #os.remove(pdf_filepath)

        #if not flag:
        #    messages.add_message(request, messages.ERROR, status_msg)
        #    return HttpResponseRedirect(reverse("upload:home"))
        return render(request, self.template_name, {"pdf_name": pdf_filename})


class Index(View):
    template_name = "index.html"

    def get(self, request):
        return render(request, self.template_name)
