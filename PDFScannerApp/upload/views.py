from django.shortcuts import render, reverse
from django.views import View
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils.encoding import smart_str

import magic
import os
#import ocrmypdf as ocr
# Create your views here.

MEDIA_DIR = settings.MEDIA_ROOT
PDF_DIR = os.path.join(MEDIA_DIR, "pdfs")

class Success(View):
    template_name = "success.html"

    def convert(self, pdf_filename):
        pdf_filepath = os.path.join(PDF_DIR, pdf_filename)
        if not os.path.isfile(pdf_filepath):
            return False, ""

        new_pdf_filename = pdf_filename[:-4] + "_searchable.pdf"
        new_pdf_filepath = os.path.join(PDF_DIR, new_pdf_filename)

        #ocr.ocr(input_file=pdf_filepath, output_file=new_pdf_filepath, skip_text=True)

        if os.path.isfile(new_pdf_filepath):
            return True, new_pdf_filepath
        return False, ""

    def post(self, request):
        pdf_file = request.FILES["pdf_file"]
        mime_type = magic.from_buffer(pdf_file.open().read(1024)).lower()
        if 'pdf' not in mime_type:
            messages.add_message(request, messages.ERROR, "Please upload a PDF document!")
            return HttpResponseRedirect(reverse('upload:home'))

        fs = FileSystemStorage(PDF_DIR)
        pdf_filename = fs.save(pdf_file.name, pdf_file)
        flag, new_pdf_filename = self.convert(pdf_filename)
        if not flag:
            messages.add_message(request, messages.ERROR, "Sorry, unable to convert the PDF document!!")
            return HttpResponseRedirect(reverse('upload:home'))

        # new_pdf_filepath = os.path.join(PDF_DIR, new_pdf_filename)

        # response = HttpResponse(content_type='application/force-download')
        # response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(new_pdf_filename)
        # response['X-Sendfile'] = smart_str(new_pdf_filepath)

        return render(request, self.template_name, {"pdf_filepath":new_pdf_filename})

class Index(View):
    template_name = "index.html"

    def get(self, request):
        return render(request, self.template_name)
